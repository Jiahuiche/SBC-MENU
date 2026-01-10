"""
Test del módulo de Adaptación
==============================
Script para probar el flujo completo: Retrieve → Adapt
"""

import sys
import os

# Agregar el directorio CBR al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'CBR'))

from CBR.Retrieve import load_case_base, retrieve_cases, print_results
from CBR.Adapt import adapt_menu, print_adaptation_results, load_all_knowledge_bases


def test_adaptation():
    """Test completo del módulo de adaptación."""
    
    print("="*70)
    print("🧪 TEST DE ADAPTACIÓN CBR")
    print("="*70 + "\n")
    
    # Caso de prueba: usuario vegano que quiere comida mediterránea
    user_input = {
        'restrictions': ['vegan', 'gluten-free'],
        'cuisine': 'Mediterranean'
    }
    
    print("📋 Input del usuario:")
    print(f"   • Restricciones: {user_input['restrictions']}")
    print(f"   • Cultura: {user_input['cuisine']}")
    print()
    
    # Cargar bases de datos
    print("🔄 Cargando bases de datos...")
    case_base = load_case_base('Base_Casos/casos_cbr.json')
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    if not case_base:
        print("❌ Error: No se pudo cargar la base de casos")
        return
    
    print(f"✅ Base de casos: {len(case_base)} casos")
    print(f"✅ Restricciones: {len(restricciones_db)} tipos")
    print(f"✅ Contextos culturales: {len(contexto_db)} contextos")
    print()
    
    # Recuperar casos similares
    print("🔍 Buscando casos similares...")
    results = retrieve_cases(user_input, case_base)
    
    # Mostrar top 3 resultados
    print_results(results, top_n=3)
    
    # Buscar un caso que necesite adaptación de restricciones (no solo cultura)
    # El caso 6 es Mediterranean pero no vegan
    case_to_adapt = None
    for result in results:
        compliance = result.get('compliance', {})
        if compliance.get('restrictions_not_met'):
            case_to_adapt = result
            break
    
    if not case_to_adapt:
        # Si no hay, usar el primero
        case_to_adapt = results[0]
    
    print(f"🎯 Adaptando caso ID: {case_to_adapt['case'].get('id_caso')}")
    print(f"   Restricciones no cumplidas: {case_to_adapt.get('compliance', {}).get('restrictions_not_met', [])}")
    print(f"   Cultura no cumplida: {case_to_adapt.get('compliance', {}).get('culture_not_met', 'Ninguna')}")
    
    # Adaptar el caso seleccionado
    print("\n🔧 Adaptando el menú...")
    adaptation_result = adapt_menu(
        case_to_adapt,
        user_input,
        restricciones_db,
        contexto_db,
        ontologia_db,
        pairing_db
    )
    
    # Mostrar resultados de adaptación
    print_adaptation_results(adaptation_result)
    
    return adaptation_result


def test_specific_case():
    """Test con un caso específico para verificar sustituciones."""
    
    print("\n" + "="*70)
    print("🧪 TEST DE SUSTITUCIÓN ESPECÍFICA")
    print("="*70 + "\n")
    
    # Cargar bases de conocimiento
    from CBR.Adapt import (
        find_ingredients_violating_restriction,
        find_substitute_candidates,
        select_best_substitute,
        get_known_substitutes,
        load_all_knowledge_bases
    )
    
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    # Test: ingredientes que violan vegan
    test_ingredients = ['butter', 'eggs', 'tomato', 'onion', 'garlic', 'cheese']
    restrictions = ['vegan']
    
    print(f"📋 Ingredientes de prueba: {test_ingredients}")
    print(f"📋 Restricciones a cumplir: {restrictions}")
    print()
    
    # Verificar restricción vegan
    violating = find_ingredients_violating_restriction(
        test_ingredients, 'vegan', restricciones_db
    )
    
    print(f"❌ Ingredientes que violan 'vegan': {violating}")
    print()
    
    # Buscar sustitutos para cada ingrediente violador
    for ingredient in violating:
        print(f"🔍 Buscando sustituto para: {ingredient}")
        
        # Intento 1: Ontología (misma cultura)
        candidates, level = find_substitute_candidates(ingredient, ontologia_db, search_all_cultures=False)
        print(f"   Ontología (misma cultura): {len(candidates)} candidatos")
        
        other_ingredients = [i for i in test_ingredients if i not in violating]
        
        best = None
        if candidates:
            best = select_best_substitute(
                candidates, 
                other_ingredients, 
                pairing_db,
                all_restrictions=restrictions,
                restricciones_db=restricciones_db
            )
        
        # Intento 2: Ontología (todas las culturas)
        if not best:
            candidates, level = find_substitute_candidates(ingredient, ontologia_db, search_all_cultures=True)
            print(f"   Ontología (todas culturas): {len(candidates)} candidatos")
            
            if candidates:
                best = select_best_substitute(
                    candidates, 
                    other_ingredients, 
                    pairing_db,
                    all_restrictions=restrictions,
                    restricciones_db=restricciones_db
                )
        
        # Intento 3: Sustitutos conocidos
        if not best:
            known = get_known_substitutes(ingredient, restrictions, restricciones_db)
            print(f"   Sustitutos conocidos: {known}")
            if known:
                best = known[0]  # Tomar el primero como fallback
        
        if best:
            print(f"   ✅ Mejor sustituto: {best}")
        else:
            print(f"   ⚠️  No se encontró sustituto válido")
        print()


if __name__ == "__main__":
    # Test principal
    test_adaptation()
    
    # Test específico de sustitución
    test_specific_case()
