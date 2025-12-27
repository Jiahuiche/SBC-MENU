"""
Motor CBR Profesional para Recomendación y Adaptación de Menús
==============================================================

Sistema CBR (Case-Based Reasoning) completo que incluye:
- Adaptación CULTURAL: Sustitución de ingredientes por cultura gastronómica
- Adaptación DIETÉTICA: Vegano, vegetariano, kosher, halal, gluten-free, etc.
- Adaptación ESTACIONAL: Ingredientes de temporada según la estación
- Adaptación de ESTILO: Tradicional, moderno, gourmet, casero, molecular, etc.

Ciclo CBR: Retrieve → Reuse → Revise → Retain

Autor: Sistema CBR Profesional
Fecha: 2025-12-15
"""

import json
import os
import sys
import copy
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

# ==============================================================================
# ENUMERACIONES Y TIPOS
# ==============================================================================

class AdaptationType(Enum):
    CULTURAL = "cultural"
    DIETARY = "dietary"
    SEASONAL = "seasonal"
    STYLE = "style"
    PRICE = "price"
    TIME = "time"

@dataclass
class Substitution:
    """Representa una sustitución de ingrediente"""
    course: str
    original: str
    substitute: str
    category: str
    reason: str
    adaptation_type: AdaptationType
    alternatives: List[str] = None
    notes: str = ""

@dataclass
class ProcessAdaptation:
    """Representa una adaptación de proceso de cocción"""
    course: str
    original_method: str
    new_method: str
    reason: str
    execution: str
    adaptation_type: AdaptationType

# ==============================================================================
# CARGA DE BASES DE DATOS
# ==============================================================================

