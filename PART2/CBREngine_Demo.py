"""
Motor CBR Completo para Recomendación de Menús con Adaptación Cultural
- Lee cbr_menu_database.json y cultural_ingredients_database.json
- Calcula similitud entre preferencias de usuario y menús existentes
- Recupera los menús más similares
- Adapta culturalmente los ingredientes según preferencias
- Demuestra el ciclo CBR: Retrieve → Reuse → Revise → Retain
"""
import json
import math
import os
import sys
from typing import Dict, List, Tuple

def load_cbr_database(filepath='cbr_menu_database.json'):
    """Carga la base de datos CBR"""
    # Buscar en PART2 si no se encuentra en el directorio actual
    if not os.path.exists(filepath):
        part2_path = os.path.join('PART2', filepath)
        if os.path.exists(part2_path):
            filepath = part2_path
    
    with open(filepath, 'r', encoding='utf-8') as f:
        database = json.load(f)
    return database

def load_cultural_ingredients(filepath='cultural_ingredients_database.json'):
    """Carga la base de datos de ingredientes culturales"""
    # Buscar en PART2 si no se encuentra en el directorio actual
    if not os.path.exists(filepath):
        part2_path = os.path.join('PART2', filepath)
        if os.path.exists(part2_path):
            filepath = part2_path
    
    with open(filepath, 'r', encoding='utf-8') as f:
        cultural_db = json.load(f)
    return cultural_db

def normalize_culture_name(culture: str) -> str:
    """Normaliza el nombre de la cultura para búsqueda"""
    # Manejar casos especiales
    culture_lower = culture.lower()
    
    mappings = {
        'mexican': 'Mexicana/Tex-Mex',
        'mexicana': 'Mexicana/Tex-Mex',
        'tex-mex': 'Mexicana/Tex-Mex',
        'italian': 'Italiana',
        'italiana': 'Italiana',
        'mediterranean': 'Mediterránea',
        'mediterránea': 'Mediterránea',
        'american': 'Americana',
        'americana': 'Americana',
        'chinese': 'China',
        'china': 'China',
        'indian': 'India',
        'india': 'India',
        'japanese': 'Japonesa',
        'japonesa': 'Japonesa',
        'peruvian': 'Peruana',
        'peruana': 'Peruana'
    }
    
    return mappings.get(culture_lower, culture)

def calculate_similarity(user_prefs: Dict, menu: Dict) -> float:
    """
    Calcula similitud entre preferencias del usuario y un menú
    
    Usa diferentes métricas según el tipo de feature:
    - Numéricos: Distancia normalizada inversa
    - Booleanos: Coincidencia binaria
    - Categóricos: Coincidencia exacta
    
    Returns:
        float: similarity score (0-1)
    """
    
    features = menu['features']
    sim_features = menu['similarity_features']
    
    score = 0
    total_weight = 0
    
    # === CULTURA (Peso: 25%) ===
    culture_weight = 0.25
    if 'cultura' in user_prefs and 'cultura' in features:
        # Coincidencia exacta de cultura
        if user_prefs['cultura'].lower() == features['cultura'].lower():
            culture_score = 1.0
        else:
            # Coincidencia parcial (e.g., "Italiana" vs "Mediterránea/Italiana")
            user_culture = user_prefs['cultura'].lower()
            menu_culture = features['cultura'].lower()
            if user_culture in menu_culture or menu_culture in user_culture:
                culture_score = 0.7
            else:
                culture_score = 0.0
        
        score += culture_weight * culture_score
        total_weight += culture_weight
    
    # === ESTILO DE COCINA (Peso: 15%) ===
    style_weight = 0.15
    if 'estilo_cocina' in user_prefs and 'estilo_cocina' in features:
        user_style = user_prefs['estilo_cocina'].lower()
        menu_style = features['estilo_cocina'].lower()
        
        if user_style == menu_style:
            style_score = 1.0
        elif user_style in menu_style or menu_style in user_style:
            style_score = 0.6
        else:
            style_score = 0.0
        
        score += style_weight * style_score
        total_weight += style_weight
    
    # === FEATURES DIETÉTICOS (Peso: 30%) ===
    dietary_weight = 0.3
    dietary_score = 0
    
    # Restricciones booleanas
    dietary_checks = [
        ('is_vegan', 1.0),
        ('is_vegetarian', 0.8),
        ('is_gluten_free', 0.9),
        ('is_dairy_free', 0.7),
        ('is_kosher', 0.6),
        ('is_halal', 0.6)
    ]
    
    for key, importance in dietary_checks:
        if key in user_prefs:
            if user_prefs[key] == features[key]:
                dietary_score += importance
            elif user_prefs[key] and not features[key]:
                # Usuario requiere pero menú no cumple - penalización fuerte
                dietary_score -= importance * 0.5
    
    # Normalizar dietary_score
    max_dietary_score = sum(imp for _, imp in dietary_checks)
    if max_dietary_score > 0:
        dietary_score = max(0, min(1, dietary_score / max_dietary_score))
        score += dietary_weight * dietary_score
        total_weight += dietary_weight
    
    # === PRECIO (Peso: 20%) ===
    price_weight = 0.2
    if 'max_price' in user_prefs:
        menu_price = features['total_price_per_serving']
        max_price = user_prefs['max_price']
        
        if menu_price <= max_price:
            # Menú dentro del presupuesto - puntuación alta
            price_score = 1.0 - (0.2 * (menu_price / max_price))
        else:
            # Menú fuera del presupuesto - penalización
            price_score = max(0, 1.0 - ((menu_price - max_price) / max_price))
        
        score += price_weight * price_score
        total_weight += price_weight
    
    # === TIEMPO (Peso: 5%) ===
    time_weight = 0.05
    if 'max_time' in user_prefs:
        menu_time = features['avg_ready_time_minutes']
        max_time = user_prefs['max_time']
        
        if menu_time <= max_time:
            time_score = 1.0 - (0.2 * (menu_time / max_time))
        else:
            time_score = max(0, 1.0 - ((menu_time - max_time) / max_time))
        
        score += time_weight * time_score
        total_weight += time_weight
    
    # === ESTACIÓN (Peso: 5%) ===
    season_weight = 0.05
    if 'season' in user_prefs:
        user_season = user_prefs['season'].lower()
        menu_season = features['season'].lower()
        if user_season == menu_season or menu_season == 'any season' or user_season == 'any-season':
            score += season_weight
        total_weight += season_weight
    
    # Normalizar score final
    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = 0.5  # Score neutro si no hay preferencias
    
    return final_score

