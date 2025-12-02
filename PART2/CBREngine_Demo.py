"""
Motor CBR Simple para Recomendación de Menús
- Lee cbr_menu_database.json
- Calcula similitud entre preferencias de usuario y menús existentes
- Recupera los menús más similares
- Demuestra el ciclo CBR: Retrieve → Reuse → Revise → Retain
"""
import json
import math
from typing import Dict, List, Tuple

def load_cbr_database(filepath='cbr_menu_database.json'):
    """Carga la base de datos CBR"""
    with open(filepath, 'r', encoding='utf-8') as f:
        database = json.load(f)
    return database

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
    
    # === FEATURES DIETÉTICOS (Peso: 40%) ===
    dietary_weight = 0.4
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
    
    # === PRECIO (Peso: 30%) ===
    price_weight = 0.3
    if 'max_price' in user_prefs:
        menu_price = features['total_price_per_serving']
        max_price = user_prefs['max_price']
        
        if menu_price <= max_price:
            # Menú dentro del presupuesto - puntuación alta
            # Cuanto más barato mejor (pero no penalizar mucho)
            price_score = 1.0 - (0.2 * (menu_price / max_price))
        else:
            # Menú fuera del presupuesto - penalización
            price_score = max(0, 1.0 - ((menu_price - max_price) / max_price))
        
        score += price_weight * price_score
        total_weight += price_weight
    
    # === TIEMPO (Peso: 20%) ===
    time_weight = 0.2
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
        if user_prefs['season'] == features['season'] or features['season'] == 'Any season':
            score += season_weight
        total_weight += season_weight
    
    # === COMPLEJIDAD (Peso: 5%) ===
    complexity_weight = 0.05
    if 'preferred_complexity' in user_prefs:
        # preferred_complexity: 'simple' (0-30), 'moderate' (30-70), 'complex' (70-100)
        complexity = sim_features['complexity_score']
        pref = user_prefs['preferred_complexity']
        
        if pref == 'simple' and complexity < 30:
            complexity_score = 1.0
        elif pref == 'moderate' and 30 <= complexity <= 70:
            complexity_score = 1.0
        elif pref == 'complex' and complexity > 70:
            complexity_score = 1.0
        else:
            # Penalización suave por desviación
            complexity_score = 0.5
        
        score += complexity_weight * complexity_score
        total_weight += complexity_weight
    
    # Normalizar score final
    if total_weight > 0:
        final_score = score / total_weight
    else:
        final_score = 0.5  # Score neutro si no hay preferencias
    
    return final_score

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

def reuse_menu(menu: Dict, user_prefs: Dict) -> Dict:
    """
    FASE 2 CBR: REUSE
    Adapta el menú recuperado a las necesidades exactas del usuario
    
    (En este ejemplo simplificado, solo marcamos qué debería adaptarse)
    """
    adapted_menu = menu.copy()
    adapted_menu['adaptations'] = []
    
    features = menu['features']
    
    # Verificar si necesita adaptaciones
    if user_prefs.get('max_price') and features['total_price_per_serving'] > user_prefs['max_price']:
        adapted_menu['adaptations'].append({
            'type': 'price_reduction',
            'reason': f"Reduce price from ${features['total_price_per_serving']:.2f} to ${user_prefs['max_price']:.2f}",
            'suggestion': 'Replace expensive ingredients with cheaper alternatives'
        })
    
    if user_prefs.get('is_vegan') and not features['is_vegan']:
        adapted_menu['adaptations'].append({
            'type': 'dietary_adaptation',
            'reason': 'User requires vegan menu',
            'suggestion': 'Replace non-vegan courses with vegan alternatives from database'
        })
    
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
    
    # Adaptaciones si existen
    if 'adaptations' in menu and menu['adaptations']:
        print(f"\n🔧 ADAPTACIONES NECESARIAS:")
        for adaptation in menu['adaptations']:
            print(f"   - {adaptation['type']}: {adaptation['reason']}")
            print(f"     Sugerencia: {adaptation['suggestion']}")

