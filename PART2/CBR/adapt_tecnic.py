import os, json, copy
from copy import deepcopy
# ============================================================================
# CONFIGURACIÓN DE RUTAS
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..')

# Bases de conocimiento
CULT_TECNIC_PATH = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ontologia_cultura_tecnicas.json')
TECNIC_SUST_PATH = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ontologia_tecnica_sustituciones.json')
# ============================================================================
# UTILIDADES
# ============================================================================
def load_knowledge_base(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
def extract_techniques(structured_instructions: list) -> list:
    techniques = set()
    for step in structured_instructions:
        action = step.get('preparation_action', '').lower()
        techniques.add(action)
    return techniques
# ============================================================================
# FUNCIONES DE ADAPTACIÓN DE TÉCNICAS
# ============================================================================
def adapt_course(course: dict, set_culture_tecnics: set, tecnic_sust_knowledge: dict) -> int:
    set_tecniques = set(extract_techniques(course.get('structured_instructions', [])))
    set_tecnic_to_adapt = set_tecniques-set_culture_tecnics #used tecniques that are not in the target culture
    if not set_tecnic_to_adapt:
        print("  ✅ All techniques are suitable for the target culture.")
        return course
    else:
        print(f"  ⚠️  Techniques to adapt: {set_tecnic_to_adapt}")
    change = {}
    for tec in set_tecnic_to_adapt:
        substitutions = set(tecnic_sust_knowledge.get(tec, []))
        good_substitutions = substitutions.intersection(set_culture_tecnics)
        if good_substitutions:
            print(f"  🔄 Adapting technique '{tec}' with substitutions: {good_substitutions}")
            change[tec] = good_substitutions.pop()
    num_subs = 0
    for step in course.get('structured_instructions', []):
        action = step.get('preparation_action', '').lower()
        if action in change:
            old_action = step['preparation_action']
            step['preparation_action'] = change[action]
            num_subs += 1
    course['_adaptation_tecnic'] = {
        'substitutions': change,
        'original_techniques': list(set_tecniques),
        'techniques_substituted': num_subs,
        'techniques_kept': len(set_tecniques) - num_subs,
        'tecniques_removed': 0,
        'removed_techniques': []
    }
    return course


# ============================================================================
# FUNCION PRINCIPAL
# ============================================================================
def adapt_menu_tecniques(prev_adapted_solution: dict) -> dict:
    cult_tecnic_knowledge = load_knowledge_base(CULT_TECNIC_PATH)
    tecnic_sust_knowledge = load_knowledge_base(TECNIC_SUST_PATH)

    target_culture = 'Chinese'#prev_adapted_solution.get("culture_adapted", "").strip()
    set_culture_tecnics = set(cult_tecnic_knowledge.get(target_culture, []))
    adapted_solution = deepcopy(prev_adapted_solution)
    menu = adapted_solution.get("menu", {})
    courses = menu.get("courses", {})
    
    # Adaptar cada plato
    new_courses = deepcopy(courses)
    total_subs = 0
    for course_name, course_data in courses.items():
        print(f"\n🍽️ Adapting course: {course_name} - {course_data.get('title', 'Unknown')}")
        new_course = adapt_course(
            deepcopy(course_data),
            set_culture_tecnics,
            tecnic_sust_knowledge
        )
        print(new_course.get('_adaptation_tecnic', {}).get('techniques_substituted', 0))
        total_subs += new_course.get('_adaptation_tecnic', {}).get('techniques_substituted', 0)
        new_courses[course_name] = new_course
    adapted_solution['total_tecnic_substitutions'] = total_subs
    adapted_solution['menu']['courses'] = new_courses    
    return adapted_solution
    
if __name__ == "__main__":
    prev_adapted_solution = {'adapted': True, 'restrictions_adapted': [], 'culture_adapted': 'china', 'total_substitutions': 0, 'total_removed': 0, 'menu': {'menu_id': 1, 'menu_name': 'Menu 1: Corn Salsa', 'description': 'Complete menu featuring Corn Salsa as main course', 'courses': {'starter': {'recipe_id': 640062, 'title': 'Corn Avocado Salsa', 'servings': 2, 'price_per_serving': 130.73, 'ready_in_minutes': 0, 'ingredients': ['avocado', 'balsamic vinegar', 'cumin', 'corn', 'garlic', 'bell pepper'], 'restrictions': ['vegan', 'gluten free', 'vegetarian', 'dairy free'], 'instructions': '<ol><li>Preheat oven to 375 degrees.</li><li>Spread corn flat on a baking sheet.</li><li>Spray lightly with olive oil spray.</li><li>Roast corn in the oven for about 8-10 minutes. (Be careful not to brown too much or burn.)</li><li>Remove from heat and allow to cool.</li><li>Finely chop red pepper and garlic and mix in a bowl.</li><li>Peel and coarsely chop avocado and add to bowl.</li><li>Add cooled corn.</li><li>Mix in cumin and vinegar and blend well.</li></ol>', 'structured_instructions': [{'order': 1, 'preparation_action': 'preheat', 'where': [], 'ingredients': [], 'tools': [], 'temperature': '375 degrees', 'time': None}, {'order': 2, 'preparation_action': 'spread', 'where': ['baking sheet'], 'ingredients': ['corn'], 'tools': [], 'temperature': None, 'time': None}, {'order': 3, 'preparation_action': 'spray', 'where': [], 'ingredients': [], 'tools': ['olive oil spray'], 'temperature': None, 'time': None}, {'order': 4, 'preparation_action': 'roast', 'where': ['oven'], 'ingredients': ['corn'], 'tools': [], 'temperature': None, 'time': '8-10 minutes'}, {'order': 5, 'preparation_action': 'remove', 'where': [], 'ingredients': [], 'tools': [], 'temperature': None, 'time': None}, {'order': 6, 'preparation_action': 'allow', 'where': [], 'ingredients': [], 'tools': [], 'temperature': None, 'time': None}, {'order': 7, 'preparation_action': 'chop', 'where': [], 'ingredients': ['red pepper', 'garlic'], 'tools': [], 'temperature': None, 'time': None}, {'order': 8, 'preparation_action': 'peel', 'where': [], 'ingredients': ['avocado'], 'tools': [], 'temperature': None, 'time': None}, {'order': 9, 'preparation_action': 'chop', 'where': [], 'ingredients': ['avocado'], 'tools': [], 'temperature': None, 'time': None}, {'order': 10, 'preparation_action': 'add', 'where': [], 'ingredients': ['corn'], 'tools': [], 'temperature': None, 'time': None}, {'order': 11, 'preparation_action': 'mix', 'where': ['bowl'], 'ingredients': [], 'tools': [], 'temperature': None, 'time': None}, {'order': 12, 'preparation_action': 'add', 'where': [], 'ingredients': ['cumin', 'vinegar'], 'tools': [], 'temperature': None, 'time': None}, {'order': 13, 'preparation_action': 'blend', 'where': [], 'ingredients': [], 'tools': [], 'temperature': None, 'time': None}], '_adaptation': {'substitutions': [], 'original_ingredients': ['avocado', 'balsamic vinegar', 'cumin', 'corn', 'garlic', 'bell pepper'], 'ingredients_substituted': 0, 'ingredients_removed': 0, 'ingredients_kept': 0, 'removed_ingredients': []}}, 'main': {'recipe_id': 640104, 'title': 'Corn Salsa', 'servings': 4, 'price_per_serving': 150.92, 'ready_in_minutes': 0, 'ingredients': ['bell pepper', 'celery', 'ears of corn - boil and from the cob', 'basil', 'garlic', 'jalapeño', 'onion', 'salt', 'sugar', 'pickle', 'vine tomato', 'vinegar'], 'restrictions': ['vegan', 'gluten free', 'vegetarian', 'dairy free'], 'instructions': '<ol><li>Combine all of the above ingredients in a bowl.</li><li>Combine the ingredients for the dressing and add to the salsa.</li><li>Serve chilled.</li></ol>', 'structured_instructions': [{'order': 1, 'preparation_action': 'combine', 'where': ['bowl'], 'ingredients': ['bell pepper', 'celery', 'ears of corn', 'basil', 'garlic', 'jalapeño', 'onion', 'salt', 'sugar', 'pickle', 'vine tomato'], 'tools': ['bowl'], 'temperature': None, 'time': None}, {'order': 2, 'preparation_action': 'combine', 'where': [], 'ingredients': ['vinegar', 'salsa'], 'tools': [], 'temperature': None, 'time': None}, {'order': 3, 'preparation_action': 'serve', 'where': [], 'ingredients': [], 'tools': [], 'temperature': 'chilled', 'time': None}], '_adaptation': {'substitutions': [], 'original_ingredients': ['bell pepper', 'celery', 'ears of corn - boil and from the cob', 'basil', 'garlic', 'jalapeño', 'onion', 'salt', 'sugar', 'pickle', 'vine tomato', 'vinegar'], 'ingredients_substituted': 0, 'ingredients_removed': 0, 'ingredients_kept': 0, 'removed_ingredients': []}}, 'dessert': {'recipe_id': 655202, 'title': 'Peanut Brittle', 'servings': 4, 'price_per_serving': 107.1, 'ready_in_minutes': 0, 'ingredients': ['butter', 'soda', 'coconut', 'corn syrup', 'peanuts', 'salt', 'sugar', 'water'], 'restrictions': ['gluten free', 'vegetarian'], 'instructions': '<ol><li>Pour sugar, corn syrup and water into saucepan. Cook, stirring only until sugar is dissolved. Continue cooking until sugar begins to turn light brown (300 degrees) by candy thermometer. Remove from heat. Add salt, soda, butter and stir as little as possible, only to mix well. Stir in peanuts and coconut.Spread on a greased sheet of waxed paper set on top of a baking sheet and let the mixture cool and harden.</li></ol>', 'structured_instructions': [{'order': 1, 'preparation_action': 'pour', 'where': ['saucepan'], 'ingredients': ['sugar', 'corn syrup', 'water'], 'tools': [], 'temperature': None, 'time': None}, {'order': 2, 'preparation_action': 'cook', 'where': ['saucepan'], 'ingredients': ['sugar', 'corn syrup', 'water'], 'tools': ['candy thermometer'], 'temperature': '300 degrees', 'time': None}, {'order': 3, 'preparation_action': 'remove', 'where': ['saucepan'], 'ingredients': [], 'tools': [], 'temperature': None, 'time': None}, {'order': 4, 'preparation_action': 'add', 'where': ['saucepan'], 'ingredients': ['salt', 'soda', 'butter'], 'tools': [], 'temperature': None, 'time': None}, {'order': 5, 'preparation_action': 'stir', 'where': ['saucepan'], 'ingredients': ['salt', 'soda', 'butter'], 'tools': [], 'temperature': None, 'time': None}, {'order': 6, 'preparation_action': 'stir', 'where': ['saucepan'], 'ingredients': ['peanuts', 'coconut'], 'tools': [], 'temperature': None, 'time': None}, {'order': 7, 'preparation_action': 'spread', 'where': ['baking sheet'], 'ingredients': [], 'tools': [], 'temperature': None, 'time': None}, {'order': 8, 'preparation_action': 'let', 'where': [], 'ingredients': [], 'tools': [], 'temperature': None, 'time': 'cool and harden'}], '_adaptation': {'substitutions': [], 'original_ingredients': ['butter', 'soda', 'coconut', 'corn syrup', 'peanuts', 'salt', 'sugar', 'water'], 'ingredients_substituted': 0, 'ingredients_removed': 0, 'ingredients_kept': 0, 'removed_ingredients': []}}}, 'features': {'total_price_per_serving': 388.75, 'price_category': 'moderate', 'avg_ready_time_minutes': 0, 'time_category': 'quick', 'season': 'Summer', 'wine_pairing': ' No wine pairing', 'is_kosher': True, 'is_halal': True, 'common_dietary_restrictions': ['vegetarian', 'gluten free'], 'is_vegetarian': True, 'is_vegan': False, 'is_gluten_free': True, 'is_dairy_free': False, 'cultura': 'American', 'estilo_cocina': 'Tradicional'}, 'similarity_features': {'total_ingredients_count': 22, 'complexity_score': 52.0, 'health_factor': 61.7, 'cuisine_diversity': 0}}}
    # prev_adapted_solution seria el output de la adaptacion por ingredientes y cultura
    adapted_menu = adapt_menu_tecniques(prev_adapted_solution)   
    print("\nAdapted Menu with Technique Adaptations:")
    print(json.dumps(adapted_menu, indent=2)) 
            