def adapt_ingredients_culturally(ingredients: List[str], target_culture: str, cultural_db: Dict) -> Tuple[List[str], List[Dict]]:
    """
    Adapta ingredientes a la cultura objetivo usando reglas de sustitución
    
    Args:
        ingredients: Lista de ingredientes originales
        target_culture: Cultura objetivo
        cultural_db: Base de datos cultural
    
    Returns:
        (adapted_ingredients, substitutions_made)
    """
    target_culture = normalize_culture_name(target_culture)
    substitution_rules = cultural_db.get('substitution_rules', {})
    
    adapted_ingredients = []
    substitutions_made = []
    
    for ingredient in ingredients:
        ingredient_lower = ingredient.lower().strip()
        substituted = False
        
        # Buscar en cada categoría de sustitución
        for category, rules in substitution_rules.items():
            for base_ingredient, culture_mapping in rules.items():
                if base_ingredient in ingredient_lower or ingredient_lower in base_ingredient:
                    # Encontrar sustitución para la cultura objetivo
                    if target_culture in culture_mapping:
                        new_ingredient = culture_mapping[target_culture]
                        
                        if new_ingredient != 'none' and new_ingredient != base_ingredient:
                            adapted_ingredients.append(new_ingredient)
                            substitutions_made.append({
                                'original': ingredient,
                                'substitution': new_ingredient,
                                'category': category,
                                'reason': f'Cultural adaptation to {target_culture}'
                            })
                            substituted = True
                            break
            if substituted:
                break
        
        # Si no se encontró sustitución, mantener ingrediente original
        if not substituted:
            adapted_ingredients.append(ingredient)
    
    return adapted_ingredients, substitutions_made

def retrieve_similar_menus(user_prefs: Dict, database: Dict, top_k: int = 3) -> List[Tuple[Dict, float]]:
    """
    FASE 1 CBR: RETRIEVE
    Recupera los k menús más similares a las preferencias del usuario
    
    Returns:
        List of (menu, similarity_score) tuples, ordered by similarity
    """
    menus = database['menus']
    
    # Calcular similitud para cada menú
    similarities = []
    for menu in menus:
        sim_score = calculate_similarity(user_prefs, menu)
        similarities.append((menu, sim_score))
    
    # Ordenar por similitud (mayor a menor)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    return similarities[:top_k]

