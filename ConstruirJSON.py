"""
API Script para obtener recetas de Spoonacular y exportarlas a JSON
- Obtiene recetas aleatorias según filtros (dietas, intolerancias, tipo de comida)
- Procesa ingredientes para clasificación estacional y verificación kosher/halal
- Genera un archivo JSON válido con todas las recetas (acumulativo)
"""
import spoonacular
from spoonacular.models.get_random_recipes200_response import GetRandomRecipes200Response
from spoonacular.rest import ApiException
from pprint import pprint
import os
import json

#pip install git+https://github.com/ddsky/spoonacular-api-clients.git#subdirectory=python
def is_kosher_ingredient(ingredient_name):
    """Check if an ingredient is kosher-friendly by checking each word"""
    non_kosher_words = {
        'pork', 'bacon', 'ham', 'lard', 'sausage','shellfish', 'shrimp', 'lobster', 'crab', 
        'clam', 'oyster', 'mussel', 'scallop', 'catfish', 'eel', 'shark',
        'gelatin', 'rennet', 'lard','ray', 'gelatin', 'rennet', 'vanilla extract', 'worcestershire sauce'
    }
    ingredient_lower = ingredient_name.lower()
    # Tokenize the ingredient name into individual words
    words = ingredient_lower.split()
    
    # Check if any word matches non-kosher ingredients
    for word in words:
        if word in non_kosher_words:
            return False

    for term in non_kosher_words:
        if term in ingredient_lower:
            return False
            
    return True
        

def is_halal_ingredient(ingredient_name):
    non_halal_words = {
        'pork', 'bacon', 'ham', 'alcohol', 'wine', 'beer', 'liquor', 'rum',
        'whiskey', 'vodka', 'gin', 'brandy', 'gelatin', 'rennet', 'lard'
    }
    
    ingredient_lower = ingredient_name.lower()
    
    # Check for exact word matches
    words = ingredient_lower.split()
    for word in words:
        if word in non_halal_words:
            return False
    
    # Check for partial matches
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
        # If both are already False, we can break early
        if not is_kosher and not is_halal:
            break
            
    return is_kosher, is_halal

def classify_by_season_simple(ingredients_list):
     
    # Key seasonal ingredients (one word matches)
    seasonal_ingredients = {
        'spring': {'asparagus', 'artichoke', 'rhubarb', 'pea', 'radish', 'spinach', 'fava bean'},
        'summer': {'berry', 'peach', 'watermelon', 'corn', 'fig', 'zucchini', 'nectarine'},
        'fall': {'pumpkin', 'squash', 'cranberry','brussel sprout', 'sweet potato', 'persimmon', 'chestnut'},
        'winter': {'citrus', 'pomegranate', 'kale', 'collard', 'leek', 'parsnip', 'turnip'}
    }
    
    found_seasons = set()
    
    for ingredient in ingredients_list:
        ingredient_lower = ingredient.lower()
        
        # Check each word in the ingredient name
        words = ingredient_lower.split()
        
        for word in words:
            for season, ingredients in seasonal_ingredients.items():
                if word in ingredients:
                    found_seasons.add(season)
    
    # Return results based on the three cases
    if len(found_seasons) == 1:
        # Only one season found
        season = list(found_seasons)[0]
        return [season], season.capitalize()
    
    else:
        # No seasonal ingredients found
        return ['any-season'], "Any season"


def suggest_wine_for_main(ingredients_list):
    """Simple wine pairing for main courses based on key ingredients"""
    
    ingredients_lower = ' '.join(ingredients_list).lower()
    
    # Simple ingredient-based wine pairing
    if any(meat in ingredients_lower for meat in ['beef', 'steak', 'lamb', 'pork']):
        return "Red wine"
    elif any(poultry in ingredients_lower for poultry in ['chicken', 'turkey', 'duck']):
        return "White wine or light Red wine"
    elif any(fish in ingredients_lower for fish in ['fish', 'salmon', 'tuna', 'cod']):
        return "White wine"
    elif any(seafood in ingredients_lower for seafood in ['shrimp', 'lobster', 'crab', 'scallop']):
        return "White wine"
    elif any(pasta in ingredients_lower for pasta in ['pasta', 'spaghetti', 'noodle']):
        return "Red wine or White wine"
    elif any(vegetarian in ingredients_lower for vegetarian in ['tofu', 'bean', 'lentil', 'vegetable']):
        return "Light Red wine or White wine"
    else:
        return " No wine pairing"


