"""
Generador de Base de Datos CBR para Menús Completos
- Analiza filtered_recipes111.json
- Selecciona recetas representativas de Starter, Main y Dessert
- Genera 10 menús completos con diversidad máxima
- Criterios: cocinas variadas, restricciones dietéticas, estacionalidad, precio
- Output: cbr_menu_database.json
"""
import json
import random
from collections import defaultdict

def load_recipes(filepath='filtered_recipes111.json'):
    """Carga todas las recetas"""
    with open(filepath, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    return recipes

def categorize_recipes(recipes):
    """Separa recetas por dishClass"""
    categorized = {
        'Starter': [],
        'Main': [],
        'Dessert': [],
        'Mixed': []
    }
    
    for recipe in recipes:
        dish_class = recipe.get('dishClass', 'Mixed')
        categorized[dish_class].append(recipe)
    
    return categorized

def calculate_diversity_score(recipe):
    """Calcula score de diversidad (priorizando recetas interesantes)"""
    score = 0
    
    # Precio equilibrado (ni muy barato ni muy caro)
    price = recipe.get('pricePerServing', 0)
    if 50 < price < 300:
        score += 10
    
    # Tiene restricciones dietéticas (más interesante para CBR)
    restrictions = recipe.get('restrictions', [])
    score += len(restrictions) * 5
    
    # Estacionalidad específica (no "any-season")
    season_text = recipe.get('seasonText', 'Any season')
    if season_text != 'Any season':
        score += 15
    
    # Número de ingredientes moderado (no muy simple ni muy complejo)
    num_ingredients = len(recipe.get('ingredients', []))
    if 5 <= num_ingredients <= 15:
        score += 10
    
    # Wine pairing disponible
    wine = recipe.get('winePairing', 'No wine pairing')
    if wine != 'No wine pairing':
        score += 20
    
    # Kosher o Halal
    if recipe.get('isKosher', False):
        score += 5
    if recipe.get('isHalal', False):
        score += 5
    
    return score

def select_diverse_recipes(recipes, n=10, ensure_variety=True):
    """Selecciona recetas diversas usando clustering manual"""
    
    # Agrupar por características clave
    groups = defaultdict(list)
    
    for recipe in recipes:
        # Crear clave de grupo: (season, tiene_restricciones, rango_precio)
        season = recipe.get('seasonText', 'Any season')
        has_restrictions = len(recipe.get('restrictions', [])) > 0
        price = recipe.get('pricePerServing', 0)
        
        # Categoría de precio
        if price < 50:
            price_cat = 'budget'
        elif price < 150:
            price_cat = 'medium'
        elif price < 300:
            price_cat = 'premium'
        else:
            price_cat = 'luxury'
        
        # Clave única
        key = (season, has_restrictions, price_cat)
        groups[key].append(recipe)
    
    # Seleccionar 1-2 recetas de cada grupo
    selected = []
    for group_recipes in groups.values():
        # Ordenar por diversity score
        group_recipes.sort(key=calculate_diversity_score, reverse=True)
        
        # Tomar las mejores
        num_to_take = min(2, len(group_recipes))
        selected.extend(group_recipes[:num_to_take])
    
    # Si no tenemos suficientes, añadir las mejores restantes
    if len(selected) < n:
        remaining = [r for r in recipes if r not in selected]
        remaining.sort(key=calculate_diversity_score, reverse=True)
        selected.extend(remaining[:n - len(selected)])
    
    # Si tenemos demasiadas, quedarnos con las mejores
    selected.sort(key=calculate_diversity_score, reverse=True)
    return selected[:n]

def create_menu(menu_id, starter, main, dessert):
    """Crea un objeto menú completo"""
    
    # Calcular características del menú
    total_price = sum([
        starter.get('pricePerServing', 0),
        main.get('pricePerServing', 0),
        dessert.get('pricePerServing', 0)
    ])
    
    avg_time = (
        starter.get('readyInMinutes', 0) +
        main.get('readyInMinutes', 0) +
        dessert.get('readyInMinutes', 0)
    ) // 3
    
    # Combinar restricciones (intersección - lo que TODO el menú cumple)
    starter_restrictions = set(starter.get('restrictions', []))
    main_restrictions = set(main.get('restrictions', []))
    dessert_restrictions = set(dessert.get('restrictions', []))
    
    common_restrictions = list(
        starter_restrictions & main_restrictions & dessert_restrictions
    )
    
    # Determinar si es kosher/halal (todo debe serlo)
    is_kosher = all([
        starter.get('isKosher', False),
        main.get('isKosher', False),
        dessert.get('isKosher', False)
    ])
    
    is_halal = all([
        starter.get('isHalal', False),
        main.get('isHalal', False),
        dessert.get('isHalal', False)
    ])
    
    # Estación dominante (usar la del Main)
    season = main.get('seasonText', 'Any season')
    
    # Wine pairing (usar el del Main)
    wine = main.get('winePairing', 'No wine pairing')
    
    menu = {
        "menu_id": menu_id,
        "menu_name": f"Menu {menu_id}: {main['title']}",
        "description": f"Complete menu featuring {main['title']} as main course",
        
        # Platos
        "courses": {
            "starter": {
                "recipe_id": starter['id'],
                "title": starter['title'],
                "servings": starter.get('servings', 0),
                "price_per_serving": starter.get('pricePerServing', 0),
                "ready_in_minutes": starter.get('readyInMinutes', 0),
                "ingredients": starter.get('ingredients', []),
                "restrictions": starter.get('restrictions', [])
            },
            "main": {
                "recipe_id": main['id'],
                "title": main['title'],
                "servings": main.get('servings', 0),
                "price_per_serving": main.get('pricePerServing', 0),
                "ready_in_minutes": main.get('readyInMinutes', 0),
                "ingredients": main.get('ingredients', []),
                "restrictions": main.get('restrictions', [])
            },
            "dessert": {
                "recipe_id": dessert['id'],
                "title": dessert['title'],
                "servings": dessert.get('servings', 0),
                "price_per_serving": dessert.get('pricePerServing', 0),
                "ready_in_minutes": dessert.get('readyInMinutes', 0),
                "ingredients": dessert.get('ingredients', []),
                "restrictions": dessert.get('restrictions', [])
            }
        },
        
        # Features para CBR (características del menú completo)
        "features": {
            "total_price_per_serving": round(total_price, 2),
            "price_category": categorize_price(total_price),
            "avg_ready_time_minutes": avg_time,
            "time_category": categorize_time(avg_time),
            "season": season,
            "wine_pairing": wine,
            "is_kosher": is_kosher,
            "is_halal": is_halal,
            "common_dietary_restrictions": common_restrictions,
            "is_vegetarian": all([
                starter.get('vegetarian', False),
                main.get('vegetarian', False),
                dessert.get('vegetarian', False)
            ]),
            "is_vegan": all([
                starter.get('vegan', False),
                main.get('vegan', False),
                dessert.get('vegan', False)
            ]),
            "is_gluten_free": all([
                starter.get('glutenFree', False),
                main.get('glutenFree', False),
                dessert.get('glutenFree', False)
            ]),
            "is_dairy_free": all([
                starter.get('dairyFree', False),
                main.get('dairyFree', False),
                dessert.get('dairyFree', False)
            ])
        },
        
        # Metadata para similarity matching
        "similarity_features": {
            "total_ingredients_count": len(set(
                starter.get('ingredients', []) +
                main.get('ingredients', []) +
                dessert.get('ingredients', [])
            )),
            "complexity_score": calculate_complexity(starter, main, dessert),
            "health_factor": calculate_health_factor(starter, main, dessert),
            "cuisine_diversity": len(set([
                c for recipe in [starter, main, dessert]
                for c in recipe.get('cuisines', [])
            ]))
        }
    }
    
    return menu

def categorize_price(total_price):
    """Categoriza precio total del menú"""
    if total_price < 150:
        return "budget"
    elif total_price < 400:
        return "moderate"
    elif total_price < 700:
        return "premium"
    else:
        return "luxury"

def categorize_time(avg_time):
    """Categoriza tiempo promedio"""
    if avg_time < 20:
        return "quick"
    elif avg_time < 45:
        return "moderate"
    else:
        return "elaborate"

def calculate_complexity(starter, main, dessert):
    """Calcula complejidad del menú (0-100)"""
    total_ingredients = (
        len(starter.get('ingredients', [])) +
        len(main.get('ingredients', [])) +
        len(dessert.get('ingredients', []))
    )
    
    # Normalizar a 0-100
    # Asumiendo 5-50 ingredientes totales
    complexity = min(100, (total_ingredients / 50) * 100)
    return round(complexity, 1)

def calculate_health_factor(starter, main, dessert):
    """Calcula factor de salud del menú (0-100)"""
    health_scores = []
    
    for recipe in [starter, main, dessert]:
        # Puntos por restricciones saludables
        score = 0
        if recipe.get('vegetarian', False):
            score += 20
        if recipe.get('vegan', False):
            score += 30
        if recipe.get('glutenFree', False):
            score += 15
        if recipe.get('dairyFree', False):
            score += 10
        
        health_scores.append(min(100, score))
    
    avg_health = sum(health_scores) / 3
    return round(avg_health, 1)

def generate_cbr_menus(recipes, n_menus=10):
    """Genera n menús representativos para CBR"""
    
    print(f"\n{'='*70}")
    print(f"🍽️  GENERANDO BASE DE DATOS CBR DE MENÚS")
    print(f"{'='*70}\n")
    
    # Categorizar recetas
    categorized = categorize_recipes(recipes)
    
    print(f"📊 Recetas disponibles:")
    print(f"   - Starters: {len(categorized['Starter'])}")
    print(f"   - Mains: {len(categorized['Main'])}")
    print(f"   - Desserts: {len(categorized['Dessert'])}")
    print(f"   - Mixed: {len(categorized['Mixed'])}")
    print()
    
    # Seleccionar recetas diversas de cada categoría
    print(f"🎯 Seleccionando recetas representativas...")
    
    selected_starters = select_diverse_recipes(categorized['Starter'], n=n_menus)
    selected_mains = select_diverse_recipes(categorized['Main'], n=n_menus)
    selected_desserts = select_diverse_recipes(categorized['Dessert'], n=n_menus)
    
    print(f"   ✓ {len(selected_starters)} Starters seleccionados")
    print(f"   ✓ {len(selected_mains)} Mains seleccionados")
    print(f"   ✓ {len(selected_desserts)} Desserts seleccionados")
    print()
    
    # Crear menús combinando recetas
    menus = []
    
    for i in range(n_menus):
        menu = create_menu(
            menu_id=i + 1,
            starter=selected_starters[i % len(selected_starters)],
            main=selected_mains[i % len(selected_mains)],
            dessert=selected_desserts[i % len(selected_desserts)]
        )
        menus.append(menu)
    
    print(f"✅ {len(menus)} menús generados\n")
    
    return menus

def save_cbr_database(menus, output_file='cbr_menu_database.json'):
    """Guarda base de datos CBR en formato JSON robusto"""
    
    database = {
        "metadata": {
            "version": "1.0",
            "created_date": "2025-12-01",
            "description": "CBR Menu Database - Representative complete menus for Case-Based Reasoning",
            "total_menus": len(menus),
            "structure": "Each menu contains Starter + Main + Dessert with complete features for similarity matching"
        },
        "menus": menus,
        "cbr_features_index": {
            "numerical_features": [
                "total_price_per_serving",
                "avg_ready_time_minutes",
                "total_ingredients_count",
                "complexity_score",
                "health_factor",
                "cuisine_diversity"
            ],
            "categorical_features": [
                "price_category",
                "time_category",
                "season",
                "wine_pairing"
            ],
            "boolean_features": [
                "is_kosher",
                "is_halal",
                "is_vegetarian",
                "is_vegan",
                "is_gluten_free",
                "is_dairy_free"
            ],
            "list_features": [
                "common_dietary_restrictions"
            ]
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Base de datos guardada en: {output_file}\n")
    
    return database

def print_summary(database):
    """Imprime resumen de la base de datos"""
    print(f"{'='*70}")
    print(f"📋 RESUMEN DE BASE DE DATOS CBR")
    print(f"{'='*70}\n")
    
    menus = database['menus']
    
    print(f"🍽️  Total de Menús: {len(menus)}\n")
    
    for menu in menus:
        features = menu['features']
        print(f"Menu {menu['menu_id']}: {menu['menu_name']}")
        print(f"   Starter: {menu['courses']['starter']['title']}")
        print(f"   Main:    {menu['courses']['main']['title']}")
        print(f"   Dessert: {menu['courses']['dessert']['title']}")
        print(f"   Precio:  ${features['total_price_per_serving']:.2f} ({features['price_category']})")
        print(f"   Tiempo:  {features['avg_ready_time_minutes']} min ({features['time_category']})")
        print(f"   Estación: {features['season']}")
        print(f"   Vino:    {features['wine_pairing']}")
        
        # Restricciones
        restrictions = []
        if features['is_vegetarian']:
            restrictions.append("Vegetarian")
        if features['is_vegan']:
            restrictions.append("Vegan")
        if features['is_gluten_free']:
            restrictions.append("Gluten-Free")
        if features['is_kosher']:
            restrictions.append("Kosher")
        if features['is_halal']:
            restrictions.append("Halal")
        
        if restrictions:
            print(f"   Restricciones: {', '.join(restrictions)}")
        
        print()
    
    print(f"{'='*70}\n")

def main():
    """Pipeline principal"""
    
    # Cargar recetas
    print("📂 Cargando filtered_recipes111.json...")
    recipes = load_recipes()
    print(f"✅ Cargadas {len(recipes)} recetas\n")
    
    # Generar menús CBR
    menus = generate_cbr_menus(recipes, n_menus=10)
    
    # Guardar base de datos
    database = save_cbr_database(menus)
    
    # Imprimir resumen
    print_summary(database)
    
    print("🎯 Base de datos CBR lista para usar en sistema de recomendación de menús!")
    print("   Usa las 'features' y 'similarity_features' para calcular similitud entre menús.\n")

if __name__ == "__main__":
    main()
