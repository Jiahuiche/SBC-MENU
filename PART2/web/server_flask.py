#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Servidor Flask para Sistema CBR de Menús Gastronómicos
=======================================================
Alternativa a Node.js usando Python/Flask

Para ejecutar:
    python server_flask.py

Luego abrir: http://localhost:3000
"""

import os
import sys
import json
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

# Añadir directorio CBR al path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CBR_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), 'CBR')
sys.path.insert(0, CBR_DIR)

from Retrieve import load_case_base, retrieve_cases, retrieve_case_by_id
from Adapt import load_all_knowledge_bases, adapt_menu
from Revise import revise_menu
from Retain import retain_case
from case_usefulness import (
    calculate_similarity_to_case_base,
    calculate_novelty_score,
    calculate_trace_score,
    calculate_case_usefulness
)

# Configuración
app = Flask(__name__, static_folder='public', static_url_path='')
PORT = 3000

# Rutas
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CASE_BASE_PATH = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
SESSIONS_FILE = os.path.join(DATA_DIR, 'sessions.json')

# Asegurar que existe el directorio de datos
os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(SESSIONS_FILE):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump({'sessions': {}}, f)


def read_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ============================================================================
# RUTAS ESTÁTICAS
# ============================================================================

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')


@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory('public/css', path)


@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory('public/js', path)


# ============================================================================
# API: CBR BÚSQUEDA
# ============================================================================

@app.route('/api/cbr/search', methods=['POST'])
def cbr_search():
    try:
        data = request.get_json()
        session_id = data.get('sessionId', f'session_{datetime.now().timestamp()}')
        preferences = data.get('preferences', {})
        
        print(f'🔍 Búsqueda CBR recibida: {preferences}')
        
        # Cargar bases de conocimiento
        case_base = load_case_base(CASE_BASE_PATH)
        restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
        
        if not case_base:
            return jsonify({'success': False, 'error': 'No se pudo cargar la base de casos'})
        
        # FASE 1: RETRIEVE
        retrieved = retrieve_cases(preferences, case_base)
        
        if not retrieved:
            return jsonify({'success': False, 'error': 'No se encontraron casos similares'})
        
        best_result = retrieved[0]
        
        # Top 3 casos
        top_cases = []
        for r in retrieved[:3]:
            case = r['case']
            top_cases.append({
                'case_id': case.get('id_caso'),
                'score': round(r['score'], 3),
                'event_type': case.get('problema', {}).get('tipo_evento', 'N/A'),
                'culture': case.get('problema', {}).get('cultura_preferible', 'N/A'),
                'restrictions': case.get('problema', {}).get('restricciones_alimentarias', [])
            })
        
        # FASE 2: ADAPT
        adaptation = adapt_menu(
            best_result, preferences,
            restricciones_db, contexto_db, ontologia_db, pairing_db
        )
        
        adapted_menu = adaptation.get('menu', {})
        
        # Extraer sustituciones CON JUSTIFICACIONES COMPLETAS
        substitutions = []
        for course_name, course_data in adapted_menu.get('courses', {}).items():
            if isinstance(course_data, dict):
                _adaptation = course_data.get('_adaptation', {})
                for sub in _adaptation.get('substitutions', []):
                    substitutions.append({
                        'course': course_name,
                        'original': sub.get('original'),
                        'substitute': sub.get('substitute'),
                        'reason': sub.get('reason', []),
                        'action': sub.get('action', 'substituted'),
                        'search_attempts': sub.get('search_attempts', []),
                        'candidates_found': sub.get('candidates_found', 0),
                        'note': sub.get('note', ''),
                        'warning': sub.get('warning', '')
                    })
        
        # Extraer información de cultura pendiente
        culture_info = []
        for course_name, course_data in adapted_menu.get('courses', {}).items():
            if isinstance(course_data, dict):
                _adaptation = course_data.get('_adaptation', {})
                cult_adapt = _adaptation.get('culture_adaptation', {})
                if cult_adapt.get('culture_pending_next_rounds', 0) > 0:
                    culture_info.append({
                        'course': course_name,
                        'pending_count': cult_adapt.get('culture_pending_next_rounds', 0),
                        'pending_ingredients': cult_adapt.get('pending_ingredients', []),
                        'changed_this_round': cult_adapt.get('culture_changed_this_round', 0)
                    })
        
        # FASE 3: REVISE
        revision = revise_menu(
            adapted_menu,
            preferences.get('restrictions', []),
            preferences.get('culture', ''),
            adaptation_steps=substitutions,
            interactive=False
        )
        
        performance = revision.get('performance', 0.8)
        violations = revision.get('violations', [])
        
        # Preparar resultado
        courses_output = {}
        for course_name in ['starter', 'main', 'dessert']:
            if course_name in adapted_menu.get('courses', {}):
                course = adapted_menu['courses'][course_name]
                courses_output[course_name] = {
                    'title': course.get('title', 'Sin título'),
                    'ingredients': course.get('ingredients', []),
                    'price': course.get('price_per_serving', 0),
                    'restrictions': course.get('restrictions', [])
                }
        
        features = adapted_menu.get('features', {})
        
        result = {
            'success': True,
            'sessionId': session_id,
            'case_id': best_result['case'].get('id_caso'),
            'score': round(best_result['score'], 3),
            'top_cases': top_cases,
            'menu': {
                'courses': courses_output,
                'season': features.get('season', 'any'),
                'culture': features.get('dominant_culture', 'N/A'),
                'price_per_serving': features.get('total_price_per_serving', 0),
                'restrictions': features.get('common_dietary_restrictions', [])
            },
            'adaptation': {
                'adapted': adaptation.get('adapted', False),
                'substitutions': substitutions,
                'total_changes': len(substitutions),
                'culture_pending': adaptation.get('culture_pending', False),
                'culture_pending_count': adaptation.get('culture_pending_count', 0),
                'culture_pending_ingredients': adaptation.get('culture_pending_ingredients', []),
                'culture_info_by_course': culture_info,
                'restrictions_adapted': adaptation.get('restrictions_adapted', []),
                'culture_adapted': adaptation.get('culture_adapted'),
                'adaptation_note': adaptation.get('culture_adaptation_note')
            },
            'validation': {
                'performance': round(performance * 100, 1),
                'violations': len(violations),
                'violation_details': violations[:5],
                'is_valid': len(violations) == 0
            }
        }
        
        # Guardar sesión
        sessions = read_json(SESSIONS_FILE)
        if session_id not in sessions['sessions']:
            sessions['sessions'][session_id] = {
                'created': datetime.now().isoformat(),
                'searches': []
            }
        
        sessions['sessions'][session_id]['searches'].append({
            'timestamp': datetime.now().isoformat(),
            'preferences': preferences,
            'case_id': result['case_id'],
            'score': result['score']
        })
        
        write_json(SESSIONS_FILE, sessions)
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f'❌ Error en CBR search: {e}')
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API: AJUSTE CULTURAL
# ============================================================================

@app.route('/api/cbr/adjust', methods=['POST'])
def cbr_adjust():
    try:
        data = request.get_json()
        case_id = data.get('case_id')
        culture_adjustment = data.get('culture_adjustment')
        culture_target = data.get('culture_adjustment_target')
        restrictions = data.get('restrictions', [])
        
        print(f'🔧 Ajuste cultural: {culture_adjustment} -> {culture_target}')
        
        if not all([case_id, culture_adjustment, culture_target]):
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros requeridos'
            })
        
        # Cargar bases
        case_base = load_case_base(CASE_BASE_PATH)
        restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
        
        # Recuperar caso
        case = retrieve_case_by_id(case_id, case_base, CASE_BASE_PATH)
        
        if not case:
            return jsonify({'success': False, 'error': f'Caso {case_id} no encontrado'})
        
        # Ejecutar ajuste
        retrieved_result = {
            'case': case,
            'compliance': {},
            'user_restrictions': restrictions
        }
        
        user_input = {
            'culture_adjustment': culture_adjustment,
            'culture_adjustment_target': culture_target,
            'restrictions': restrictions
        }
        
        adaptation = adapt_menu(
            retrieved_result, user_input,
            restricciones_db, contexto_db, ontologia_db, pairing_db
        )
        
        if adaptation.get('is_culture_adjustment'):
            return jsonify({
                'success': True,
                'adjusted': adaptation.get('adjusted', False),
                'message': adaptation.get('message', ''),
                'adjustment_details': adaptation.get('adjustment_details', {}),
                'menu': adaptation.get('menu', {})
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo aplicar el ajuste cultural'
            })
        
    except Exception as e:
        print(f'❌ Error en ajuste: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# API: EVALUACIÓN Y RETAIN
# ============================================================================

@app.route('/api/cbr/evaluate', methods=['POST'])
def cbr_evaluate():
    try:
        data = request.get_json()
        menu = data.get('menu', {})
        original_input = data.get('original_input', {})
        adaptation_steps = data.get('adaptation_steps', [])
        revision = data.get('revision', {})
        user_feedback = data.get('user_feedback', 3)
        
        print(f'⭐ Evaluación recibida: {user_feedback}/5')
        
        # Cargar base
        case_base = load_case_base(CASE_BASE_PATH)
        
        # Añadir feedback
        revision['user_feedback'] = user_feedback / 5.0
        
        retention = retain_case(
            menu, original_input, adaptation_steps, revision,
            case_base=case_base, filepath=CASE_BASE_PATH
        )
        
        return jsonify({
            'success': True,
            'case_saved': retention.get('case_saved', False),
            'usefulness': retention.get('usefulness', 0),
            'reason': retention.get('reason', '')
        })
        
    except Exception as e:
        print(f'❌ Error en evaluación: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print(f'''
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║      ◆  MAISON CBR - Sistema de Menús Gastronómicos  ◆          ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Servidor Flask activo en: http://localhost:{PORT}                 ║
║                                                                  ║
║  API Endpoints:                                                  ║
║    POST /api/cbr/search    - Búsqueda CBR                        ║
║    POST /api/cbr/adjust    - Ajuste cultural (2ª ronda)          ║
║    POST /api/cbr/evaluate  - Evaluar y guardar caso              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    ''')
    
    app.run(host='0.0.0.0', port=PORT, debug=True)