def find_database_path(filename: str) -> str:
    """Encuentra la ruta correcta de un archivo de base de datos"""
    possible_paths = [
        filename,
        os.path.join('PART2', filename),
        os.path.join(os.path.dirname(__file__), filename),
        os.path.join(os.path.dirname(__file__), 'PART2', filename)
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    raise FileNotFoundError(f"No se encontró el archivo: {filename}")

def load_cbr_database(filepath: str = 'cbr_menu_database.json') -> Dict:
    """Carga la base de datos de menús CBR"""
    path = find_database_path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_cultural_ingredients(filepath: str = 'cultural_ingredients_database.json') -> Dict:
    """Carga la base de datos de ingredientes culturales"""
    path = find_database_path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_dietary_substitutions(filepath: str = 'dietary_substitutions_database.json') -> Dict:
    """Carga la base de datos de sustituciones dietéticas"""
    path = find_database_path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_seasonal_ingredients(filepath: str = 'seasonal_ingredients_database.json') -> Dict:
    """Carga la base de datos de ingredientes estacionales"""
    path = find_database_path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_cooking_styles(filepath: str = 'cooking_style_database.json') -> Dict:
    """Carga la base de datos de estilos de cocina"""
    path = find_database_path(filepath)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_all_databases() -> Dict[str, Dict]:
    """Carga todas las bases de datos necesarias"""
    return {
        'menus': load_cbr_database(),
        'cultural': load_cultural_ingredients(),
        'dietary': load_dietary_substitutions(),
        'seasonal': load_seasonal_ingredients(),
        'styles': load_cooking_styles()
    }

# ==============================================================================
# NORMALIZACIÓN Y UTILIDADES
# ==============================================================================

def normalize_culture_name(culture: str) -> str:
    """Normaliza el nombre de la cultura para búsqueda"""
    mappings = {
        'mexican': 'Mexicana/Tex-Mex', 'mexicana': 'Mexicana/Tex-Mex', 'tex-mex': 'Mexicana/Tex-Mex',
        'italian': 'Italiana', 'italiana': 'Italiana',
        'mediterranean': 'Mediterránea', 'mediterránea': 'Mediterránea',
        'american': 'Americana', 'americana': 'Americana',
        'chinese': 'China', 'china': 'China',
        'indian': 'India', 'india': 'India',
        'japanese': 'Japonesa', 'japonesa': 'Japonesa',
        'peruvian': 'Peruana', 'peruana': 'Peruana',
        'french': 'Mediterránea/Francesa', 'francesa': 'Mediterránea/Francesa'
    }
    return mappings.get(culture.lower().strip(), culture)

def normalize_season(season: str) -> str:
    """Normaliza el nombre de la estación"""
    mappings = {
        'spring': 'Spring', 'primavera': 'Spring',
        'summer': 'Summer', 'verano': 'Summer',
        'fall': 'Fall', 'autumn': 'Fall', 'otoño': 'Fall',
        'winter': 'Winter', 'invierno': 'Winter',
        'any': 'any-season', 'any-season': 'any-season', 'cualquiera': 'any-season'
    }
    return mappings.get(season.lower().strip(), season)

def normalize_style(style: str) -> str:
    """Normaliza el nombre del estilo de cocina"""
    mappings = {
        'traditional': 'Tradicional', 'tradicional': 'Tradicional',
        'modern': 'Moderno', 'moderno': 'Moderno', 'contemporary': 'Moderno',
        'gourmet': 'Gourmet', 'fine dining': 'Gourmet', 'haute cuisine': 'Gourmet',
        'home': 'Casero', 'casero': 'Casero', 'homestyle': 'Casero',
        'fusion': 'Fusión', 'fusión': 'Fusión',
        'minimalist': 'Minimalista', 'minimalista': 'Minimalista',
        'molecular': 'Molecular',
        'farm-to-table': 'Farm-to-Table', 'farm to table': 'Farm-to-Table',
        'vegan creative': 'Vegano Creativo', 'vegano creativo': 'Vegano Creativo',
        'healthy': 'Saludable', 'saludable': 'Saludable'
    }
    return mappings.get(style.lower().strip(), style)

def ingredient_matches(ingredient: str, target: str) -> bool:
    """Verifica si un ingrediente coincide con un objetivo (búsqueda flexible)"""
    ing_lower = ingredient.lower().strip()
    target_lower = target.lower().strip()
    return target_lower in ing_lower or ing_lower in target_lower

# ==============================================================================
# CÁLCULO DE SIMILITUD
# ==============================================================================

def calculate_similarity(user_prefs: Dict, menu: Dict) -> float:
    """
    Calcula la similitud entre preferencias del usuario y un menú.
    
    Ponderación:
    - Cultura: 20%
    - Estilo: 15%
    - Dietético: 35%
    - Precio: 15%
    - Estación: 10%
    - Tiempo: 5%
    """
    features = menu['features']
    score = 0.0
    total_weight = 0.0
    
    # === CULTURA (20%) ===
    if 'cultura' in user_prefs and 'cultura' in features:
        weight = 0.20
        user_culture = normalize_culture_name(user_prefs['cultura'])
        menu_culture = features['cultura']
        
        if user_culture.lower() == menu_culture.lower():
            culture_score = 1.0
        elif user_culture.lower() in menu_culture.lower() or menu_culture.lower() in user_culture.lower():
            culture_score = 0.7
        else:
            culture_score = 0.0
        
        score += weight * culture_score
        total_weight += weight
    
    # === ESTILO (15%) ===
    if 'estilo_cocina' in user_prefs and 'estilo_cocina' in features:
        weight = 0.15
        user_style = normalize_style(user_prefs['estilo_cocina'])
        menu_style = features['estilo_cocina']
        
        if user_style.lower() == menu_style.lower():
            style_score = 1.0
        elif user_style.lower() in menu_style.lower() or menu_style.lower() in user_style.lower():
            style_score = 0.6
        else:
            style_score = 0.2  # Estilos diferentes pero adaptables
        
        score += weight * style_score
        total_weight += weight
    
    # === RESTRICCIONES DIETÉTICAS (35%) ===
    weight = 0.35
    dietary_score = 0.0
    dietary_checks = [
        ('is_vegan', 1.0, True),      # (key, importance, is_critical)
        ('is_vegetarian', 0.8, True),
        ('is_gluten_free', 0.9, True),
        ('is_dairy_free', 0.7, False),
        ('is_kosher', 0.8, True),
        ('is_halal', 0.8, True)
    ]
    
    total_dietary_importance = 0
    for key, importance, is_critical in dietary_checks:
        if key in user_prefs:
            total_dietary_importance += importance
            if user_prefs[key] == features.get(key, False):
                dietary_score += importance
            elif user_prefs[key] and not features.get(key, False):
                # Usuario requiere pero menú no cumple
                if is_critical:
                    dietary_score -= importance * 0.3  # Penalización menor (se puede adaptar)
    
    if total_dietary_importance > 0:
        dietary_score = max(0, min(1, dietary_score / total_dietary_importance))
    else:
        dietary_score = 1.0  # Sin restricciones = compatible
    
    score += weight * dietary_score
    total_weight += weight
    
    # === PRECIO (15%) ===
    if 'max_price' in user_prefs:
        weight = 0.15
        menu_price = features.get('total_price_per_serving', 0)
        max_price = user_prefs['max_price']
        
        if max_price > 0:
            if menu_price <= max_price:
                price_score = 1.0 - (0.2 * menu_price / max_price)
            else:
                overage = (menu_price - max_price) / max_price
                price_score = max(0, 1.0 - overage)
        else:
            price_score = 1.0
        
        score += weight * price_score
        total_weight += weight
    
    # === ESTACIÓN (10%) ===
    if 'season' in user_prefs:
        weight = 0.10
        user_season = normalize_season(user_prefs['season'])
        menu_season = features.get('season', 'any-season')
        
        if user_season == 'any-season' or menu_season.lower() == 'any season':
            season_score = 0.8
        elif user_season.lower() == menu_season.lower():
            season_score = 1.0
        else:
            # Estaciones adyacentes tienen mejor puntuación
            season_order = ['Spring', 'Summer', 'Fall', 'Winter']
            try:
                user_idx = season_order.index(user_season)
                menu_idx = season_order.index(menu_season)
                distance = min(abs(user_idx - menu_idx), 4 - abs(user_idx - menu_idx))
                season_score = max(0, 1.0 - distance * 0.3)
            except ValueError:
                season_score = 0.5
        
        score += weight * season_score
        total_weight += weight
    
    # === TIEMPO (5%) ===
    if 'max_time' in user_prefs:
        weight = 0.05
        menu_time = features.get('avg_ready_time_minutes', 0)
        max_time = user_prefs['max_time']
        
        if max_time > 0 and menu_time > 0:
            if menu_time <= max_time:
                time_score = 1.0
            else:
                overage = (menu_time - max_time) / max_time
                time_score = max(0, 1.0 - overage)
        else:
            time_score = 1.0
        
        score += weight * time_score
        total_weight += weight
    
    # Normalizar
    return score / total_weight if total_weight > 0 else 0.5

# ==============================================================================
# ADAPTACIÓN CULTURAL
# ==============================================================================

def adapt_ingredients_culturally(
    ingredients: List[str], 
    target_culture: str, 
    cultural_db: Dict,
    course: str
) -> Tuple[List[str], List[Substitution]]:
    """
    Adapta ingredientes a la cultura objetivo usando reglas de sustitución.
    """
    target_culture = normalize_culture_name(target_culture)
    substitution_rules = cultural_db.get('substitution_rules', {})
    
    adapted = []
    substitutions = []
    
    for ingredient in ingredients:
        ing_lower = ingredient.lower().strip()
        substituted = False
        
        for category, rules in substitution_rules.items():
            if substituted:
                break
            for base_ing, culture_map in rules.items():
                if ingredient_matches(ing_lower, base_ing):
                    if target_culture in culture_map:
                        new_ing = culture_map[target_culture]
                        if new_ing and new_ing != 'none' and new_ing.lower() != base_ing.lower():
                            adapted.append(new_ing)
                            substitutions.append(Substitution(
                                course=course,
                                original=ingredient,
                                substitute=new_ing,
                                category=category,
                                reason=f"Adaptación cultural a {target_culture}",
                                adaptation_type=AdaptationType.CULTURAL
                            ))
                            substituted = True
                            break
        
        if not substituted:
            adapted.append(ingredient)
    
    return adapted, substitutions

# ==============================================================================
# ADAPTACIÓN DIETÉTICA
# ==============================================================================

def get_dietary_restrictions(user_prefs: Dict) -> List[str]:
    """Obtiene lista de restricciones dietéticas activas"""
    restrictions = []
    mapping = {
        'is_vegan': 'vegan',
        'is_vegetarian': 'vegetarian',
        'is_gluten_free': 'gluten_free',
        'is_dairy_free': 'dairy_free',
        'is_kosher': 'kosher',
        'is_halal': 'halal',
        'is_nut_free': 'nut_free',
        'is_low_sodium': 'low_sodium',
        'is_low_sugar': 'low_sugar'
    }
    
    for key, value in mapping.items():
        if user_prefs.get(key, False):
            restrictions.append(value)
    
    return restrictions

def adapt_ingredients_dietary(
    ingredients: List[str],
    restrictions: List[str],
    dietary_db: Dict,
    course: str
) -> Tuple[List[str], List[Substitution]]:
    """
    Adapta ingredientes según restricciones dietéticas.
    Prioridad: vegan > vegetarian > otros
    """
    substitution_rules = dietary_db.get('substitution_rules', {})
    classifications = dietary_db.get('ingredient_classifications', {})
    
    adapted = []
    substitutions = []
    
    # Construir lista de ingredientes prohibidos por restricción
    forbidden = {}
    for restriction in restrictions:
        forbidden[restriction] = set()
        
        if restriction == 'vegan':
            # Prohibidos: todos los productos animales
            forbidden[restriction].update(classifications.get('proteins', {}).get('animal_proteins', []))
            forbidden[restriction].update(classifications.get('proteins', {}).get('seafood', []))
            forbidden[restriction].update(classifications.get('proteins', {}).get('dairy_proteins', []))
            for dairy_type in classifications.get('dairy', {}).values():
                if isinstance(dairy_type, list):
                    forbidden[restriction].update(dairy_type)
            forbidden[restriction].add('honey')
            forbidden[restriction].add('eggs')
            
        elif restriction == 'vegetarian':
            forbidden[restriction].update(classifications.get('proteins', {}).get('animal_proteins', []))
            forbidden[restriction].update(classifications.get('proteins', {}).get('seafood', []))
            
        elif restriction == 'gluten_free':
            for gluten_type in classifications.get('gluten_containing', {}).values():
                if isinstance(gluten_type, list):
                    forbidden[restriction].update(gluten_type)
                    
        elif restriction == 'dairy_free':
            for dairy_type in classifications.get('dairy', {}).values():
                if isinstance(dairy_type, list):
                    forbidden[restriction].update(dairy_type)
                    
        elif restriction == 'nut_free':
            for nut_type in classifications.get('nuts_and_seeds', {}).values():
                if isinstance(nut_type, list):
                    forbidden[restriction].update(nut_type)
    
    for ingredient in ingredients:
        ing_lower = ingredient.lower().strip()
        needs_substitution = False
        active_restriction = None
        
        # Verificar si el ingrediente viola alguna restricción
        for restriction in restrictions:
            for forbidden_item in forbidden.get(restriction, []):
                if ingredient_matches(ing_lower, forbidden_item):
                    needs_substitution = True
                    active_restriction = restriction
                    break
            if needs_substitution:
                break
        
        if needs_substitution and active_restriction:
            # Buscar sustitución
            rules = substitution_rules.get(active_restriction, {})
            substitute_found = False
            
            for category, items in rules.items():
                if substitute_found:
                    break
                for base_ing, sub_info in items.items():
                    if ingredient_matches(ing_lower, base_ing):
                        if isinstance(sub_info, dict):
                            new_ing = sub_info.get('substitute', '')
                            alternatives = sub_info.get('alternatives', [])
                            notes = sub_info.get('notes', '')
                        else:
                            new_ing = sub_info
                            alternatives = []
                            notes = ''
                        
                        if new_ing:
                            adapted.append(new_ing)
                            substitutions.append(Substitution(
                                course=course,
                                original=ingredient,
                                substitute=new_ing,
                                category=category,
                                reason=f"Adaptación dietética ({active_restriction})",
                                adaptation_type=AdaptationType.DIETARY,
                                alternatives=alternatives,
                                notes=notes
                            ))
                            substitute_found = True
                            break
            
            if not substitute_found:
                # Marcar para eliminación
                substitutions.append(Substitution(
                    course=course,
                    original=ingredient,
                    substitute="[ELIMINAR]",
                    category="prohibited",
                    reason=f"Sin sustituto disponible para {active_restriction}",
                    adaptation_type=AdaptationType.DIETARY
                ))
        else:
            adapted.append(ingredient)
    
    # Filtrar elementos marcados para eliminación
    adapted = [ing for ing in adapted if ing != "[ELIMINAR]"]
    
    return adapted, substitutions

# ==============================================================================
# ADAPTACIÓN ESTACIONAL
# ==============================================================================

def adapt_ingredients_seasonal(
    ingredients: List[str],
    target_season: str,
    seasonal_db: Dict,
    course: str
) -> Tuple[List[str], List[Substitution]]:
    """
    Adapta ingredientes a la estación objetivo.
    """
    target_season = normalize_season(target_season)
    if target_season == 'any-season':
        return ingredients, []
    
    seasonal_subs = seasonal_db.get('seasonal_substitutions', {})
    seasonal_ingredients = seasonal_db.get('seasonal_ingredients', {})
    
    adapted = []
    substitutions = []
    
    # Obtener ingredientes de temporada para la estación objetivo
    target_peak = set()
    if target_season in seasonal_ingredients:
        for category in ['vegetables', 'fruits', 'herbs']:
            cat_data = seasonal_ingredients[target_season].get(category, {})
            if isinstance(cat_data, dict):
                target_peak.update(cat_data.get('primary', []))
                target_peak.update(cat_data.get('secondary', []))
            elif isinstance(cat_data, list):
                target_peak.update(cat_data)
    
    for ingredient in ingredients:
        ing_lower = ingredient.lower().strip()
        substitute_found = False
        
        # Buscar en sustituciones estacionales
        for category, items in seasonal_subs.items():
            if substitute_found:
                break
            for base_ing, info in items.items():
                if ingredient_matches(ing_lower, base_ing):
                    peak = info.get('peak_season', '')
                    
                    # Si el ingrediente no está en su temporada peak
                    if peak and peak != target_season:
                        out_of_season = info.get('out_of_season_substitutes', {})
                        if target_season in out_of_season:
                            subs_list = out_of_season[target_season]
                            if subs_list:
                                new_ing = subs_list[0] if isinstance(subs_list, list) else subs_list
                                adapted.append(new_ing)
                                substitutions.append(Substitution(
                                    course=course,
                                    original=ingredient,
                                    substitute=new_ing,
                                    category=category,
                                    reason=f"Adaptación estacional a {target_season}",
                                    adaptation_type=AdaptationType.SEASONAL,
                                    alternatives=subs_list[1:] if isinstance(subs_list, list) and len(subs_list) > 1 else [],
                                    notes=f"Ingrediente original peak: {peak}"
                                ))
                                substitute_found = True
                                break
        
        if not substitute_found:
            adapted.append(ingredient)
    
    return adapted, substitutions

# ==============================================================================
# ADAPTACIÓN DE ESTILO
# ==============================================================================

def adapt_for_style(
    menu: Dict,
    target_style: str,
    style_db: Dict,
    user_prefs: Dict
) -> Tuple[Dict, List[Substitution], List[ProcessAdaptation]]:
    """
    Adapta un menú al estilo de cocina objetivo.
    Incluye sustituciones de ingredientes y adaptaciones de proceso.
    """
    target_style = normalize_style(target_style)
    adapted_menu = copy.deepcopy(menu)
    
    ingredient_subs = []
    process_adaptations = []
    
    style_definitions = style_db.get('style_definitions', {})
    ingredient_upgrades = style_db.get('ingredient_upgrades', {})
    style_sub_rules = style_db.get('style_substitution_rules', {})
    presentation = style_db.get('presentation_adaptations', {})
    
    target_def = style_definitions.get(target_style, {})
    
    # === ADAPTACIÓN DE INGREDIENTES POR ESTILO ===
    if target_style in ingredient_upgrades.get('to_Gourmet', {}) or target_style == 'Gourmet':
        upgrades = ingredient_upgrades.get('to_Gourmet', {})
        for course_name in ['starter', 'main', 'dessert']:
            if course_name in adapted_menu.get('courses', {}):
                course = adapted_menu['courses'][course_name]
                new_ingredients = []
                
                for ing in course.get('ingredients', []):
                    ing_lower = ing.lower().strip()
                    upgraded = False
                    
                    for category, items in upgrades.items():
                        for base_ing, upgrade_list in items.items():
                            if ingredient_matches(ing_lower, base_ing):
                                new_ing = upgrade_list[0] if isinstance(upgrade_list, list) else upgrade_list
                                new_ingredients.append(new_ing)
                                ingredient_subs.append(Substitution(
                                    course=course_name,
                                    original=ing,
                                    substitute=new_ing,
                                    category=category,
                                    reason=f"Upgrade para estilo {target_style}",
                                    adaptation_type=AdaptationType.STYLE,
                                    alternatives=upgrade_list[1:] if isinstance(upgrade_list, list) else []
                                ))
                                upgraded = True
                                break
                        if upgraded:
                            break
                    
                    if not upgraded:
                        new_ingredients.append(ing)
                
                course['ingredients'] = new_ingredients
    
    elif target_style == 'Saludable':
        upgrades = ingredient_upgrades.get('to_Saludable', {})
        for course_name in ['starter', 'main', 'dessert']:
            if course_name in adapted_menu.get('courses', {}):
                course = adapted_menu['courses'][course_name]
                new_ingredients = []
                
                for ing in course.get('ingredients', []):
                    ing_lower = ing.lower().strip()
                    substituted = False
                    
                    for category, items in upgrades.items():
                        for base_ing, sub_list in items.items():
                            if ingredient_matches(ing_lower, base_ing):
                                new_ing = sub_list[0] if isinstance(sub_list, list) else sub_list
                                new_ingredients.append(new_ing)
                                ingredient_subs.append(Substitution(
                                    course=course_name,
                                    original=ing,
                                    substitute=new_ing,
                                    category=category,
                                    reason=f"Adaptación saludable",
                                    adaptation_type=AdaptationType.STYLE
                                ))
                                substituted = True
                                break
                        if substituted:
                            break
                    
                    if not substituted:
                        new_ingredients.append(ing)
                
                course['ingredients'] = new_ingredients
    
    # === ADAPTACIÓN DE MÉTODOS DE COCCIÓN ===
    process_mods = style_sub_rules.get('process_modifications', {})
    
    if target_style in ['Saludable', 'Moderno', 'Gourmet']:
        for mod_category, mods in process_mods.items():
            for original_method, adaptations in mods.items():
                if f"to_{target_style}" in adaptations:
                    new_method = adaptations[f"to_{target_style}"]
                    process_adaptations.append(ProcessAdaptation(
                        course="general",
                        original_method=original_method,
                        new_method=new_method,
                        reason=f"Adaptación de técnica para estilo {target_style}",
                        execution=adaptations.get('execution', ''),
                        adaptation_type=AdaptationType.STYLE
                    ))
    
    # === ADAPTACIÓN DE PRESENTACIÓN ===
    if target_style in presentation:
        adapted_menu['presentation_guidelines'] = presentation[target_style]
    
    # === TÉCNICAS RECOMENDADAS/EVITAR ===
    if target_def:
        adapted_menu['recommended_techniques'] = target_def.get('typical_techniques', [])
        adapted_menu['avoid_techniques'] = target_def.get('avoid', [])
    
    return adapted_menu, ingredient_subs, process_adaptations

# ==============================================================================
# FASE 1: RETRIEVE
# ==============================================================================

def retrieve_similar_menus(
    user_prefs: Dict, 
    database: Dict, 
    top_k: int = 3
) -> List[Tuple[Dict, float]]:
    """
    FASE 1 CBR: RETRIEVE
    Recupera los k menús más similares a las preferencias del usuario.
    """
    menus = database.get('menus', [])
    
    similarities = []
    for menu in menus:
        score = calculate_similarity(user_prefs, menu)
        similarities.append((menu, score))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_k]

