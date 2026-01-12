"""
Módulo de Revisión (Revise)
============================
Fase REVISE del ciclo CBR:
1. Validación interna de restricciones
2. Interacción con usuario para feedback y ajustes
"""

import json
import os
from typing import Dict, List, Tuple, Optional, Any

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..')
RESTRICCIONES_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ingredientes_por_restriccion.json')


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def load_restricciones_db() -> dict:
    """Carga la base de datos de restricciones."""
    try:
        with open(RESTRICCIONES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def normalize_restriction(restriction: str) -> str:
    """Normaliza el nombre de una restricción."""
    return restriction.lower().replace('-', '_').replace(' ', '_').strip()


def normalize_ingredient(ingredient: str) -> str:
    """Normaliza el nombre de un ingrediente."""
    return ingredient.lower().replace('-', ' ').strip()


# ============================================================================
# VALIDACIÓN INTERNA DE RESTRICCIONES
# ============================================================================

def validate_dietary_restrictions(
    menu: Dict[str, Any],
    restrictions: List[str],
    restricciones_db: dict = None
) -> Tuple[bool, List[Dict]]:
    """
    Valida que el menú cumpla con las restricciones alimentarias.
    
    Usa ingredientes_por_restriccion.json que tiene estructura:
    {
        "vegan": {
            "ingredients_allowed": [...],
            "ingredients_forbidden": [...]
        },
        ...
    }
    """
    if restricciones_db is None:
        restricciones_db = load_restricciones_db()
    
    violations = []
    courses = menu.get('courses', {})
    
    for restriction in restrictions:
        # Normalizar clave de restricción
        rest_key = restriction.lower().replace('_', '-').strip()
        rest_data = restricciones_db.get(rest_key, {})
        
        if not rest_data:
            # Intentar con formato alternativo
            rest_key_alt = restriction.lower().replace('-', '_').strip()
            rest_data = restricciones_db.get(rest_key_alt, {})
        
        if not rest_data:
            continue
        
        # Obtener ingredientes prohibidos
        forbidden = set(
            normalize_ingredient(i) 
            for i in rest_data.get('ingredients_forbidden', [])
        )
        
        # También verificar ingredientes permitidos para doble check
        allowed = set(
            normalize_ingredient(i) 
            for i in rest_data.get('ingredients_allowed', [])
        )
        
        for course_name, course_data in courses.items():
            if not isinstance(course_data, dict):
                continue
            
            ingredients = course_data.get('ingredients', [])
            
            for ingredient in ingredients:
                ing_norm = normalize_ingredient(ingredient)
                
                # Verificar si está explícitamente prohibido
                is_forbidden = ing_norm in forbidden
                
                # Si no está en ninguna lista, buscar con matching parcial
                if not is_forbidden and ing_norm not in allowed:
                    for forb in forbidden:
                        # Matching por palabra clave principal
                        if forb == ing_norm or (len(ing_norm) > 3 and forb in ing_norm):
                            is_forbidden = True
                            break
                
                if is_forbidden:
                    violations.append({
                        'course': course_name,
                        'ingredient': ingredient,
                        'restriction': restriction,
                        'message': f"'{ingredient}' viola restricción '{restriction}'"
                    })
    
    is_valid = len(violations) == 0
    return is_valid, violations


def validate_culture_match(
    menu: Dict[str, Any],
    target_culture: str
) -> Tuple[float, List[str]]:
    """
    Evalúa qué tan bien el menú coincide con la cultura objetivo.
    
    Returns:
        Tuple[float, List[str]]: (score 0-1, ingredientes que no coinciden)
    """
    if not target_culture:
        return 1.0, []
    
    # Obtener cultura del menú desde features
    menu_culture = menu.get('features', {}).get('cultura', '')
    
    if not menu_culture:
        return 0.5, []  # Sin información
    
    target_norm = target_culture.lower()
    menu_norm = menu_culture.lower()
    
    # Match exacto o parcial
    if target_norm == menu_norm or target_norm in menu_norm or menu_norm in target_norm:
        return 1.0, []
    
    return 0.5, []  # Cultura diferente pero no es violación crítica


# ============================================================================
# INTERACCIÓN CON USUARIO
# ============================================================================

def get_user_feedback() -> Dict[str, Any]:
    """
    Solicita feedback del usuario sobre el menú propuesto.
    
    Returns:
        Dict con:
        - rating: puntuación global (0-10)
        - new_restrictions: nuevas restricciones a añadir
        - culture_adjustments: ajustes de cultura (+/- cultura)
        - needs_revision: True si hay cambios que requieren re-adaptación
    """
    print("\n" + "="*70)
    print("📝 FEEDBACK DEL USUARIO")
    print("="*70)
    
    result = {
        'rating': None,
        'new_restrictions': [],
        'culture_adjustments': [],
        'needs_revision': False
    }
    
    # 1. Puntuación global
    print("\n1. PUNTUACIÓN GLOBAL DEL MENÚ")
    print("   Escala: 0 (muy malo) - 10 (perfecto)")
    while True:
        try:
            rating_input = input("   → Puntuación (0-10): ").strip()
            if not rating_input:
                rating = 7.0  # Default
            else:
                rating = float(rating_input)
            if 0 <= rating <= 10:
                result['rating'] = rating / 10.0  # Normalizar a 0-1
                break
            print("   ⚠️ Por favor, ingrese un valor entre 0 y 10")
        except ValueError:
            print("   ⚠️ Por favor, ingrese un número válido")
    
    # 2. Restricciones adicionales
    print("\n2. RESTRICCIONES ALIMENTARIAS ADICIONALES")
    print("   Opciones: vegan, vegetarian, gluten-free, dairy-free,")
    print("             kosher, halal, nut-free, soy-free, shellfish-free")
    print("   (Presione Enter sin escribir nada para continuar)")
    
    while True:
        entry = input("   → Añadir restricción: ").strip().lower()
        if not entry:
            break
        if entry not in result['new_restrictions']:
            result['new_restrictions'].append(entry)
            result['needs_revision'] = True
            print(f"      ✅ Añadida: {entry}")
    
    # 3. Ajustes de cultura
    print("\n3. AJUSTES DE CULTURA GASTRONÓMICA")
    print("   Opciones: Italian, Chinese, Japanese, Korean, Latin American," \
              " South Asian, Mediterranean, French/Western European," \
              " Middle Eastern/North African, East Asian, American")
    print("   Use '+' para añadir ingredientes de esa cultura")
    print("   Use '-' para eliminar ingredientes de esa cultura")
    print("   Ejemplo: +italian  o  -chinese")
    print("   (Presione Enter sin escribir nada para continuar)")
    
    while True:
        entry = input("   → Ajuste (+/- cultura): ").strip().lower()
        if not entry:
            break
        
        if entry.startswith('+') and len(entry) > 1:
            culture = entry[1:].strip()
            result['culture_adjustments'].append({
                'action': 'add',
                'culture': culture
            })
            result['needs_revision'] = True
            print(f"      ✅ Añadir toques de: {culture}")
        elif entry.startswith('-') and len(entry) > 1:
            culture = entry[1:].strip()
            result['culture_adjustments'].append({
                'action': 'remove',
                'culture': culture
            })
            result['needs_revision'] = True
            print(f"      ✅ Reducir toques de: {culture}")
        else:
            print("      ⚠️ Formato inválido. Use +cultura o -cultura")
    
    # Resumen
    print("\n" + "-"*50)
    print("📊 RESUMEN DEL FEEDBACK:")
    print(f"   • Puntuación: {result['rating']*10:.1f}/10")
    if result['new_restrictions']:
        print(f"   • Nuevas restricciones: {', '.join(result['new_restrictions'])}")
    if result['culture_adjustments']:
        for adj in result['culture_adjustments']:
            symbol = '+' if adj['action'] == 'add' else '-'
            print(f"   • Cultura: {symbol}{adj['culture']}")
    if result['needs_revision']:
        print("   ⚠️ Se requiere nueva adaptación")
    print("-"*50)
    
    return result


# ============================================================================
# FUNCIÓN PRINCIPAL DE REVISE
# ============================================================================

def revise_menu(
    adapted_menu: Dict[str, Any],
    user_restrictions: List[str],
    user_culture: str = None,
    adaptation_steps: List[Dict] = None,
    interactive: bool = True
) -> Dict[str, Any]:
    """
    Fase REVISE: Valida el menú adaptado y obtiene feedback del usuario.
    
    Args:
        adapted_menu: Menú adaptado (con 'courses' y opcionalmente 'features')
        user_restrictions: Restricciones alimentarias del usuario
        user_culture: Cultura preferida del usuario
        adaptation_steps: Pasos de adaptación realizados
        interactive: Si True, solicita feedback del usuario
        
    Returns:
        Dict con resultados de la revisión
    """
    print("\n" + "="*70)
    print("🔍 FASE REVISE: Validación del Menú")
    print("="*70)
    
    if adaptation_steps is None:
        adaptation_steps = []
    
    # 1. Validación de restricciones alimentarias
    print("\n📋 Validando restricciones alimentarias...")
    is_valid, violations = validate_dietary_restrictions(
        adapted_menu, user_restrictions
    )
    
    if is_valid:
        print("   ✅ Todas las restricciones alimentarias cumplidas")
    else:
        print(f"   ❌ Se encontraron {len(violations)} violaciones:")
        for v in violations[:5]:  # Mostrar máximo 5
            print(f"      • {v['message']}")
    
    # 2. Validación de cultura
    print("\n📋 Validando coincidencia cultural...")
    culture_score, culture_issues = validate_culture_match(
        adapted_menu, user_culture
    )
    print(f"   Score cultural: {culture_score:.0%}")
    
    # 3. Calcular métricas
    constraint_satisfaction = 1.0 if is_valid else max(0, 1 - len(violations) * 0.1)
    
    result = {
        'is_valid': is_valid,
        'violations': violations,
        'constraint_satisfaction': constraint_satisfaction,
        'culture_score': culture_score,
        'adaptation_steps_count': len(adaptation_steps),
        'user_feedback': None,
        'new_restrictions': [],
        'culture_adjustments': [],
        'needs_revision': False
    }
    
    # 4. Feedback del usuario (si es interactivo)
    if interactive:
        feedback = get_user_feedback()
        result['user_feedback'] = feedback['rating']
        result['new_restrictions'] = feedback['new_restrictions']
        result['culture_adjustments'] = feedback['culture_adjustments']
        result['needs_revision'] = feedback['needs_revision']
    
    # 5. Calcular performance score
    if result['user_feedback'] is not None:
        # Combinación de validación interna y feedback
        result['performance'] = (
            constraint_satisfaction * 0.4 +
            culture_score * 0.2 +
            result['user_feedback'] * 0.4
        )
    else:
        result['performance'] = (
            constraint_satisfaction * 0.6 +
            culture_score * 0.4
        )
    
    print(f"\n🎯 Performance Score: {result['performance']:.2%}")
    
    return result


# ============================================================================
# VISUALIZACIÓN
# ============================================================================

def print_menu_summary(menu: Dict[str, Any]):
    """Muestra un resumen del menú para revisión del usuario."""
    print("\n" + "="*70)
    print("🍽️  MENÚ PROPUESTO")
    print("="*70)
    
    courses = menu.get('courses', {})
    
    for course_name, course_data in courses.items():
        if not isinstance(course_data, dict):
            continue
        
        title = course_data.get('title', course_name.upper())
        ingredients = course_data.get('ingredients', [])
        
        print(f"\n📍 {course_name.upper()}: {title}")
        print(f"   Ingredientes: {', '.join(ingredients[:8])}")
        if len(ingredients) > 8:
            print(f"                 ...y {len(ingredients)-8} más")
    
    features = menu.get('features', {})
    if features:
        print(f"\n📊 Características:")
        if features.get('cultura'):
            print(f"   • Cultura: {features['cultura']}")
        if features.get('season'):
            print(f"   • Temporada: {features['season']}")
    
    print("="*70)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test básico
    test_menu = {
        'courses': {
            'starter': {
                'title': 'Ensalada Mediterránea',
                'ingredients': ['tomato', 'olive oil', 'feta cheese', 'cucumber']
            },
            'main': {
                'title': 'Pasta Primavera',
                'ingredients': ['pasta', 'zucchini', 'bell pepper', 'garlic', 'basil']
            }
        },
        'features': {
            'cultura': 'Mediterranean'
        }
    }
    
    print_menu_summary(test_menu)
    
    result = revise_menu(
        adapted_menu=test_menu,
        user_restrictions=['vegan'],
        user_culture='italian',
        interactive=True
    )
    
    print(f"\n✅ Resultado: {result}")
