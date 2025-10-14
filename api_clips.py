import spoonacular
from spoonacular.models.get_random_recipes200_response import GetRandomRecipes200Response
from spoonacular.rest import ApiException
from pprint import pprint
import os
import json
#pip install git+https://github.com/ddsky/spoonacular-api-clients/tree/master/python/.git
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
diets = None 
intolerances = None  
meal_type = "main dish"  
num_recipes = 3 # Por ejemplo, obtener 5 recetas

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

                wine_pairing = ""
                if hasattr(recipe_data, 'wine_pairing') and recipe_data.wine_pairing and hasattr(recipe_data.wine_pairing, 'paired_wines'):
                    wine_pairing = ", ".join(recipe_data.wine_pairing.paired_wines)
                else:
                    wine_pairing = 'No wine pairing'

                # wine_pairing = ", ".join(recipe_data.wine_pairing) if hasattr(recipe_data, 'wine_pairing') else 'No wine pairing'
                vegan = recipe_data.vegan if hasattr(recipe_data, 'vegan') else 'False'
                gluten_free = recipe_data.gluten_free if hasattr(recipe_data, 'gluten_free') else 'False'
                vegetarian = recipe_data.vegetarian if hasattr(recipe_data, 'vegetarian') else 'False'
                dairy_free = recipe_data.dairy_free if hasattr(recipe_data, 'dairy_free') else 'False'

                # Crear lista de intolerancias que estén presentes
                restrictions = []
                for intolerance in all_intolerances:
                    # Verificar si la intolerancia está presente y es True
                    intolerance_value = getattr(recipe_data, intolerance.lower(), False)
                    if intolerance_value:
                        restrictions.append(intolerance)

                # Convertir la lista de restricciones a una cadena
                restrictions_str = ", ".join(restrictions) if restrictions else "No restrictions"

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
                f.write(f"\n(definstance Recipe_{recipe_id} \n " 
                        f"(title \"{title}\") \n"                        
                        f"(diets \"{diets}\") \n "
                        f"(meal_types \"{meal_types}\") \n"
                        f"(wine_pairing \"{wine_pairing}\") "
                        f"(is_vegan {(vegan)}) "
                        f"(is_gluten_free {str(gluten_free)}) "
                        f"(is_vegetarian {str(vegetarian)}) \n"
                        f"(is_dairy_free {str(dairy_free)}) \n"
                        f"(restrictions \"{restrictions_str}\") "
                        f")\n")

                # Filtrar la receta para el archivo JSON
                filtered_recipe = {
                    "id": recipe_id,
                    "title": title,
                    "servings": servings,
                    "pricePerServing": price_per_serving,
                    "diets": recipe_data.diets if hasattr(recipe_data, 'diets') else [],
                    "mealTypes": recipe_data.dish_types if hasattr(recipe_data, 'dish_types') else [],
                    "winePairing": wine_pairing,
                    "vegan": vegan,
                    "glutenFree": gluten_free,
                    "vegetarian": vegetarian,
                    "dairyFree": dairy_free,
                    "restrictions": restrictions
                }

                # Añadir la receta filtrada a la lista
                filtered_recipes.append(filtered_recipe)

        # Guardar las recetas filtradas en un archivo JSON
        with open("filtered_recipes.json", "a") as json_file:
            json.dump(filtered_recipes, json_file, indent=4)
        
        print("Recetas exportadas a 'recipes_clips.clp' y 'filtered_recipes.json'")

    except Exception as e:
        print("Excepción al llamar a la API de Spoonacular: %s\n" % e)