# ==============================================================================
# FASE 2: REUSE
# ==============================================================================

def reuse_menu(
    menu: Dict, 
    user_prefs: Dict, 
    databases: Dict[str, Dict]
) -> Tuple[Dict, List[Substitution], List[ProcessAdaptation]]:
    """
    FASE 2 CBR: REUSE
    Adapta el menú recuperado a las necesidades exactas del usuario.
    """
    adapted_menu = copy.deepcopy(menu)
    all_substitutions = []
    all_process_adaptations = []
    
    adapted_menu['adaptations_summary'] = {
        'cultural': [],
        'dietary': [],
        'seasonal': [],
        'style': [],
        'process': []
    }
    
    features = menu.get('features', {})
    
    # === 1. ADAPTACIÓN CULTURAL ===
    if 'cultura' in user_prefs:
        target_culture = normalize_culture_name(user_prefs['cultura'])
        menu_culture = features.get('cultura', '')
        
        if target_culture.lower() != menu_culture.lower():
            cultural_db = databases.get('cultural', {})
            
            for course_name in ['starter', 'main', 'dessert']:
                if course_name in adapted_menu.get('courses', {}):
                    course = adapted_menu['courses'][course_name]
                    original_ingredients = course.get('ingredients', [])
                    
                    adapted_ing, subs = adapt_ingredients_culturally(
                        original_ingredients, target_culture, cultural_db, course_name
                    )
                    
                    if subs:
                        course['ingredients'] = adapted_ing
                        course['original_ingredients'] = original_ingredients
                        all_substitutions.extend(subs)
                        adapted_menu['adaptations_summary']['cultural'].extend(subs)
    
    # === 2. ADAPTACIÓN DIETÉTICA ===
    dietary_restrictions = get_dietary_restrictions(user_prefs)
    
    if dietary_restrictions:
        dietary_db = databases.get('dietary', {})
        
        for course_name in ['starter', 'main', 'dessert']:
            if course_name in adapted_menu.get('courses', {}):
                course = adapted_menu['courses'][course_name]
                current_ingredients = course.get('ingredients', [])
                
                adapted_ing, subs = adapt_ingredients_dietary(
                    current_ingredients, dietary_restrictions, dietary_db, course_name
                )
                
                if subs:
                    if 'original_ingredients' not in course:
                        course['original_ingredients'] = current_ingredients
                    course['ingredients'] = adapted_ing
                    all_substitutions.extend(subs)
                    adapted_menu['adaptations_summary']['dietary'].extend(subs)
    
    # === 3. ADAPTACIÓN ESTACIONAL ===
    if 'season' in user_prefs:
        target_season = normalize_season(user_prefs['season'])
        menu_season = features.get('season', 'any-season')
        
        if target_season != 'any-season' and target_season.lower() != menu_season.lower():
            seasonal_db = databases.get('seasonal', {})
            
            for course_name in ['starter', 'main', 'dessert']:
                if course_name in adapted_menu.get('courses', {}):
                    course = adapted_menu['courses'][course_name]
                    current_ingredients = course.get('ingredients', [])
                    
                    adapted_ing, subs = adapt_ingredients_seasonal(
                        current_ingredients, target_season, seasonal_db, course_name
                    )
                    
                    if subs:
                        if 'original_ingredients' not in course:
                            course['original_ingredients'] = current_ingredients
                        course['ingredients'] = adapted_ing
                        all_substitutions.extend(subs)
                        adapted_menu['adaptations_summary']['seasonal'].extend(subs)
    
    # === 4. ADAPTACIÓN DE ESTILO ===
    if 'estilo_cocina' in user_prefs:
        target_style = normalize_style(user_prefs['estilo_cocina'])
        menu_style = features.get('estilo_cocina', '')
        
        if target_style.lower() != menu_style.lower():
            style_db = databases.get('styles', {})
            
            adapted_menu, style_subs, process_adaptations = adapt_for_style(
                adapted_menu, target_style, style_db, user_prefs
            )
            
            all_substitutions.extend(style_subs)
            all_process_adaptations.extend(process_adaptations)
            adapted_menu['adaptations_summary']['style'].extend(style_subs)
            adapted_menu['adaptations_summary']['process'].extend(process_adaptations)
    
    # === 5. ADAPTACIONES ADICIONALES (precio, tiempo) ===
    if user_prefs.get('max_price') and features.get('total_price_per_serving', 0) > user_prefs['max_price']:
        adapted_menu['price_adaptation_needed'] = {
            'current': features['total_price_per_serving'],
            'target': user_prefs['max_price'],
            'suggestion': 'Considerar ingredientes más económicos o reducir porciones'
        }
    
    if user_prefs.get('max_time') and features.get('avg_ready_time_minutes', 0) > user_prefs.get('max_time', float('inf')):
        adapted_menu['time_adaptation_needed'] = {
            'current': features['avg_ready_time_minutes'],
            'target': user_prefs['max_time'],
            'suggestion': 'Usar técnicas de cocción más rápidas o ingredientes pre-preparados'
        }
    
    return adapted_menu, all_substitutions, all_process_adaptations

