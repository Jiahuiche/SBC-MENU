"""
Módulo de Retención (Retain)
=============================
Fase RETAIN del ciclo CBR:
Decide si guardar el caso en la base de casos basándose en utilidad.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..')
CASE_BASE_FILE = os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json')


# ============================================================================
# CARGA Y GUARDADO DE BASE DE CASOS
# ============================================================================

def load_case_base(filepath: str = None) -> List[Dict]:
    """Carga la base de casos."""
    if filepath is None:
        filepath = CASE_BASE_FILE
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('casos', [])
    except FileNotFoundError:
        print(f"⚠️ Base de casos no encontrada: {filepath}")
        return []
    except json.JSONDecodeError:
        print(f"⚠️ Error leyendo JSON: {filepath}")
        return []


def save_case_base(cases: List[Dict], filepath: str = None):
    """Guarda la base de casos."""
    if filepath is None:
        filepath = CASE_BASE_FILE
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({'casos': cases}, f, indent=2, ensure_ascii=False)
        print(f"✅ Base de casos guardada: {len(cases)} casos")
    except Exception as e:
        print(f"❌ Error guardando base de casos: {e}")
        raise


# ============================================================================
# CÁLCULO DE UTILIDAD
# ============================================================================

def calculate_similarity_to_base(
    new_case: Dict[str, Any],
    case_base: List[Dict]
) -> float:
    """
    Calcula la similitud máxima del nuevo caso con la base existente.
    
    Returns:
        float: Similitud máxima (0-1). Alto = caso redundante.
    """
    if not case_base:
        return 0.0  # Sin casos similares
    
    max_similarity = 0.0
    
    # Extraer ingredientes del nuevo caso
    new_ingredients = set()
    new_courses = new_case.get('solucion', {}).get('courses', {})
    for course_data in new_courses.values():
        if isinstance(course_data, dict):
            for ing in course_data.get('ingredients', []):
                new_ingredients.add(ing.lower())
    
    # Extraer restricciones
    new_restrictions = set(
        r.lower() for r in 
        new_case.get('problema', {}).get('restricciones_alimentarias', [])
    )
    
    for existing_case in case_base:
        # Ingredientes del caso existente
        existing_ingredients = set()
        existing_courses = existing_case.get('solucion', {}).get('courses', {})
        for course_data in existing_courses.values():
            if isinstance(course_data, dict):
                for ing in course_data.get('ingredients', []):
                    existing_ingredients.add(ing.lower())
        
        # Restricciones del caso existente
        existing_restrictions = set(
            r.lower() for r in 
            existing_case.get('problema', {}).get('restricciones_alimentarias', [])
        )
        
        # Jaccard para ingredientes
        if new_ingredients and existing_ingredients:
            intersection = len(new_ingredients & existing_ingredients)
            union = len(new_ingredients | existing_ingredients)
            ing_sim = intersection / union if union > 0 else 0
        else:
            ing_sim = 0
        
        # Jaccard para restricciones
        if new_restrictions and existing_restrictions:
            intersection = len(new_restrictions & existing_restrictions)
            union = len(new_restrictions | existing_restrictions)
            rest_sim = intersection / union if union > 0 else 0
        else:
            rest_sim = 0.5  # Sin restricciones = neutral
        
        # Similitud combinada
        similarity = ing_sim * 0.7 + rest_sim * 0.3
        max_similarity = max(max_similarity, similarity)
    
    return max_similarity


def calculate_novelty(
    new_case: Dict[str, Any],
    case_base: List[Dict]
) -> float:
    """
    Calcula qué tan novedoso es el caso.
    
    Returns:
        float: Novelty score (0-1). Alto = muy novedoso.
    """
    if not case_base:
        return 1.0  # Primer caso siempre es novedoso
    
    # Contar frecuencia de ingredientes en la base
    ingredient_freq = {}
    total_cases = len(case_base)
    
    for case in case_base:
        case_ingredients = set()
        courses = case.get('solucion', {}).get('courses', {})
        for course_data in courses.values():
            if isinstance(course_data, dict):
                for ing in course_data.get('ingredients', []):
                    case_ingredients.add(ing.lower())
        
        for ing in case_ingredients:
            ingredient_freq[ing] = ingredient_freq.get(ing, 0) + 1
    
    # Ingredientes del nuevo caso
    new_ingredients = set()
    new_courses = new_case.get('solucion', {}).get('courses', {})
    for course_data in new_courses.values():
        if isinstance(course_data, dict):
            for ing in course_data.get('ingredients', []):
                new_ingredients.add(ing.lower())
    
    if not new_ingredients:
        return 0.5
    
    # Calcular rareza promedio
    rarity_scores = []
    for ing in new_ingredients:
        freq = ingredient_freq.get(ing, 0)
        rarity = 1 - (freq / total_cases)  # Menos frecuente = más raro
        rarity_scores.append(rarity)
    
    return sum(rarity_scores) / len(rarity_scores) if rarity_scores else 0.5


def calculate_trace_score(adaptation_steps: List[Dict]) -> float:
    """
    Calcula el score basado en las adaptaciones realizadas.
    
    Returns:
        float: Trace score (0-1). Alto = muchas adaptaciones = valioso aprendizaje.
    """
    if not adaptation_steps:
        return 0.0
    
    # Máximo esperado de pasos de adaptación
    max_steps = 10
    
    # Pesos por tipo de operación
    operation_weights = {
        'substituted': 1.0,
        'removed': 0.8,
        'kept': 0.3,
        'added': 1.0
    }
    
    weighted_score = 0
    for step in adaptation_steps:
        action = step.get('action', 'unknown')
        weight = operation_weights.get(action, 0.5)
        weighted_score += weight
    
    # Normalizar
    score = min(weighted_score / max_steps, 1.0)
    return score


def calculate_usefulness(
    performance: float,
    similarity: float,
    novelty: float,
    trace: float,
    weights: Dict[str, float] = None
) -> float:
    """
    Calcula la utilidad del caso.
    
    IMPORTANTE: Alta similitud = caso redundante = penalización.
    
    Args:
        performance: Qué tan bien resolvió el problema (0-1)
        similarity: Similitud máxima con casos existentes (0-1)
        novelty: Qué tan novedoso es (0-1)
        trace: Esfuerzo de adaptación (0-1)
        weights: Pesos personalizados
        
    Returns:
        float: Usefulness score (0-1)
    """
    if weights is None:
        weights = {
            'performance': 0.40,
            'dissimilarity': 0.15,  # Usamos (1-similarity)
            'novelty': 0.25,
            'trace': 0.20
        }
    
    # Penalizar casos muy similares (redundantes)
    dissimilarity = 1.0 - similarity
    
    usefulness = (
        weights['performance'] * performance +
        weights['dissimilarity'] * dissimilarity +
        weights['novelty'] * novelty +
        weights['trace'] * trace
    )
    
    return min(max(usefulness, 0.0), 1.0)


# ============================================================================
# CREACIÓN DE CASO
# ============================================================================

def create_new_case(
    menu: Dict[str, Any],
    problema: Dict[str, Any],
    adaptation_steps: List[Dict],
    usefulness: float,
    revision_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Crea un nuevo caso con la estructura correcta para la base de casos.
    
    Estructura: id_caso, problema, solucion, utilidad, traza
    
    Traza tiene solo 3 campos:
    - sustitucion: lista de tuplas [elemento_quitado, elemento_nuevo]
    - eliminacion: lista de elementos eliminados
    - adicion: lista de elementos añadidos
    """
    # Generar ID único
    case_id = int(datetime.now().timestamp())
    
    # Extraer operadores de adaptación en la nueva estructura
    sustituciones = []  # Lista de [original, sustituto]
    eliminaciones = []  # Lista de elementos eliminados
    adiciones = []      # Lista de elementos añadidos
    
    for step in adaptation_steps:
        action = step.get('action', 'unknown')
        original = step.get('original', '')
        substitute = step.get('substitute', '')
        
        if action == 'substituted':
            sustituciones.append([original, substitute])
        elif action == 'removed':
            if original and original not in eliminaciones:
                eliminaciones.append(original)
        elif action == 'added':
            if substitute and substitute not in adiciones:
                adiciones.append(substitute)
    
    # Extraer las restricciones que el menú REALMENTE cumple después de la adaptación
    # Esto viene del campo features.common_dietary_restrictions del menú adaptado
    menu_restrictions = []
    if 'features' in menu and 'common_dietary_restrictions' in menu['features']:
        menu_restrictions = menu['features']['common_dietary_restrictions']
    
    # Si no hay restricciones en features, usar las del problema (fallback)
    if not menu_restrictions:
        menu_restrictions = problema.get('restrictions', [])
    
    return {
        'id_caso': case_id,
        'problema': {
            'restricciones_alimentarias': menu_restrictions,
            'cultura_preferible': problema.get('culture', problema.get('cuisine', ''))
        },
        'solucion': menu,
        'utilidad': round(usefulness, 3),
        'traza': {
            'sustitucion': sustituciones,
            'eliminacion': eliminaciones,
            'adicion': adiciones
        }
    }


