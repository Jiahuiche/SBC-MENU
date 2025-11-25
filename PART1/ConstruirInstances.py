"""
Script para convertir recetas desde JSON a instancias CLIPS
- Lee filtered_recipes111.json
- Convierte cada receta a formato definstances de CLIPS
- Genera recipes_clips.clp con todas las instancias
"""

import json
import re


def sanitize_for_clips(text):
    """
    Convierte texto a formato válido para CLIPS:
    - Reemplaza espacios por guiones
    - Elimina caracteres especiales
    - Convierte a minúsculas
    """
    if not text or text == "":
        return ""
    
    # Convertir a minúsculas
    text = text.lower()
    
    # Reemplazar espacios y caracteres especiales por guiones
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    
    # Eliminar guiones al inicio/final
    text = text.strip('-')
    
    return text

def detect_restrictions_from_ingredients(ingredients):
    """
    Detecta restricciones alimentarias basadas en los ingredientes.
    Retorna un conjunto de restricciones detectadas.
    """

    restrictions = set()
    
    
    ingredients_text = ' '.join(ingredients).lower()
    
    
    # Detectar frutos secos
    nut_patterns = [
        'almond', 'walnut', 'hazelnut',
        'peanut', 'pistachio', 'cashew',
        'nuts', 'macadamia-nut', 'pine-nut',
    ]
    
    nut_detected = any(pattern in ingredients_text for pattern in nut_patterns)
    if not nut_detected:
        restrictions.add('nut-free')
    
    # Detectar mariscos específicamente
    shellfish_patterns = [
        'shrimp', 'prawn', 'lobster',
        'crab', 'mussel', 'clam',
        'oyster', 'scallop', 'shellfish'
    ]
    
    shellfish_detected = any(pattern in ingredients_text for pattern in shellfish_patterns)
    if not shellfish_detected:
        restrictions.add('shellfish-free')
    
    # Detectar soja
    soy_patterns = [
        'soy', 'tofu', 'tempeh', 'soy-sauce',
        'soy-milk', 'edamame'
    ]
    
    soy_detected = any(pattern in ingredients_text for pattern in soy_patterns)
    if not soy_detected:
        restrictions.add('soy-free')
    
    return restrictions

def infer_wine_pairing(recipe):
    """Determina el tipo de vino recomendado si falta o es 'No wine pairing'."""
    current = recipe.get('winePairing')
    if current and current.strip() and current.strip().lower() != 'no wine pairing':
        return current

    ingredients = recipe.get('ingredients') or []
    ingredients_text = ' '.join(str(item).lower() for item in ingredients)

    meal_types_field = recipe.get('mealTypes')
    if isinstance(meal_types_field, str):
        meal_tokens = [token.strip().lower() for token in meal_types_field.split(',') if token.strip()]
    elif isinstance(meal_types_field, list):
        meal_tokens = [str(token).strip().lower() for token in meal_types_field if str(token).strip()]
    else:
        meal_tokens = []

    keyword_groups = {
        'red': {
            'beef', 'lamb', 'steak', 'venison', 'duck', 'mushroom', 'portobello',
            'tomato', 'bbq', 'bacon', 'sausage', 'chorizo', 'pork-shoulder'
        },
        'white': {
            'chicken', 'turkey', 'cod', 'halibut', 'sole', 'shrimp', 'scallop',
            'lobster', 'crab', 'clam', 'mussel', 'tilapia', 'bass', 'lemon', 'herb',
            'garlic', 'butter', 'goat cheese', 'feta', 'chevre'
        },
        'rose': {
            'salmon', 'tuna', 'charcuterie', 'prosciutto', 'pesto', 'tomato',
            'berry', 'strawberry', 'raspberry'
        },
        'sparkling': {
            'fried', 'tempura', 'batter', 'quiche', 'cheese', 'brie', 'gouda',
            'creamy', 'brunch', 'sushi'
        },
        'dessert': {
            'chocolate', 'cocoa', 'caramel', 'honey', 'maple', 'custard', 'cream',
            'cheesecake', 'ice cream', 'mousse', 'tiramisu', 'pie', 'cake', 'tart'
        },
        'aromatic_white': {
            'curry', 'chili', 'jalapeno', 'chipotle', 'harissa', 'sriracha',
            'ginger', 'lemongrass', 'thai', 'coconut milk'
        },
    }

    scores = {key: 0 for key in keyword_groups.keys()}

    for category, keywords in keyword_groups.items():
        for keyword in keywords:
            if keyword in ingredients_text:
                scores[category] += 1

    if any(token in {'dessert', 'sweet', 'treat'} for token in meal_tokens):
        scores['dessert'] += 3

    if any(token in {'starter', 'appetizer', 'antipasti', 'snack', 'fingerfood'} for token in meal_tokens):
        scores['sparkling'] += 1

    wine_types = {
        'red': "Red wine",
        'white': "White wine",
        'rose': "Rosé wine",
        'sparkling': "Sparkling wine",
        'dessert': "Dessert wine",
        'aromatic_white': "Aromatic white wine",
        'default': "No wine pairing"
    }

    priority = ['dessert', 'aromatic_white', 'red', 'white', 'rose', 'sparkling']
    best_category = 'default'
    best_score = 0
    for category in priority:
        score = scores.get(category, 0)
        if score > best_score:
            best_score = score
            best_category = category

    if best_score == 0:
        return wine_types['default']

    return wine_types.get(best_category, wine_types['default'])


