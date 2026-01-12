#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Puente Python para Node.js - Sistema CBR de Menús
==================================================
Conecta la web con los módulos CBR actuales:
- Retrieve.py: Recuperación de casos similares
- Adapt.py: Adaptación de menús
- Revise.py: Validación de resultados
- Retain.py: Almacenamiento de casos útiles
"""

import sys
import os
import json

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

# Rutas a bases de datos
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CASE_BASE_PATH = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')


def run_cbr_search(user_input: dict) -> dict:
    """
    Ejecuta una búsqueda CBR completa (Retrieve + Adapt + Revise).
    
    Args:
        user_input: Preferencias del usuario:
            - event_type: Tipo de evento (wedding, congress, family_reunion, etc.)
            - culture: Cultura gastronómica deseada
            - restrictions: Lista de restricciones alimentarias
            - season: Estación del año
            - min_price, max_price: Rango de precios
            - quiere_tarta: Si quiere tarta (para bodas)
            - max_people: Número máximo de personas
            
    Returns:
        Dict con resultado del CBR
    """
    try:
        # Cargar bases de conocimiento
        case_base = load_case_base(CASE_BASE_PATH)
        restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
        
        if not case_base:
            return {
                'success': False,
                'error': 'No se pudo cargar la base de casos'
            }
        
        # ================================================================
        # FASE 1: RETRIEVE
        # ================================================================
        retrieved = retrieve_cases(user_input, case_base)
        
        if not retrieved:
            return {
                'success': False,
                'error': 'No se encontraron casos similares'
            }
        
        best_result = retrieved[0]
        
        # Top 3 casos para mostrar
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
        
        # ================================================================
        # FASE 2: ADAPT
        # ================================================================
        adaptation = adapt_menu(
            best_result, user_input,
            restricciones_db, contexto_db, ontologia_db, pairing_db
        )
        
        adapted_menu = adaptation.get('menu', {})
        
        # Extraer sustituciones
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
                        'action': sub.get('action', 'substituted')
                    })
        
        # ================================================================
        # FASE 3: REVISE
        # ================================================================
        revision = revise_menu(
            adapted_menu,
            user_input.get('restrictions', []),
            user_input.get('culture', ''),
            adaptation_steps=substitutions,
            interactive=False
        )
        
        performance = revision.get('performance', 0.8)
        violations = revision.get('violations', [])
        
        # ================================================================
        # PREPARAR RESULTADO
        # ================================================================
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
                'culture_pending_count': adaptation.get('culture_pending_count', 0)
            },
            'validation': {
                'performance': round(performance * 100, 1),
                'violations': len(violations),
                'violation_details': violations[:5],
                'is_valid': len(violations) == 0
            }
        }
        
        return result
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def run_culture_adjustment(user_input: dict) -> dict:
    """
    Ejecuta un ajuste cultural de segunda ronda.
    
    Args:
        user_input: Debe contener:
            - case_id: ID del caso a ajustar
            - culture_adjustment: 'add' o 'remove'
            - culture_adjustment_target: Cultura objetivo
            - restrictions: Restricciones a mantener
            
    Returns:
        Dict con resultado del ajuste
    """
    try:
        case_id = user_input.get('case_id')
        culture_adjustment = user_input.get('culture_adjustment')
        culture_target = user_input.get('culture_adjustment_target')
        
        if not all([case_id, culture_adjustment, culture_target]):
            return {
                'success': False,
                'error': 'Faltan parámetros: case_id, culture_adjustment, culture_adjustment_target'
            }
        
        # Cargar bases
        case_base = load_case_base(CASE_BASE_PATH)
        restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
        
        # Recuperar caso por ID
        case = retrieve_case_by_id(case_id, case_base, CASE_BASE_PATH)
        
        if not case:
            return {
                'success': False,
                'error': f'Caso {case_id} no encontrado'
            }
        
        # Crear estructura para adapt_menu
        retrieved_result = {
            'case': case,
            'compliance': {},
            'user_restrictions': user_input.get('restrictions', [])
        }
        
        # Ejecutar adaptación cultural
        adaptation = adapt_menu(
            retrieved_result, user_input,
            restricciones_db, contexto_db, ontologia_db, pairing_db
        )
        
        if adaptation.get('is_culture_adjustment'):
            return {
                'success': True,
                'adjusted': adaptation.get('adjusted', False),
                'message': adaptation.get('message', ''),
                'adjustment_details': adaptation.get('adjustment_details', {}),
                'menu': adaptation.get('menu', {})
            }
        else:
            return {
                'success': False,
                'error': 'No se pudo aplicar el ajuste cultural'
            }
            
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def run_retain(user_input: dict) -> dict:
    """
    Evalúa y potencialmente guarda un caso en la base.
    
    Args:
        user_input: Debe contener:
            - menu: El menú adaptado
            - original_input: El input original del usuario
            - adaptation_steps: Pasos de adaptación
            - revision: Resultado de la revisión
            - user_feedback: Puntuación del usuario (1-5)
            
    Returns:
        Dict con resultado de retain
    """
    try:
        case_base = load_case_base(CASE_BASE_PATH)
        
        menu = user_input.get('menu', {})
        original_input = user_input.get('original_input', {})
        adaptation_steps = user_input.get('adaptation_steps', [])
        revision = user_input.get('revision', {})
        
        # Añadir feedback del usuario
        user_rating = user_input.get('user_feedback', 3)
        revision['user_feedback'] = user_rating / 5.0  # Normalizar a 0-1
        
        retention = retain_case(
            menu, original_input, adaptation_steps, revision,
            case_base=case_base, filepath=CASE_BASE_PATH
        )
        
        return {
            'success': True,
            'case_saved': retention.get('case_saved', False),
            'usefulness': retention.get('usefulness', 0),
            'reason': retention.get('reason', '')
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Punto de entrada para llamadas desde Node.js."""
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'No input provided'}))
        sys.exit(1)
    
    try:
        input_data = json.loads(sys.argv[1])
        action = input_data.get('action', 'search')
        
        if action == 'search':
            result = run_cbr_search(input_data.get('preferences', {}))
        elif action == 'adjust':
            result = run_culture_adjustment(input_data.get('preferences', {}))
        elif action == 'retain':
            result = run_retain(input_data.get('data', {}))
        else:
            result = {'success': False, 'error': f'Unknown action: {action}'}
        
        print(json.dumps(result, ensure_ascii=False))
        
    except json.JSONDecodeError as e:
        print(json.dumps({'success': False, 'error': f'Invalid JSON: {e}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