# ==============================================================================
# FASE 3: REVISE
# ==============================================================================

def revise_menu(
    adapted_menu: Dict, 
    user_prefs: Dict,
    all_substitutions: List[Substitution]
) -> Tuple[bool, List[str], List[str]]:
    """
    FASE 3 CBR: REVISE
    Valida si el menú adaptado cumple todas las restricciones del usuario.
    
    Returns:
        (is_valid, critical_issues, warnings)
    """
    critical_issues = []
    warnings = []
    features = adapted_menu.get('features', {})
    
    # === VALIDAR RESTRICCIONES DIETÉTICAS CRÍTICAS ===
    dietary_checks = [
        ('is_vegan', 'Vegano'),
        ('is_vegetarian', 'Vegetariano'),
        ('is_gluten_free', 'Sin Gluten'),
        ('is_kosher', 'Kosher'),
        ('is_halal', 'Halal')
    ]
    
    for key, name in dietary_checks:
        if user_prefs.get(key, False):
            # Verificar si hay sustituciones que no se pudieron hacer
            failed_subs = [s for s in all_substitutions 
                          if s.adaptation_type == AdaptationType.DIETARY 
                          and s.substitute == "[ELIMINAR]"]
            
            if failed_subs:
                warnings.append(f"⚠️ Algunos ingredientes no tienen sustituto {name} y fueron eliminados")
            
            if not features.get(key, False):
                # El menú original no cumple, verificar si se adaptó correctamente
                dietary_subs = [s for s in all_substitutions 
                               if s.adaptation_type == AdaptationType.DIETARY]
                if not dietary_subs:
                    critical_issues.append(f"❌ No se pudo adaptar el menú para requisito {name}")
    
    # === VALIDAR PRECIO ===
    if 'max_price' in user_prefs:
        menu_price = features.get('total_price_per_serving', 0)
        max_price = user_prefs['max_price']
        tolerance = 1.1  # 10% tolerancia
        
        if menu_price > max_price * tolerance:
            critical_issues.append(
                f"❌ Precio ${menu_price:.2f} excede presupuesto ${max_price:.2f} (tolerancia 10%)"
            )
        elif menu_price > max_price:
            warnings.append(
                f"⚠️ Precio ${menu_price:.2f} ligeramente sobre presupuesto ${max_price:.2f}"
            )
    
    # === VALIDAR TIEMPO ===
    if 'max_time' in user_prefs:
        menu_time = features.get('avg_ready_time_minutes', 0)
        max_time = user_prefs['max_time']
        tolerance = 1.15  # 15% tolerancia
        
        if menu_time > 0 and menu_time > max_time * tolerance:
            critical_issues.append(
                f"❌ Tiempo {menu_time} min excede límite {max_time} min"
            )
        elif menu_time > max_time:
            warnings.append(
                f"⚠️ Tiempo {menu_time} min ligeramente sobre límite {max_time} min"
            )
    
    # === VALIDAR ADAPTACIONES EXITOSAS ===
    total_subs = len(all_substitutions)
    successful_subs = len([s for s in all_substitutions if s.substitute != "[ELIMINAR]"])
    
    if total_subs > 0:
        success_rate = successful_subs / total_subs
        if success_rate < 0.8:
            warnings.append(
                f"⚠️ Solo {success_rate*100:.0f}% de las adaptaciones fueron exitosas"
            )
    
    is_valid = len(critical_issues) == 0
    return is_valid, critical_issues, warnings