def reuse_menu(menu: Dict, user_prefs: Dict, cultural_db: Dict) -> Dict:
    """
    FASE 2 CBR: REUSE
    Adapta el menú recuperado a las necesidades exactas del usuario
    Incluye adaptación cultural de ingredientes
    """
    adapted_menu = json.loads(json.dumps(menu))  # Deep copy
    adapted_menu['adaptations'] = []
    adapted_menu['cultural_substitutions'] = []
    
    features = menu['features']
    
    # === ADAPTACIÓN CULTURAL ===
    if 'cultura' in user_prefs:
        target_culture = user_prefs['cultura']
        menu_culture = features.get('cultura', '')
        
        if target_culture.lower() != menu_culture.lower():
            # Adaptar ingredientes de cada curso
            for course_name in ['starter', 'main', 'dessert']:
                if course_name in adapted_menu['courses']:
                    course = adapted_menu['courses'][course_name]
                    original_ingredients = course['ingredients']
                    
                    adapted_ingr, substitutions = adapt_ingredients_culturally(
                        original_ingredients, 
                        target_culture, 
                        cultural_db
                    )
                    
                    if substitutions:
                        course['ingredients'] = adapted_ingr
                        course['original_ingredients'] = original_ingredients
                        adapted_menu['cultural_substitutions'].extend([
                            {
                                'course': course_name,
                                **sub
                            } for sub in substitutions
                        ])
            
            if adapted_menu['cultural_substitutions']:
                adapted_menu['adaptations'].append({
                    'type': 'cultural_adaptation',
                    'reason': f"Adapted from {menu_culture} to {target_culture} cuisine",
                    'total_substitutions': len(adapted_menu['cultural_substitutions'])
                })
    
    # === ADAPTACIÓN DE PRECIO ===
    if user_prefs.get('max_price') and features['total_price_per_serving'] > user_prefs['max_price']:
        adapted_menu['adaptations'].append({
            'type': 'price_reduction',
            'reason': f"Reduce price from ${features['total_price_per_serving']:.2f} to ${user_prefs['max_price']:.2f}",
            'suggestion': 'Replace expensive ingredients with cheaper alternatives'
        })
    
    # === ADAPTACIÓN DIETÉTICA ===
    if user_prefs.get('is_vegan') and not features['is_vegan']:
        adapted_menu['adaptations'].append({
            'type': 'dietary_adaptation',
            'reason': 'User requires vegan menu',
            'suggestion': 'Replace non-vegan courses with vegan alternatives from database'
        })
    
    if user_prefs.get('is_vegetarian') and not features['is_vegetarian']:
        adapted_menu['adaptations'].append({
            'type': 'dietary_adaptation',
            'reason': 'User requires vegetarian menu',
            'suggestion': 'Replace meat courses with vegetarian alternatives'
        })
    
    # === ADAPTACIÓN DE TIEMPO ===
    if user_prefs.get('max_time') and features['avg_ready_time_minutes'] > user_prefs['max_time']:
        adapted_menu['adaptations'].append({
            'type': 'time_reduction',
            'reason': f"Reduce time from {features['avg_ready_time_minutes']} to {user_prefs['max_time']} minutes",
            'suggestion': 'Use pre-prepared ingredients or simpler cooking methods'
        })
    
    return adapted_menu

def revise_menu(adapted_menu: Dict, user_prefs: Dict) -> Tuple[bool, List[str]]:
    """
    FASE 3 CBR: REVISE
    Valida si el menú adaptado cumple todas las restricciones del usuario
    
    Returns:
        (is_valid, list_of_issues)
    """
    issues = []
    features = adapted_menu['features']
    
    # Validar restricciones dietéticas CRÍTICAS
    critical_dietary = ['is_vegan', 'is_vegetarian', 'is_gluten_free', 'is_kosher', 'is_halal']
    for key in critical_dietary:
        if user_prefs.get(key) and not features[key]:
            issues.append(f"❌ Menu does not satisfy {key} requirement")
    
    # Validar precio (tolerancia 10%)
    if 'max_price' in user_prefs:
        if features['total_price_per_serving'] > user_prefs['max_price'] * 1.1:
            issues.append(f"❌ Menu exceeds budget: ${features['total_price_per_serving']:.2f} > ${user_prefs['max_price']:.2f}")
    
    # Validar tiempo (tolerancia 15%)
    if 'max_time' in user_prefs:
        if features['avg_ready_time_minutes'] > user_prefs['max_time'] * 1.15:
            issues.append(f"❌ Menu takes too long: {features['avg_ready_time_minutes']} min > {user_prefs['max_time']} min")
    
    is_valid = len(issues) == 0
    return is_valid, issues

def retain_menu(new_menu: Dict, database: Dict, success: bool):
    """
    FASE 4 CBR: RETAIN
    Si el menú fue exitoso, añadirlo a la base de datos para futuros casos
    
    (En este ejemplo simplificado, solo mostramos el mensaje)
    """
    if success:
        print("   ✅ Este menú podría añadirse a la base de datos para futuras consultas")
    else:
        print("   ❌ Este menú no fue satisfactorio, no se retiene")

