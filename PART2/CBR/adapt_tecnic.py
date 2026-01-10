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

def load_knowledge_base(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)¡
    return data

def adapt_course(course: dict, target_culture: str, cult_tecnic_knowledge: dict, tecnic_sust_knowledge: dict) -> dict:
    adapted_course = deepcopy(course)
    print(adapted_course)
    
    return adapted_course

def adapt_menu_tecniques(user_input: dict, prev_adapted_solution: dict) -> dict:
    cult_tecnic_knowledge = load_knowledge_base(CULT_TECNIC_PATH)
    tecnic_sust_knowledge = load_knowledge_base(TECNIC_SUST_PATH)

    taget_culture = user_input.get("culture", "").strip()
    adapted_solution = deepcopy(prev_adapted_solution)
    menu = adapted_solution.get("menu", {})
    courses = menu.get("courses", {})

    # Adaptar cada plato
    adapted_courses = {}
    total_substitutions = 0
    total_removed = 0
    
    for course_name, course_data in courses.items():
        adapted_course = adapt_course(
            course_data,
            taget_culture, 
            cult_tecnic_knowledge,
            tecnic_sust_knowledge
        )
        adapted_courses[course_name] = adapted_course
        adaptation_info = adapted_course.get('_adaptation', {})
        total_substitutions += adaptation_info.get('ingredients_substituted', 0)
        total_removed += adaptation_info.get('ingredients_removed', 0)
    adapted_solution['menu']['courses'] = adapted_courses

    return adapted_solution
    
    if __name__ == "__main__":
        # Ejemplo de uso
        user_input = {
            "culture": "Mediterránea"
        }
        prev_adapted_solution = {
            "menu": {
                "courses": {
                    "starter": {
                        "title": "Bruschetta",
                        "ingredients": ["bread", "tomato", "basil", "garlic", "olive oil"]
                    },
                    "main": {
                        "title": "Chicken Parmesan",
                        "ingredients": ["chicken breast", "parmesan cheese", "tomato sauce", "mozzarella cheese"]
                    },
                    "dessert": {
                        "title": "Tiramisu",
                        "ingredients": ["mascarpone cheese", "coffee", "ladyfingers", "cocoa powder"]
                    }
                }
            }
        }
        adapted_menu = adapt_menu_tecniques(user_input, prev_adapted_solution)
        print(json.dumps(adapted_menu, indent=2, ensure_ascii=False))