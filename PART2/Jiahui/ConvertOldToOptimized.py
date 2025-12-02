"""
Conversor de formato antiguo a formato optimizado
- Lee filtered_recipes111.json (formato antiguo de ConstruirJSON.py)
- Convierte a recipes_optimized.json (formato optimizado para clustering)
- Calcula features derivadas
"""
import json
import os
from ExpandDatabase_Optimized import (
    is_kosher_ingredient, is_halal_ingredient, check_kosher_halal,
    classify_by_season, suggest_wine_pairing, determine_dish_class,
    calculate_complexity_score, calculate_value_score, 
    calculate_nutrient_density, categorize_price
)

def convert_old_to_optimized(input_file=None, output_file='recipes_optimized.json'):
    """Convierte formato antiguo a formato optimizado"""
    
    print(f"\n{'='*70}")
    print(f"🔄 CONVIRTIENDO FORMATO ANTIGUO A OPTIMIZADO")
    print(f"{'='*70}\n")
    
    # Si no se proporciona input_file, buscar en ubicaciones conocidas
    if input_file is None:
        # Obtener el directorio del script actual
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Rutas posibles relativas al script
        possible_paths = [
            os.path.join(script_dir, '..', 'PART1', 'filtered_recipes111.json'),  # ../PART1/
            os.path.join(script_dir, '..', 'filtered_recipes111.json'),           # ../
            os.path.join(script_dir, 'filtered_recipes111.json'),                 # ./
            r'C:\AI5\SBC\SBC-MENU\PART1\filtered_recipes111.json'                # Ruta absoluta
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                input_file = path
                print(f"✅ Archivo encontrado en: {input_file}\n")
                break
        
        if input_file is None:
            print(f"❌ Error: No se pudo encontrar filtered_recipes111.json")
            print(f"   Rutas buscadas:")
            for path in possible_paths:
                print(f"      - {path}")
            return False
    
    # Verificar que existe el archivo de entrada
    if not os.path.exists(input_file):
        print(f"❌ Error: No se encuentra {input_file}")
        print(f"   Por favor, verifica la ruta del archivo.")
        return False
    
    # Cargar recetas antiguas
    print(f"📂 Cargando {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        old_recipes = json.load(f)
    
    print(f"✅ Cargadas {len(old_recipes)} recetas\n")
    
    # Convertir cada receta
    optimized_recipes = []
    
    for idx, old_recipe in enumerate(old_recipes, 1):
        try:
            # ===== EXTRACCIÓN DE DATOS BÁSICOS =====
            recipe_id = old_recipe.get('id', 0)
            title = old_recipe.get('title', 'Unknown')
            
            # Ingredientes
            ingredients_raw = old_recipe.get('ingredients', [])
            if isinstance(ingredients_raw, str):
                ingredients = [ing.strip() for ing in ingredients_raw.split(',')]
            else:
                ingredients = ingredients_raw
            
            # Dish types
            dish_types_raw = old_recipe.get('dishTypes', [])
            if isinstance(dish_types_raw, str):
                dish_types = [dt.strip() for dt in dish_types_raw.split(',')]
            else:
                dish_types = dish_types_raw
            
            # Cuisines
            cuisines_raw = old_recipe.get('cuisines', [])
            if isinstance(cuisines_raw, str):
                cuisines = [c.strip() for c in cuisines_raw.split(',')]
            else:
                cuisines = cuisines_raw
            
            # Diets
            diets_raw = old_recipe.get('diets', [])
            if isinstance(diets_raw, str):
                diets = [d.strip() for d in diets_raw.split(',')]
            else:
                diets = diets_raw
            
            # ===== FEATURES NUMÉRICAS =====
            price_per_serving = old_recipe.get('pricePerServing', 0)
            ready_in_minutes = old_recipe.get('readyInMinutes', 0)
            servings = old_recipe.get('servings', 1)
            health_score = old_recipe.get('healthScore', 0)
            spoonacular_score = old_recipe.get('spoonacularScore', 0)
            
            # Calorías (aproximado si no existe)
            calories = old_recipe.get('calories', 500)
            
            # ===== FEATURES CATEGÓRICAS =====
            vegan = old_recipe.get('vegan', False)
            vegetarian = old_recipe.get('vegetarian', False)
            gluten_free = old_recipe.get('glutenFree', False)
            dairy_free = old_recipe.get('dairyFree', False)
            very_healthy = old_recipe.get('veryHealthy', False)
            cheap = old_recipe.get('cheap', False)
            
            # Kosher/Halal
            is_kosher, is_halal = check_kosher_halal(ingredients)
            
            # Dish class
            dish_class = old_recipe.get('dishClass', determine_dish_class(dish_types))
            
            # Season
            season = old_recipe.get('season', classify_by_season(ingredients))
            
            # ===== FEATURES DERIVADAS =====
            num_ingredients = len(ingredients)
            complexity_score = calculate_complexity_score(num_ingredients, ready_in_minutes)
            value_score = calculate_value_score(spoonacular_score, price_per_serving)
            nutrient_density = calculate_nutrient_density(health_score, calories)
            restriction_count = sum([vegan, vegetarian, gluten_free, dairy_free])
            price_category = categorize_price(price_per_serving)
            
            # Top 5 ingredientes
            key_ingredients = ingredients[:5] if len(ingredients) >= 5 else ingredients
            
            # ===== TASTE PROFILE (aproximado) =====
            taste_profile = old_recipe.get('taste', {
                'sweetness': 0,
                'saltiness': 0,
                'sourness': 0,
                'bitterness': 0,
                'savoriness': 0
            })
            
            # ===== METADATA =====
            wine_pairing = old_recipe.get('wine_pairing', 
                                         suggest_wine_pairing(ingredients, dish_types))
            aggregate_likes = old_recipe.get('aggregateLikes', 0)
            
            # ===== CONSTRUIR RECETA OPTIMIZADA =====
            optimized_recipe = {
                'id': recipe_id,
                'title': title,
                
                'features_numeric': {
                    'price_per_serving': price_per_serving,
                    'ready_in_minutes': ready_in_minutes,
                    'servings': servings,
                    'health_score': health_score,
                    'spoonacular_score': spoonacular_score,
                    'calories': calories,
                    'sweetness': taste_profile.get('sweetness', 0),
                    'saltiness': taste_profile.get('saltiness', 0),
                    'sourness': taste_profile.get('sourness', 0),
                    'bitterness': taste_profile.get('bitterness', 0),
                    'savoriness': taste_profile.get('savoriness', 0),
                    'num_ingredients': num_ingredients
                },
                
                'features_categorical': {
                    'vegan': vegan,
                    'vegetarian': vegetarian,
                    'gluten_free': gluten_free,
                    'dairy_free': dairy_free,
                    'very_healthy': very_healthy,
                    'cheap': cheap,
                    'dish_class': dish_class,
                    'season': season,
                    'price_category': price_category
                },
                
                'features_text': {
                    'cuisines': cuisines,
                    'diets': diets,
                    'dish_types': dish_types,
                    'occasions': [],  # No disponible en formato antiguo
                    'ingredients': ingredients
                },
                
                'taste_profile': taste_profile,
                
                'derived_features': {
                    'complexity_score': complexity_score,
                    'value_score': value_score,
                    'nutrient_density': nutrient_density,
                    'restriction_count': restriction_count,
                    'key_ingredients': key_ingredients,
                    'price_category': price_category
                },
                
                'metadata': {
                    'wine_pairing': wine_pairing,
                    'aggregate_likes': aggregate_likes,
                    'kosher': is_kosher,
                    'halal': is_halal
                }
            }
            
            optimized_recipes.append(optimized_recipe)
            
            if idx % 100 == 0:
                print(f"   Procesadas {idx}/{len(old_recipes)} recetas...")
                
        except Exception as e:
            print(f"⚠️ Error procesando receta {idx} (ID: {old_recipe.get('id', 'unknown')}): {e}")
            continue
    
    # Guardar recetas optimizadas
    print(f"\n💾 Guardando {len(optimized_recipes)} recetas en {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(optimized_recipes, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"✅ CONVERSIÓN COMPLETADA")
    print(f"{'='*70}")
    print(f"📊 Resumen:")
    print(f"   - Recetas originales: {len(old_recipes)}")
    print(f"   - Recetas convertidas: {len(optimized_recipes)}")
    print(f"   - Archivo de salida: {output_file}")
    print(f"{'='*70}\n")
    
    return True

if __name__ == "__main__":
    success = convert_old_to_optimized()
    if success:
        print("🎯 Próximo paso: Ejecutar main.py para clustering completo\n")
    else:
        print("❌ Conversión fallida. Revisa los errores anteriores.\n")