# ============================================================================
# FUNCIÓN PRINCIPAL DE RETAIN
# ============================================================================

def retain_case(
    adapted_menu: Dict[str, Any],
    problema: Dict[str, Any],
    adaptation_steps: List[Dict],
    revision_results: Dict[str, Any],
    case_base: List[Dict] = None,
    threshold: float = 0.5,
    save_failed: bool = True,
    filepath: str = None
) -> Dict[str, Any]:
    """
    Fase RETAIN: Decide si guardar el caso en la base.
    
    Args:
        adapted_menu: Menú adaptado
        problema: Problema del usuario (restrictions, culture)
        adaptation_steps: Pasos de adaptación realizados
        revision_results: Resultados de la fase REVISE
        case_base: Base de casos (se carga si es None)
        threshold: Umbral mínimo de utilidad para guardar
        save_failed: Si True, guarda casos fallidos para aprender
        filepath: Ruta de la base de casos
        
    Returns:
        Dict con decisión de retención y métricas
    """
    print("\n" + "="*70)
    print("💾 FASE RETAIN: Evaluación de Utilidad")
    print("="*70)
    
    # Cargar base de casos si no se proporciona
    if case_base is None:
        case_base = load_case_base(filepath)
    
    # Crear estructura del caso para evaluación
    new_case_struct = {
        'problema': {
            'restricciones_alimentarias': problema.get('restrictions', []),
            'cultura_preferible': problema.get('culture', problema.get('cuisine', ''))
        },
        'solucion': adapted_menu
    }
    
    # Calcular métricas
    performance = revision_results.get('performance', 0.5)
    similarity = calculate_similarity_to_base(new_case_struct, case_base)
    novelty = calculate_novelty(new_case_struct, case_base)
    trace = calculate_trace_score(adaptation_steps)
    
    # Calcular utilidad
    usefulness = calculate_usefulness(performance, similarity, novelty, trace)
    
    # Mostrar métricas
    print(f"\n📈 Métricas de Utilidad:")
    print(f"   • Performance:    {performance:.3f}")
    print(f"   • Similitud:      {similarity:.3f} (alto = redundante)")
    print(f"   • Novelty:        {novelty:.3f}")
    print(f"   • Trace:          {trace:.3f}")
    print(f"   ─────────────────────────")
    print(f"   → Utilidad:       {usefulness:.3f}")
    
    # Decisión de retención
    is_valid = revision_results.get('is_valid', True)
    should_save = usefulness >= threshold
    saved_as_failed = False
    
    # Guardar casos fallidos para aprender de errores
    if not is_valid and save_failed:
        print(f"\n⚠️ Caso fallido detectado - se guardará para aprendizaje")
        should_save = True
        saved_as_failed = True
    
    result = {
        'usefulness': usefulness,
        'performance': performance,
        'similarity': similarity,
        'novelty': novelty,
        'trace': trace,
        'threshold': threshold,
        'should_retain': should_save,
        'saved_as_failed': saved_as_failed,
        'case_saved': False,
        'new_case_id': None
    }
    
    # Guardar si procede
    if should_save:
        new_case = create_new_case(
            adapted_menu, problema, adaptation_steps, usefulness, revision_results
        )
        
        case_base.append(new_case)
        save_case_base(case_base, filepath)
        
        result['case_saved'] = True
        result['new_case_id'] = new_case['id_caso']
        
        if saved_as_failed:
            print(f"\n⚠️ DECISIÓN: CASO GUARDADO (fallido - para aprendizaje)")
        else:
            print(f"\n✅ DECISIÓN: CASO GUARDADO")
        print(f"   ID: {new_case['id_caso']}")
        print(f"   Utilidad: {usefulness:.3f}")
    else:
        print(f"\n❌ DECISIÓN: CASO DESCARTADO")
        print(f"   Utilidad ({usefulness:.3f}) < Umbral ({threshold})")
    
    return result


