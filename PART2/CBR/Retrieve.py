"""
Módulo de Recuperación Simple (Retrieve)
=========================================
Sistema de matching exacto sin pesos.
Cada coincidencia suma 1 punto.
"""

import json
import os


def load_case_base(filepath='Bases_Casos/casos_cbr.json'):
    """Carga la base de casos desde el archivo JSON."""
    # Ajustar la ruta si estamos en el directorio CBR
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('casos', [])
    except FileNotFoundError:
        print(f"⚠️  Error: No se encontró el archivo {filepath}")
        return []
    except json.JSONDecodeError:
        print(f"⚠️  Error: El archivo {filepath} no es un JSON válido")
        return []


def normalize_restriction(restriction):
    """Normaliza una restricción para comparación."""
    return restriction.lower().replace('-', ' ').replace('_', ' ').strip()


def normalize_culture(culture):
    """Normaliza una cultura para comparación."""
    return culture.lower().replace('-', ' ').replace('_', ' ').strip()


def check_culture_match(user_cuisine, case_culture):
    """
    Verifica si hay coincidencia de cultura (parcial o exacta).
    
    Returns:
        bool: True si hay coincidencia
    """
    if not user_cuisine or not case_culture:
        return False
    
    user_norm = normalize_culture(user_cuisine)
    case_norm = normalize_culture(case_culture)
    
    # Matching exacto o parcial
    return user_norm == case_norm or user_norm in case_norm or case_norm in user_norm


def calculate_similarity(user_input, case_problem):
    """
    Calcula la similitud entre el input del usuario y el problema del caso.
    Matching exacto: cada coincidencia suma 1 punto.
    
    Args:
        user_input (dict): Diccionario con las preferencias del usuario
        case_problem (dict): Campo 'problema' del caso
        
    Returns:
        int: Puntuación de similitud
    """
    score = 0
    
    # 1. Matching de restricciones alimentarias
    user_restrictions = user_input.get('restrictions', [])
    case_restrictions = case_problem.get('restricciones_alimentarias', [])
    
    # Normalizar a minúsculas para comparación
    user_restrictions_normalized = [normalize_restriction(r) for r in user_restrictions]
    case_restrictions_normalized = [normalize_restriction(r) for r in case_restrictions]
    
    # Contar coincidencias exactas
    for user_rest in user_restrictions_normalized:
        if user_rest in case_restrictions_normalized:
            score += 1
    
    # 2. Matching de cultura culinaria
    user_cuisine = user_input.get('cuisine', '').lower()
    case_culture = case_problem.get('cultura_preferible', '').lower()
    
    if check_culture_match(user_cuisine, case_culture):
        score += 1
    
    return score


def analyze_case_compliance(user_input, case):
    """
    Analiza qué restricciones y cultura NO cumple la solución del caso.
    
    Args:
        user_input (dict): Diccionario con las preferencias del usuario
        case (dict): Caso completo con 'problema' y 'solucion'
        
    Returns:
        dict: Diccionario con:
            - 'restrictions_not_met': lista de restricciones no cumplidas
            - 'culture_not_met': cultura no cumplida (o None si cumple)
            - 'courses_analysis': análisis detallado por plato
    """
    result = {
        'restrictions_not_met': [],
        'culture_not_met': None,
        'courses_analysis': {}
    }
    
    user_restrictions = [normalize_restriction(r) for r in user_input.get('restrictions', [])]
    user_cuisine = user_input.get('cuisine', '')
    
    solution = case.get('solucion', {})
    courses = solution.get('courses', {})
    
    # Analizar cada plato (starter, main, dessert)
    for course_name, course_data in courses.items():
        course_restrictions = [normalize_restriction(r) for r in course_data.get('restrictions', [])]
        course_ingredients = course_data.get('ingredients', [])
        
        # Verificar restricciones no cumplidas para este plato
        course_restrictions_not_met = []
        for user_rest in user_restrictions:
            if user_rest not in course_restrictions:
                course_restrictions_not_met.append(user_rest)
        
        result['courses_analysis'][course_name] = {
            'title': course_data.get('title', 'Unknown'),
            'ingredients': course_ingredients,
            'restrictions_declared': course_data.get('restrictions', []),
            'restrictions_not_met': course_restrictions_not_met
        }
        
        # Agregar restricciones no cumplidas a la lista global
        for rest in course_restrictions_not_met:
            if rest not in result['restrictions_not_met']:
                result['restrictions_not_met'].append(rest)
    
    # Verificar cultura
    case_culture = case.get('problema', {}).get('cultura_preferible', '')
    if user_cuisine and not check_culture_match(user_cuisine, case_culture):
        result['culture_not_met'] = user_cuisine
    
    return result


