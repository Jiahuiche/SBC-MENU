"""
API Script OPTIMIZADO para obtener recetas de Spoonacular
- Estructura de datos optimizada para Clustering y CBR
- Extrae solo campos relevantes para análisis de similitud
- Calcula features derivadas automáticamente
- Genera JSON organizado por categorías de features
"""
import spoonacular
from spoonacular.models.get_random_recipes200_response import GetRandomRecipes200Response
from spoonacular.rest import ApiException
from pprint import pprint
import os
import json
import math

#pip install git+https://github.com/ddsky/spoonacular-api-clients.git#subdirectory=python

# ============================================================================
# FUNCIONES DE VERIFICACIÓN KOSHER/HALAL
# ============================================================================

def is_kosher_ingredient(ingredient_name):
    """Check if an ingredient is kosher-friendly"""
    non_kosher_words = {
        'pork', 'bacon', 'ham', 'lard', 'sausage','shellfish', 'shrimp', 'lobster', 'crab', 
        'clam', 'oyster', 'mussel', 'scallop', 'catfish', 'eel', 'shark',
        'gelatin', 'rennet', 'vanilla extract', 'worcestershire sauce'
    }
    ingredient_lower = ingredient_name.lower()
    words = ingredient_lower.split()
    
    for word in words:
        if word in non_kosher_words:
            return False
    for term in non_kosher_words:
        if term in ingredient_lower:
            return False
    return True

def is_halal_ingredient(ingredient_name):
    """Check if an ingredient is halal-friendly"""
    non_halal_words = {
        'pork', 'bacon', 'ham', 'alcohol', 'wine', 'beer', 'liquor', 'rum',
        'whiskey', 'vodka', 'gin', 'brandy', 'gelatin', 'rennet', 'lard'
    }
    ingredient_lower = ingredient_name.lower()
    words = ingredient_lower.split()
    
    for word in words:
        if word in non_halal_words:
            return False
    for term in non_halal_words:
        if term in ingredient_lower:
            return False
    return True

def check_kosher_halal(ingredients_list):
    """Check if recipe is kosher and halal based on ingredients"""
    is_kosher = True
    is_halal = True
    
    for ingredient_name in ingredients_list:
        if not is_kosher_ingredient(ingredient_name):
            is_kosher = False
        if not is_halal_ingredient(ingredient_name):
            is_halal = False
        if not is_kosher and not is_halal:
            break
    return is_kosher, is_halal

# ============================================================================
# CLASIFICACIÓN ESTACIONAL
# ============================================================================

def classify_by_season(ingredients_list):
    """Classify recipe by season based on key ingredients"""
    seasonal_ingredients = {
        'spring': {'asparagus', 'artichoke', 'rhubarb', 'pea', 'radish', 'spinach', 'fava bean'},
        'summer': {'berry', 'peach', 'watermelon', 'corn', 'fig', 'zucchini', 'nectarine'},
        'autumn': {'pumpkin', 'squash', 'cranberry','brussel sprout', 'sweet potato', 'persimmon', 'chestnut'},
        'winter': {'citrus', 'pomegranate', 'kale', 'collard', 'leek', 'parsnip', 'turnip'}
    }
    
    found_seasons = set()
    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower()
        words = ingredient_lower.split()
        for word in words:
            for season, ingredients in seasonal_ingredients.items():
                if word in ingredients:
                    found_seasons.add(season)
    
    if len(found_seasons) == 1:
        return list(found_seasons)[0]
    else:
        return 'any-season'

# ============================================================================
# MARIDAJE DE VINO INTELIGENTE
# ============================================================================

