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


# Mapeo de culturas en inglés a español/variantes
CULTURE_MAPPINGS = {
    'latin american': ['latina', 'latin', 'latin american', 'latinoamericana', 'sudamericana', 'mexicana', 'tex-mex', 'central american', 'south american', 'caribbean', 'caribeña'],
    'french/western european': ['french/western european,''francesa', 'french', 'western european', 'europea occidental', 'european', 'alemana', 'german', 'british', 'británica', 'holandesa', 'dutch', 'belga', 'belgian'],
    'mediterranean': ['mediterránea', 'mediterranea', 'mediterranean', 'griega', 'greek', 'italiana', 'francesa', 'española', 'spanish', 'turkish', 'turca'],
    'south asian': ['india', 'indian', 'south asian', 'asiática del sur', 'hindú', 'pakistani', 'paquistaní', 'bangladeshi', 'sri lankan', 'nepalese', 'nepalí'],
    'chinese': ['china', 'chinese', 'chino', 'cantonese', 'cantonés', 'szechuan', 'sichuan', 'mandarin', 'hunan', 'shanghai'],
    'american': ['americana', 'american', 'estadounidense', 'usa', 'us', 'north american', 'norteamericana'],
    'italian': ['italiana', 'italian', 'italy', 'italia', 'mediterránea/italiana', 'sicilian', 'siciliana', 'tuscan', 'toscana'],
    'east asian': ['asiática', 'asian', 'east asian', 'asiática oriental', 'oriental', 'southeast asian', 'asiática del sudeste'],
    'japanese': ['japonesa', 'japanese', 'japan', 'japón', 'nippon'],
    'middle eastern/north african': ['middle eastern/north african', 'middle eastern', 'north african', 'medio oriente', 'norte de áfrica', 'árabe', 'arab', 'turkish', 'turca', 'persian', 'persa', 'moroccan', 'marroquí', 'lebanese', 'libanesa', 'egyptian', 'egipcia'],
    'korean': ['coreana', 'korean', 'korea', 'corea', 'south korean', 'norte coreana'],
}

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
# ANÁLISIS DE CULTURA
# ============================================================================

def find_culture_ingredients(culture: str, contexto_db: dict) -> Set[str]:
    """
    Encuentra todos los ingredientes asociados a una cultura.
    Usa coincidencia parcial y mapeo de traducciones para manejar variaciones.
    
    Args:
        culture: Cultura buscada (ej: 'American', 'Mexican', 'Mediterranean')
        contexto_db: Base de datos de ingredientes por contexto
        
    Returns:
        Set de ingredientes normalizados asociados a la cultura
    """
    culture_lower = culture.lower().strip()
    all_ingredients = set()
    
    # Obtener variantes de la cultura
    culture_variants = CULTURE_MAPPINGS.get(culture_lower, [culture_lower])
    # Siempre incluir la cultura original
    if culture_lower not in culture_variants:
        culture_variants = [culture_lower] + list(culture_variants)
    
    for context_key, context_data in contexto_db.items():
        context_culture = context_data.get('culture', '').lower()
        context_key_lower = context_key.lower()
        
        # Verificar coincidencia con cualquier variante
        match_found = False
        for variant in culture_variants:
            if (variant in context_culture or 
                context_culture in variant or
                variant in context_key_lower):
                match_found = True
                break
        
        if match_found:
            ingredients = context_data.get('ingredients', [])
            for ing in ingredients:
                all_ingredients.add(normalize_ingredient(ing))
    
    return all_ingredients


