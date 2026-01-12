"""
Módulo de Adaptación (Adapt)
=============================
Sistema de adaptación de menús basado en:
1. Restricciones alimentarias
2. Cultura culinaria
3. Food pairing molecular
"""

import json
import os
import copy
from typing import Dict, List, Tuple, Optional, Set

# ============================================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
# Bases de conocimiento
RESTRICCIONES_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ingredientes_por_restriccion.json')
CONTEXTO_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ingredientes_por_contexto.json')
ONTOLOGIA_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ontologia_ingredientes_cultura.json')
PAIRING_FILE = os.path.join(BASE_DIR, 'Otras_Bases', 'molecular_pairing_db.json')


# ============================================================================
# FUNCIONES DE CARGA DE DATOS
# ============================================================================

def load_json_file(filepath: str) -> dict:
    """Carga un archivo JSON."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  Error: No se encontró el archivo {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"⚠️  Error: El archivo {filepath} no es un JSON válido")
        return {}


def load_all_knowledge_bases() -> Tuple[dict, dict, dict, dict]:
    """Carga todas las bases de conocimiento necesarias."""
    restricciones = load_json_file(RESTRICCIONES_FILE)
    contexto = load_json_file(CONTEXTO_FILE)
    ontologia = load_json_file(ONTOLOGIA_FILE)
    pairing = load_json_file(PAIRING_FILE)
    
    return restricciones, contexto, ontologia, pairing


# ============================================================================
# NORMALIZACIÓN
# ============================================================================

def normalize_ingredient(ingredient: str) -> str:
    """Normaliza un ingrediente para comparación."""
    return ingredient.lower().strip().replace('-', ' ').replace('_', ' ')


def normalize_restriction(restriction: str) -> str:
    """Normaliza una restricción para usarla como clave."""
    return restriction.lower().strip().replace(' ', '-').replace('_', '-')


def denormalize_ingredient_for_ontology(ingredient: str) -> str:
    """Convierte un ingrediente normalizado al formato de la ontología (con guiones)."""
    return ingredient.lower().strip().replace(' ', '-').replace('_', '-')


# Sustitutos conocidos para ingredientes que no tienen alternativas en su categoría
# Útil para restricciones como vegan donde necesitamos cambiar a otra categoría
KNOWN_SUBSTITUTES = {
    # Sustitutos veganos para lácteos
    'butter': ['coconut oil', 'olive oil', 'vegan butter', 'margarine'],
    'cheese': ['nutritional yeast', 'cashew cheese', 'tofu'],
    'milk': ['almond milk', 'oat milk', 'soy milk', 'coconut milk'],
    'cream': ['coconut cream', 'cashew cream', 'oat cream'],
    'yogurt': ['coconut yogurt', 'soy yogurt', 'almond yogurt'],
    'eggs': ['flax egg', 'chia egg', 'silken tofu', 'applesauce', 'banana'],
    'egg': ['flax egg', 'chia egg', 'silken tofu', 'applesauce', 'banana'],
    'honey': ['maple syrup', 'agave nectar', 'date syrup'],
    # Sustitutos sin gluten
    'flour': ['almond flour', 'rice flour', 'oat flour', 'coconut flour'],
    'bread': ['gluten free bread', 'rice bread'],
    'pasta': ['rice pasta', 'quinoa pasta', 'zucchini noodles'],
    'soy sauce': ['coconut aminos', 'tamari'],
    # Sustitutos sin frutos secos
    'almond': ['sunflower seeds', 'pumpkin seeds'],
    'peanut': ['sunflower seed butter', 'soy butter'],
    'cashew': ['sunflower seeds', 'hemp seeds'],
}


# ============================================================================
# ANÁLISIS DE RESTRICCIONES ALIMENTARIAS
# ============================================================================

def find_ingredients_violating_restriction(
    ingredients: List[str], 
    restriction: str, 
    restricciones_db: dict
) -> List[str]:
    """
    Encuentra ingredientes que violan una restricción alimentaria.
    
    Un ingrediente viola la restricción si:
    - Está en ingredients_forbidden, O
    - NO está en ingredients_allowed (y la lista de allowed tiene elementos)
    
    Usa matching flexible para manejar variaciones de nombres.
    
    Args:
        ingredients: Lista de ingredientes del plato
        restriction: Restricción a verificar (ej: 'vegan', 'gluten-free')
        restricciones_db: Base de datos de restricciones
        
    Returns:
        Lista de ingredientes que violan la restricción
    """
    # Normalizar la restricción para usarla como clave
    restriction_key = normalize_restriction(restriction)
    
    restriction_data = restricciones_db.get(restriction_key, {})
    
    if not restriction_data:
        print(f"⚠️  Restricción '{restriction_key}' no encontrada en la base de datos")
        return []
    
    # Obtener listas de ingredientes permitidos y prohibidos
    allowed = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_allowed', []))
    forbidden = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_forbidden', []))
    
    violating = []
    
    for ingredient in ingredients:
        ing_normalized = normalize_ingredient(ingredient)
        
        # Primero verificar si está explícitamente prohibido
        is_forbidden = ing_normalized in forbidden
        
        # Verificar si está permitido (matching exacto o flexible)
        is_allowed = ing_normalized in allowed
        
        # Si no hay match exacto, intentar matching flexible
        if not is_allowed and not is_forbidden:
            # Buscar si algún ingrediente permitido contiene este nombre o viceversa
            for allowed_ing in allowed:
                if (ing_normalized in allowed_ing or 
                    allowed_ing in ing_normalized or
                    ing_normalized.split()[0] == allowed_ing):  # Match por primera palabra
                    is_allowed = True
                    break
            
            # También verificar en forbidden con matching flexible
            if not is_allowed:
                for forbidden_ing in forbidden:
                    if (ing_normalized in forbidden_ing or 
                        forbidden_ing in ing_normalized):
                        is_forbidden = True
                        break
        
        # Si está en ambas listas (error de datos), priorizar forbidden
        if is_forbidden and is_allowed:
            is_allowed = False
        
        # Solo agregar si está prohibido o no está permitido
        if is_forbidden or not is_allowed:
            violating.append(ingredient)
    
    return violating


# ============================================================================
# ANÁLISIS DE CULTURA (usando ontología)
# ============================================================================

# Culturas disponibles en la ontología
AVAILABLE_CULTURES = [
    'Latin American', 'French/Western European', 'Mediterranean', 'South Asian',
    'Chinese', 'American', 'Italian', 'East Asian', 'Japanese',
    'Middle Eastern/North African', 'Korean', 'Global/Common', 'Unspecified'
]

# Mapeo de culturas específicas a culturas de la ontología
CULTURE_TO_ONTOLOGY = {
    # Latin American
    'mexican': 'Latin American',
    'tex-mex': 'Latin American',
    'caribbean': 'Latin American',
    'brazilian': 'Latin American',
    'peruvian': 'Latin American',
    'argentinian': 'Latin American',
    # French/Western European
    'french': 'French/Western European',
    'german': 'French/Western European',
    'british': 'French/Western European',
    'dutch': 'French/Western European',
    'belgian': 'French/Western European',
    # Mediterranean
    'greek': 'Mediterranean',
    'spanish': 'Mediterranean',
    'turkish': 'Mediterranean',
    # East Asian
    'thai': 'East Asian',
    'vietnamese': 'East Asian',
    'southeast asian': 'East Asian',
    # Middle Eastern
    'arab': 'Middle Eastern/North African',
    'persian': 'Middle Eastern/North African',
    'moroccan': 'Middle Eastern/North African',
    'lebanese': 'Middle Eastern/North African',
    'egyptian': 'Middle Eastern/North African',
    # South Asian
    'indian': 'South Asian',
    'pakistani': 'South Asian',
    'bangladeshi': 'South Asian',
}


def normalize_culture_name(culture: str) -> Optional[str]:
    """
    Normaliza el nombre de una cultura para que coincida con las claves de la ontología.
    
    Args:
        culture: Nombre de cultura del usuario
        
    Returns:
        Nombre normalizado que coincide con la ontología, o None si no se encuentra
    """
    culture_lower = culture.lower().strip()
    
    # Primero, verificar si es una cultura específica que debe mapearse
    if culture_lower in CULTURE_TO_ONTOLOGY:
        return CULTURE_TO_ONTOLOGY[culture_lower]
    
    # Luego, buscar coincidencia directa o parcial con las culturas disponibles
    for available in AVAILABLE_CULTURES:
        if culture_lower == available.lower():
            return available
        # También buscar coincidencia parcial
        if culture_lower in available.lower() or available.lower() in culture_lower:
            return available
    
    return None


def is_ingredient_in_culture(
    ingredient: str,
    culture: str,
    ontologia_db: dict
) -> bool:
    """
    Verifica si un ingrediente pertenece a una cultura específica en la ontología.
    
    Args:
        ingredient: Ingrediente a verificar
        culture: Cultura deseada (debe coincidir con las claves de la ontología)
        ontologia_db: Base de datos de ontología
        
    Returns:
        True si el ingrediente está en esa cultura, False si no
    """
    ing_normalized = denormalize_ingredient_for_ontology(ingredient)
    ontology_tree = ontologia_db.get('ontology_tree', {})
    
    # Normalizar nombre de cultura
    culture_key = normalize_culture_name(culture)
    if not culture_key:
        return False
    
    # Obtener el nodo de la cultura
    culture_node = ontology_tree.get(culture_key, {})
    if not culture_node:
        return False
    
    # Buscar el ingrediente en todas las categorías de esta cultura
    def search_in_node(node: dict) -> bool:
        if '__ingredients' in node:
            if ing_normalized in node['__ingredients']:
                return True
        
        for key, value in node.items():
            if key != '__ingredients' and isinstance(value, dict):
                if search_in_node(value):
                    return True
        
        return False
    
    return search_in_node(culture_node)


def find_ingredients_not_in_culture(
    ingredients: List[str], 
    culture: str, 
    ontologia_db: dict
) -> List[str]:
    """
    Encuentra ingredientes que NO pertenecen a la cultura deseada.
    Busca directamente en la ontología.
    
    Args:
        ingredients: Lista de ingredientes del plato
        culture: Cultura deseada (ej: 'Italian', 'Mediterranean', 'American')
        ontologia_db: Base de datos de ontología
        
    Returns:
        Lista de ingredientes que NO están en la cultura deseada
    """
    # Verificar que la cultura existe
    culture_key = normalize_culture_name(culture)
    if not culture_key:
        print(f"⚠️  Cultura '{culture}' no encontrada en la ontología")
        print(f"   Culturas disponibles: {', '.join(AVAILABLE_CULTURES)}")
        return []
    
    not_in_culture = []
    
    for ingredient in ingredients:
        # Verificar si el ingrediente está en la cultura deseada
        if not is_ingredient_in_culture(ingredient, culture_key, ontologia_db):
            not_in_culture.append(ingredient)
    
    return not_in_culture


# ============================================================================
# BÚSQUEDA EN ONTOLOGÍA
# ============================================================================

def find_ingredient_in_ontology(
    ingredient: str, 
    ontologia_db: dict
) -> Optional[Dict]:
    """
    Busca un ingrediente en la ontología y devuelve su ubicación.
    
    Args:
        ingredient: Ingrediente a buscar
        ontologia_db: Base de datos de ontología
        
    Returns:
        Dict con 'culture', 'category', 'subcategory', 'path' o None si no se encuentra
    """
    ing_normalized = denormalize_ingredient_for_ontology(ingredient)
    ontology_tree = ontologia_db.get('ontology_tree', {})
    
    for culture, categories in ontology_tree.items():
        if not isinstance(categories, dict):
            continue
            
        for category, subcategories in categories.items():
            if not isinstance(subcategories, dict):
                continue
            
            # Revisar ingredientes directamente en la categoría
            if '__ingredients' in subcategories:
                if ing_normalized in subcategories['__ingredients']:
                    return {
                        'culture': culture,
                        'category': category,
                        'subcategory': None,
                        'path': [culture, category]
                    }
            
            # Revisar subcategorías
            for subcategory, content in subcategories.items():
                if subcategory == '__ingredients':
                    continue
                    
                if isinstance(content, dict):
                    if '__ingredients' in content:
                        if ing_normalized in content['__ingredients']:
                            return {
                                'culture': culture,
                                'category': category,
                                'subcategory': subcategory,
                                'path': [culture, category, subcategory]
                            }
                    
                    # Nivel más profundo
                    for sub_sub, sub_content in content.items():
                        if sub_sub == '__ingredients':
                            continue
                        if isinstance(sub_content, dict) and '__ingredients' in sub_content:
                            if ing_normalized in sub_content['__ingredients']:
                                return {
                                    'culture': culture,
                                    'category': category,
                                    'subcategory': subcategory,
                                    'path': [culture, category, subcategory, sub_sub]
                                }
    
    return None


def get_ingredients_from_node(node: dict) -> List[str]:
    """Extrae todos los ingredientes de un nodo de la ontología (recursivo)."""
    ingredients = []
    
    if '__ingredients' in node:
        ingredients.extend(node['__ingredients'])
    
    for key, value in node.items():
        if key != '__ingredients' and isinstance(value, dict):
            ingredients.extend(get_ingredients_from_node(value))
    
    return ingredients


def find_substitute_candidates(
    ingredient: str, 
    ontologia_db: dict
) -> Tuple[List[str], str]:
    """
    Encuentra ingredientes candidatos para sustituir al ingrediente dado.
    Busca primero en la subcategoría, luego en la categoría.
    Solo busca dentro de la cultura original del ingrediente.
    
    Args:
        ingredient: Ingrediente a sustituir
        ontologia_db: Base de datos de ontología
        
    Returns:
        Tuple de (lista de candidatos, nivel donde se encontraron)
    """
    location = find_ingredient_in_ontology(ingredient, ontologia_db)
    
    if not location:
        return [], 'not_found'
    
    ontology_tree = ontologia_db.get('ontology_tree', {})
    culture = location['culture']
    category = location['category']
    subcategory = location.get('subcategory')
    
    ing_normalized = denormalize_ingredient_for_ontology(ingredient)
    candidates = []
    level = 'subcategory'
    
    # Intentar primero en subcategoría
    if subcategory:
        try:
            subcategory_node = ontology_tree[culture][category][subcategory]
            candidates = get_ingredients_from_node(subcategory_node)
        except (KeyError, TypeError):
            pass
    
    # Si no hay suficientes candidatos, buscar en categoría
    if len(candidates) <= 1:
        level = 'category'
        try:
            category_node = ontology_tree[culture][category]
            candidates = get_ingredients_from_node(category_node)
        except (KeyError, TypeError):
            pass
    
    # Eliminar duplicados y excluir el ingrediente original
    candidates = list(set(c for c in candidates if c != ing_normalized))
    
    return candidates, level


# ============================================================================
# FOOD PAIRING MOLECULAR
# ============================================================================

def calculate_pairing_score(
    candidate: str, 
    other_ingredients: List[str], 
    pairing_db: dict
) -> float:
    """
    Calcula el score de food pairing entre un candidato y otros ingredientes.
    
    Args:
        candidate: Ingrediente candidato
        other_ingredients: Lista de otros ingredientes del plato
        pairing_db: Base de datos de food pairing
        
    Returns:
        Score total de pairing
    """
    # Normalizar candidato para búsqueda en la base de datos
    candidate_lower = candidate.lower().replace('-', ' ')
    
    # Obtener los pairings del candidato
    candidate_pairings = {}
    
    # Buscar el candidato en la base de datos
    for key, pairings in pairing_db.items():
        key_normalized = key.lower()
        if candidate_lower in key_normalized or key_normalized in candidate_lower:
            for p in pairings:
                pair_name = p.get('pair', '').lower()
                score = p.get('score', 0)
                candidate_pairings[pair_name] = max(candidate_pairings.get(pair_name, 0), score)
    
    # Calcular score total con otros ingredientes
    total_score = 0
    
    for other in other_ingredients:
        other_normalized = normalize_ingredient(other)
        
        # Buscar coincidencia en los pairings del candidato
        for pair_name, score in candidate_pairings.items():
            if other_normalized in pair_name or pair_name in other_normalized:
                total_score += score
                break
    
    return total_score


def select_best_substitute(
    candidates: List[str], 
    other_ingredients: List[str], 
    pairing_db: dict,
    restriction: Optional[str] = None,
    restricciones_db: Optional[dict] = None,
    all_restrictions: Optional[List[str]] = None
) -> Optional[str]:
    """
    Selecciona el mejor sustituto basándose en food pairing.
    Si hay restricciones, filtra candidatos que las cumplan TODAS.
    
    Args:
        candidates: Lista de candidatos
        other_ingredients: Otros ingredientes del plato
        pairing_db: Base de datos de food pairing
        restriction: Restricción principal a cumplir (opcional, deprecated)
        restricciones_db: Base de datos de restricciones (opcional)
        all_restrictions: Lista de todas las restricciones a cumplir (opcional)
        
    Returns:
        Mejor candidato o None
    """
    if not candidates:
        return None
    
    # Determinar lista de restricciones a verificar
    restrictions_to_check = all_restrictions if all_restrictions else ([restriction] if restriction else [])
    
    # Filtrar por restricciones
    valid_candidates = candidates
    if restrictions_to_check and restricciones_db:
        for rest in restrictions_to_check:
            if not rest:
                continue
            restriction_key = normalize_restriction(rest)
            restriction_data = restricciones_db.get(restriction_key, {})
            allowed = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_allowed', []))
            forbidden = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_forbidden', []))
            
            # Filtrar candidatos que cumplan esta restricción
            valid_candidates = [
                c for c in valid_candidates 
                if normalize_ingredient(c.replace('-', ' ')) in allowed 
                and normalize_ingredient(c.replace('-', ' ')) not in forbidden
            ]
    
    if not valid_candidates:
        return None
    
    if len(valid_candidates) == 1:
        return valid_candidates[0]
    
    # Calcular scores de pairing
    scored_candidates = []
    for candidate in valid_candidates:
        score = calculate_pairing_score(candidate, other_ingredients, pairing_db)
        scored_candidates.append((candidate, score))
    
    # Ordenar por score descendente
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    return scored_candidates[0][0]


# ============================================================================
# MÓDULO PRINCIPAL DE ADAPTACIÓN
# ============================================================================

# Configuración de adaptación gradual para cultura
MAX_CULTURE_SUBSTITUTIONS_PER_ROUND = 3  # Máximo de ingredientes a cambiar por cultura en cada ronda


# ============================================================================
# AJUSTE CULTURAL (SEGUNDA RONDA)
# ============================================================================

def get_all_ingredients_from_culture(culture: str, ontologia_db: dict) -> List[str]:
    """
    Obtiene TODOS los ingredientes de una cultura específica de la ontología.
    
    Args:
        culture: Nombre de la cultura (ej: 'Italian', 'Mediterranean')
        ontologia_db: Base de datos de ontología
        
    Returns:
        Lista de todos los ingredientes de esa cultura
    """
    culture_key = normalize_culture_name(culture)
    if not culture_key:
        print(f"⚠️  Cultura '{culture}' no encontrada en la ontología")
        return []
    
    ontology_tree = ontologia_db.get('ontology_tree', {})
    culture_node = ontology_tree.get(culture_key, {})
    
    if not culture_node:
        return []
    
    return get_ingredients_from_node(culture_node)


def find_ingredient_to_remove_from_culture(
    ingredients: List[str],
    culture: str,
    ontologia_db: dict
) -> Optional[str]:
    """
    Encuentra un ingrediente del plato que pertenezca a la cultura especificada
    para poder eliminarlo (operación 'remove').
    
    Args:
        ingredients: Lista de ingredientes actuales del plato
        culture: Cultura de la cual queremos eliminar un ingrediente
        ontologia_db: Base de datos de ontología
        
    Returns:
        Ingrediente a eliminar o None si no hay ninguno de esa cultura
    """
    for ingredient in ingredients:
        if is_ingredient_in_culture(ingredient, culture, ontologia_db):
            return ingredient
    return None


def find_ingredient_to_add_from_culture(
    current_ingredients: List[str],
    culture: str,
    ontologia_db: dict,
    pairing_db: dict,
    restrictions: List[str] = None,
    restricciones_db: dict = None
) -> Optional[str]:
    """
    Encuentra un ingrediente de la cultura especificada para añadir al plato.
    Usa food pairing para elegir el mejor candidato.
    
    Args:
        current_ingredients: Ingredientes actuales del plato
        culture: Cultura de la cual queremos añadir un ingrediente
        ontologia_db: Base de datos de ontología
        pairing_db: Base de datos de food pairing
        restrictions: Restricciones alimentarias a cumplir
        restricciones_db: Base de datos de restricciones
        
    Returns:
        Ingrediente a añadir o None si no se encuentra ninguno válido
    """
    # Obtener todos los ingredientes de la cultura
    culture_ingredients = get_all_ingredients_from_culture(culture, ontologia_db)
    
    if not culture_ingredients:
        return None
    
    # Excluir ingredientes que ya están en el plato
    current_normalized = set(normalize_ingredient(i) for i in current_ingredients)
    candidates = [
        ing for ing in culture_ingredients 
        if normalize_ingredient(ing.replace('-', ' ')) not in current_normalized
    ]
    
    if not candidates:
        return None
    
    # Filtrar por restricciones si las hay
    if restrictions and restricciones_db:
        valid_candidates = []
        for candidate in candidates:
            is_valid = True
            for restriction in restrictions:
                restriction_key = normalize_restriction(restriction)
                restriction_data = restricciones_db.get(restriction_key, {})
                forbidden = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_forbidden', []))
                
                if normalize_ingredient(candidate.replace('-', ' ')) in forbidden:
                    is_valid = False
                    break
            
            if is_valid:
                valid_candidates.append(candidate)
        
        candidates = valid_candidates
    
    if not candidates:
        return None
    
    # Usar food pairing para seleccionar el mejor
    best_candidate = select_best_substitute(
        candidates,
        current_ingredients,
        pairing_db,
        all_restrictions=restrictions,
        restricciones_db=restricciones_db
    )
    
    # Si no hay match de pairing, elegir uno aleatorio de los primeros 10
    if not best_candidate and candidates:
        import random
        best_candidate = random.choice(candidates[:min(10, len(candidates))])
    
    return best_candidate


def apply_culture_adjustment(
    menu: dict,
    adjustment_type: str,
    target_culture: str,
    ontologia_db: dict = None,
    pairing_db: dict = None,
    restrictions: List[str] = None,
    restricciones_db: dict = None
) -> Dict:
    """
    Aplica un ajuste cultural obligatorio al menú (añadir o eliminar ingrediente).
    
    Esta función se usa en SEGUNDA RONDA cuando el usuario quiere:
    - 'add': Añadir un toque de una cultura → añade 1 ingrediente de esa cultura
    - 'remove': Eliminar un toque de una cultura → elimina 1 ingrediente de esa cultura
    
    Args:
        menu: Menú a ajustar (estructura con 'courses')
        adjustment_type: 'add' o 'remove'
        target_culture: Cultura objetivo del ajuste
        ontologia_db: Base de datos de ontología
        pairing_db: Base de datos de food pairing
        restrictions: Restricciones alimentarias a respetar
        restricciones_db: Base de datos de restricciones
        
    Returns:
        Dict con el menú ajustado e información del cambio
    """
    # Cargar bases si no se proporcionan
    if ontologia_db is None or pairing_db is None:
        _, _, ontologia_db, pairing_db = load_all_knowledge_bases()
    if restricciones_db is None:
        restricciones_db, _, _, _ = load_all_knowledge_bases()
    
    adjusted_menu = copy.deepcopy(menu)
    courses = adjusted_menu.get('courses', {})
    
    adjustment_made = False
    adjustment_details = {
        'type': adjustment_type,
        'culture': target_culture,
        'course_affected': None,
        'ingredient_added': None,
        'ingredient_removed': None
    }
    
    # Intentar aplicar el ajuste en uno de los platos (preferir main, luego starter, luego dessert)
    course_priority = ['main', 'starter', 'dessert']
    
    for course_name in course_priority:
        if course_name not in courses:
            continue
        
        course_data = courses[course_name]
        current_ingredients = course_data.get('ingredients', [])
        
        if adjustment_type == 'add':
            # AÑADIR ingrediente de la cultura
            new_ingredient = find_ingredient_to_add_from_culture(
                current_ingredients,
                target_culture,
                ontologia_db,
                pairing_db,
                restrictions,
                restricciones_db
            )
            
            if new_ingredient:
                # Añadir el ingrediente
                current_ingredients.append(new_ingredient.replace('-', ' '))
                courses[course_name]['ingredients'] = current_ingredients
                
                adjustment_made = True
                adjustment_details['course_affected'] = course_name
                adjustment_details['ingredient_added'] = new_ingredient.replace('-', ' ')
                
                # Añadir info de adaptación
                if '_adaptation' not in courses[course_name]:
                    courses[course_name]['_adaptation'] = {'substitutions': []}
                courses[course_name]['_adaptation']['substitutions'].append({
                    'original': None,
                    'substitute': new_ingredient.replace('-', ' '),
                    'reason': [f"Añadido toque de cultura '{target_culture}'"],
                    'action': 'added'
                })
                break
                
        elif adjustment_type == 'remove':
            # ELIMINAR ingrediente de la cultura
            ingredient_to_remove = find_ingredient_to_remove_from_culture(
                current_ingredients,
                target_culture,
                ontologia_db
            )
            
            if ingredient_to_remove:
                # Eliminar el ingrediente
                current_ingredients.remove(ingredient_to_remove)
                courses[course_name]['ingredients'] = current_ingredients
                
                adjustment_made = True
                adjustment_details['course_affected'] = course_name
                adjustment_details['ingredient_removed'] = ingredient_to_remove
                
                # Añadir info de adaptación
                if '_adaptation' not in courses[course_name]:
                    courses[course_name]['_adaptation'] = {'substitutions': []}
                courses[course_name]['_adaptation']['substitutions'].append({
                    'original': ingredient_to_remove,
                    'substitute': None,
                    'reason': [f"Eliminado toque de cultura '{target_culture}'"],
                    'action': 'removed'
                })
                break
    
    adjusted_menu['courses'] = courses
    
    return {
        'adjusted': adjustment_made,
        'menu': adjusted_menu,
        'adjustment_details': adjustment_details,
        'message': _generate_adjustment_message(adjustment_made, adjustment_details)
    }


def _generate_adjustment_message(success: bool, details: dict) -> str:
    """Genera un mensaje descriptivo del ajuste realizado."""
    if not success:
        if details['type'] == 'add':
            return f"❌ No se pudo añadir ingrediente de cultura '{details['culture']}' (no hay candidatos válidos)"
        else:
            return f"❌ No se pudo eliminar ingrediente de cultura '{details['culture']}' (no hay ingredientes de esa cultura)"
    
    if details['type'] == 'add':
        return f"✅ Añadido '{details['ingredient_added']}' ({details['culture']}) en {details['course_affected']}"
    else:
        return f"✅ Eliminado '{details['ingredient_removed']}' ({details['culture']}) de {details['course_affected']}"


def get_known_substitutes(ingredient: str, restrictions: List[str], restricciones_db: dict) -> List[str]:
    """
    Obtiene sustitutos conocidos para un ingrediente que cumplan las restricciones.
    
    Args:
        ingredient: Ingrediente a sustituir
        restrictions: Lista de restricciones a cumplir
        restricciones_db: Base de datos de restricciones
        
    Returns:
        Lista de sustitutos válidos
    """
    ing_normalized = normalize_ingredient(ingredient)
    
    # Buscar en el diccionario de sustitutos conocidos
    candidates = []
    for key, substitutes in KNOWN_SUBSTITUTES.items():
        if key in ing_normalized or ing_normalized in key:
            candidates.extend(substitutes)
    
    if not candidates:
        return []
    
    # Filtrar por restricciones
    valid_substitutes = []
    for candidate in candidates:
        is_valid = True
        for restriction in restrictions:
            restriction_key = normalize_restriction(restriction)
            restriction_data = restricciones_db.get(restriction_key, {})
            allowed = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_allowed', []))
            forbidden = set(normalize_ingredient(i) for i in restriction_data.get('ingredients_forbidden', []))
            
            candidate_normalized = normalize_ingredient(candidate)
            
            # Si está prohibido o no está permitido, no es válido
            if candidate_normalized in forbidden:
                is_valid = False
                break
            # Si hay lista de permitidos y no está, marcamos como posiblemente inválido
            # pero solo si la lista existe y tiene elementos
            # (algunos ingredientes pueden no estar catalogados)
        
        if is_valid:
            valid_substitutes.append(candidate)
    
    return valid_substitutes


def adapt_course(
    course_data: dict, 
    restrictions_not_met: List[str],
    culture_not_met: Optional[str],
    restricciones_db: dict,
    contexto_db: dict,  # DEPRECATED: Ya no se usa, se mantiene por compatibilidad
    ontologia_db: dict,
    pairing_db: dict,
    max_culture_subs: int = MAX_CULTURE_SUBSTITUTIONS_PER_ROUND
) -> Dict:
    """
    Adapta un plato individual para cumplir con restricciones y cultura.
    
    IMPORTANTE: 
    - Las restricciones alimentarias son HARD CONDITIONS: se cambian TODOS de una vez.
    - La cultura es SOFT CONSTRAINT: se cambian máximo 2-3 ingredientes por ronda
      para permitir adaptaciones graduales en rondas siguientes.
    
    Args:
        course_data: Datos del plato (ingredientes, título, etc.)
        restrictions_not_met: Lista de restricciones no cumplidas
        culture_not_met: Cultura no cumplida (o None)
        restricciones_db: Base de datos de restricciones
        contexto_db: DEPRECATED - Ya no se usa (se mantiene por compatibilidad)
        ontologia_db: Base de datos de ontología (usada para cultura)
        pairing_db: Base de datos de food pairing
        max_culture_subs: Máximo de sustituciones por cultura en esta ronda (default: 3)
        
    Returns:
        Dict con el plato adaptado e información de cambios
    """
    original_ingredients = course_data.get('ingredients', [])
    
    # Conjunto de ingredientes a sustituir y sus razones
    restriction_ingredients = set()  # Ingredientes que violan restricciones (HARD)
    culture_ingredients = []  # Ingredientes que no cuadran con la cultura (SOFT, lista ordenada)
    substitution_reasons = {}  # ingredient -> lista de razones
    restriction_violations = {}  # ingredient -> lista de restricciones violadas (hard constraints)
    
    # 1. Verificar restricciones alimentarias (HARD CONSTRAINTS - cambiar TODOS)
    for restriction in restrictions_not_met:
        violating = find_ingredients_violating_restriction(
            original_ingredients, restriction, restricciones_db
        )
        for ing in violating:
            restriction_ingredients.add(ing)
            if ing not in substitution_reasons:
                substitution_reasons[ing] = []
                restriction_violations[ing] = []
            substitution_reasons[ing].append(f"viola restricción '{restriction}'")
            restriction_violations[ing].append(restriction)
    
    # 2. Verificar cultura (SOFT CONSTRAINT - cambiar solo max_culture_subs por ronda)
    #    Ahora usa la ontología directamente
    culture_violations_all = []  # Todos los que violan cultura
    if culture_not_met:
        not_in_culture = find_ingredients_not_in_culture(
            original_ingredients, culture_not_met, ontologia_db
        )
        for ing in not_in_culture:
            # Solo agregar si NO viola también una restricción (evitar duplicados)
            if ing not in restriction_ingredients:
                culture_violations_all.append(ing)
                if ing not in substitution_reasons:
                    substitution_reasons[ing] = []
                substitution_reasons[ing].append(f"no pertenece a cultura '{culture_not_met}'")
    
    # Limitar las sustituciones de cultura a max_culture_subs por ronda
    culture_ingredients_to_change = culture_violations_all[:max_culture_subs]
    culture_ingredients_pending = culture_violations_all[max_culture_subs:]
    
    # Combinar: todas las restricciones + cultura limitada
    ingredients_to_substitute = restriction_ingredients.union(set(culture_ingredients_to_change))
    culture_violations = set(culture_ingredients_to_change)
    
    # 3. Realizar sustituciones
    substitutions = []
    new_ingredients = []
    removed_ingredients = []
    
    for ingredient in original_ingredients:
        if ingredient in ingredients_to_substitute:
            # Otros ingredientes (los que no se sustituyen)
            other_ingredients = [i for i in original_ingredients if i not in ingredients_to_substitute]
            
            # Determinar si es hard constraint (restricción) o soft (cultura)
            is_hard_constraint = ingredient in restriction_violations and len(restriction_violations[ingredient]) > 0
            
            # Estrategia de búsqueda
            best_substitute = None
            search_attempts = []
            
            # Intento 1: Buscar en la misma cultura (subcategoría → categoría)
            candidates, level = find_substitute_candidates(ingredient, ontologia_db)
            search_attempts.append(f"ontología ({level}): {len(candidates)} candidatos")
            
            if candidates:
                best_substitute = select_best_substitute(
                    candidates, 
                    other_ingredients, 
                    pairing_db,
                    all_restrictions=restrictions_not_met,
                    restricciones_db=restricciones_db
                )
            
            # Intento 2: Usar sustitutos conocidos como fallback
            if not best_substitute:
                known_subs = get_known_substitutes(ingredient, restrictions_not_met, restricciones_db)
                search_attempts.append(f"fallback conocidos: {len(known_subs)} candidatos")
                
                if known_subs:
                    # Seleccionar el mejor usando food pairing
                    best_substitute = select_best_substitute(
                        known_subs,
                        other_ingredients,
                        pairing_db,
                        all_restrictions=restrictions_not_met,
                        restricciones_db=restricciones_db
                    )
                    # Si no hay coincidencia de pairing, usar el primero
                    if not best_substitute and known_subs:
                        best_substitute = known_subs[0]
            
            # Decidir qué hacer con el ingrediente
            if best_substitute:
                # Se encontró sustituto
                new_ingredients.append(best_substitute.replace('-', ' '))
                substitutions.append({
                    'original': ingredient,
                    'substitute': best_substitute.replace('-', ' '),
                    'reason': substitution_reasons.get(ingredient, []),
                    'search_attempts': search_attempts,
                    'candidates_found': len(candidates) if candidates else 0,
                    'action': 'substituted'
                })
            elif is_hard_constraint:
                # HARD CONSTRAINT: No se encontró sustituto → ELIMINAR ingrediente
                removed_ingredients.append(ingredient)
                substitutions.append({
                    'original': ingredient,
                    'substitute': None,
                    'reason': substitution_reasons.get(ingredient, []),
                    'search_attempts': search_attempts,
                    'action': 'removed',
                    'warning': f"Ingrediente ELIMINADO por violar restricción(es): {', '.join(restriction_violations.get(ingredient, []))}"
                })
            else:
                # SOFT CONSTRAINT (solo cultura): Mantener original si no hay sustituto
                new_ingredients.append(ingredient)
                substitutions.append({
                    'original': ingredient,
                    'substitute': None,
                    'reason': substitution_reasons.get(ingredient, []),
                    'search_attempts': search_attempts,
                    'action': 'kept',
                    'note': 'Mantenido (solo viola cultura, no restricción alimentaria)'
                })
        else:
            new_ingredients.append(ingredient)
    
    # 4. Crear el resultado
    adapted_course = copy.deepcopy(course_data)
    adapted_course['ingredients'] = new_ingredients
    
    # Actualizar las restricciones del plato para reflejar que ahora cumple las restricciones adaptadas
    current_restrictions = set(adapted_course.get('restrictions', []))
    for restriction in restrictions_not_met:
        # Normalizar la restricción antes de añadirla
        normalized_restriction = restriction.lower().replace('-', ' ').strip()
        current_restrictions.add(normalized_restriction)
    adapted_course['restrictions'] = list(current_restrictions)
    
    # Calcular cuántas sustituciones de cultura se hicieron realmente
    culture_subs_done = len([s for s in substitutions 
                             if s.get('action') == 'substituted' 
                             and any('cultura' in r for r in s.get('reason', []))])
    
    adapted_course['_adaptation'] = {
        'substitutions': substitutions,
        'original_ingredients': original_ingredients,
        'ingredients_substituted': len([s for s in substitutions if s.get('action') == 'substituted']),
        'ingredients_removed': len(removed_ingredients),
        'ingredients_kept': len([s for s in substitutions if s.get('action') == 'kept']),
        'removed_ingredients': removed_ingredients,
        # Info sobre adaptación gradual de cultura
        'culture_adaptation': {
            'total_culture_violations': len(culture_violations_all) if culture_not_met else 0,
            'culture_changed_this_round': len(culture_ingredients_to_change),
            'culture_pending_next_rounds': len(culture_ingredients_pending),
            'pending_ingredients': culture_ingredients_pending,
            'max_per_round': max_culture_subs
        }
    }
    
    return adapted_course


def adapt_menu(
    retrieved_result: dict,
    user_input: dict,
    restricciones_db: dict = None,
    contexto_db: dict = None,
    ontologia_db: dict = None,
    pairing_db: dict = None
) -> Dict:
    """
    Adapta un menú completo basándose en el análisis de cumplimiento.
    
    IMPORTANTE:
    - Las restricciones alimentarias son HARD CONDITIONS: se cambian TODOS de una vez.
    - La cultura es SOFT CONSTRAINT: se cambian máximo 2-3 ingredientes por ronda,
      permitiendo adaptaciones graduales en rondas siguientes si el usuario pide
      más toque de la misma cultura.
    
    SEGUNDA RONDA (ajuste cultural):
    Si user_input contiene 'culture_adjustment' ('add' o 'remove') y 'culture_adjustment_target',
    se aplica el ajuste cultural obligatorio en lugar de la adaptación normal.
    
    Args:
        retrieved_result: Resultado del módulo Retrieve (contiene 'case' y 'compliance')
        user_input: Input del usuario con restricciones y cultura
                    Campos especiales para segunda ronda:
                    - culture_adjustment: 'add' | 'remove' | None
                    - culture_adjustment_target: cultura objetivo del ajuste
        restricciones_db, contexto_db, ontologia_db, pairing_db: Bases de conocimiento
        
    Returns:
        Menú adaptado con información detallada de cambios
    """
    # Cargar bases de conocimiento si no se proporcionan
    if None in [restricciones_db, contexto_db, ontologia_db, pairing_db]:
        restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    case = retrieved_result.get('case', {})
    compliance = retrieved_result.get('compliance', {})
    
    # =========================================================================
    # SEGUNDA RONDA: Ajuste cultural obligatorio
    # =========================================================================
    culture_adjustment = user_input.get('culture_adjustment')
    culture_adjustment_target = user_input.get('culture_adjustment_target')
    
    if culture_adjustment and culture_adjustment_target:
        # Es una segunda ronda con ajuste cultural
        menu = case.get('solucion', {})
        user_restrictions = user_input.get('restrictions', [])
        
        adjustment_result = apply_culture_adjustment(
            menu=menu,
            adjustment_type=culture_adjustment,
            target_culture=culture_adjustment_target,
            ontologia_db=ontologia_db,
            pairing_db=pairing_db,
            restrictions=user_restrictions,
            restricciones_db=restricciones_db
        )
        
        return {
            'adapted': adjustment_result['adjusted'],
            'is_culture_adjustment': True,
            'culture_adjustment_type': culture_adjustment,
            'culture_adjustment_target': culture_adjustment_target,
            'adjustment_details': adjustment_result['adjustment_details'],
            'message': adjustment_result['message'],
            'menu': adjustment_result['menu'],
            'restrictions_adapted': [],
            'culture_adapted': None,
            'total_substitutions': 1 if adjustment_result['adjusted'] else 0,
            'total_removed': 1 if adjustment_result['adjusted'] and culture_adjustment == 'remove' else 0,
            'culture_pending': False,
            'culture_pending_count': 0
        }
    
    # =========================================================================
    # PRIMERA RONDA: Adaptación normal
    # =========================================================================
    restrictions_not_met = compliance.get('restrictions_not_met', [])
    culture_not_met = compliance.get('culture_not_met')
    
    # Obtener todas las restricciones del usuario (no solo las no cumplidas)
    user_restrictions = retrieved_result.get('user_restrictions', [])
    
    # Si cumple todo, devolver el caso sin cambios
    if not restrictions_not_met and not culture_not_met:
        return {
            'adapted': False,
            'reason': 'El caso cumple con todas las restricciones y cultura',
            'menu': case.get('solucion', {}),
            'culture_pending': False,
            'culture_pending_count': 0
        }
    
    # Adaptar cada plato
    solution = case.get('solucion', {})
    courses = solution.get('courses', {})
    
    adapted_courses = {}
    total_substitutions = 0
    total_removed = 0
    total_culture_pending = 0
    all_pending_ingredients = []
    
    for course_name, course_data in courses.items():
        adapted_course = adapt_course(
            course_data,
            restrictions_not_met,
            culture_not_met,
            restricciones_db,
            contexto_db,
            ontologia_db,
            pairing_db
        )
        
        # IMPORTANTE: Actualizar las restricciones del plato después de la adaptación
        # Si se adaptó para cumplir restricciones, añadirlas a la lista de restricciones del plato
        current_restrictions = set(adapted_course.get('restrictions', []))
        for restriction in restrictions_not_met:
            # Normalizar para añadir de forma consistente
            restriction_normalized = restriction.lower().replace('_', ' ').replace('-', ' ')
            # Añadir la restricción si no está ya
            if restriction_normalized not in [r.lower().replace('_', ' ').replace('-', ' ') for r in current_restrictions]:
                current_restrictions.add(restriction)
        adapted_course['restrictions'] = list(current_restrictions)
        
        adapted_courses[course_name] = adapted_course
        adaptation_info = adapted_course.get('_adaptation', {})
        total_substitutions += adaptation_info.get('ingredients_substituted', 0)
        total_removed += adaptation_info.get('ingredients_removed', 0)
        
        # Recopilar info de adaptación gradual de cultura
        culture_info = adaptation_info.get('culture_adaptation', {})
        total_culture_pending += culture_info.get('culture_pending_next_rounds', 0)
        all_pending_ingredients.extend(culture_info.get('pending_ingredients', []))
    
    # Construir resultado
    adapted_solution = copy.deepcopy(solution)
    adapted_solution['courses'] = adapted_courses
    
    # Actualizar también las features del menú para reflejar las restricciones adaptadas
    if 'features' in adapted_solution:
        features = adapted_solution['features']
        # Añadir las restricciones adaptadas a common_dietary_restrictions
        current_common = set(features.get('common_dietary_restrictions', []))
        for restriction in restrictions_not_met:
            current_common.add(restriction)
        features['common_dietary_restrictions'] = list(current_common)
    
    return {
        'adapted': True,
        'restrictions_adapted': restrictions_not_met,
        'culture_adapted': culture_not_met,
        'total_substitutions': total_substitutions,
        'total_removed': total_removed,
        'menu': adapted_solution,
        # Info sobre adaptación gradual de cultura
        'culture_pending': total_culture_pending > 0,
        'culture_pending_count': total_culture_pending,
        'culture_pending_ingredients': all_pending_ingredients,
        'culture_adaptation_note': f"Se adaptaron {MAX_CULTURE_SUBSTITUTIONS_PER_ROUND} ingredientes por plato. "
                                   f"Quedan {total_culture_pending} ingredientes pendientes para próximas rondas." 
                                   if total_culture_pending > 0 else None
    }


# ============================================================================
# VISUALIZACIÓN
# ============================================================================

def print_adaptation_results(adaptation_result: dict):
    """Muestra los resultados de la adaptación de forma legible."""
    print("\n" + "="*70)
    print("RESULTADOS DE LA ADAPTACIÓN")
    print("="*70 + "\n")
    
    if not adaptation_result.get('adapted'):
        print(f"✅ {adaptation_result.get('reason')}")
        return
    
    print(f"🔄 Adaptaciones realizadas:")
    print(f"   • Restricciones adaptadas: {', '.join(adaptation_result.get('restrictions_adapted', [])) or 'Ninguna'}")
    
    culture = adaptation_result.get('culture_adapted')
    if culture:
        print(f"   • Cultura adaptada: {culture}")
    
    print(f"   • Total de sustituciones: {adaptation_result.get('total_substitutions', 0)}")
    print(f"   • Total de ingredientes eliminados: {adaptation_result.get('total_removed', 0)}")
    
    # Mostrar info de adaptación gradual de cultura
    if adaptation_result.get('culture_pending'):
        pending_count = adaptation_result.get('culture_pending_count', 0)
        pending_ingredients = adaptation_result.get('culture_pending_ingredients', [])
        print(f"\n   📌 ADAPTACIÓN GRADUAL DE CULTURA:")
        print(f"      • Ingredientes pendientes para próximas rondas: {pending_count}")
        if pending_ingredients:
            print(f"      • Ingredientes que se pueden adaptar: {', '.join(pending_ingredients[:5])}")
            if len(pending_ingredients) > 5:
                print(f"        ... y {len(pending_ingredients) - 5} más")
        print(f"      💡 Tip: Pide 'más toque {culture}' para continuar adaptando")
    
    print()
    
    menu = adaptation_result.get('menu', {})
    courses = menu.get('courses', {})
    
    for course_name, course_data in courses.items():
        print(f"📍 {course_name.upper()}: {course_data.get('title', 'Sin título')}")
        
        adaptation_info = course_data.get('_adaptation', {})
        substitutions = adaptation_info.get('substitutions', [])
        removed = adaptation_info.get('removed_ingredients', [])
        culture_info = adaptation_info.get('culture_adaptation', {})
        
        if substitutions:
            print("   Cambios realizados:")
            for sub in substitutions:
                original = sub.get('original')
                substitute = sub.get('substitute')
                action = sub.get('action', 'unknown')
                reasons = sub.get('reason', [])
                
                if action == 'substituted':
                    print(f"      ✅ {original} → {substitute}")
                    print(f"         Razón: {', '.join(reasons)}")
                elif action == 'removed':
                    print(f"      🗑️  {original} → ELIMINADO")
                    print(f"         Razón: {', '.join(reasons)}")
                    print(f"         ⚠️  {sub.get('warning', '')}")
                elif action == 'kept':
                    print(f"      ⚡ {original} → Mantenido (soft constraint)")
                    print(f"         Nota: {sub.get('note', '')}")
        else:
            print("   ✅ Sin cambios necesarios")
        
        if removed:
            print(f"   🗑️  Ingredientes eliminados: {', '.join(removed)}")
        
        # Mostrar info de cultura pendiente por plato
        if culture_info.get('culture_pending_next_rounds', 0) > 0:
            pending = culture_info.get('pending_ingredients', [])
            print(f"   ⏳ Pendiente cultura ({len(pending)}): {', '.join(pending[:3])}" + 
                  (f"... +{len(pending)-3}" if len(pending) > 3 else ""))
        
        print(f"   📋 Ingredientes finales: {', '.join(course_data.get('ingredients', []))}")
        print()
    
    print("="*70 + "\n")


# ============================================================================
# MAIN PARA TESTING
# ============================================================================

def main():
    """Función principal para testing del módulo."""
    from Retrieve import load_case_base, retrieve_cases
    from input_module import get_user_restrictions
    
    # 1. Obtener input del usuario
    print("="*70)
    print("MÓDULO DE ADAPTACIÓN - TEST")
    print("="*70 + "\n")
    
    print("Paso 1: Recopilando preferencias del usuario...\n")
    user_input = get_user_restrictions()
    
    # 2. Cargar base de casos
    print("\nPaso 2: Cargando bases de datos...")
    case_base = load_case_base(os.path.join(BASE_DIR, 'Base_Casos', 'casos_cbr.json'))
    restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    if not case_base:
        print("❌ No se pudo cargar la base de casos.")
        return
    
    print(f"✅ Se cargaron {len(case_base)} casos.\n")
    
    # 3. Recuperar el caso más similar
    print("Paso 3: Buscando el caso más similar...")
    results = retrieve_cases(user_input, case_base)
    
    if not results:
        print("❌ No se encontraron casos similares.")
        return
    
    best_result = results[0]
    print(f"✅ Mejor caso encontrado: ID {best_result['case'].get('id_caso')} "
          f"(puntuación: {best_result['score']})")
    
    compliance = best_result.get('compliance', {})
    print(f"   Restricciones no cumplidas: {compliance.get('restrictions_not_met', [])}")
    print(f"   Cultura no cumplida: {compliance.get('culture_not_met', 'Ninguna')}")
    
    # 4. Adaptar el menú
    print("\nPaso 4: Adaptando el menú...")
    adaptation_result = adapt_menu(
        best_result,
        user_input,
        restricciones_db,
        contexto_db,
        ontologia_db,
        pairing_db
    )
    
    # 5. Mostrar resultados
    print_adaptation_results(adaptation_result)
    
    return adaptation_result


if __name__ == "__main__":
    print(BASE_DIR)
    adapt_result = main()
    print("Adaptation Result:", adapt_result)