def suggest_wine_pairing(ingredients_list, dish_types):
    """Intelligent wine pairing based on ingredients and dish type"""
    ingredients_lower = ' '.join(ingredients_list).lower()
    dish_types_lower = ' '.join(dish_types).lower() if dish_types else ''
    
    # Scoring system
    scores = {
        'red': 0,
        'white': 0,
        'rose': 0,
        'sparkling': 0,
        'dessert': 0,
        'aromatic_white': 0
    }
    
    # Red wine indicators
    if any(meat in ingredients_lower for meat in ['beef', 'steak', 'lamb', 'pork', 'duck', 'venison']):
        scores['red'] += 3
    if any(ing in ingredients_lower for ing in ['mushroom', 'tomato', 'bbq', 'bacon']):
        scores['red'] += 1
    
    # White wine indicators
    if any(poultry in ingredients_lower for poultry in ['chicken', 'turkey']):
        scores['white'] += 2
    if any(fish in ingredients_lower for fish in ['cod', 'halibut', 'sole', 'tilapia', 'bass']):
        scores['white'] += 3
    if any(seafood in ingredients_lower for seafood in ['shrimp', 'lobster', 'crab', 'scallop']):
        scores['white'] += 3
    if any(ing in ingredients_lower for ing in ['lemon', 'garlic', 'butter', 'herb']):
        scores['white'] += 1
    
    # Rosé indicators
    if any(ing in ingredients_lower for ing in ['salmon', 'tuna', 'prosciutto', 'berry']):
        scores['rose'] += 2
    
    # Sparkling indicators
    if any(ing in ingredients_lower for ing in ['fried', 'cheese', 'brie', 'creamy']):
        scores['sparkling'] += 1
    if any(dt in dish_types_lower for dt in ['appetizer', 'starter', 'brunch']):
        scores['sparkling'] += 2
    
    # Dessert wine indicators
    if any(ing in ingredients_lower for ing in ['chocolate', 'caramel', 'honey', 'maple']):
        scores['dessert'] += 3
    if any(dt in dish_types_lower for dt in ['dessert', 'treat']):
        scores['dessert'] += 5
    
    # Aromatic white indicators (Asian/spicy cuisine)
    if any(ing in ingredients_lower for ing in ['curry', 'chili', 'ginger', 'lemongrass', 'coconut']):
        scores['aromatic_white'] += 3
    
    # Select best match
    wine_map = {
        'red': 'Red wine',
        'white': 'White wine',
        'rose': 'Rosé wine',
        'sparkling': 'Sparkling wine',
        'dessert': 'Dessert wine',
        'aromatic_white': 'Aromatic white wine'
    }
    
    best_wine = max(scores, key=scores.get)
    if scores[best_wine] > 0:
        return wine_map[best_wine]
    return 'No wine pairing'

# ============================================================================
# CLASIFICACIÓN DE TIPO DE PLATO
# ============================================================================

STARTER_TERMS = {
    'starter', 'appetizer', 'antipasti', 'antipasto', 'snack', 'fingerfood',
    'side dish', 'side-dish', 'salad', 'soup', 'breakfast', 'brunch', 'morning meal'
}
MAIN_TERMS = {
    'main course', 'main-course', 'main dish', 'main-dish', 'main', 'dinner', 'lunch'
}
DESSERT_TERMS = {'dessert', 'treat'}

def determine_dish_class(dish_types):
    """Determine if recipe is Starter, Main, or Dessert"""
    if not dish_types:
        return 'Mixed'
    
    normalized = {term.strip().lower() for term in dish_types if term}
    
    if normalized & DESSERT_TERMS:
        return 'Dessert'
    if normalized & MAIN_TERMS:
        return 'Main'
    if normalized & STARTER_TERMS:
        return 'Starter'
    
    return 'Mixed'

# ============================================================================
# FEATURES DERIVADAS
# ============================================================================

def calculate_complexity_score(num_ingredients, ready_minutes):
    """Calculate complexity score based on ingredients and time"""
    if num_ingredients == 0 and ready_minutes == 0:
        return 5.0
    ingredient_factor = min(num_ingredients / 2, 10)  # Max 10 points
    time_factor = min(ready_minutes / 6, 10)          # Max 10 points
    return round((ingredient_factor + time_factor) / 2, 1)

def calculate_value_score(spoonacular_score, price_per_serving):
    """Calculate value = quality/price ratio"""
    if price_per_serving == 0:
        return 0.0
    return round(spoonacular_score / price_per_serving, 2)

