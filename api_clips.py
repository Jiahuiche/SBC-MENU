import spoonacular
from spoonacular.models.get_random_recipes200_response import GetRandomRecipes200Response
from spoonacular.rest import ApiException
from pprint import pprint
import os
import json
#pip install git+https://github.com/ddsky/spoonacular-api-clients.git#subdirectory=python
def preprocess_ingredients_with_default_image(ingredients, default_image="no_image_available.png"):
    """
    Ensures each ingredient dictionary/object in the list has a non-empty 'image' attribute or key.
    If missing or empty, assigns default_image.

    Parameters:
        ingredients (list): List of ingredient objects or dicts (e.g., from recipe_data.extended_ingredients)
        default_image (str): Default image string to assign if 'image' is missing or empty.

    Returns:
        list: The processed list with ensured 'image' attributes.
    """
    for ingredient in ingredients:
        # Check if ingredient is an object with attributes
        if hasattr(ingredient, 'image'):
            if not getattr(ingredient, 'image'):
                setattr(ingredient, 'image', default_image)
        # Or if ingredient is a dict
        elif isinstance(ingredient, dict):
            if not ingredient.get('image'):
                ingredient['image'] = default_image
        else:
            # Ingredient type unknown, optionally handle or raise error
            pass  
    return ingredients

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
def format_ingredient_for_clips(ingredient):
    """Convert ingredient name to CLIPS-friendly symbol (no spaces, no quotes)"""
    return ingredient.replace(' ', '-').replace('"', '').replace("'", "")

def bool_to_symbol(value):
    """Convert boolean to CLIPS TRUE/FALSE"""
    return "TRUE" if value else "FALSE"

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
diets = None  # Puedes cambiar a 'vegan', 'pescetarian', etc.
intolerances = 'gluten,dairy'  # Puedes combinar múltiples intolerancias separándolas con comas
meal_type = "main"  #siempre poner 'main course', 'appetizer' o 'dessert'
num_recipes = 10

if meal_type ==  'main course': 
                    dish_class = 'Main'

elif meal_type == 'appetizer':
    dish_class = 'Starter'
