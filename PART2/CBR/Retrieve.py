"""
Módulo de Recuperación Simple (Retrieve)
=========================================
Sistema de matching exacto sin pesos.
Cada coincidencia suma 1 punto.
"""

import json
import os


def load_case_base(filepath='Base_Casos/casos_cbr.json'):
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


def retrieve_case_by_id(case_id: int, case_base: list = None, filepath: str = 'Base_Casos/casos_cbr.json') -> dict:
    """
    Recupera un caso específico por su ID.
    Útil para segundas rondas donde queremos el caso de la ronda anterior.
    
    Args:
        case_id: ID del caso a recuperar
        case_base: Base de casos (opcional, se carga si no se proporciona)
        filepath: Ruta al archivo de casos
        
    Returns:
        Dict con el caso encontrado o None si no existe
    """
    if case_base is None:
        case_base = load_case_base(filepath)
    
    for case in case_base:
        if case.get('id_caso') == case_id:
            return case
    
    print(f"⚠️  No se encontró el caso con ID: {case_id}")
    return None


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


def normalize_season(season):
    """Normaliza una estación para comparación."""
    return season.lower().replace('-', ' ').replace('_', ' ').strip()


# Valores que indican "cualquier estación" (acepta todas)
ANY_SEASON_VALUES = ['any', 'any season', 'todas', 'all', 'all seasons', '', 'any-season']


def is_any_season(season):
    """Verifica si el valor de estación significa 'cualquier estación'."""
    if not season:
        return True
    return normalize_season(season) in ANY_SEASON_VALUES


def check_season_match(user_season, case_season):
    """
    Verifica si hay coincidencia de estación.
    
    Args:
        user_season: Estación solicitada por el usuario
        case_season: Estación del caso
        
    Returns:
        bool: True si hay coincidencia, si el usuario acepta cualquier estación,
              o False si no especifica estación (no suma punto)
    """
    # Si el usuario no especifica estación, no suma punto
    if not user_season:
        return False
    
    # Si el usuario acepta cualquier estación, siempre hay match
    if is_any_season(user_season):
        return True
    
    if not case_season:
        return False
    
    user_norm = normalize_season(user_season)
    case_norm = normalize_season(case_season)
    
    # Matching exacto o parcial
    return user_norm == case_norm or user_norm in case_norm or case_norm in user_norm


def check_price_in_range(min_price, max_price, case_price):
    """
    Verifica si el precio del caso está dentro del rango del usuario.
    
    Args:
        min_price: Precio mínimo del usuario
        max_price: Precio máximo del usuario
        case_price: Precio por ración del caso
        
    Returns:
        bool: True si el precio está dentro del rango
    """
    if case_price is None or case_price <= 0:
        return False
    
    # Si el usuario no especifica rango, no suma puntos
    if min_price is None and max_price is None:
        return False
    
    # Usar valores por defecto si no se especifican
    min_p = min_price if min_price is not None else 0
    max_p = max_price if max_price is not None else float('inf')
    
    return min_p <= case_price <= max_p


# Pesos para la función de similitud
SIMILARITY_WEIGHTS = {
    'restriction': 2.0,   # Mayor peso: restricciones alimentarias
    'culture': 1.5,       # Peso intermedio: cultura culinaria
    'season': 1.0,        # Peso base: estación
    'price': 1.0          # Peso base: precio
}