# ============================================================================
# ESTADÍSTICAS
# ============================================================================

def get_case_base_stats(case_base: List[Dict] = None) -> Dict[str, Any]:
    """Obtiene estadísticas de la base de casos."""
    if case_base is None:
        case_base = load_case_base()
    
    if not case_base:
        return {'size': 0, 'message': 'Base de casos vacía'}
    
    utilities = [c.get('utilidad', 0) for c in case_base]
    
    # Contar casos con adaptaciones (nueva estructura de traza)
    cases_with_adaptations = 0
    for c in case_base:
        traza = c.get('traza', {})
        # Nueva estructura: sustitucion, eliminacion, adicion
        has_new_format = (
            len(traza.get('sustitucion', [])) > 0 or
            len(traza.get('eliminacion', [])) > 0 or
            len(traza.get('adicion', [])) > 0
        )
        # Compatibilidad con estructura antigua
        has_old_format = len(traza.get('operadores_aplicados', [])) > 0
        
        if has_new_format or has_old_format:
            cases_with_adaptations += 1
    
    return {
        'size': len(case_base),
        'avg_utility': sum(utilities) / len(utilities),
        'min_utility': min(utilities),
        'max_utility': max(utilities),
        'cases_with_adaptations': cases_with_adaptations
    }


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test de utilidad
    test_steps = [
        {'action': 'substituted', 'original': 'butter', 'substitute': 'olive oil'},
        {'action': 'removed', 'original': 'cheese'}
    ]
    
    trace_score = calculate_trace_score(test_steps)
    print(f"Trace score: {trace_score}")
    
    # Estadísticas
    stats = get_case_base_stats()
    print(f"\n📊 Estadísticas de la base de casos:")
    for k, v in stats.items():
        print(f"   {k}: {v}")