def find_ingredients_not_in_culture(
    ingredients: List[str], 
    culture: str, 
    contexto_db: dict
) -> List[str]:
    """
    Encuentra ingredientes que no pertenecen a la cultura deseada.
    
    Args:
        ingredients: Lista de ingredientes del plato
        culture: Cultura deseada
        contexto_db: Base de datos de ingredientes por contexto
        
    Returns:
        Lista de ingredientes que no pertenecen a la cultura
    """
    culture_ingredients = find_culture_ingredients(culture, contexto_db)
    
    if not culture_ingredients:
        print(f"⚠️  No se encontraron ingredientes para la cultura '{culture}'")
        return []
    
    not_in_culture = []
    
    for ingredient in ingredients:
        ing_normalized = normalize_ingredient(ingredient)
        if ing_normalized not in culture_ingredients:
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
    ontologia_db: dict,
    search_all_cultures: bool = False
) -> Tuple[List[str], str]:
    """
    Encuentra ingredientes candidatos para sustituir al ingrediente dado.
    Busca primero en la subcategoría, luego en la categoría.
    
    Args:
        ingredient: Ingrediente a sustituir
        ontologia_db: Base de datos de ontología
        search_all_cultures: Si True, busca en todas las culturas en la misma categoría
        
    Returns:
        Tuple de (lista de candidatos, nivel donde se encontraron)
    """
    location = find_ingredient_in_ontology(ingredient, ontologia_db)
    
    if not location:
        return [], 'not_found'
    
    ontology_tree = ontologia_db.get('ontology_tree', {})
    category = location['category']
    subcategory = location.get('subcategory')
    
    ing_normalized = denormalize_ingredient_for_ontology(ingredient)
    candidates = []
    level = 'subcategory'
    
    if search_all_cultures:
        # Buscar en todas las culturas dentro de la misma categoría/subcategoría
        for culture_name, categories in ontology_tree.items():
            if not isinstance(categories, dict):
                continue
            
            if category in categories:
                category_node = categories[category]
                if not isinstance(category_node, dict):
                    continue
                
                # Si hay subcategoría, buscar primero ahí
                if subcategory and subcategory in category_node:
                    subcategory_node = category_node[subcategory]
                    candidates.extend(get_ingredients_from_node(subcategory_node))
                else:
                    # Buscar en toda la categoría
                    candidates.extend(get_ingredients_from_node(category_node))
        
        level = 'all_cultures'
    else:
        culture = location['culture']
        
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
    contexto_db: dict,
    ontologia_db: dict,
    pairing_db: dict
) -> Dict:
    """
    Adapta un plato individual para cumplir con restricciones y cultura.
    
    IMPORTANTE: Las restricciones alimentarias son HARD CONDITIONS.
    Si no se encuentra sustituto, el ingrediente se ELIMINA.
    
    Args:
        course_data: Datos del plato (ingredientes, título, etc.)
        restrictions_not_met: Lista de restricciones no cumplidas
        culture_not_met: Cultura no cumplida (o None)
        restricciones_db: Base de datos de restricciones
        contexto_db: Base de datos de ingredientes por contexto
        ontologia_db: Base de datos de ontología
        pairing_db: Base de datos de food pairing
        
    Returns:
        Dict con el plato adaptado e información de cambios
    """
    original_ingredients = course_data.get('ingredients', [])
    
    # Conjunto de ingredientes a sustituir y sus razones
    ingredients_to_substitute = set()
    substitution_reasons = {}  # ingredient -> lista de razones
    restriction_violations = {}  # ingredient -> lista de restricciones violadas (hard constraints)
    
    # 1. Verificar restricciones alimentarias (HARD CONSTRAINTS)
    for restriction in restrictions_not_met:
        violating = find_ingredients_violating_restriction(
            original_ingredients, restriction, restricciones_db
        )
        for ing in violating:
            ingredients_to_substitute.add(ing)
            if ing not in substitution_reasons:
                substitution_reasons[ing] = []
                restriction_violations[ing] = []
            substitution_reasons[ing].append(f"viola restricción '{restriction}'")
            restriction_violations[ing].append(restriction)
    
    # 2. Verificar cultura (SOFT CONSTRAINT - no eliminar si no hay sustituto)
    culture_violations = set()
    if culture_not_met:
        not_in_culture = find_ingredients_not_in_culture(
            original_ingredients, culture_not_met, contexto_db
        )
        for ing in not_in_culture:
            ingredients_to_substitute.add(ing)
            culture_violations.add(ing)
            if ing not in substitution_reasons:
                substitution_reasons[ing] = []
            substitution_reasons[ing].append(f"no pertenece a cultura '{culture_not_met}'")
    
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
            
            # Estrategia de búsqueda progresiva
            best_substitute = None
            search_attempts = []
            
            # Intento 1: Buscar en la misma cultura/categoría
            candidates, level = find_substitute_candidates(ingredient, ontologia_db, search_all_cultures=False)
            search_attempts.append(f"misma cultura ({level}): {len(candidates)} candidatos")
            
            if candidates:
                best_substitute = select_best_substitute(
                    candidates, 
                    other_ingredients, 
                    pairing_db,
                    all_restrictions=restrictions_not_met,
                    restricciones_db=restricciones_db
                )
            
            # Intento 2: Si no se encontró, buscar en todas las culturas
            if not best_substitute:
                candidates, level = find_substitute_candidates(ingredient, ontologia_db, search_all_cultures=True)
                search_attempts.append(f"todas culturas ({level}): {len(candidates)} candidatos")
                
                if candidates:
                    best_substitute = select_best_substitute(
                        candidates, 
                        other_ingredients, 
                        pairing_db,
                        all_restrictions=restrictions_not_met,
                        restricciones_db=restricciones_db
                    )
            
            # Intento 3: Usar sustitutos conocidos como fallback
            if not best_substitute:
                known_subs = get_known_substitutes(ingredient, restrictions_not_met, restricciones_db)
                search_attempts.append(f"sustitutos conocidos: {len(known_subs)} candidatos")
                
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
    adapted_course['_adaptation'] = {
        'substitutions': substitutions,
        'original_ingredients': original_ingredients,
        'ingredients_substituted': len([s for s in substitutions if s.get('action') == 'substituted']),
        'ingredients_removed': len(removed_ingredients),
        'ingredients_kept': len([s for s in substitutions if s.get('action') == 'kept']),
        'removed_ingredients': removed_ingredients
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
    
    Args:
        retrieved_result: Resultado del módulo Retrieve (contiene 'case' y 'compliance')
        user_input: Input del usuario con restricciones y cultura
        restricciones_db, contexto_db, ontologia_db, pairing_db: Bases de conocimiento
        
    Returns:
        Menú adaptado con información detallada de cambios
    """
    # Cargar bases de conocimiento si no se proporcionan
    if None in [restricciones_db, contexto_db, ontologia_db, pairing_db]:
        restricciones_db, contexto_db, ontologia_db, pairing_db = load_all_knowledge_bases()
    
    case = retrieved_result.get('case', {})
    compliance = retrieved_result.get('compliance', {})
    
    restrictions_not_met = compliance.get('restrictions_not_met', [])
    culture_not_met = compliance.get('culture_not_met')
    
    # Si cumple todo, devolver el caso sin cambios
    if not restrictions_not_met and not culture_not_met:
        return {
            'adapted': False,
            'reason': 'El caso cumple con todas las restricciones y cultura',
            'menu': case.get('solucion', {})
        }
    
    # Adaptar cada plato
    solution = case.get('solucion', {})
    courses = solution.get('courses', {})
    
    adapted_courses = {}
    total_substitutions = 0
    total_removed = 0
    
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
        adapted_courses[course_name] = adapted_course
        adaptation_info = adapted_course.get('_adaptation', {})
        total_substitutions += adaptation_info.get('ingredients_substituted', 0)
        total_removed += adaptation_info.get('ingredients_removed', 0)
    
    # Construir resultado
    adapted_solution = copy.deepcopy(solution)
    adapted_solution['courses'] = adapted_courses
    
    return {
        'adapted': True,
        'restrictions_adapted': restrictions_not_met,
        'culture_adapted': culture_not_met,
        'total_substitutions': total_substitutions,
        'total_removed': total_removed,
        'menu': adapted_solution
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
    print(f"   • Restricciones adaptadas: {', '.join(adaptation_result.get('restrictions_adapted', []))}")
    
    culture = adaptation_result.get('culture_adapted')
    if culture:
        print(f"   • Cultura adaptada: {culture}")
    
    print(f"   • Total de sustituciones: {adaptation_result.get('total_substitutions', 0)}")
    print(f"   • Total de ingredientes eliminados: {adaptation_result.get('total_removed', 0)}")
    print()
    
    menu = adaptation_result.get('menu', {})
    courses = menu.get('courses', {})
    
    for course_name, course_data in courses.items():
        print(f"📍 {course_name.upper()}: {course_data.get('title', 'Sin título')}")
        
        adaptation_info = course_data.get('_adaptation', {})
        substitutions = adaptation_info.get('substitutions', [])
        removed = adaptation_info.get('removed_ingredients', [])
        
        if substitutions:
            print("   Cambios:")
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