else:
    dish_class = 'Dessert'

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
        # Obtener recetas aleatorias
        api_response = api_instance.get_random_recipes(
            include_nutrition=False, 
            include_tags=include_tags, 
            exclude_tags=None, 
            number=number
        )
        print("The response of RecipesApi->get_random_recipes:\n")
        pprint(api_response)

        # Crear una lista para almacenar las recetas filtradas
        filtered_recipes = []


        # Abrir el archivo CLIPS para escribir las instancias
        with open("recipes_clips.clp", "a") as f:
            for recipe_data in api_response.recipes:
                # Acceder a los atributos de RecipeInformation correctamente
                recipe_id = recipe_data.id if hasattr(recipe_data, 'id') else 'NoID'
                title = recipe_data.title if hasattr(recipe_data, 'title') else 'NoTitle'
                servings = recipe_data.servings if hasattr(recipe_data, 'servings') else 0
                price_per_serving = recipe_data.price_per_serving if hasattr(recipe_data, 'price_per_serving') else 0
                diets = ", ".join(recipe_data.diets) if hasattr(recipe_data, 'diets') else 'No diet'
                meal_types = ", ".join(recipe_data.dish_types) if hasattr(recipe_data, 'dish_types') else 'No dish type'

                

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

                # Convertir la lista de restricciones a formato CLIPS multislot
                if restrictions:
                    restrictions_clips = ' '.join([format_ingredient_for_clips(restriction) for restriction in restrictions])
                    restrictions_text = ", ".join(restrictions)
                else:
                    restrictions_clips = 'none'
                    restrictions_text = "No restrictions"


                # Comprobar si la imagen es None y asignar un valor predeterminado si es necesario
                image_url = recipe_data.image if hasattr(recipe_data, 'image') and recipe_data.image else "No image available"
                
                # Comprobar si el tipo de imagen es válido (al menos un carácter)
                image_type = recipe_data.image_type if hasattr(recipe_data, 'image_type') and recipe_data.image_type else "No image type available"

                if hasattr(recipe_data, 'image_type'):
                    if not recipe_data.image_type or recipe_data.image_type.strip() == "":
                        recipe_data.image_type = "unknown"  # or e.g. "jpg"
                    else:
                        # In case imageType attribute is missing, set default
                        setattr(recipe_data, 'image_type', "unknown")

                

                # Comprobar si el campo 'aisle' existe y asignar valor predeterminado si es necesario
                aisle = ""
                if hasattr(recipe_data, 'extended_ingredients'):
                    for ingredient in recipe_data.extended_ingredients:
                        aisle = ingredient.aisle if hasattr(ingredient, 'aisle') and ingredient.aisle else ""
                        ingredients = [ingredient.name for ingredient in recipe_data.extended_ingredients if hasattr(ingredient, 'name')]

                        if ingredients:
                            ingredients_clips = ' '.join([format_ingredient_for_clips(ingredient) for ingredient in ingredients])

                            # Simple seasonal classification
                            seasons, season_text = classify_by_season_simple(ingredients)
                            # Format seasons for CLIPS multislot
                            seasons_clips = ' '.join(seasons)
                            
                            is_kosher, is_halal = check_kosher_halal(ingredients)
                            
                        else:
                            ingredients_clips = 'No-ingredients'
                            is_kosher, is_halal = False, False
                            seasons, season_text = ['any-season'], "Any season"
                            seasons_clips = 'any-season'
                
                wine_pairing = ""
                if hasattr(recipe_data, 'wine_pairing') and recipe_data.wine_pairing and hasattr(recipe_data.wine_pairing, 'paired_wines'):
                    wine_pairing = ", ".join(recipe_data.wine_pairing.paired_wines)
                else:
                    # Only suggest wine for main courses
                    if dish_class == 'Main':
                        wine_pairing = suggest_wine_for_main(ingredients)
                    else:
                        wine_pairing = "No wine pairing"

                for ingredient in recipe_data.extended_ingredients:
                    image = ingredient.image if hasattr(ingredient, 'image') and ingredient.image else "no_image_available.png"

                if hasattr(recipe_data, 'extended_ingredients') and recipe_data.extended_ingredients:
                    recipe_data.extended_ingredients = preprocess_ingredients_with_default_image(recipe_data.extended_ingredients )

                for ingredient in recipe_data.extended_ingredients:
                    # Ensure aisle is a string, defaulting to empty string if None
                    if ingredient.aisle is None:
                        ingredient.aisle = ""
                

                if hasattr(recipe_data, "extended_ingredients") and recipe_data.extended_ingredients:
                    for ingredient in recipe_data.extended_ingredients:
                        if ingredient.aisle is None:
                            ingredient.aisle = ""  # o "unknown"

                

                # Escribir la instancia en formato CLIPS
                                
                f.write(f"(definstance Recipe_{recipe_id} of {dish_class}\n")
                f.write(f"  (title \"{title}\")\n")
                f.write(f"  (servings {servings})\n")
                f.write(f"  (price {price_per_serving/servings:.2f})\n")
                f.write(f"  (wine_pairing \"{wine_pairing}\")\n")
                f.write(f"  (restrictions {restrictions_clips})\n")
                f.write(f"  (restrictions_text \"{restrictions_text}\")\n")
                f.write(f"  (is_vegan {bool_to_symbol(vegan)})\n")
                f.write(f"  (is_gluten_free {bool_to_symbol(gluten_free)})\n")
                f.write(f"  (is_vegetarian {bool_to_symbol(vegetarian)})\n")
                f.write(f"  (is_dairy_free {bool_to_symbol(dairy_free)})\n")
                f.write(f"  (is_kosher {bool_to_symbol(is_kosher)})\n")
                f.write(f"  (is_halal {bool_to_symbol(is_halal)})\n")
                f.write(f"  (ingredients {ingredients_clips})\n")
                f.write(f"  (seasons {seasons_clips})\n")
                f.write(f"  (season_text \"{season_text}\"))\n\n")

                # Filtrar la receta para el archivo JSON
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

                # filtered_recipe = api_response.to_dict()
                # Añadir la receta filtrada a la lista
                filtered_recipes.append(filtered_recipe)

        # Guardar las recetas filtradas en un archivo JSON
        with open("filtered_recipes.json", "a") as json_file:
            json.dump(filtered_recipes, json_file, indent=4)
        
        print("Recetas exportadas a 'recipes_clips.clp' y 'filtered_recipes.json'")

    except Exception as e:
        print("Excepción al llamar a la API de Spoonacular: %s\n" % e)
