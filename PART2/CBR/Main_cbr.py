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
    python main.py --demo    # Modo demo sin interacción
    python main.py --test    # Ejecutar juegos de prueba
    python main.py --test -v # Tests en modo verbose
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import patch
from io import StringIO


# ============================================================================
# CLASE PARA CAPTURAR SALIDA EN ARCHIVO Y CONSOLA
# ============================================================================

class TeeOutput:
    """Clase que escribe simultáneamente en consola y archivo."""
    def __init__(self, file_handle, original_stdout):
        self.file = file_handle
        self.stdout = original_stdout
    
    def write(self, message):
        self.stdout.write(message)
        self.file.write(message)
        self.file.flush()
    
    def flush(self):
        self.stdout.flush()
        self.file.flush()

# Añadir directorio al path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Importar módulos CBR
from input_module import get_user_restrictions
from Retrieve import load_case_base, retrieve_cases, print_results
from Adapt import adapt_menu, load_all_knowledge_bases
from Revise import revise_menu, print_menu_summary
from Retain import retain_case, get_case_base_stats, calculate_similarity_to_base, calculate_novelty, calculate_trace_score, calculate_usefulness
from adapt_tecnic import adapt_menu_tecniques, print_adaptation_results


# ============================================================================
# CONFIGURACIÓN
# ============================================================================

BASE_DIR = os.path.join(SCRIPT_DIR, '..')
CASE_BASE_PATH = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')
TEST_CASES_PATH = os.path.join(BASE_DIR, 'Juegos_Prueba', 'test_cases_extended.json')
TEST_RESULTS_PATH = os.path.join(SCRIPT_DIR, 'test_results_extended.json')


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
        
        # Si fue un ajuste cultural de segunda ronda, mostrar el resultado especial
        if adaptation_result.get('is_culture_adjustment'):
            print(f"\n🎨 AJUSTE CULTURAL APLICADO:")
            print(f"   {adaptation_result.get('message')}")
            # Limpiar los campos de ajuste para evitar que se repitan
            current_input.pop('culture_adjustment', None)
            current_input.pop('culture_adjustment_target', None)
        
        adaptation_result_tecnic = adapt_menu_tecniques(current_input, adaptation_result)
        print_adaptation_results(adaptation_result_tecnic)
        
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
                # Pasar el ajuste cultural al módulo de adaptación
                for adj in culture_adjustments:
                    # Añadir campos especiales para que adapt_menu aplique el ajuste obligatorio
                    current_input['culture_adjustment'] = adj['action']  # 'add' o 'remove'
                    current_input['culture_adjustment_target'] = adj['culture']  # cultura objetivo
                    
                    # También actualizar la cultura preferida si es 'add'
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
# MODO TEST (JUEGOS DE PRUEBA)
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