def print_menu_summary(menu: Dict, similarity: float = None):
    """Imprime resumen de un menú"""
    features = menu['features']
    courses = menu['courses']
    
    if similarity is not None:
        print(f"\n{'='*70}")
        print(f"📊 Similitud: {similarity*100:.1f}%")
    print(f"{'='*70}")
    print(f"🍽️  {menu['menu_name']}")
    print(f"{'='*70}")
    
    # Mostrar cultura y estilo
    if 'cultura' in features:
        print(f"\n🌍 CULTURA: {features['cultura']}")
    if 'estilo_cocina' in features:
        print(f"👨‍🍳 ESTILO: {features['estilo_cocina']}")
    
    print(f"\n🥗 STARTER: {courses['starter']['title']}")
    print(f"   - Precio: ${courses['starter']['price_per_serving']:.2f}")
    print(f"   - Ingredientes: {', '.join(courses['starter']['ingredients'][:5])}...")
    
    print(f"\n🍖 MAIN COURSE: {courses['main']['title']}")
    print(f"   - Precio: ${courses['main']['price_per_serving']:.2f}")
    print(f"   - Ingredientes: {', '.join(courses['main']['ingredients'][:5])}...")
    
    print(f"\n🍰 DESSERT: {courses['dessert']['title']}")
    print(f"   - Precio: ${courses['dessert']['price_per_serving']:.2f}")
    print(f"   - Ingredientes: {', '.join(courses['dessert']['ingredients'][:5])}...")
    
    print(f"\n💰 TOTAL: ${features['total_price_per_serving']:.2f} ({features['price_category']})")
    print(f"⏱️  TIEMPO: {features['avg_ready_time_minutes']} min ({features['time_category']})")
    print(f"🌿 ESTACIÓN: {features['season']}")
    print(f"🍷 VINO: {features['wine_pairing']}")
    
    # Restricciones
    restrictions = []
    if features['is_vegan']:
        restrictions.append("🌱 Vegan")
    elif features['is_vegetarian']:
        restrictions.append("🥬 Vegetarian")
    if features['is_gluten_free']:
        restrictions.append("🌾 Gluten-Free")
    if features['is_kosher']:
        restrictions.append("✡️  Kosher")
    if features['is_halal']:
        restrictions.append("☪️  Halal")
    
    if restrictions:
        print(f"\n✅ RESTRICCIONES: {' | '.join(restrictions)}")
    
    # Sustituciones culturales
    if 'cultural_substitutions' in menu and menu['cultural_substitutions']:
        print(f"\n🔄 ADAPTACIONES CULTURALES ({len(menu['cultural_substitutions'])} cambios):")
        for sub in menu['cultural_substitutions'][:5]:  # Mostrar primeras 5
            print(f"   [{sub['course']}] {sub['original']} → {sub['substitution']}")
        if len(menu['cultural_substitutions']) > 5:
            print(f"   ... y {len(menu['cultural_substitutions']) - 5} más")
    
    # Otras adaptaciones
    if 'adaptations' in menu and menu['adaptations']:
        print(f"\n🔧 OTRAS ADAPTACIONES:")
        for adaptation in menu['adaptations']:
            if adaptation['type'] != 'cultural_adaptation':
                print(f"   - {adaptation['type']}: {adaptation['reason']}")

