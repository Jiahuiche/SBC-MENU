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


def extract_meal_types(recipe):
    """
    Extrae tipos de comida desde mealTypes.
    Convierte la cadena separada por comas a lista de símbolos.
    """
    meal_types_symbols = []
    
    if 'mealTypes' in recipe and recipe['mealTypes']:
        # mealTypes es un string separado por comas
        meal_types_str = recipe['mealTypes']
        meal_types_list = [mt.strip() for mt in meal_types_str.split(',')]
        
        for meal_type in meal_types_list:
            sanitized = sanitize_for_clips(meal_type)
            if sanitized:
                meal_types_symbols.append(sanitized)
    
    return meal_types_symbols if meal_types_symbols else ['main-course']


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


def recipe_to_clips_instance(recipe):
    """
    Convierte una receta JSON a una instancia CLIPS.
    Retorna el string de la instancia en formato CLIPS.
    """
    recipe_id = recipe.get('id', 0)
    instance_name = f"Recipe_{recipe_id}"
    
    # Extraer campos
    title = escape_clips_string(recipe.get('title', 'Unknown Recipe'))
    servings = recipe.get('servings', 1)
    price = calculate_price(recipe)
    wine_pairing = escape_clips_string(recipe.get('winePairing', 'No wine pairing'))
    
    restrictions = extract_restrictions(recipe)
    ingredients = extract_ingredients(recipe)
    meal_types = extract_meal_types(recipe)
    seasons = extract_seasons(recipe)
    season_text = escape_clips_string(recipe.get('seasonText', ''))
    
    # Construir la instancia CLIPS
    instance_str = f'  ([{instance_name}] of ONTOLOGY::Recipe\n'
    instance_str += f'    (title "{title}")\n'
    instance_str += f'    (servings {servings})\n'
    instance_str += f'    (price {price})\n'
    instance_str += f'    (wine_pairing "{wine_pairing}")\n'
    
    # Multislot meal_types
    instance_str += f'    (meal_types {" ".join(meal_types)})\n'
    
    # Multislot restrictions
    instance_str += f'    (restrictions {" ".join(restrictions)})\n'
    
    # Multislot ingredients
    instance_str += f'    (ingredients {" ".join(ingredients)})\n'
    
    # Slot seasons (símbolo único)
    instance_str += f'    (seasons {seasons})\n'
    
    # Slot season_text (string)
    instance_str += f'    (season_text "{season_text}"))'
    
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