# ==============================================================================
# FASE 4: RETAIN
# ==============================================================================

def retain_menu(
    adapted_menu: Dict, 
    success: bool,
    database_path: str = None
) -> Dict:
    """
    FASE 4 CBR: RETAIN
    Si el menú fue exitoso, prepararlo para añadir a la base de datos.
    """
    if success:
        # Crear nuevo caso para la base de datos
        new_case = {
            'menu_id': f"adapted_{adapted_menu.get('menu_id', 'new')}",
            'menu_name': f"Adapted: {adapted_menu.get('menu_name', 'Menu')}",
            'source_menu_id': adapted_menu.get('menu_id'),
            'adaptation_date': '2025-12-15',
            'courses': adapted_menu.get('courses', {}),
            'features': adapted_menu.get('features', {}),
            'adaptations_applied': adapted_menu.get('adaptations_summary', {}),
            'success': True
        }
        
        print("   ✅ Caso exitoso - Listo para añadir a la base de datos")
        print(f"   📁 ID del nuevo caso: {new_case['menu_id']}")
        
        # En producción, aquí se guardaría en la base de datos
        # save_to_database(new_case, database_path)
        
        return new_case
    else:
        print("   ❌ Caso no exitoso - No se retiene")
        return None

# ==============================================================================
# IMPRESIÓN Y FORMATEO
# ==============================================================================