def calculate_nutrient_density(health_score, calories):
    """Calculate nutrient density = health/calories"""
    if calories == 0:
        return 0.0
    return round(health_score / calories, 3)

def categorize_price(price_per_serving):
    """Categorize price into budget/mid/premium"""
    if price_per_serving < 15:
        return 'budget'
    elif price_per_serving < 40:
        return 'mid'
    else:
        return 'premium'

# ============================================================================
# EXTRACCIÓN Y CONSTRUCCIÓN DE ESTRUCTURA OPTIMIZADA
# ============================================================================

def build_optimized_recipe(recipe_data):
    """
    Construye estructura optimizada para clustering y CBR
    Solo incluye campos relevantes organizados por categoría
    """
    
    # ===== EXTRACCIÓN DE DATOS BÁSICOS =====
    recipe_id = recipe_data.id if hasattr(recipe_data, 'id') else 0
    title = recipe_data.title if hasattr(recipe_data, 'title') else 'Unknown'
    
    # ===== FEATURES NUMÉRICAS =====
    servings = recipe_data.servings if hasattr(recipe_data, 'servings') else 1
    price_per_serving_raw = recipe_data.price_per_serving if hasattr(recipe_data, 'price_per_serving') else 0
    price_per_serving = round(price_per_serving_raw / 100, 2)  # Convertir centavos a euros
    
    ready_in_minutes = recipe_data.ready_in_minutes if hasattr(recipe_data, 'ready_in_minutes') else 0
    health_score = recipe_data.health_score if hasattr(recipe_data, 'health_score') else 50
    spoonacular_score = recipe_data.spoonacular_score if hasattr(recipe_data, 'spoonacular_score') else 50.0
    
    # Calorías (de nutrition si está disponible)
    calories = 0
    if hasattr(recipe_data, 'nutrition') and recipe_data.nutrition:
        if hasattr(recipe_data.nutrition, 'nutrients'):
            for nutrient in recipe_data.nutrition.nutrients:
                if hasattr(nutrient, 'name') and nutrient.name.lower() == 'calories':
                    calories = int(nutrient.amount) if hasattr(nutrient, 'amount') else 0
                    break
    
    # ===== FEATURES CATEGÓRICAS =====
    vegan = recipe_data.vegan if hasattr(recipe_data, 'vegan') else False
    vegetarian = recipe_data.vegetarian if hasattr(recipe_data, 'vegetarian') else False
    gluten_free = recipe_data.gluten_free if hasattr(recipe_data, 'gluten_free') else False
    dairy_free = recipe_data.dairy_free if hasattr(recipe_data, 'dairy_free') else False
    very_healthy = recipe_data.very_healthy if hasattr(recipe_data, 'very_healthy') else False
    cheap = recipe_data.cheap if hasattr(recipe_data, 'cheap') else False
    
    # ===== FEATURES DE TEXTO =====
    cuisines = recipe_data.cuisines if hasattr(recipe_data, 'cuisines') and recipe_data.cuisines else []
    diets = recipe_data.diets if hasattr(recipe_data, 'diets') and recipe_data.diets else []
    dish_types = recipe_data.dish_types if hasattr(recipe_data, 'dish_types') and recipe_data.dish_types else []
    occasions = recipe_data.occasions if hasattr(recipe_data, 'occasions') and recipe_data.occasions else []
    
    # Clasificación de plato
    dish_class = determine_dish_class(dish_types)
    
    # Ingredientes
    ingredients = []
    if hasattr(recipe_data, 'extended_ingredients') and recipe_data.extended_ingredients:
        ingredients = [ing.name for ing in recipe_data.extended_ingredients if hasattr(ing, 'name')]
    
    # Temporada
    season = classify_by_season(ingredients) if ingredients else 'any-season'
    
    # ===== PERFIL DE SABOR =====
    taste_profile = None
    if hasattr(recipe_data, 'taste') and recipe_data.taste:
        taste_profile = {
            'sweetness': getattr(recipe_data.taste, 'sweetness', 0),
            'saltiness': getattr(recipe_data.taste, 'saltiness', 0),
            'sourness': getattr(recipe_data.taste, 'sourness', 0),
            'bitterness': getattr(recipe_data.taste, 'bitterness', 0),
            'savoriness': getattr(recipe_data.taste, 'savoriness', 0)
        }
    
    # ===== MARIDAJE DE VINO =====
    wine_pairing = "No wine pairing"
    if hasattr(recipe_data, 'wine_pairing') and recipe_data.wine_pairing:
        if hasattr(recipe_data.wine_pairing, 'paired_wines') and recipe_data.wine_pairing.paired_wines:
            wine_pairing = ", ".join(str(w) for w in recipe_data.wine_pairing.paired_wines)
    
    # Si no hay wine pairing de la API, sugerir uno
    if wine_pairing == "No wine pairing" or not wine_pairing:
        wine_pairing = suggest_wine_pairing(ingredients, dish_types)
    
    # ===== VERIFICACIÓN KOSHER/HALAL =====
    is_kosher, is_halal = check_kosher_halal(ingredients) if ingredients else (False, False)
    
    # ===== FEATURES DERIVADAS =====
    complexity_score = calculate_complexity_score(len(ingredients), ready_in_minutes)
    value_score = calculate_value_score(spoonacular_score, price_per_serving)
    nutrient_density = calculate_nutrient_density(health_score, calories) if calories > 0 else 0
    restriction_count = sum([vegan, vegetarian, gluten_free, dairy_free])
    key_ingredients = ingredients[:5] if len(ingredients) >= 5 else ingredients
    price_category = categorize_price(price_per_serving)
    
    # ===== METADATA =====
    aggregate_likes = recipe_data.aggregate_likes if hasattr(recipe_data, 'aggregate_likes') else 0
    
    # ===== CONSTRUIR ESTRUCTURA OPTIMIZADA =====
    optimized_recipe = {
        "id": recipe_id,
        "title": title,
        
        "features_numeric": {
            "price_per_serving": price_per_serving,
            "ready_in_minutes": ready_in_minutes,
            "servings": servings,
            "health_score": health_score,
            "spoonacular_score": spoonacular_score,
            "calories": calories
        },
        
        "features_categorical": {
            "vegan": vegan,
            "vegetarian": vegetarian,
            "gluten_free": gluten_free,
            "dairy_free": dairy_free,
            "very_healthy": very_healthy,
            "cheap": cheap,
            "dish_class": dish_class,
            "season": season
        },
        
        "features_text": {
            "cuisines": cuisines,
            "diets": diets,
            "dish_types": dish_types,
            "occasions": occasions,
            "ingredients": ingredients
        },
        
        "taste_profile": taste_profile,
        
        "derived_features": {
            "complexity_score": complexity_score,
            "value_score": value_score,
            "nutrient_density": nutrient_density,
            "restriction_count": restriction_count,
            "key_ingredients": key_ingredients,
            "price_category": price_category
        },
        
        "metadata": {
            "wine_pairing": wine_pairing,
            "aggregate_likes": aggregate_likes,
            "kosher": is_kosher,
            "halal": is_halal
        }
    }
    
    return optimized_recipe