def run_single_test(
    test_case: Dict,
    case_base: List,
    verbose: bool = False,
    save_cases: bool = False,
    log_file = None
) -> Dict:
    """
    Ejecuta un único caso de prueba usando el ciclo CBR completo.
    Similar al modo manual pero con datos del test_case y mock inputs.
    
    Args:
        test_case: Caso de prueba con input y mock_user_inputs
        case_base: Base de casos cargada
        verbose: Si True, muestra información detallada
        save_cases: Si True, permite guardar casos en la base
        log_file: Archivo donde escribir la salida (opcional)
        
    Returns:
        Dict con resultados del test
    """
    test_id = test_case.get('id', 'UNKNOWN')
    description = test_case.get('description', 'Sin descripción')
    user_input = test_case.get('input', {})
    mock_inputs = test_case.get('mock_user_inputs', [])
    
    result = {
        'test_id': test_id,
        'description': description,
        'status': 'PENDING',
        'passed': False,
        'execution_time': 0,
        'iterations': 0,
        'final_menu': None,
        'case_saved': False,
        'error': None
    }
    
    start_time = time.time()
    
    # Guardar stdout original
    original_stdout = sys.stdout
    
    try:
        # ================================================================
        # REDIRIGIR STDOUT A ARCHIVO Y CONSOLA DESDE EL INICIO
        # ================================================================
        if log_file:
            tee = TeeOutput(log_file, original_stdout)
            sys.stdout = tee
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"🧪 TEST: {test_id}")
            print(f"{'='*70}")
            print(f"📝 {description}")
            print(f"🔹 Input: {json.dumps(user_input, indent=2)}")
            print(f"🔹 Mock inputs: {mock_inputs}")
        
        # ================================================================
        # CASO ESPECIAL: Base de casos vacía (TEST_025)
        # ================================================================
        if test_id == "TEST_025":
            sys.stdout = original_stdout  # Restaurar antes de salir
            retrieved = retrieve_cases(user_input, [])
            result['status'] = 'PASS' if len(retrieved) == 0 else 'FAIL'
            result['passed'] = (len(retrieved) == 0)
            result['execution_time'] = time.time() - start_time
            return result
        
        # ================================================================
        # EJECUTAR CICLO CBR COMPLETO (como modo manual)
        # ================================================================
        
        # Mockear los inputs del usuario para las partes interactivas
        mock_input_iter = iter(mock_inputs)
        
        def mock_input_func(prompt=""):
            """Función mock que devuelve los inputs predefinidos."""
            try:
                value = next(mock_input_iter)
                # Imprimir el prompt y la respuesta mockeada
                print(f"{prompt}{value}")
                return value
            except StopIteration:
                # Si se acabaron los inputs, devolver string vacío
                print(f"{prompt}")
                return ""
        
        # Patchear input() en todos los módulos relevantes
        with patch('builtins.input', side_effect=mock_input_func), \
             patch('Revise.input', side_effect=mock_input_func), \
             patch('input_module.input', side_effect=mock_input_func):
            # Ejecutar el ciclo CBR completo
            cbr_results = run_cbr_cycle(user_input)
        
        # Restaurar stdout
        sys.stdout = original_stdout
        
        # Extraer resultados
        result['iterations'] = cbr_results.get('iterations', 0)
        result['final_menu'] = cbr_results.get('final_menu')
        result['case_saved'] = cbr_results.get('case_saved', False)
        result['success'] = cbr_results.get('success', False)
        
        # Si el ciclo se ejecutó sin errores, es PASS
        result['status'] = 'PASS'
        result['passed'] = True
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"CBR Cycle completed:")
            print(f"  Success: {cbr_results.get('success')}")
            print(f"  Iterations: {result['iterations']}")
            print(f"  Case saved: {result['case_saved']}")
            print(f"  Result: ✅ PASS")
        
    except Exception as e:
        # Restaurar stdout en caso de error
        sys.stdout = original_stdout
        
        result['status'] = 'ERROR'
        result['error'] = str(e)
        result['passed'] = False
        
        if verbose:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
    
    result['execution_time'] = time.time() - start_time
    return result


def print_test_summary(results: Dict):
    """Imprime un resumen de los resultados de tests."""
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
    
    failed_tests = [t for t in results['test_results'] if t['status'] != 'PASSED']
    if failed_tests:
        print("\n" + "-"*50)
        print("Tests no pasados:")
        for t in failed_tests:
            print(f"   • {t['test_id']}: {t['status']}")
            if t.get('error'):
                print(f"     Error: {t['error']}")
    
    print("\n" + "="*70)
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
    elif pass_rate >= 80:
        print("👍 La mayoría de tests pasaron")
    elif pass_rate >= 50:
        print("⚠️ Algunos tests fallaron")
    else:
        print("❌ La mayoría de tests fallaron")
    
    print("="*70 + "\n")