def print_menu_summary(menu: Dict, similarity: float = None):
    """Imprime resumen completo de un menú"""
    features = menu.get('features', {})
    courses = menu.get('courses', {})
    
    print(f"\n{'='*70}")
    if similarity is not None:
        print(f"📊 SIMILITUD: {similarity*100:.1f}%")
    print(f"{'='*70}")
    print(f"🍽️  {menu.get('menu_name', 'Menú Sin Nombre')}")
    print(f"{'='*70}")
    
    # Cultura y estilo
    if 'cultura' in features:
        print(f"\n🌍 CULTURA: {features['cultura']}")
    if 'estilo_cocina' in features:
        print(f"👨‍🍳 ESTILO: {features['estilo_cocina']}")
    
    # Cursos
    for course_name, emoji in [('starter', '🥗'), ('main', '🍖'), ('dessert', '🍰')]:
        if course_name in courses:
            course = courses[course_name]
            print(f"\n{emoji} {course_name.upper()}: {course.get('title', 'N/A')}")
            print(f"   💰 Precio: ${course.get('price_per_serving', 0):.2f}")
            ingredients = course.get('ingredients', [])[:5]
            print(f"   🧂 Ingredientes: {', '.join(ingredients)}{'...' if len(course.get('ingredients', [])) > 5 else ''}")
    
    # Totales
    print(f"\n{'─'*70}")
    print(f"💰 TOTAL: ${features.get('total_price_per_serving', 0):.2f} ({features.get('price_category', 'N/A')})")
    print(f"⏱️  TIEMPO: {features.get('avg_ready_time_minutes', 0)} min ({features.get('time_category', 'N/A')})")
    print(f"🌿 ESTACIÓN: {features.get('season', 'N/A')}")
    print(f"🍷 VINO: {features.get('wine_pairing', 'N/A')}")
    
    # Restricciones
    restrictions = []
    if features.get('is_vegan'): restrictions.append("🌱 Vegano")
    elif features.get('is_vegetarian'): restrictions.append("🥬 Vegetariano")
    if features.get('is_gluten_free'): restrictions.append("🌾 Sin Gluten")
    if features.get('is_dairy_free'): restrictions.append("🥛 Sin Lácteos")
    if features.get('is_kosher'): restrictions.append("✡️ Kosher")
    if features.get('is_halal'): restrictions.append("☪️ Halal")
    
    if restrictions:
        print(f"\n✅ CERTIFICACIONES: {' | '.join(restrictions)}")