def extract_ingredients(recipe):
    """
    Extrae y sanitiza lista de ingredientes para CLIPS.
    Convierte cada ingrediente a formato símbolo válido.
    """
    if 'ingredients' not in recipe or not recipe['ingredients']:
        return ['unknown-ingredient']
    
    ingredients_symbols = []
    for ingredient in recipe['ingredients']:
        sanitized = sanitize_for_clips(ingredient)
        if sanitized:
            ingredients_symbols.append(sanitized)
    
    return ingredients_symbols if ingredients_symbols else ['unknown-ingredient']

def extract_restrictions(recipe):
    """
    Extrae restricciones desde variables booleanas y campo restrictions.
    Fusiona todas las restricciones en una lista de símbolos CLIPS.
    """
    restrictions_set = set()
    
    # Variables booleanas que indican restricciones
    bool_restrictions = {
        'vegan': 'vegan',
        'glutenFree': 'gluten-free',
        'vegetarian': 'vegetarian',
        'dairyFree': 'dairy-free',
        'isKosher': 'kosher',
        'isHalal': 'halal'
    }
    
    # Añadir restricciones booleanas que sean True
    for field, restriction_name in bool_restrictions.items():
        if recipe.get(field, False) == True:
            restrictions_set.add(restriction_name)
    
    # Añadir restricciones del campo 'restrictions' (lista de strings)
    if 'restrictions' in recipe and recipe['restrictions']:
        for restriction in recipe['restrictions']:
            sanitized = sanitize_for_clips(restriction)
            if sanitized:
                restrictions_set.add(sanitized)

    #Detectar restricciones basadas en ingredientes
    ingredients = extract_ingredients(recipe)
    ingredient_restrictions = detect_restrictions_from_ingredients(ingredients)
    restrictions_set.update(ingredient_restrictions)
    
    # Si no hay restricciones, indicar "no-restrictions"
    if not restrictions_set:
        restrictions_set.add('no-restrictions')
    
    return sorted(list(restrictions_set))


def extract_ingredients(recipe):
    """
    Extrae y sanitiza lista de ingredientes para CLIPS.
    Convierte cada ingrediente a formato símbolo válido.
    """
    if 'ingredients' not in recipe or not recipe['ingredients']:
        return ['unknown-ingredient']
    
    ingredients_symbols = []
    for ingredient in recipe['ingredients']:
        sanitized = sanitize_for_clips(ingredient)
        if sanitized:
            ingredients_symbols.append(sanitized)
    
    return ingredients_symbols if ingredients_symbols else ['unknown-ingredient']