def save_test_results(results: Dict, filepath: str = TEST_RESULTS_PATH):
    """Guarda los resultados en un archivo JSON."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📁 Resultados guardados en: {filepath}")
    except Exception as e:
        print(f"⚠️ No se pudieron guardar resultados: {e}")


def test_mode(
    verbose: bool = False,
    save_cases: bool = False,
    specific_test: Optional[str] = None
) -> Dict:
    """
    Ejecuta los juegos de prueba del sistema CBR.
    Usa el ciclo CBR completo (como modo manual) con datos de test_cases.
    
    Args:
        verbose: Modo verbose con detalles
        save_cases: Si guardar casos en la base
        specific_test: ID de test específico a ejecutar
        
    Returns:
        Dict con resumen de resultados
    """
    # Crear archivo de log
    log_filename = os.path.join(SCRIPT_DIR, f'test_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
    
    print("\n" + "="*70)
    print("🧪 JUEGOS DE PRUEBA - Sistema CBR de Menús")
    print("="*70)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📄 Log guardado en: {log_filename}")
    
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
    print("ℹ️  Ejecutando ciclo CBR completo con iteraciones (como modo manual)")
    
    # Cargar base de casos
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
    
    # Abrir archivo de log
    with open(log_filename, 'w', encoding='utf-8') as log_file:
        log_file.write("="*70 + "\n")
        log_file.write("🧪 JUEGOS DE PRUEBA - Sistema CBR de Menús\n")
        log_file.write("="*70 + "\n")
        log_file.write(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"📋 Tests a ejecutar: {len(test_cases)}\n")
        log_file.write("\n" + "-"*70 + "\n")
        log_file.write("EJECUTANDO TESTS\n")
        log_file.write("-"*70 + "\n")
        log_file.flush()
        
        for i, test_case in enumerate(test_cases, 1):
            test_id = test_case.get('id', f'TEST_{i}')
            
            header = f"\n[{i}/{len(test_cases)}] {test_id}: {test_case.get('description', '')}..."
            print(header)
            log_file.write(header + "\n")
            log_file.flush()
            
            test_result = run_single_test(
                test_case, case_base,
                verbose=verbose,
                save_cases=save_cases,
                log_file=log_file
            )
            
            results['test_results'].append(test_result)
            results['total_time'] += test_result.get('execution_time', 0)
            
            if test_result['status'] == 'PASS':
                results['passed'] += 1
                status_msg = f"   ✅ PASS ({test_result['execution_time']:.2f}s, {test_result['iterations']} iterations)"
            elif test_result['status'] == 'FAIL':
                results['failed'] += 1
                status_msg = f"   ❌ FAIL ({test_result['execution_time']:.2f}s)"
            else:
                results['errors'] += 1
                status_msg = f"   ⚠️ ERROR: {test_result.get('error', 'Unknown')}"
            
            print(status_msg)
            log_file.write(status_msg + "\n\n")
            log_file.flush()
    
    # Mostrar resumen
    print_test_summary(results)
    
    # Guardar resultados JSON
    save_test_results(results)
    
    print(f"\n📄 Log completo guardado en: {log_filename}")
    
    return results


# ============================================================================
# MODO SELECTOR
# ============================================================================

def select_mode():
    """Pregunta al usuario qué modo desea ejecutar."""
    print("\n" + "="*70)
    print("🍽️  SISTEMA CBR DE MENÚS GASTRONÓMICOS")
    print("="*70)
    print("\nSeleccione el modo de ejecución:")
    print("  1. Modo Manual (Interactivo)")
    print("  2. Juegos de Prueba (Test Suite)")
    print("  3. Modo Demo (Sin interacción)")
    print("  0. Salir")
    print("="*70)
    
    while True:
        try:
            choice = input("\nIngrese su elección (0-3): ").strip()
            
            if choice == '1':
                return 'manual'
            elif choice == '2':
                return 'test'
            elif choice == '3':
                return 'demo'
            elif choice == '0':
                print("\n👋 ¡Hasta luego!")
                sys.exit(0)
            else:
                print("❌ Opción inválida. Por favor ingrese 0, 1, 2 o 3.")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            sys.exit(0)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sistema CBR para Menús Gastronómicos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de ejecución:
  (sin argumentos)  Modo interactivo normal
  --demo            Modo demo sin interacción
  --test            Ejecutar juegos de prueba
  --test -v         Tests en modo verbose
  --test -t ID      Ejecutar un test específico
"""
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Ejecutar en modo demo (sin interacción)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Ejecutar juegos de prueba'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Modo verbose para tests'
    )
    parser.add_argument(
        '-t', '--test-id',
        type=str,
        help='Ejecutar solo un test específico (ej: TEST_001)'
    )
    parser.add_argument(
        '--save-test-cases',
        action='store_true',
        help='Guardar casos generados durante tests (no recomendado)'
    )
    
    args = parser.parse_args()
    
    # Si hay argumentos de línea de comandos, usarlos
    if args.demo:
        demo_mode()
    elif args.test:
        test_mode(
            verbose=args.verbose,
            save_cases=args.save_test_cases,
            specific_test=args.test_id
        )
    # Si no hay argumentos, preguntar al usuario
    elif len(sys.argv) == 1:
        mode = select_mode()
        
        if mode == 'manual':
            main()
        elif mode == 'test':
            # Preguntar opciones de test
            print("\n" + "-"*70)
            print("OPCIONES DE JUEGOS DE PRUEBA")
            print("-"*70)
            
            verbose_input = input("\n¿Modo verbose (muestra detalles)? (s/N): ").strip().lower()
            verbose = verbose_input in ['s', 'si', 'sí', 'yes', 'y']
            
            specific_test_input = input("\n¿Ejecutar test específico? (Ingrese ID o presione Enter para todos): ").strip()
            specific_test = specific_test_input if specific_test_input else None
            
            save_input = input("\n⚠️  ¿Permitir guardar casos? (NO recomendado) (s/N): ").strip().lower()
            save_cases = save_input in ['s', 'si', 'sí', 'yes', 'y']
            
            print("\n" + "="*70)
            
            test_mode(
                verbose=verbose,
                save_cases=save_cases,
                specific_test=specific_test
            )
        elif mode == 'demo':
            demo_mode()
    else:
        # Modo por defecto si hay argumentos no reconocidos
        main()