STARTER_TERMS = {
    'starter', 'appetizer', 'antipasti', 'antipasto', 'snack', 'fingerfood',
    'side dish', 'side-dish', 'salad', 'soup', 'breakfast', 'brunch', 'morning meal'
}
MAIN_TERMS = {
    'main course', 'main-course', 'main dish', 'main-dish', 'main', 'dinner', 'lunch'
}
DESSERT_TERMS = {'dessert', 'treat'}
DISH_CLASS_BY_FILTER = {
    'main course': 'Main',
    'main': 'Main',
    'appetizer': 'Starter',
    'side dish': 'Starter',
    'dessert': 'Dessert'
}


def determine_dish_class(meal_type_filter, dish_types):
    """Resolve recipe dish class using API dish types and requested meal type."""
    base_class = DISH_CLASS_BY_FILTER.get(meal_type_filter, 'Mixed')
    if not dish_types:
        return base_class

    normalized = {term.strip().lower() for term in dish_types if term}

    if normalized & DESSERT_TERMS:
        return 'Dessert'
    if normalized & MAIN_TERMS:
        return 'Main'
    if normalized & STARTER_TERMS:
        return 'Starter'

    return base_class

# Definir las intolerancias posibles
all_intolerances = [
    "dairy", "egg", "gluten", "grain", "peanut", "seafood", 
    "sesame", "shellfish", "soy", "sulfite", "tree nut", "wheat"
]

# Configuración de la API
configuration = spoonacular.Configuration(
    host="https://api.spoonacular.com"
)
configuration.api_key['apiKeyScheme'] = os.environ["API_KEY"]

# Definir filtros de búsqueda
diets = 'vegan'  # Puedes cambiar a 'vegan', 'pescetarian', etc.
intolerances = None  # Pon None para no filtrar por intolerancias
meal_type = 'main course'  # Pon uno de estos main course, appetizer o side dish, dessert (para que salga wine pairing)
num_recipes = 500

tags = []
if diets:
    tags.append(diets)
if intolerances:
    tags.append(intolerances)
if meal_type:
    tags.append(meal_type)

