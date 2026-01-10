#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JUEGOS DE PRUEBA - Sistema CBR de Menús
========================================

Ejecuta automáticamente todos los casos de prueba definidos en test_cases.json
y genera un reporte con los resultados.

Uso:
    python juegos_prueba.py           # Ejecutar todos los tests
    python juegos_prueba.py --verbose # Modo verbose con detalles
    python juegos_prueba.py --test ID # Ejecutar un test específico
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Añadir directorio al path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Importar módulos CBR
from Retrieve import load_case_base, retrieve_cases
from Adapt import adapt_menu, load_all_knowledge_bases
from Revise import revise_menu, print_menu_summary
from Retain import retain_case, get_case_base_stats, calculate_similarity_to_base, calculate_novelty, calculate_trace_score, calculate_usefulness


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

BASE_DIR = os.path.join(SCRIPT_DIR, '..')
CASE_BASE_PATH = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')
TEST_CASES_PATH = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'test_cases.json')
RESULTS_PATH = os.path.join(SCRIPT_DIR, 'test_results.json')


# ============================================================================
# FUNCIONES DE CARGA
# ============================================================================

def load_test_cases(filepath: str = TEST_CASES_PATH) -> List[Dict]:
    """Carga los casos de prueba desde el archivo JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('test_cases', [])
    except FileNotFoundError:
        print(f"❌ Archivo de tests no encontrado: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parseando JSON: {e}")
        return []


# ============================================================================
# EJECUCIÓN DE UN TEST
# ============================================================================

def run_single_test(
    test_case: Dict,
    case_base: Dict,
    restricciones_db: Dict,
    contexto_db: Dict,
    ontologia_db: Dict,
    pairing_db: Dict,
    verbose: bool = False,
    save_cases: bool = False
) -> Dict:
    """
    Ejecuta un único caso de prueba.
    
    Args:
        test_case: Caso de prueba con input y expected
        case_base: Base de casos cargada
        restricciones_db, contexto_db, ontologia_db, pairing_db: Bases de conocimiento
        verbose: Si True, muestra información detallada
        save_cases: Si True, permite guardar casos en la base
        
    Returns:
        Dict con resultados del test
    """
    test_id = test_case.get('id', 'UNKNOWN')
    description = test_case.get('description', 'Sin descripción')
    user_input = test_case.get('input', {})
    expected = test_case.get('expected', {})
    
    result = {
        'test_id': test_id,
        'description': description,
        'status': 'PENDING',
        'passed': False,
        'execution_time': 0,
        'phases': {},
        'error': None
    }
    
    start_time = time.time()
    
    try:
        if verbose:
            print(f"\n{'='*60}")
            print(f"🧪 {test_id}: {description}")
            print(f"{'='*60}")
            print(f"   Input: {user_input}")
        
        # ================================================================
        # FASE RETRIEVE
        # ================================================================
        retrieve_start = time.time()
        retrieved = retrieve_cases(user_input, case_base)
        retrieve_time = time.time() - retrieve_start
        
        result['phases']['retrieve'] = {
            'success': len(retrieved) > 0,
            'cases_found': len(retrieved),
            'best_score': retrieved[0]['score'] if retrieved else 0,
            'time': retrieve_time
        }
        
        if verbose:
            print(f"\n   📥 RETRIEVE: {len(retrieved)} casos encontrados")
            if retrieved:
                print(f"      Mejor caso: {retrieved[0]['case'].get('id_caso')} (score: {retrieved[0]['score']:.3f})")
        
        if not retrieved:
            result['status'] = 'NO_CASES_FOUND'
            result['passed'] = not expected.get('should_find_case', True)
            return result
        
        best_result = retrieved[0]
        best_case = best_result['case']
        
        # ================================================================
        # FASE ADAPT
        # ================================================================
        adapt_start = time.time()
        adaptation = adapt_menu(
            best_result, user_input,
            restricciones_db, contexto_db, ontologia_db, pairing_db
        )
        adapt_time = time.time() - adapt_start
        
        adapted_menu = adaptation.get('menu', {})
        
        # Contar sustituciones
        total_substitutions = 0
        adaptation_steps = []
        for course_name, course_data in adapted_menu.get('courses', {}).items():
            if isinstance(course_data, dict):
                _adaptation = course_data.get('_adaptation', {})
                subs = _adaptation.get('substitutions', [])
                total_substitutions += len(subs)
                adaptation_steps.extend(subs)
        
        result['phases']['adapt'] = {
            'success': True,
            'substitutions': total_substitutions,
            'time': adapt_time
        }
        
        if verbose:
            print(f"   🔧 ADAPT: {total_substitutions} sustituciones realizadas")
            print(f"      Tiempo: {adapt_time:.3f}s")
        
        # ================================================================
        # FASE REVISE (sin interacción)
        # ================================================================
        revise_start = time.time()
        revision = revise_menu(
            adapted_menu,
            user_input.get('restrictions', []),
            user_input.get('culture', user_input.get('cuisine', '')),
            adaptation_steps=adaptation_steps,
            interactive=False  # ¡Sin interacción!
        )
        revise_time = time.time() - revise_start
        
        # Simular feedback del usuario basado en performance
        performance = revision.get('performance', 0.8)
        violations = revision.get('violations', [])
        
        # El feedback simulado depende de las violaciones
        if len(violations) == 0:
            simulated_feedback = 0.9
        elif len(violations) <= 2:
            simulated_feedback = 0.7
        else:
            simulated_feedback = 0.5
        
        revision['user_feedback'] = simulated_feedback
        
        result['phases']['revise'] = {
            'success': len(violations) == 0,
            'performance': performance,
            'violations': len(violations),
            'violation_details': violations[:3],  # Máximo 3 para el reporte
            'time': revise_time
        }
        
        if verbose:
            print(f"   ✅ REVISE: Performance {performance:.1%}, {len(violations)} violaciones")
            if violations:
                for v in violations[:3]:
                    print(f"      ⚠️ {v.get('ingredient', 'N/A')}: {v.get('reason', 'N/A')}")
        
        # ================================================================
        # FASE RETAIN (sin guardar por defecto en tests)
        # ================================================================
        retain_start = time.time()
        
        # Para tests, usamos una copia de la base para no modificarla
        if save_cases:
            retention = retain_case(
                adapted_menu, user_input, adaptation_steps, revision,
                case_base=case_base, filepath=CASE_BASE_PATH
            )
        else:
            # Calcular utilidad sin guardar
            # Crear estructura del caso para evaluación
            new_case_struct = {
                'problema': {
                    'restricciones_alimentarias': user_input.get('restrictions', []),
                    'cultura_preferible': user_input.get('culture', user_input.get('cuisine', ''))
                },
                'solucion': adapted_menu
            }
            
            # Calcular métricas individuales
            perf = revision.get('performance', 0.5)
            sim = calculate_similarity_to_base(new_case_struct, case_base)
            nov = calculate_novelty(new_case_struct, case_base)
            trc = calculate_trace_score(adaptation_steps)
            
            # Calcular utilidad
            usefulness = calculate_usefulness(perf, sim, nov, trc)
            
            retention = {
                'case_saved': False,
                'usefulness': usefulness,
                'reason': 'Test mode - no save'
            }
        
        retain_time = time.time() - retain_start
        
        result['phases']['retain'] = {
            'success': True,
            'usefulness': retention.get('usefulness', 0),
            'would_save': retention.get('usefulness', 0) >= 0.5,
            'time': retain_time
        }
        
        if verbose:
            print(f"   💾 RETAIN: Utilidad {retention.get('usefulness', 0):.3f}")
        
        # ================================================================
        # EVALUACIÓN DEL TEST
        # ================================================================
        result['execution_time'] = time.time() - start_time
        
        # Verificar expectativas
        passed = True
        
        # ¿Se esperaba encontrar casos?
        if expected.get('should_find_case', True) and len(retrieved) == 0:
            passed = False
        
        # ¿Score mínimo esperado?
        min_score = expected.get('min_score', 0)
        if best_result['score'] < min_score:
            passed = False
        
        # ¿Sin violaciones requerido?
        if expected.get('no_violations', False) and len(violations) > 0:
            passed = False
        
        result['passed'] = passed
        result['status'] = 'PASSED' if passed else 'FAILED'
        
        if verbose:
            status_icon = "✅" if passed else "❌"
            print(f"\n   {status_icon} Resultado: {result['status']}")
            print(f"   ⏱️ Tiempo total: {result['execution_time']:.3f}s")
        
    except Exception as e:
        result['status'] = 'ERROR'
        result['error'] = str(e)
        result['execution_time'] = time.time() - start_time
        
        if verbose:
            print(f"\n   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    return result


# ============================================================================
# EJECUCIÓN DE TODOS LOS TESTS
# ============================================================================

def run_all_tests(
    verbose: bool = False,
    save_cases: bool = False,
    specific_test: Optional[str] = None
) -> Dict:
    """
    Ejecuta todos los casos de prueba.
    
    Args:
        verbose: Modo verbose
        save_cases: Si guardar casos en la base
        specific_test: ID de test específico a ejecutar
        
    Returns:
        Dict con resumen de resultados
    """
    print("\n" + "="*70)
    print("🧪 JUEGOS DE PRUEBA - Sistema CBR de Menús")
    print("="*70)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Cargar casos de prueba
    test_cases = load_test_cases()
    if not test_cases:
        print("❌ No hay casos de prueba para ejecutar")
        return {'error': 'No test cases found'}
    
    # Filtrar si hay test específico
    if specific_test:
        test_cases = [t for t in test_cases if t.get('id') == specific_test]
        if not test_cases:
            print(f"❌ Test '{specific_test}' no encontrado")
            return {'error': f'Test {specific_test} not found'}
    
    print(f"📋 Tests a ejecutar: {len(test_cases)}")
    
    # Cargar bases de conocimiento
    print("\n⏳ Cargando bases de conocimiento...")
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    # Cargar base de casos (load_case_base devuelve lista de casos)
    case_base = load_case_base(CASE_BASE_PATH)
    if not case_base:
        print("❌ No se pudo cargar la base de casos")
        return {'error': 'Could not load case base'}
    
    print(f"✅ Base de casos cargada: {len(case_base)} casos")
    
    # Ejecutar tests
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_tests': len(test_cases),
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'total_time': 0,
        'test_results': []
    }
    
    print("\n" + "-"*70)
    print("EJECUTANDO TESTS")
    print("-"*70)
    
    for i, test_case in enumerate(test_cases, 1):
        test_id = test_case.get('id', f'TEST_{i}')
        
        if not verbose:
            print(f"\n[{i}/{len(test_cases)}] {test_id}: {test_case.get('description', '')}...")
        
        test_result = run_single_test(
            test_case, case_base,
            restricciones_db, contexto_db, ontologia_db, pairing_db,
            verbose=verbose,
            save_cases=save_cases
        )
        
        results['test_results'].append(test_result)
        results['total_time'] += test_result.get('execution_time', 0)
        
        # Contar resultados
        if test_result['status'] == 'PASSED':
            results['passed'] += 1
            if not verbose:
                print(f"   ✅ PASSED ({test_result['execution_time']:.2f}s)")
        elif test_result['status'] == 'FAILED':
            results['failed'] += 1
            if not verbose:
                print(f"   ❌ FAILED ({test_result['execution_time']:.2f}s)")
        else:
            results['errors'] += 1
            if not verbose:
                print(f"   ⚠️ ERROR: {test_result.get('error', 'Unknown')}")
    
    # Mostrar resumen
    print_summary(results)
    
    # Guardar resultados
    save_results(results)
    
    return results


# ============================================================================
# RESUMEN Y REPORTE
# ============================================================================

def print_summary(results: Dict):
    """Imprime un resumen de los resultados."""
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)
    
    total = results['total_tests']
    passed = results['passed']
    failed = results['failed']
    errors = results['errors']
    
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n   Total tests:  {total}")
    print(f"   ✅ Passed:    {passed} ({pass_rate:.1f}%)")
    print(f"   ❌ Failed:    {failed}")
    print(f"   ⚠️ Errors:    {errors}")
    print(f"\n   ⏱️ Tiempo total: {results['total_time']:.2f}s")
    print(f"   ⏱️ Promedio por test: {results['total_time']/total:.2f}s")
    
    # Mostrar tests fallidos
    failed_tests = [t for t in results['test_results'] if t['status'] != 'PASSED']
    if failed_tests:
        print("\n" + "-"*50)
        print("Tests no pasados:")
        for t in failed_tests:
            print(f"   • {t['test_id']}: {t['status']}")
            if t.get('error'):
                print(f"     Error: {t['error']}")
            if t['phases'].get('revise', {}).get('violations', 0) > 0:
                print(f"     Violaciones: {t['phases']['revise']['violation_details']}")
    
    print("\n" + "="*70)
    
    # Indicador visual final
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
    elif pass_rate >= 80:
        print("👍 La mayoría de tests pasaron")
    elif pass_rate >= 50:
        print("⚠️ Algunos tests fallaron")
    else:
        print("❌ La mayoría de tests fallaron")
    
    print("="*70 + "\n")


def save_results(results: Dict, filepath: str = RESULTS_PATH):
    """Guarda los resultados en un archivo JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📁 Resultados guardados en: {filepath}")
    except Exception as e:
        print(f"⚠️ No se pudieron guardar resultados: {e}")


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Ejecuta juegos de prueba del Sistema CBR'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verbose con detalles de cada test'
    )
    parser.add_argument(
        '--test', '-t',
        type=str,
        help='Ejecutar solo un test específico (ej: TEST_001)'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Guardar casos generados en la base (no recomendado para tests)'
    )
    
    args = parser.parse_args()
    
    run_all_tests(
        verbose=args.verbose,
        save_cases=args.save,
        specific_test=args.test
    )


if __name__ == "__main__":
    main()