def extract_mealtypes(recipe):
    """Obtiene la lista de tipos de comida desde mealTypes."""
    raw = recipe.get('mealTypes')
    if not raw:
        return ['mixed']

    if isinstance(raw, str):
        candidates = [item.strip() for item in raw.split(',') if item.strip()]
    elif isinstance(raw, list):
        candidates = []
        for entry in raw:
            if isinstance(entry, str):
                value = entry.strip()
                if value:
                    candidates.append(value)
    else:
        candidates = []

    meal_types = []
    for candidate in candidates:
        sanitized = sanitize_for_clips(candidate)
        if sanitized and sanitized not in meal_types:
            meal_types.append(sanitized)

    return meal_types if meal_types else ['mixed']


def extract_seasons(recipe):
    """
    Extrae estación(es) desde el campo seasons.
    Retorna símbolo CLIPS válido para la ontología.
    """
    if 'seasons' not in recipe or not recipe['seasons']:
        return 'any-season'
    
    seasons = recipe['seasons']
    
    # Si es una lista, tomar el primer elemento
    if isinstance(seasons, list):
        if len(seasons) > 0:
            season = seasons[0]
        else:
            return 'any-season'
    else:
        season = seasons
    
    # Sanitizar y validar contra allowed-symbols
    season_sanitized = sanitize_for_clips(season)
    
    # Mapeo a símbolos permitidos en la ontología
    valid_seasons = ['any-season', 'spring', 'summer', 'autumn', 'winter']
    
    if season_sanitized in valid_seasons:
        return season_sanitized
    else:
        return 'any-season'


def calculate_price(recipe):
    """
    Calcula el precio según la lógica especificada:
    1. Si existe priceCalculated, usar ese valor
    2. Si no, calcular pricePerServing / servings
    """
    if 'priceCalculated' in recipe and recipe['priceCalculated'] is not None:
        return round(recipe['priceCalculated'], 2)
    elif 'pricePerServing' in recipe and 'servings' in recipe:
        servings = recipe['servings']
        if servings > 0:
            return round(recipe['pricePerServing'] / servings, 2)
    
    return 0.0


def escape_clips_string(text):
    """
    Escapa caracteres especiales en strings de CLIPS.
    CLIPS requiere escapar comillas dobles dentro de strings.
    """
    if not text:
        return ""
    
    # Escapar comillas dobles
    text = text.replace('"', '\\"')
    
    return text

def determine_complexity(recipe_id):
    """
    Determines if a recipe is complex based on its ID.
    Returns True for 25% of recipes (when ID mod 4 equals 0)
    """
    return 'TRUE' if recipe_id % 4 == 0 else 'FALSE'