def retrieve_cases(user_input, case_base):
    """
    Recupera y ordena los casos según similitud con el input del usuario.
    
    Args:
        user_input (dict): Diccionario con las preferencias del usuario
        case_base (list): Lista de casos de la base de conocimiento
        
    Returns:
        list: Lista de diccionarios con:
              - 'case': caso completo
              - 'score': puntuación de similitud
              - 'compliance': análisis de cumplimiento (restricciones/cultura no cumplidas)
              ordenada por puntuación descendente
    """
    results = []
    
    for case in case_base:
        problem = case.get('problema', {})
        score = calculate_similarity(user_input, problem)
        
        # Analizar qué restricciones/cultura no cumple
        compliance = analyze_case_compliance(user_input, case)
        
        # Guardamos el caso completo junto con su puntuación y análisis
        results.append({
            'case': case,
            'score': score,
            'compliance': compliance
        })
    
    # Ordenar por puntuación descendente
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results


def print_results(results, top_n=5):
    """
    Muestra los resultados del retrieve de forma legible.
    
    Args:
        results (list): Lista de resultados del retrieve
        top_n (int): Número de casos a mostrar
    """
    print("\n" + "="*70)
    print("RESULTADOS DEL RETRIEVE")
    print("="*70 + "\n")
    
    if not results:
        print("❌ No se encontraron casos en la base de conocimiento.\n")
        return
    
    # Mostrar solo los top N casos
    for i, result in enumerate(results[:top_n], 1):
        case = result['case']
        score = result['score']
        compliance = result.get('compliance', {})
        
        # Información del caso
        case_id = case.get('id_caso', 'N/A')
        solution = case.get('solucion', {})
        menu_name = solution.get('menu_name', 'Sin nombre')
        
        print(f"🏆 Ranking #{i}  |  Caso ID: {case_id}  |  Puntuación: {score} puntos")
        print(f"   {menu_name}")
        
        # Mostrar el problema del caso
        problem = case.get('problema', {})
        restrictions = problem.get('restricciones_alimentarias', [])
        culture = problem.get('cultura_preferible', 'N/A')
        
        print(f"   • Cultura: {culture}")
        print(f"   • Restricciones: {', '.join(restrictions) if restrictions else 'Ninguna'}")
        
        # Mostrar análisis de cumplimiento
        restrictions_not_met = compliance.get('restrictions_not_met', [])
        culture_not_met = compliance.get('culture_not_met')
        
        if restrictions_not_met or culture_not_met:
            print(f"   ⚠️  Adaptaciones necesarias:")
            if restrictions_not_met:
                print(f"      - Restricciones no cumplidas: {', '.join(restrictions_not_met)}")
            if culture_not_met:
                print(f"      - Cultura no cumplida: {culture_not_met}")
        else:
            print(f"   ✅ Cumple todas las restricciones y cultura")
        
        print()
    
    print("="*70 + "\n")


def main():
    """Función principal para testing del módulo."""
    from input_module import get_user_restrictions
    
    # 1. Obtener input del usuario
    print("Paso 1: Recopilando preferencias del usuario...\n")
    user_input = get_user_restrictions()
    
    # 2. Cargar base de casos
    print("\nPaso 2: Cargando base de casos...")
    case_base = load_case_base('Otras_Bases/casos_cbr.json')
    
    if not case_base:
        print("❌ No se pudo cargar la base de casos. Verifique la ruta.")
        return
    
    print(f"✅ Se cargaron {len(case_base)} casos.\n")
    
    # 3. Recuperar casos similares
    print("Paso 3: Buscando casos similares...")
    results = retrieve_cases(user_input, case_base)
    
    # 4. Mostrar resultados
    print_results(results, top_n=5)
    
    # 5. Devolver resultados para otros módulos
    return results


if __name__ == "__main__":
    main()
