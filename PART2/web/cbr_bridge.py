#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Puente Python para Node.js - Sistema CBR de Menús
==================================================
Recibe preferencias en JSON, ejecuta CBR y devuelve resultado en JSON.
"""

import sys
import os
import json

# Añadir directorio padre al path para importar CBREngine_Complete
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CBREngine_Complete import (
    load_all_databases,
    retrieve_similar_menus,
    reuse_menu,
    revise_menu,
    calculate_similarity
)

def serialize_substitution(sub):
    """Convierte Substitution a dict serializable"""
    return {
        'original': sub.original,
        'substitute': sub.substitute,
        'type': sub.adaptation_type.value,
        'course': sub.course,
        'notes': sub.notes
    }

def serialize_process_adaptation(proc):
    """Convierte ProcessAdaptation a dict serializable"""
    return {
        'original_method': proc.original_method,
        'new_method': proc.new_method,
        'course': proc.course,
        'execution': proc.execution
    }

def run_cbr(preferences):
    """Ejecuta el sistema CBR y devuelve resultado JSON"""
    try:
        # Cargar bases de datos
        databases = load_all_databases()
        
        # FASE 1: RETRIEVE
        similar_menus = retrieve_similar_menus(preferences, databases['menus'], top_k=3)
        
        if not similar_menus:
            return {
                'success': False,
                'error': 'No se encontraron menús similares'
            }
        
        best_menu, best_similarity = similar_menus[0]
        
        # Top 3 para mostrar
        top_menus = []
        for menu, sim in similar_menus:
            top_menus.append({
                'menu_id': menu.get('menu_id'),
                'menu_name': menu.get('menu_name'),
                'similarity': round(sim * 100, 1),
                'culture': menu.get('features', {}).get('cultura', 'N/A'),
                'style': menu.get('features', {}).get('estilo_cocina', 'N/A')
            })
        
        # FASE 2: REUSE
        adapted_menu, substitutions, process_adaptations = reuse_menu(
            best_menu, preferences, databases
        )
        
        # FASE 3: REVISE
        is_valid, critical_issues, warnings = revise_menu(
            adapted_menu, preferences, substitutions
        )
        
        # Preparar cursos con ingredientes
        courses = {}
        for course_name in ['starter', 'main', 'dessert']:
            if course_name in adapted_menu.get('courses', {}):
                course = adapted_menu['courses'][course_name]
                courses[course_name] = {
                    'title': course.get('title', 'N/A'),
                    'price': course.get('price_per_serving', 0),
                    'ingredients': course.get('ingredients', [])[:10],
                    'ready_time': course.get('ready_in_minutes', 0)
                }
        
        # Preparar características
        features = adapted_menu.get('features', {})
        
        result = {
            'success': True,
            'menu': {
                'menu_id': adapted_menu.get('menu_id'),
                'menu_name': adapted_menu.get('menu_name'),
                'courses': courses,
                'total_price': features.get('total_price_per_serving', 0),
                'avg_time': features.get('avg_ready_time_minutes', 0),
                'season': features.get('season', 'N/A'),
                'wine_pairing': features.get('wine_pairing', 'N/A'),
                'culture': features.get('cultura', 'N/A'),
                'style': features.get('estilo_cocina', 'N/A'),
                'certifications': {
                    'is_vegan': features.get('is_vegan', False),
                    'is_vegetarian': features.get('is_vegetarian', False),
                    'is_gluten_free': features.get('is_gluten_free', False),
                    'is_dairy_free': features.get('is_dairy_free', False),
                    'is_kosher': features.get('is_kosher', False),
                    'is_halal': features.get('is_halal', False)
                }
            },
            'similarity': round(best_similarity * 100, 1),
            'top_menus': top_menus,
            'adaptations': {
                'substitutions': [serialize_substitution(s) for s in substitutions],
                'process_changes': [serialize_process_adaptation(p) for p in process_adaptations],
                'total_changes': len(substitutions) + len(process_adaptations)
            },
            'validation': {
                'is_valid': is_valid,
                'critical_issues': critical_issues,
                'warnings': warnings
            }
        }
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'success': False, 'error': 'No preferences provided'}))
        sys.exit(1)
    
    try:
        preferences = json.loads(sys.argv[1])
        result = run_cbr(preferences)
        print(json.dumps(result, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(json.dumps({'success': False, 'error': f'Invalid JSON: {e}'}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}))
        sys.exit(1)