def generate_explanation(recipe):
    """
    Genera una explicación gastronómica única y atractiva para cada plato.
    Combina información sobre ingredientes, sabor, vino, restricciones y estación.
    """
    import random
    
    title = recipe.get('title', 'Unknown Recipe')
    ingredients = recipe.get('ingredients', [])
    meal_types_raw = recipe.get('mealTypes', '')
    wine_pairing = infer_wine_pairing(recipe)
    restrictions = extract_restrictions(recipe)
    season = extract_seasons(recipe)
    
    # Extraer palabras clave de ingredientes
    key_ingredients = []
    highlight_words = ['chocolate', 'salmon', 'chicken', 'beef', 'lamb', 'mushroom', 
                       'cheese', 'shrimp', 'garlic', 'lemon', 'coconut', 'curry',
                       'tomato', 'bacon', 'avocado', 'strawberry', 'pumpkin']
    
    for ing in ingredients[:8]:  # Revisar primeros ingredientes
        ing_lower = str(ing).lower()
        for hw in highlight_words:
            if hw in ing_lower:
                key_ingredients.append(hw)
                break
    
    # Detectar perfil de sabor
    flavor_profiles = []
    spicy_keywords = ['chili', 'chipotle', 'jalapeno', 'cayenne', 'sriracha', 'harissa']
    comfort_keywords = ['cream', 'cheese', 'butter', 'pasta', 'potato', 'bacon']
    fresh_keywords = ['lemon', 'lime', 'herb', 'salad', 'vegetable', 'citrus']
    rich_keywords = ['chocolate', 'caramel', 'wine', 'duck', 'beef', 'cream']
    
    ingredients_text = ' '.join(str(i).lower() for i in ingredients)
    
    if any(k in ingredients_text for k in spicy_keywords):
        flavor_profiles.append(random.choice(['spicy', 'bold and spicy', 'fiery', 'with a kick']))
    if any(k in ingredients_text for k in comfort_keywords):
        flavor_profiles.append(random.choice(['comforting', 'indulgent', 'rich and creamy', 'satisfying']))
    if any(k in ingredients_text for k in fresh_keywords):
        flavor_profiles.append(random.choice(['fresh', 'vibrant', 'light and zesty', 'refreshing']))
    if any(k in ingredients_text for k in rich_keywords):
        flavor_profiles.append(random.choice(['luxurious', 'decadent', 'sophisticated', 'elegant']))
    
    if not flavor_profiles:
        flavor_profiles = [random.choice(['delicious', 'flavorful', 'aromatic', 'balanced'])]
    
    # Templates variados para estructura
    templates = []
    
    # Template 1: Ingrediente destacado + perfil + vino
    if key_ingredients:
        templates.append(
            f"A {flavor_profiles[0]} dish featuring {', '.join(key_ingredients[:2]) if len(key_ingredients) >= 2 else key_ingredients[0]}, "
            f"perfect for those seeking {restrictions[0] if 'free' in restrictions[0] else 'authentic'} cuisine. "
            f"Pairs beautifully with {wine_pairing.lower()}{' and shines in ' + season + ' season' if season != 'any-season' else ''}."
        )
    
    # Template 2: Experiencia sensorial + restricciones
    templates.append(
        f"This {flavor_profiles[0]} creation delivers {'complex layers of flavor' if len(ingredients) > 10 else 'simple, honest taste'}. "
        f"{'Suitable for ' + ', '.join([r.replace('-', ' ') for r in restrictions[:2]]) + ' diets' if len(restrictions) > 1 else 'A versatile choice'}. "
        f"Enjoy with {wine_pairing.lower()} for an elevated experience."
    )
    
    # Template 3: Estilo culinario + momento
    meal_descriptor = 'appetizer' if 'starter' in meal_types_raw or 'appetizer' in meal_types_raw else \
                     'main course' if 'main' in meal_types_raw else \
                     'dessert' if 'dessert' in meal_types_raw else 'dish'
    
    templates.append(
        f"{'A seasonal favorite' if season != 'any-season' else 'A timeless classic'} "
        f"that brings {random.choice(['warmth', 'joy', 'comfort', 'delight', 'satisfaction'])} to your table. "
        f"This {flavor_profiles[0]} {meal_descriptor} is {random.choice(['crafted', 'prepared', 'designed', 'made'])} "
        f"with {len(ingredients)} quality ingredients and matches wonderfully with {wine_pairing.lower()}."
    )
    
    # Template 4: Ingredientes + beneficio + vino
    if key_ingredients:
        templates.append(
            f"Featuring {' and '.join(key_ingredients[:3]) if len(key_ingredients) >= 2 else 'premium ingredients'}, "
            f"this {flavor_profiles[0]} recipe offers {'wholesome nourishment' if 'vegetarian' in restrictions or 'vegan' in restrictions else 'satisfying flavors'}. "
            f"{'Perfect for ' + season + ' dining' if season != 'any-season' else 'Ideal year-round'}. "
            f"Best enjoyed with {wine_pairing.lower()}."
        )
    
    # Template 5: Estilo narrativo
    taste_words = ['tender', 'crispy', 'silky', 'robust', 'delicate', 'hearty', 'smooth']
    templates.append(
        f"Experience the {random.choice(taste_words)} texture and {flavor_profiles[0]} character of this exceptional dish. "
        f"{'Crafted for ' + ', '.join([r.replace('-', ' ') for r in restrictions[:2]]) if len(restrictions) >= 2 else 'A culinary delight'} "
        f"that harmonizes perfectly with {wine_pairing.lower()}."
    )
    
    # Seleccionar template basado en ID para consistencia pero variedad
    recipe_id = recipe.get('id', 0)
    selected = templates[recipe_id % len(templates)]
    
    # Limitar a ~3 líneas (~200 caracteres)
    if len(selected) > 250:
        selected = selected[:247] + '...'
    
    return selected