def print_adaptations_summary(
    substitutions: List[Substitution], 
    process_adaptations: List[ProcessAdaptation]
):
    """Imprime resumen de todas las adaptaciones realizadas"""
    
    if not substitutions and not process_adaptations:
        print("\n✅ El menú no requirió adaptaciones")
        return
    
    print(f"\n{'='*70}")
    print(f"🔄 ADAPTACIONES REALIZADAS")
    print(f"{'='*70}")
    
    # Agrupar por tipo
    by_type = {}
    for sub in substitutions:
        type_name = sub.adaptation_type.value
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(sub)
    
    type_emojis = {
        'cultural': '🌍',
        'dietary': '🥗',
        'seasonal': '🍂',
        'style': '👨‍🍳',
        'price': '💰',
        'time': '⏱️'
    }
    
    type_names = {
        'cultural': 'CULTURALES',
        'dietary': 'DIETÉTICAS',
        'seasonal': 'ESTACIONALES',
        'style': 'DE ESTILO',
        'price': 'DE PRECIO',
        'time': 'DE TIEMPO'
    }
    
    for type_key, subs in by_type.items():
        emoji = type_emojis.get(type_key, '🔧')
        name = type_names.get(type_key, type_key.upper())
        
        print(f"\n{emoji} ADAPTACIONES {name} ({len(subs)} cambios):")
        for sub in subs[:10]:  # Mostrar máximo 10
            if sub.substitute != "[ELIMINAR]":
                print(f"   [{sub.course}] {sub.original} → {sub.substitute}")
                if sub.notes:
                    print(f"         💡 {sub.notes}")
            else:
                print(f"   [{sub.course}] {sub.original} → [ELIMINADO]")
        
        if len(subs) > 10:
            print(f"   ... y {len(subs) - 10} más")
    
    if process_adaptations:
        print(f"\n⚙️ ADAPTACIONES DE PROCESO ({len(process_adaptations)} cambios):")
        for proc in process_adaptations:
            print(f"   [{proc.course}] {proc.original_method} → {proc.new_method}")
            if proc.execution:
                print(f"         📝 {proc.execution}")

# ==============================================================================
# SISTEMA CBR COMPLETO
# ==============================================================================

def run_cbr_system(user_prefs: Dict, verbose: bool = True) -> Tuple[Dict, bool]:
    """
    Ejecuta el sistema CBR completo.
    
    Returns:
        (adapted_menu, is_valid)
    """
    if verbose:
        print(f"\n{'#'*70}")
        print(f"# SISTEMA CBR PROFESIONAL DE MENÚS")
        print(f"{'#'*70}")
    
    # Cargar todas las bases de datos
    if verbose:
        print("\n📂 Cargando bases de datos...")
    
    databases = load_all_databases()
    
    if verbose:
        print(f"   ✅ Menús CBR: {databases['menus']['metadata']['total_menus']} menús")
        print(f"   ✅ Culturas: {len(databases['cultural'].get('cultural_ingredients', {}))} culturas")
        print(f"   ✅ Restricciones dietéticas: {len(databases['dietary'].get('substitution_rules', {}))} tipos")
        print(f"   ✅ Estaciones: {len(databases['seasonal'].get('seasonal_ingredients', {}))} estaciones")
        print(f"   ✅ Estilos: {len(databases['styles'].get('style_definitions', {}))} estilos")
    
    # Mostrar preferencias
    if verbose:
        print(f"\n{'='*70}")
        print(f"🔍 PREFERENCIAS DEL USUARIO")
        print(f"{'='*70}")
        if 'cultura' in user_prefs:
            print(f"   🌍 Cultura: {user_prefs['cultura']}")
        if 'estilo_cocina' in user_prefs:
            print(f"   👨‍🍳 Estilo: {user_prefs['estilo_cocina']}")
        if 'season' in user_prefs:
            print(f"   🍂 Estación: {user_prefs['season']}")
        if 'max_price' in user_prefs:
            print(f"   💰 Presupuesto máx: ${user_prefs['max_price']}")
        
        dietary = []
        if user_prefs.get('is_vegan'): dietary.append("Vegano")
        if user_prefs.get('is_vegetarian'): dietary.append("Vegetariano")
        if user_prefs.get('is_gluten_free'): dietary.append("Sin Gluten")
        if user_prefs.get('is_dairy_free'): dietary.append("Sin Lácteos")
        if user_prefs.get('is_kosher'): dietary.append("Kosher")
        if user_prefs.get('is_halal'): dietary.append("Halal")
        if dietary:
            print(f"   🥗 Dietético: {', '.join(dietary)}")
    
    # FASE 1: RETRIEVE
    if verbose:
        print(f"\n{'='*70}")
        print(f"🔍 FASE 1: RETRIEVE - Buscando menús similares...")
        print(f"{'='*70}")
    
    similar_menus = retrieve_similar_menus(user_prefs, databases['menus'], top_k=3)
    
    if verbose:
        print(f"\n📊 Top 3 menús más similares:")
        for idx, (menu, sim) in enumerate(similar_menus, 1):
            culture = menu.get('features', {}).get('cultura', 'N/A')
            style = menu.get('features', {}).get('estilo_cocina', 'N/A')
            print(f"   {idx}. {menu.get('menu_name', 'N/A')}")
            print(f"      Cultura: {culture} | Estilo: {style} | Similitud: {sim*100:.1f}%")
    
    # Seleccionar el mejor
    best_menu, best_similarity = similar_menus[0]
    
    if verbose:
        print_menu_summary(best_menu, best_similarity)
    
    # FASE 2: REUSE
    if verbose:
        print(f"\n{'='*70}")
        print(f"♻️ FASE 2: REUSE - Adaptando menú...")
        print(f"{'='*70}")
    
    adapted_menu, substitutions, process_adaptations = reuse_menu(
        best_menu, user_prefs, databases
    )
    
    if verbose:
        print_adaptations_summary(substitutions, process_adaptations)
        print_menu_summary(adapted_menu)
    
    # FASE 3: REVISE
    if verbose:
        print(f"\n{'='*70}")
        print(f"🔍 FASE 3: REVISE - Validando adaptaciones...")
        print(f"{'='*70}")
    
    is_valid, critical_issues, warnings = revise_menu(
        adapted_menu, user_prefs, substitutions
    )
    
    if verbose:
        if is_valid:
            print(f"\n✅ VALIDACIÓN EXITOSA")
        else:
            print(f"\n❌ VALIDACIÓN CON PROBLEMAS")
        
        for issue in critical_issues:
            print(f"   {issue}")
        for warning in warnings:
            print(f"   {warning}")
    
    # FASE 4: RETAIN
    if verbose:
        print(f"\n{'='*70}")
        print(f"💾 FASE 4: RETAIN - ¿Retener caso?")
        print(f"{'='*70}")
    
    retain_menu(adapted_menu, is_valid)
    
    if verbose:
        print(f"\n{'='*70}\n")
    
    return adapted_menu, is_valid