# ============================================================================
# CONFIGURACIÓN Y EJECUCIÓN
# ============================================================================

if __name__ == "__main__":
    # Configuración de la API
    configuration = spoonacular.Configuration(
        host="https://api.spoonacular.com"
    )
    configuration.api_key['apiKeyScheme'] = os.environ.get("API_KEY")
    
    if not configuration.api_key['apiKeyScheme']:
        print("❌ Error: No se encontró API_KEY en variables de entorno")
        exit(1)
    
    # Parámetros de búsqueda
    diets = None          # 'vegan', 'vegetarian', 'pescetarian', etc.
    intolerances = None   # 'dairy', 'gluten', etc.
    meal_type = 'main course'  # 'main course', 'dessert', 'appetizer', 'side dish'
    num_recipes = 100
    
    tags = []
    if diets:
        tags.append(diets)
    if intolerances:
        tags.append(intolerances)
    if meal_type:
        tags.append(meal_type)
    
    print(f"\n{'='*70}")
    print(f"🔍 OBTENIENDO RECETAS DE SPOONACULAR (Estructura Optimizada)")
    print(f"{'='*70}")
    print(f"📋 Filtros:")
    print(f"   - Dietas: {diets if diets else 'Todas'}")
    print(f"   - Intolerancias: {intolerances if intolerances else 'Ninguna'}")
    print(f"   - Tipo de comida: {meal_type if meal_type else 'Todos'}")
    print(f"   - Número de recetas: {num_recipes}")
    print(f"{'='*70}\n")
    
    # Obtener recetas de la API
    with spoonacular.ApiClient(configuration) as api_client:
        api_instance = spoonacular.RecipesApi(api_client)
        include_tags = ",".join(tags) if tags else None
        
        try:
            import urllib3
            from urllib.parse import urlencode
            
            http = urllib3.PoolManager()
            base_url = "https://api.spoonacular.com/recipes/random"
            params = {
                'apiKey': configuration.api_key['apiKeyScheme'],
                'number': num_recipes,
                'tags': include_tags if include_tags else '',
                'addRecipeInformation': True,  # Para obtener más datos
                'fillIngredients': True        # Para ingredientes completos
            }
            
            url = f"{base_url}?{urlencode(params)}"
            response = http.request('GET', url)
            raw_data = json.loads(response.data.decode('utf-8'))
            
            # Validación de datos crudos
            if 'recipes' in raw_data:
                for recipe in raw_data['recipes']:
                    if 'imageType' not in recipe or not recipe['imageType']:
                        recipe['imageType'] = 'jpg'
                    
                    if 'extendedIngredients' in recipe and recipe['extendedIngredients']:
                        for ingredient in recipe['extendedIngredients']:
                            if 'image' not in ingredient or not ingredient['image']:
                                ingredient['image'] = 'no_image_available.png'
                            if 'aisle' not in ingredient or not ingredient['aisle']:
                                ingredient['aisle'] = 'Unknown'
                            if 'originalName' not in ingredient or not ingredient['originalName']:
                                ingredient['originalName'] = 'Unknown ingredient'
            
            # Convertir a objetos Pydantic
            api_response = GetRandomRecipes200Response.from_dict(raw_data)
            
            print(f"✅ Recibidas {len(api_response.recipes)} recetas de la API\n")
            
            # Cargar recetas existentes
            output_file = "recipes_optimized.json"
            try:
                with open(output_file, "r", encoding='utf-8') as f:
                    all_recipes = json.load(f)
                print(f"📂 Cargadas {len(all_recipes)} recetas existentes de {output_file}")
            except (FileNotFoundError, json.JSONDecodeError):
                all_recipes = []
                print(f"📂 Creando nuevo archivo {output_file}")
            
            # Procesar cada receta
            print(f"\n🔄 Procesando recetas con estructura optimizada...\n")
            new_count = 0
            
            for recipe_data in api_response.recipes:
                optimized = build_optimized_recipe(recipe_data)
                
                # Evitar duplicados por ID
                existing_ids = [r['id'] for r in all_recipes]
                if optimized['id'] not in existing_ids:
                    all_recipes.append(optimized)
                    new_count += 1
                    print(f"   ✓ {optimized['title']} (ID: {optimized['id']})")
            
            # Guardar todas las recetas
            with open(output_file, "w", encoding='utf-8') as f:
                json.dump(all_recipes, json_file=f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*70}")
            print(f"✅ COMPLETADO EXITOSAMENTE")
            print(f"{'='*70}")
            print(f"📊 Estadísticas:")
            print(f"   - Recetas nuevas añadidas: {new_count}")
            print(f"   - Total acumulado: {len(all_recipes)}")
            print(f"   - Archivo de salida: {output_file}")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"\n❌ Error al procesar recetas:")
            print(f"   {str(e)}\n")
            import traceback
            traceback.print_exc()