# Obtener las recetas de la API
with spoonacular.ApiClient(configuration) as api_client:
    api_instance = spoonacular.RecipesApi(api_client)
    include_nutrition = False
    include_tags = ",".join(tags) if tags else None
    # exclude_tags = 'drink,sauce,beverage,breakfast,bread,marinade'
    number = num_recipes

    try:
        # Obtener recetas aleatorias - Usar _preload_content=False para obtener datos crudos
        import urllib3
        http = urllib3.PoolManager()
        
        # Construir URL manualmente
        base_url = "https://api.spoonacular.com/recipes/random"
        params = {
            'apiKey': configuration.api_key['apiKeyScheme'],
            'number': number,
            'tags': include_tags if include_tags else '',
            
        }
        
        # Hacer petición HTTP directa
        from urllib.parse import urlencode
        url = f"{base_url}?{urlencode(params)}"
        response = http.request('GET', url)
        
        # Parsear JSON crudo
        import json as json_module
        raw_data = json_module.loads(response.data.decode('utf-8'))
        
        # Preprocesar datos ANTES de pasarlos a Pydantic
        if 'recipes' in raw_data:
            for recipe in raw_data['recipes']:
                # Validar imageType
                if 'imageType' not in recipe or not recipe['imageType'] or recipe['imageType'].strip() == '':
                    recipe['imageType'] = 'jpg'
                
                # Validar campos de ingredientes
                if 'extendedIngredients' in recipe and recipe['extendedIngredients']:
                    for ingredient in recipe['extendedIngredients']:
                        # Validar image
                        if 'image' not in ingredient or ingredient['image'] is None or ingredient['image'] == '':
                            ingredient['image'] = 'no_image_available.png'
                        
                        # Validar aisle
                        if 'aisle' not in ingredient or ingredient['aisle'] is None:
                            ingredient['aisle'] = 'Unknown'
                        
                        # Validar originalName
                        if 'originalName' not in ingredient or ingredient['originalName'] is None or ingredient['originalName'] == '':
                            ingredient['originalName'] = 'Unknown ingredient'
        
        # Ahora convertir a objetos Pydantic
        from spoonacular.models.get_random_recipes200_response import GetRandomRecipes200Response
        api_response = GetRandomRecipes200Response.from_dict(raw_data)
        
        print("The response of RecipesApi->get_random_recipes:\n")
        pprint(api_response)

        # Cargar recetas existentes si el archivo existe
        try:
            with open("filtered_recipes111.json", "r", encoding='utf-8') as json_file:
                filtered_recipes = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            filtered_recipes = []

        # Procesar cada receta de la API
        for recipe_data in api_response.recipes:
                # Acceder a los atributos de RecipeInformation correctamente
                recipe_id = recipe_data.id if hasattr(recipe_data, 'id') else 'NoID'
                title = recipe_data.title if hasattr(recipe_data, 'title') else 'NoTitle'
                servings = recipe_data.servings if hasattr(recipe_data, 'servings') else 0
                price_per_serving = recipe_data.price_per_serving if hasattr(recipe_data, 'price_per_serving') else 0
                diets = ", ".join(recipe_data.diets) if hasattr(recipe_data, 'diets') else 'No diet'
                raw_dish_types = []
                if hasattr(recipe_data, 'dish_types') and recipe_data.dish_types:
                    raw_dish_types = [dt for dt in recipe_data.dish_types if dt]

                meal_types = ", ".join(raw_dish_types) if raw_dish_types else 'No dish type'
                dish_class = determine_dish_class(meal_type, raw_dish_types)
                            

                # wine_pairing = ", ".join(recipe_data.wine_pairing) if hasattr(recipe_data, 'wine_pairing') else 'No wine pairing'
                vegan = recipe_data.vegan if hasattr(recipe_data, 'vegan') else 'False'
                gluten_free = recipe_data.gluten_free if hasattr(recipe_data, 'gluten_free') else 'False'
                vegetarian = recipe_data.vegetarian if hasattr(recipe_data, 'vegetarian') else 'False'
                dairy_free = recipe_data.dairy_free if hasattr(recipe_data, 'dairy_free') else 'False'

                # Crear lista de intolerancias que estén presentes
                restrictions = []
                if vegan:
                    restrictions.append("vegan")
                    
                if gluten_free:
                    restrictions.append("gluten free")
                if vegetarian:
                    restrictions.append("vegetarian")
                if dairy_free:
                    restrictions.append("dairy free")





                # Extraer ingredientes
                ingredients = []
                if hasattr(recipe_data, 'extended_ingredients') and recipe_data.extended_ingredients:
                    ingredients = [ingredient.name for ingredient in recipe_data.extended_ingredients if hasattr(ingredient, 'name')]
                
                # Clasificación estacional y verificación kosher/halal
                if ingredients:
                    seasons, season_text = classify_by_season_simple(ingredients)
                    is_kosher, is_halal = check_kosher_halal(ingredients)
                else:
                    seasons, season_text = ['any-season'], "Any season"
                    is_kosher, is_halal = False, False
                
                # Obtener wine pairing
                wine_pairing = ""
                if hasattr(recipe_data, 'wine_pairing') and recipe_data.wine_pairing and hasattr(recipe_data.wine_pairing, 'paired_wines') and recipe_data.wine_pairing.paired_wines:
                    wine_pairing = ", ".join(str(w) for w in recipe_data.wine_pairing.paired_wines)
                elif dish_class == 'Main' and ingredients:
                    wine_pairing = suggest_wine_for_main(ingredients)
                else:
                    wine_pairing = "No wine pairing"

                # Crear objeto de receta para el archivo JSON
                filtered_recipe = {
                    "id": recipe_id,
                    "title": title,
                    "servings": servings,
                    "pricePerServing": price_per_serving,
                    "priceCalculated": price_per_serving/servings,
                    "dishClass": dish_class,  # Add dish class
                    "mealTypes": meal_types,
                    "winePairing": wine_pairing,
                    "vegan": vegan,
                    "glutenFree": gluten_free,
                    "vegetarian": vegetarian,
                    "dairyFree": dairy_free,
                    "isKosher": is_kosher,
                    "isHalal": is_halal,
                    "restrictions": restrictions,
                    "ingredients": ingredients,
                    "seasons": seasons,
                    "seasonText": season_text
                }

                # Añadir la receta al array
                filtered_recipes.append(filtered_recipe)

        # Guardar TODAS las recetas en un ÚNICO array JSON válido
        with open("filtered_recipes111.json", "w", encoding='utf-8') as json_file:
            json.dump(filtered_recipes, json_file, indent=4, ensure_ascii=False)
        
        print(f"\n{'='*60}")
        print(f"✅ ÉXITO - Recetas exportadas a 'filtered_recipes111.json'")
        print(f"{'='*60}")
        print(f"📊 Total acumulado: {len(filtered_recipes)} recetas")

        print(f"{'='*60}\n")

    except Exception as e:
        print(f"\n❌ Error al llamar a la API de Spoonacular:")
        print(f"   {str(e)}\n")