def run_cbr_system(user_prefs: Dict):
    """
    Ejecuta el sistema CBR completo con las preferencias del usuario
    """
    print(f"\n{'#'*70}")
    print(f"# SISTEMA CBR DE RECOMENDACIÓN DE MENÚS")
    print(f"{'#'*70}\n")
    
    # Cargar bases de datos
    print("📂 Cargando bases de datos...")
    database = load_cbr_database()
    cultural_db = load_cultural_ingredients()
    print(f"✅ Base de datos CBR: {database['metadata']['total_menus']} menús")
    print(f"✅ Base de datos cultural: {len(cultural_db['cultural_ingredients'])} culturas\n")
    
    # Mostrar preferencias
    print(f"{'='*70}")
    print(f"🔍 PREFERENCIAS DEL USUARIO")
    print(f"{'='*70}\n")
    
    if 'cultura' in user_prefs:
        print(f"   🌍 Cultura: {user_prefs['cultura']}")
    if 'estilo_cocina' in user_prefs:
        print(f"   👨‍🍳 Estilo: {user_prefs['estilo_cocina']}")
    if 'max_price' in user_prefs:
        print(f"   💰 Presupuesto máximo: ${user_prefs['max_price']}")
    if 'season' in user_prefs:
        print(f"   🌿 Estación: {user_prefs['season']}")
    
    dietary_prefs = []
    if user_prefs.get('is_vegan'):
        dietary_prefs.append("Vegan")
    if user_prefs.get('is_vegetarian'):
        dietary_prefs.append("Vegetarian")
    if user_prefs.get('is_gluten_free'):
        dietary_prefs.append("Gluten-Free")
    
    if dietary_prefs:
        print(f"   🥗 Dietético: {', '.join(dietary_prefs)}")
    
    # FASE 1: RETRIEVE
    print(f"\n{'='*70}")
    print(f"🔍 FASE 1: RETRIEVE - Buscando menús similares...")
    print(f"{'='*70}")
    
    similar_menus = retrieve_similar_menus(user_prefs, database, top_k=3)
    
    print(f"\n✅ Top 3 menús más similares encontrados:\n")
    for idx, (menu, similarity) in enumerate(similar_menus, 1):
        culture = menu['features'].get('cultura', 'N/A')
        print(f"{idx}. {menu['menu_name']}")
        print(f"   Cultura: {culture} | Similitud: {similarity*100:.1f}%")
    
    # Seleccionar el mejor
    best_menu, best_similarity = similar_menus[0]
    print_menu_summary(best_menu, best_similarity)
    
    # FASE 2: REUSE
    print(f"\n{'='*70}")
    print(f"♻️  FASE 2: REUSE - Adaptando menú a necesidades del usuario...")
    print(f"{'='*70}")
    
    adapted_menu = reuse_menu(best_menu, user_prefs, cultural_db)
    
    if adapted_menu['adaptations']:
        print(f"\n🔧 Adaptaciones aplicadas:")
        for adaptation in adapted_menu['adaptations']:
            print(f"   - {adaptation['type']}: {adaptation.get('reason', 'N/A')}")
    else:
        print(f"\n✅ El menú no requiere adaptaciones - cumple todos los requisitos!")
    
    if adapted_menu.get('cultural_substitutions'):
        print(f"\n🔄 Sustituciones culturales: {len(adapted_menu['cultural_substitutions'])} ingredientes adaptados")
    
    # Mostrar menú adaptado
    print_menu_summary(adapted_menu)
    
    # FASE 3: REVISE
    print(f"\n{'='*70}")
    print(f"🔍 FASE 3: REVISE - Validando menú adaptado...")
    print(f"{'='*70}")
    
    is_valid, issues = revise_menu(adapted_menu, user_prefs)
    
    if is_valid:
        print(f"\n✅ VALIDACIÓN EXITOSA - El menú cumple todos los requisitos")
    else:
        print(f"\n❌ VALIDACIÓN FALLIDA - Problemas encontrados:")
        for issue in issues:
            print(f"   {issue}")
    
    # FASE 4: RETAIN
    print(f"\n{'='*70}")
    print(f"💾 FASE 4: RETAIN - ¿Retener este caso?")
    print(f"{'='*70}")
    
    retain_menu(adapted_menu, database, is_valid)
    
    print(f"\n{'='*70}\n")
    
    return adapted_menu, is_valid

def main():
    """Función principal para ejecutar demos"""
    
    # EJEMPLO 1: Usuario quiere cocina Italiana vegetariana
    print(f"\n{'='*70}")
    print(f"📋 EJEMPLO 1: Cocina Italiana Vegetariana")
    print(f"{'='*70}\n")
    
    user_prefs_1 = {
        'cultura': 'Italiana',
        'estilo_cocina': 'Moderno',
        'is_vegetarian': True,
        'max_price': 500,
        'season': 'Summer'
    }
    
    menu1, valid1 = run_cbr_system(user_prefs_1)
    
    # EJEMPLO 2: Usuario quiere cocina China con adaptación desde menú Mexicano
    print(f"\n\n{'='*70}")
    print(f"📋 EJEMPLO 2: Cocina China (adaptación cultural)")
    print(f"{'='*70}\n")
    
    user_prefs_2 = {
        'cultura': 'China',
        'estilo_cocina': 'Tradicional',
        'max_price': 400,
        'season': 'Winter'
    }
    
    menu2, valid2 = run_cbr_system(user_prefs_2)
    
    print(f"\n{'='*70}")
    print(f"🎯 DEMOSTRACIÓN COMPLETADA")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa interrumpido por el usuario\n")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"\n❌ Error: No se encontró el archivo: {e}")
        print("   Asegúrate de ejecutar desde el directorio correcto\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