# ==============================================================================
# FUNCIÓN PRINCIPAL Y DEMOS
# ==============================================================================

def main():
    """Función principal con ejemplos de demostración"""
    
    print(f"\n{'#'*70}")
    print(f"# DEMOSTRACIÓN: SISTEMA CBR PROFESIONAL DE MENÚS")
    print(f"# Con adaptaciones: Cultural + Dietética + Estacional + Estilo")
    print(f"{'#'*70}")
    
    # =========================================================================
    # EJEMPLO 1: Usuario vegano que quiere cocina italiana moderna en verano
    # =========================================================================
    print(f"\n\n{'='*70}")
    print(f"📋 EJEMPLO 1: Vegano + Italiana + Moderno + Verano")
    print(f"{'='*70}")
    
    user_prefs_1 = {
        'cultura': 'Italiana',
        'estilo_cocina': 'Moderno',
        'season': 'Summer',
        'is_vegan': True,
        'max_price': 500
    }
    
    menu1, valid1 = run_cbr_system(user_prefs_1)
    
    # =========================================================================
    # EJEMPLO 2: Usuario kosher que quiere cocina mediterránea tradicional
    # =========================================================================
    print(f"\n\n{'='*70}")
    print(f"📋 EJEMPLO 2: Kosher + Mediterránea + Tradicional + Invierno")
    print(f"{'='*70}")
    
    user_prefs_2 = {
        'cultura': 'Mediterránea',
        'estilo_cocina': 'Tradicional',
        'season': 'Winter',
        'is_kosher': True,
        'max_price': 400
    }
    
    menu2, valid2 = run_cbr_system(user_prefs_2)
    
    # =========================================================================
    # EJEMPLO 3: Usuario sin gluten que quiere cocina mexicana gourmet en otoño
    # =========================================================================
    print(f"\n\n{'='*70}")
    print(f"📋 EJEMPLO 3: Sin Gluten + Mexicana + Gourmet + Otoño")
    print(f"{'='*70}")
    
    user_prefs_3 = {
        'cultura': 'Mexicana',
        'estilo_cocina': 'Gourmet',
        'season': 'Fall',
        'is_gluten_free': True,
        'is_dairy_free': True,
        'max_price': 600
    }
    
    menu3, valid3 = run_cbr_system(user_prefs_3)
    
    # =========================================================================
    # EJEMPLO 4: Usuario halal vegetariano que quiere cocina saludable
    # =========================================================================
    print(f"\n\n{'='*70}")
    print(f"📋 EJEMPLO 4: Halal + Vegetariano + Saludable + Primavera")
    print(f"{'='*70}")
    
    user_prefs_4 = {
        'cultura': 'India',
        'estilo_cocina': 'Saludable',
        'season': 'Spring',
        'is_halal': True,
        'is_vegetarian': True,
        'max_price': 350
    }
    
    menu4, valid4 = run_cbr_system(user_prefs_4)
    
    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print(f"\n{'#'*70}")
    print(f"# RESUMEN DE DEMOS")
    print(f"{'#'*70}")
    
    results = [
        ("Vegano + Italiana + Moderno + Verano", valid1),
        ("Kosher + Mediterránea + Tradicional + Invierno", valid2),
        ("Sin Gluten + Mexicana + Gourmet + Otoño", valid3),
        ("Halal + Vegetariano + Saludable + Primavera", valid4)
    ]
    
    for name, is_valid in results:
        status = "✅ EXITOSO" if is_valid else "⚠️ CON ADVERTENCIAS"
        print(f"   {status}: {name}")
    
    print(f"\n{'#'*70}")
    print(f"# DEMOSTRACIÓN COMPLETADA")
    print(f"{'#'*70}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrumpido por el usuario\n")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"\n❌ Error: No se encontró el archivo: {e}")
        print("   Asegúrate de que todas las bases de datos estén en el directorio correcto\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