def calculate_similarity(user_input, case_problem, case_solution=None):
    """
    Calcula la similitud entre el input del usuario y el problema del caso.
    Sistema de pesos:
      - Restricciones alimentarias: 2.0 puntos cada una (mayor importancia)
      - Cultura culinaria: 1.5 puntos (importancia intermedia)
      - Estación y precio: 1.0 punto cada uno (importancia base)
    
    Args:
        user_input (dict): Diccionario con las preferencias del usuario
        case_problem (dict): Campo 'problema' del caso
        case_solution (dict): Campo 'solucion' del caso (para price y season)
        
    Returns:
        float: Puntuación de similitud ponderada
    """
    score = 0.0
    
    # 1. Matching de restricciones alimentarias (PESO ALTO: 2.0 por cada una)
    user_restrictions = user_input.get('restrictions', [])
    case_restrictions = case_problem.get('restricciones_alimentarias', [])
    
    # Normalizar a minúsculas para comparación
    user_restrictions_normalized = [normalize_restriction(r) for r in user_restrictions]
    case_restrictions_normalized = [normalize_restriction(r) for r in case_restrictions]
    
    # Contar coincidencias exactas
    for user_rest in user_restrictions_normalized:
        if user_rest in case_restrictions_normalized:
            score += SIMILARITY_WEIGHTS['restriction']
    
    # 2. Matching de cultura culinaria (PESO MEDIO: 1.5)
    user_cuisine = user_input.get('cuisine', '').lower()
    case_culture = case_problem.get('cultura_preferible', '').lower()
    
    if check_culture_match(user_cuisine, case_culture):
        score += SIMILARITY_WEIGHTS['culture']
    
    # 3. Matching de estación (season) (PESO BASE: 1.0)
    if case_solution:
        features = case_solution.get('features', {})
        
        user_season = user_input.get('season', '')
        case_season = features.get('season', '')
        
        if check_season_match(user_season, case_season):
            score += SIMILARITY_WEIGHTS['season']
        
        # 4. Matching de precio (price_per_serving dentro del rango) (PESO BASE: 1.0)
        min_price = user_input.get('min_price')
        max_price = user_input.get('max_price')
        case_price = features.get('total_price_per_serving')
        
        if check_price_in_range(min_price, max_price, case_price):
            score += SIMILARITY_WEIGHTS['price']
    
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
            - 'season_not_met': estación no cumplida (o None si cumple)
            - 'price_not_met': True si el precio está fuera del rango
            - 'courses_analysis': análisis detallado por plato
    """
    result = {
        'restrictions_not_met': [],
        'culture_not_met': None,
        'season_not_met': None,
        'price_not_met': False,
        'courses_analysis': {}
    }
    
    user_restrictions = [normalize_restriction(r) for r in user_input.get('restrictions', [])]
    user_cuisine = user_input.get('cuisine', '')
    
    solution = case.get('solucion', {})
    courses = solution.get('courses', {})
    features = solution.get('features', {})
    
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
    
    # Verificar estación
    user_season = user_input.get('season', '')
    case_season = features.get('season', '')
    # Solo verificar si el usuario especificó una estación concreta (no 'any')
    if user_season and not is_any_season(user_season):
        if not check_season_match(user_season, case_season):
            result['season_not_met'] = user_season
    
    # Verificar precio
    min_price = user_input.get('min_price')
    max_price = user_input.get('max_price')
    case_price = features.get('total_price_per_serving')
    
    if (min_price is not None or max_price is not None) and case_price is not None:
        if not check_price_in_range(min_price, max_price, case_price):
            result['price_not_met'] = True
            result['case_price'] = case_price
            result['user_price_range'] = {'min': min_price, 'max': max_price}
    
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
        solution = case.get('solucion', {})
        score = calculate_similarity(user_input, problem, solution)
        
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
        features = solution.get('features', {})
        
        print(f"🏆 Ranking #{i}  |  Caso ID: {case_id}  |  Puntuación: {score} puntos")
        print(f"   {menu_name}")
        
        # Mostrar el problema del caso
        problem = case.get('problema', {})
        restrictions = problem.get('restricciones_alimentarias', [])
        culture = problem.get('cultura_preferible', 'N/A')
        
        print(f"   • Cultura: {culture}")
        print(f"   • Restricciones: {', '.join(restrictions) if restrictions else 'Ninguna'}")
        
        # Mostrar estación y precio
        case_season = features.get('season', 'N/A')
        case_price = features.get('total_price_per_serving', 'N/A')
        print(f"   • Estación: {case_season}")
        print(f"   • Precio por ración: {case_price}€" if isinstance(case_price, (int, float)) else f"   • Precio por ración: {case_price}")
        
        # Mostrar análisis de cumplimiento
        restrictions_not_met = compliance.get('restrictions_not_met', [])
        culture_not_met = compliance.get('culture_not_met')
        season_not_met = compliance.get('season_not_met')
        price_not_met = compliance.get('price_not_met', False)
        
        if restrictions_not_met or culture_not_met or season_not_met or price_not_met:
            print(f"   ⚠️  Adaptaciones necesarias:")
            if restrictions_not_met:
                print(f"      - Restricciones no cumplidas: {', '.join(restrictions_not_met)}")
            if culture_not_met:
                print(f"      - Cultura no cumplida: {culture_not_met}")
            if season_not_met:
                print(f"      - Estación no cumplida: {season_not_met}")
            if price_not_met:
                user_range = compliance.get('user_price_range', {})
                case_price_val = compliance.get('case_price', 'N/A')
                print(f"      - Precio fuera de rango: {case_price_val}€ (rango usuario: {user_range.get('min', 0)}€ - {user_range.get('max', '∞')}€)")
        else:
            print(f"   ✅ Cumple todas las restricciones, cultura, estación y precio")
        
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
