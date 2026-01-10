#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA CBR COMPLETO PARA MENÚS GASTRONÓMICOS
==============================================

Pipeline completo del ciclo CBR:
1. INPUT    - Captura preferencias del usuario
2. RETRIEVE - Busca casos similares
3. ADAPT    - Adapta el mejor caso
4. REVISE   - Valida y obtiene feedback
5. RETAIN   - Decide si guardar el caso

Uso:
    python main.py
"""

import os
import sys

# Añadir directorio al path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Importar módulos CBR
from input_module import get_user_restrictions
from Retrieve import load_case_base, retrieve_cases, print_results
from Adapt import adapt_menu, print_adaptation_results, load_all_knowledge_bases
from Revise import revise_menu, print_menu_summary
from Retain import retain_case, get_case_base_stats


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

BASE_DIR = os.path.join(SCRIPT_DIR, '..')
CASE_BASE_PATH = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def print_header(title: str):
    """Imprime un encabezado formateado."""
    print("\n" + "="*70)
    print(f"🔹 {title}")
    print("="*70)


def format_user_input(user_data: dict) -> dict:
    """Convierte datos del input al formato esperado por Retrieve."""
    return {
        'restrictions': user_data.get('restrictions', []),
        'cuisine': user_data.get('cuisine', ''),
        'culture': user_data.get('cuisine', ''),
        'season': user_data.get('season', ''),
        'event_type': user_data.get('event_type', ''),
        'max_people': user_data.get('max_people', 1),
        'min_price': user_data.get('min_price', 0),
        'max_price': user_data.get('max_price', 100)
    }


# ============================================================================
# PIPELINE CBR PRINCIPAL
# ============================================================================

def run_cbr_cycle(user_input: dict) -> dict:
    """
    Ejecuta un ciclo completo de CBR.
    
    Args:
        user_input: Preferencias del usuario
        
    Returns:
        Dict con resultados del ciclo
    """
    results = {
        'success': False,
        'iterations': 0,
        'final_menu': None,
        'case_saved': False
    }
    
    # Cargar bases de conocimiento
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    # Cargar base de casos
    case_base = load_case_base(CASE_BASE_PATH)
    if not case_base:
        print("❌ Error: No se pudo cargar la base de casos")
        return results
    
    # Variables para el ciclo
    current_input = user_input.copy()
    max_iterations = 3
    
    while results['iterations'] < max_iterations:
        results['iterations'] += 1
        print_header(f"ITERACIÓN {results['iterations']} DEL CICLO CBR")
        
        # ====================================================================
        # FASE 1: RETRIEVE
        # ====================================================================
        print_header("FASE RETRIEVE: Búsqueda de Casos Similares")
        
        retrieved = retrieve_cases(current_input, case_base)
        
        if not retrieved:
            print("❌ No se encontraron casos similares")
            return results
        
        print_results(retrieved, top_n=3)
        
        # Tomar el mejor caso
        best_result = retrieved[0]
        best_case = best_result['case']
        compliance = best_result.get('compliance', {})
        
        print(f"\n✅ Mejor caso seleccionado: {best_case.get('id_caso')}")
        print(f"   Score: {best_result['score']}")
        
        # ====================================================================
        # FASE 2: ADAPT
        # ====================================================================
        print_header("FASE ADAPT: Adaptación del Menú")
        
        adaptation_result = adapt_menu(
            retrieved_result=best_result,
            user_input=current_input,
            restricciones_db=restricciones_db,
            contexto_db=contexto_db,
            ontologia_db=ontologia_db,
            pairing_db=pairing_db
        )
        
        print_adaptation_results(adaptation_result)
        
        # Obtener menú adaptado
        adapted_menu = adaptation_result.get('menu', {})
        
        # Extraer pasos de adaptación
        adaptation_steps = []
        for course_name, course_data in adapted_menu.get('courses', {}).items():
            if isinstance(course_data, dict):
                _adaptation = course_data.get('_adaptation', {})
                for sub in _adaptation.get('substitutions', []):
                    adaptation_steps.append(sub)
        
        # ====================================================================
        # FASE 3: REVISE
        # ====================================================================
        print_header("FASE REVISE: Validación y Feedback")
        
        # Mostrar menú propuesto
        print_menu_summary(adapted_menu)
        
        # Validar y obtener feedback
        revision_results = revise_menu(
            adapted_menu=adapted_menu,
            user_restrictions=current_input.get('restrictions', []),
            user_culture=current_input.get('culture', current_input.get('cuisine', '')),
            adaptation_steps=adaptation_steps,
            interactive=True
        )
        
        # ====================================================================
        # FASE 4: RETAIN
        # ====================================================================
        print_header("FASE RETAIN: Decisión de Almacenamiento")
        
        retention_result = retain_case(
            adapted_menu=adapted_menu,
            problema=current_input,
            adaptation_steps=adaptation_steps,
            revision_results=revision_results,
            case_base=case_base,
            threshold=0.5,
            filepath=CASE_BASE_PATH
        )
        
        results['final_menu'] = adapted_menu
        results['case_saved'] = retention_result.get('case_saved', False)
        
        # ====================================================================
        # VERIFICAR SI SE NECESITA OTRA ITERACIÓN
        # ====================================================================
        if revision_results.get('needs_revision', False):
            print("\n" + "="*70)
            print("⚠️ SE REQUIERE NUEVA ADAPTACIÓN")
            print("="*70)
            
            # Añadir nuevas restricciones
            new_restrictions = revision_results.get('new_restrictions', [])
            if new_restrictions:
                for r in new_restrictions:
                    if r not in current_input['restrictions']:
                        current_input['restrictions'].append(r)
                print(f"   Nuevas restricciones: {new_restrictions}")
            
            # Aplicar ajustes culturales
            culture_adjustments = revision_results.get('culture_adjustments', [])
            if culture_adjustments:
                # Por ahora, solo cambiar la cultura preferida
                for adj in culture_adjustments:
                    if adj['action'] == 'add':
                        current_input['culture'] = adj['culture']
                        current_input['cuisine'] = adj['culture']
                print(f"   Ajustes culturales: {culture_adjustments}")
            
            print("\n🔄 Reiniciando ciclo CBR con nuevos parámetros...\n")
            continue
        else:
            # Usuario satisfecho, terminar
            results['success'] = True
            break
    
    return results


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    """Función principal del sistema CBR."""
    print("\n" + "="*70)
    print("🍽️  SISTEMA CBR DE MENÚS GASTRONÓMICOS")
    print("="*70)
    print("Bienvenido al sistema de recomendación de menús.")
    print("Este sistema utiliza Razonamiento Basado en Casos (CBR)")
    print("para generar menús personalizados.")
    print("="*70)
    
    try:
        # PASO 1: Obtener preferencias del usuario
        print_header("PASO 1: CAPTURA DE PREFERENCIAS")
        user_data = get_user_restrictions()
        
        # Formatear input
        user_input = format_user_input(user_data)
        
        # PASO 2: Ejecutar ciclo CBR
        results = run_cbr_cycle(user_input)
        
        # PASO 3: Mostrar resultados finales
        print("\n" + "="*70)
        print("🎉 RESULTADOS FINALES")
        print("="*70)
        
        if results['success']:
            print(f"\n✅ Menú generado exitosamente")
            print(f"   Iteraciones: {results['iterations']}")
            print(f"   Caso guardado: {'Sí' if results['case_saved'] else 'No'}")
            
            if results['final_menu']:
                print_menu_summary(results['final_menu'])
        else:
            print(f"\n⚠️ No se pudo generar un menú satisfactorio")
            print(f"   Iteraciones realizadas: {results['iterations']}")
        
        # Mostrar estadísticas
        print("\n" + "-"*50)
        print("📊 Estadísticas de la Base de Casos:")
        stats = get_case_base_stats()
        for k, v in stats.items():
            if isinstance(v, float):
                print(f"   {k}: {v:.3f}")
            else:
                print(f"   {k}: {v}")
        
        print("\n" + "="*70)
        print("Gracias por usar el Sistema CBR de Menús")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Programa interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MODO DEMO (sin interacción)
# ============================================================================

def demo_mode():
    """Ejecuta una demostración sin interacción del usuario."""
    print("\n" + "="*70)
    print("🎬 MODO DEMO - Sistema CBR de Menús")
    print("="*70)
    
    # Input de ejemplo - caso que requiere adaptación
    user_input = {
        'restrictions': ['vegan', 'gluten-free'],
        'cuisine': 'italian',
        'culture': 'italian',
        'season': 'summer',
        'event_type': 'family',
        'max_people': 10,
        'min_price': 20,
        'max_price': 50
    }
    
    print("\n📋 Preferencias de ejemplo:")
    print(f"   Restricciones: {user_input['restrictions']}")
    print(f"   Cultura: {user_input['cuisine']}")
    print(f"   Temporada: {user_input['season']}")
    
    # Cargar bases
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    case_base = load_case_base(CASE_BASE_PATH)
    
    # RETRIEVE
    print_header("RETRIEVE")
    retrieved = retrieve_cases(user_input, case_base)
    if retrieved:
        best = retrieved[0]
        print(f"Mejor caso: {best['case'].get('id_caso')} (score: {best['score']})")
        
        # Mostrar qué restricciones no cumple
        compliance = best.get('compliance', {})
        if compliance.get('restrictions_not_met'):
            print(f"   Restricciones a adaptar: {compliance['restrictions_not_met']}")
        if compliance.get('culture_not_met'):
            print(f"   Cultura a adaptar: {compliance['culture_not_met']}")
        
        # ADAPT
        print_header("ADAPT")
        adaptation = adapt_menu(best, user_input, restricciones_db, contexto_db, ontologia_db, pairing_db)
        print_adaptation_results(adaptation)
        
        # Extraer pasos de adaptación
        adapted_menu = adaptation.get('menu', {})
        adaptation_steps = []
        for course_name, course_data in adapted_menu.get('courses', {}).items():
            if isinstance(course_data, dict):
                _adaptation = course_data.get('_adaptation', {})
                for sub in _adaptation.get('substitutions', []):
                    adaptation_steps.append(sub)
        
        # REVISE (no interactivo)
        print_header("REVISE")
        revision = revise_menu(
            adapted_menu, 
            user_input['restrictions'],
            user_input['culture'],
            adaptation_steps=adaptation_steps,
            interactive=False
        )
        revision['user_feedback'] = 0.85  # Simular feedback positivo
        print(f"Performance: {revision['performance']:.2%}")
        print(f"Violaciones: {len(revision.get('violations', []))}")
        
        # RETAIN
        print_header("RETAIN")
        retention = retain_case(
            adapted_menu, user_input, adaptation_steps, revision,
            case_base=case_base, filepath=CASE_BASE_PATH
        )
        print(f"Caso guardado: {retention['case_saved']}")
    
    print("\n✅ Demo completada")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--demo':
        demo_mode()
    else:
        main()