def recipe_to_clips_instance(recipe):
    """
    Convierte una receta JSON a una instancia CLIPS.
    Retorna el string de la instancia en formato CLIPS.
    """
    recipe_id = recipe.get('id', 0)
    instance_name = f"Recipe_{recipe_id}"
    
    # Extraer campos
    title = escape_clips_string(recipe.get('title', 'Unknown Recipe'))
    price = calculate_price(recipe)
    wine = infer_wine_pairing(recipe)
    wine_pairing = escape_clips_string(wine)
    explanation_text = generate_explanation(recipe)
    explanation = escape_clips_string(explanation_text)
    is_complex = determine_complexity(recipe_id)
    restrictions = extract_restrictions(recipe)
    ingredients = extract_ingredients(recipe)
    meal_types = extract_mealtypes(recipe)
    seasons = extract_seasons(recipe)
    
    # Construir la instancia CLIPS
    instance_str = f'  ([{instance_name}] of ONTOLOGY::Recipe\n'
    instance_str += f'    (title "{title}")\n'
    instance_str += f'    (price {price})\n'
    instance_str += f'    (wine_pairing "{wine_pairing}")\n'
    instance_str += f'    (explanation "{explanation}")\n'
    instance_str += f'    (is_complex {is_complex})\n'
    
    # Multislot meal-types
    instance_str += f'    (meal-types {" ".join(meal_types)})\n'
    
    # Multislot restrictions
    instance_str += f'    (restrictions {" ".join(restrictions)})\n'
    
    # Multislot ingredients
    instance_str += f'    (ingredients {" ".join(ingredients)})\n'
    
    # Slot seasons (símbolo único)
    instance_str += f'    (seasons {seasons}))'
    
    return instance_str


def convert_json_to_clips(json_file='filtered_recipes111.json', output_file='recipes_clips.clp'):
    """
    Función principal que lee el JSON y genera el archivo CLIPS.
    """
    print(f"📂 Leyendo recetas desde {json_file}...")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {json_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error al decodificar JSON: {e}")
        return
    
    print(f"✓ Se cargaron {len(recipes)} recetas")
    
    # Generar instancias CLIPS
    print(f"🔄 Convirtiendo recetas a formato CLIPS...")
    
    instances = []
    for recipe in recipes:
        instance_str = recipe_to_clips_instance(recipe)
        instances.append(instance_str)
    
    # Escribir archivo CLIPS
    print(f"💾 Escribiendo instancias en {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('(defmodule DATA\n (import ONTOLOGY ?ALL)\n (export ?ALL))\n\n')
        f.write('(definstances DATA::recipes-seed\n\n')
        f.write('\n\n'.join(instances))
        f.write('\n)\n')
    
    print(f"✅ ¡Completado! Se generaron {len(instances)} instancias en {output_file}")
    print(f"📊 Estadísticas:")
    print(f"   - Total de recetas: {len(recipes)}")
    print(f"   - Archivo de salida: {output_file}")


if __name__ == "__main__":
    # Ejecutar conversión
    convert_json_to_clips()