def cbr_cycle_demo():
    """Demuestra el ciclo completo CBR"""
    
    print(f"\n{'#'*70}")
    print(f"# DEMOSTRACIÓN DE MOTOR CBR PARA MENÚS")
    print(f"{'#'*70}\n")
    
    # Cargar base de datos
    print("📂 Cargando base de datos CBR...")
    database = load_cbr_database()
    print(f"✅ Base de datos cargada: {database['metadata']['total_menus']} menús\n")
    
    # === EJEMPLO 1: Usuario vegano con presupuesto medio ===
    print(f"\n{'='*70}")
    print(f"📋 EJEMPLO 1: Usuario Vegano con Presupuesto Medio")
    print(f"{'='*70}\n")
    
    user_prefs_1 = {
        'is_vegan': True,
        'max_price': 300,
        'max_time': 60,
        'season': 'Summer',
        'preferred_complexity': 'moderate'
    }
    
    print("🔍 Preferencias del usuario:")
    print(f"   - Dieta: Vegan")
    print(f"   - Presupuesto: Máximo $300")
    print(f"   - Tiempo: Máximo 60 min")
    print(f"   - Estación: Summer")
    print(f"   - Complejidad: Moderate")
    
    # FASE 1: RETRIEVE
    print(f"\n{'='*70}")
    print(f"🔍 FASE 1: RETRIEVE - Buscando menús similares...")
    print(f"{'='*70}")
    
    similar_menus = retrieve_similar_menus(user_prefs_1, database, top_k=3)
    
    print(f"\n✅ Top 3 menús más similares encontrados:\n")
    for idx, (menu, similarity) in enumerate(similar_menus, 1):
        print(f"{idx}. {menu['menu_name']} - Similitud: {similarity*100:.1f}%")
    
    # Seleccionar el mejor
    best_menu, best_similarity = similar_menus[0]
    print_menu_summary(best_menu, best_similarity)
    
    # FASE 2: REUSE
    print(f"\n{'='*70}")
    print(f"♻️  FASE 2: REUSE - Adaptando menú a necesidades del usuario...")
    print(f"{'='*70}")
    
    adapted_menu = reuse_menu(best_menu, user_prefs_1)
    
    if adapted_menu['adaptations']:
        print(f"\n🔧 Adaptaciones aplicadas:")
        for adaptation in adapted_menu['adaptations']:
            print(f"   - {adaptation['type']}: {adaptation['reason']}")
    else:
        print(f"\n✅ El menú no requiere adaptaciones - cumple todos los requisitos!")
    
    # FASE 3: REVISE
    print(f"\n{'='*70}")
    print(f"🔍 FASE 3: REVISE - Validando menú adaptado...")
    print(f"{'='*70}")
    
    is_valid, issues = revise_menu(adapted_menu, user_prefs_1)
    
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
    
    # === EJEMPLO 2: Usuario Kosher con presupuesto premium ===
    print(f"\n\n{'='*70}")
    print(f"📋 EJEMPLO 2: Usuario Kosher con Presupuesto Premium")
    print(f"{'='*70}\n")
    
    user_prefs_2 = {
        'is_kosher': True,
        'max_price': 600,
        'max_time': 90,
        'season': 'Winter',
        'preferred_complexity': 'complex'
    }
    
    print("🔍 Preferencias del usuario:")
    print(f"   - Dieta: Kosher")
    print(f"   - Presupuesto: Máximo $600")
    print(f"   - Tiempo: Máximo 90 min")
    print(f"   - Estación: Winter")
    print(f"   - Complejidad: Complex")
    
    # RETRIEVE
    similar_menus_2 = retrieve_similar_menus(user_prefs_2, database, top_k=3)
    best_menu_2, best_similarity_2 = similar_menus_2[0]
    
    print(f"\n✅ Mejor menú encontrado:")
    print_menu_summary(best_menu_2, best_similarity_2)
    
    print(f"\n{'='*70}\n")
    print(f"🎯 DEMOSTRACIÓN COMPLETADA")
    print(f"   La base de datos CBR puede adaptarse a diferentes perfiles de usuario")
    print(f"   usando el ciclo: Retrieve → Reuse → Revise → Retain\n")

if __name__ == "__main__":
    cbr_cycle_demo()
