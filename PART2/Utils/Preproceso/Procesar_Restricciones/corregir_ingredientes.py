"""
Script para corregir errores en ingredientes_restricciones.json
================================================================
Aplica reglas lógicas para corregir clasificaciones incorrectas
basándose en el tipo de ingrediente.
"""

import json
import os
import re
from typing import Dict, List, Set

# Rutas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..', '..')
INPUT_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ingredientes_restricciones.json')
OUTPUT_FILE = INPUT_FILE  # Sobrescribir el original
BACKUP_FILE = INPUT_FILE.replace('.json', '_backup.json')

# ============================================================================
# REGLAS DE CLASIFICACIÓN
# ============================================================================

# Palabras clave para identificar ingredientes NO VEGANOS
NON_VEGAN_KEYWORDS = [
    # Lácteos
    'butter', 'milk', 'cream', 'cheese', 'yogurt', 'yoghurt', 'whey', 'casein',
    'lactose', 'ghee', 'paneer', 'ricotta', 'mozzarella', 'parmesan', 'cheddar',
    'brie', 'feta', 'gouda', 'gruyere', 'mascarpone', 'cottage', 'sour cream',
    'buttermilk', 'half and half', 'heavy cream', 'whipped cream', 'ice cream',
    'custard', 'pudding', 'dairy', 'lait', 'fromage', 'queso',
    # Huevos
    'egg', 'yolk', 'albumin', 'meringue', 'mayonnaise', 'mayo',
    # Miel
    'honey', 'royal jelly', 'beeswax', 'propolis',
    # Carne y pescado (ya deberían estar, pero por si acaso)
    'meat', 'beef', 'pork', 'chicken', 'turkey', 'duck', 'lamb', 'veal',
    'bacon', 'ham', 'sausage', 'salami', 'prosciutto', 'pepperoni',
    'fish', 'salmon', 'tuna', 'cod', 'shrimp', 'lobster', 'crab', 'oyster',
    'clam', 'mussel', 'scallop', 'anchovy', 'sardine', 'caviar',
    'gelatin', 'lard', 'tallow', 'suet',
    # Otros productos animales
    'bone broth', 'fish sauce', 'oyster sauce', 'worcestershire',
]

# Excepciones - ingredientes que contienen palabras clave pero SÍ son veganos
VEGAN_EXCEPTIONS = [
    'coconut milk', 'coconut cream', 'coconut butter', 'coconut yogurt',
    'almond milk', 'oat milk', 'soy milk', 'rice milk', 'cashew milk',
    'hemp milk', 'flax milk', 'pea milk', 'hazelnut milk',
    'vegan butter', 'vegan cheese', 'vegan cream', 'vegan mayo',
    'vegan yogurt', 'vegan milk', 'vegan egg', 'vegan honey',
    'nut butter', 'peanut butter', 'almond butter', 'cashew butter',
    'sunflower butter', 'tahini butter', 'cocoa butter', 'shea butter',
    'apple butter', 'pumpkin butter',
    'butter bean', 'butter lettuce', 'butternut', 'buttercup squash',
    'eggplant', 'egg noodle',  # egg noodle puede ser vegano o no, lo dejamos
    'plant milk', 'dairy free', 'non dairy',
    'earth balance', 'daiya', 'follow your heart', 'miyoko',
    'nutritional yeast', 'nooch',
    'aquafaba',  # sustituto de huevo
    'flax egg', 'chia egg',
    'olive oil',  # aceite de oliva es vegano
    'vegetable oil', 'canola oil', 'sunflower oil', 'sesame oil',
    'agave', 'maple syrup', 'date syrup', 'molasses',  # alternativas a miel
]

# Palabras clave para ingredientes NO VEGETARIANOS
NON_VEGETARIAN_KEYWORDS = [
    'meat', 'beef', 'pork', 'chicken', 'turkey', 'duck', 'lamb', 'veal',
    'bacon', 'ham', 'sausage', 'salami', 'prosciutto', 'pepperoni',
    'fish', 'salmon', 'tuna', 'cod', 'anchovy', 'sardine',
    'shrimp', 'lobster', 'crab', 'oyster', 'clam', 'mussel', 'scallop',
    'gelatin', 'lard', 'tallow', 'suet', 'bone broth',
    'rennet',  # cuajo animal
    'caviar', 'roe',
]

VEGETARIAN_EXCEPTIONS = [
    'vegetarian', 'plant based', 'meatless', 'beyond', 'impossible',
    'soy bacon', 'tempeh bacon', 'coconut bacon',
    'veggie sausage', 'plant sausage',
    'jackfruit',  # usado como sustituto de carne
]

# Palabras clave para ingredientes con GLUTEN
GLUTEN_KEYWORDS = [
    'wheat', 'barley', 'rye', 'spelt', 'kamut', 'triticale', 'farro',
    'semolina', 'durum', 'bulgur', 'couscous', 'seitan',
    'bread', 'flour', 'pasta', 'noodle', 'spaghetti', 'macaroni', 'penne',
    'cracker', 'cookie', 'cake', 'pastry', 'croissant', 'bagel', 'muffin',
    'pizza dough', 'pie crust', 'tortilla',  # tortilla de trigo
    'beer', 'ale', 'lager', 'malt',
    'soy sauce',  # contiene trigo normalmente
    'panko', 'breadcrumb',
]

GLUTEN_FREE_EXCEPTIONS = [
    'gluten free', 'gf ', 'rice flour', 'almond flour', 'coconut flour',
    'oat flour', 'buckwheat', 'quinoa', 'corn flour', 'cornmeal',
    'tapioca', 'arrowroot', 'potato starch', 'rice noodle', 'rice pasta',
    'corn tortilla', 'tamari',  # soy sauce sin gluten
    'rice bread', 'gluten-free bread',
]

# Palabras clave para ingredientes con LÁCTEOS
DAIRY_KEYWORDS = [
    'milk', 'cream', 'butter', 'cheese', 'yogurt', 'yoghurt',
    'whey', 'casein', 'lactose', 'ghee', 'kefir',
    'ice cream', 'custard', 'pudding',
    'half and half', 'sour cream', 'buttermilk',
    'ricotta', 'mozzarella', 'parmesan', 'cheddar', 'brie', 'feta',
    'cottage cheese', 'cream cheese', 'mascarpone',
]

DAIRY_FREE_EXCEPTIONS = [
    'coconut milk', 'coconut cream', 'coconut butter', 'coconut yogurt',
    'almond milk', 'oat milk', 'soy milk', 'rice milk', 'cashew milk',
    'vegan butter', 'vegan cheese', 'vegan cream', 'dairy free',
    'non dairy', 'plant milk', 'nut milk',
    'butter bean', 'butter lettuce', 'butternut', 'buttercup',
    'peanut butter', 'almond butter', 'nut butter', 'cocoa butter',
    'apple butter', 'olive oil',
]

# Palabras clave para MARISCOS (shellfish)
SHELLFISH_KEYWORDS = [
    'shrimp', 'prawn', 'lobster', 'crab', 'crawfish', 'crayfish',
    'oyster', 'clam', 'mussel', 'scallop', 'squid', 'calamari',
    'octopus', 'snail', 'escargot', 'abalone', 'conch',
]

# Palabras clave para SOJA
SOY_KEYWORDS = [
    'soy', 'soya', 'tofu', 'tempeh', 'edamame', 'miso',
    'soy sauce', 'tamari', 'soy milk', 'soy protein',
]

SOY_FREE_EXCEPTIONS = [
    'soy free', 'coconut aminos',
]

# Palabras clave para FRUTOS SECOS
NUT_KEYWORDS = [
    'almond', 'cashew', 'walnut', 'pecan', 'pistachio', 'hazelnut',
    'macadamia', 'brazil nut', 'chestnut', 'pine nut', 'pinenut',
    'nut butter', 'nut milk', 'mixed nuts', 'praline',
    'marzipan', 'frangipane', 'nougat',
]

NUT_FREE_EXCEPTIONS = [
    'nut free', 'coconut',  # coconut no es un tree nut
    'nutmeg',  # no es un fruto seco
    'butternut', 'water chestnut', 'tiger nut',
    'peanut',  # peanut es legumbre, no tree nut (aunque algunas personas lo incluyen)
]


def matches_keywords(ingredient: str, keywords: List[str], exceptions: List[str] = None) -> bool:
    """
    Verifica si un ingrediente coincide con alguna palabra clave,
    teniendo en cuenta las excepciones.
    """
    ing_lower = ingredient.lower()
    
    # Primero verificar excepciones
    if exceptions:
        for exc in exceptions:
            if exc.lower() in ing_lower:
                return False
    
    # Luego verificar palabras clave
    for keyword in keywords:
        # Buscar como palabra completa o parte de palabra compuesta
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, ing_lower):
            return True
        # También buscar sin word boundary para casos como "buttermilk"
        if keyword.lower() in ing_lower:
            return True
    
    return False


def correct_ingredient_restrictions(ingredient_data: Dict) -> Dict:
    """
    Corrige las restricciones de un ingrediente basándose en reglas lógicas.
    """
    canonical_name = ingredient_data.get('canonical_name', '')
    raw_forms = ingredient_data.get('raw_forms', [])
    
    # Combinar todas las formas del nombre para análisis
    all_names = [canonical_name] + raw_forms
    name_combined = ' '.join(all_names).lower()
    
    restrictions = ingredient_data.get('restrictions', {})
    
    # Hacer una copia para modificar
    new_restrictions = restrictions.copy()
    
    # 1. Verificar VEGAN
    is_non_vegan = matches_keywords(name_combined, NON_VEGAN_KEYWORDS, VEGAN_EXCEPTIONS)
    if is_non_vegan and new_restrictions.get('vegan') == 'TRUE':
        new_restrictions['vegan'] = 'FALSE'
    
    # 2. Verificar VEGETARIAN
    is_non_vegetarian = matches_keywords(name_combined, NON_VEGETARIAN_KEYWORDS, VEGETARIAN_EXCEPTIONS)
    if is_non_vegetarian and new_restrictions.get('vegetarian') == 'TRUE':
        new_restrictions['vegetarian'] = 'FALSE'
    
    # 3. Verificar GLUTEN_FREE
    has_gluten = matches_keywords(name_combined, GLUTEN_KEYWORDS, GLUTEN_FREE_EXCEPTIONS)
    if has_gluten and new_restrictions.get('gluten_free') == 'TRUE':
        new_restrictions['gluten_free'] = 'FALSE'
    
    # 4. Verificar DAIRY_FREE
    has_dairy = matches_keywords(name_combined, DAIRY_KEYWORDS, DAIRY_FREE_EXCEPTIONS)
    if has_dairy and new_restrictions.get('dairy_free') == 'TRUE':
        new_restrictions['dairy_free'] = 'FALSE'
    
    # 5. Verificar SHELLFISH_FREE
    has_shellfish = matches_keywords(name_combined, SHELLFISH_KEYWORDS)
    if has_shellfish and new_restrictions.get('shellfish_free') == 'TRUE':
        new_restrictions['shellfish_free'] = 'FALSE'
    
    # 6. Verificar SOY_FREE
    has_soy = matches_keywords(name_combined, SOY_KEYWORDS, SOY_FREE_EXCEPTIONS)
    if has_soy and new_restrictions.get('soy_free') == 'TRUE':
        new_restrictions['soy_free'] = 'FALSE'
    
    # 7. Verificar NUT_FREE
    has_nuts = matches_keywords(name_combined, NUT_KEYWORDS, NUT_FREE_EXCEPTIONS)
    if has_nuts and new_restrictions.get('nut_free') == 'TRUE':
        new_restrictions['nut_free'] = 'FALSE'
    
    # Reglas de consistencia:
    # Si no es vegetarian, tampoco puede ser vegan
    if new_restrictions.get('vegetarian') == 'FALSE':
        if new_restrictions.get('vegan') == 'TRUE':
            new_restrictions['vegan'] = 'FALSE'
    
    # Si no es dairy_free, no puede ser vegan
    if new_restrictions.get('dairy_free') == 'FALSE':
        if new_restrictions.get('vegan') == 'TRUE':
            new_restrictions['vegan'] = 'FALSE'
    
    ingredient_data['restrictions'] = new_restrictions
    return ingredient_data


def analyze_changes(original: Dict, corrected: Dict) -> List[Dict]:
    """Analiza los cambios realizados."""
    changes = []
    
    orig_restrictions = original.get('restrictions', {})
    corr_restrictions = corrected.get('restrictions', {})
    
    for key in orig_restrictions:
        if orig_restrictions[key] != corr_restrictions.get(key):
            changes.append({
                'ingredient': original.get('canonical_name'),
                'restriction': key,
                'before': orig_restrictions[key],
                'after': corr_restrictions.get(key)
            })
    
    return changes


def main():
    """Función principal."""
    print("="*70)
    print("🔧 CORRECCIÓN DE INGREDIENTES_RESTRICCIONES.JSON")
    print("="*70 + "\n")
    
    # Cargar archivo
    print("📂 Cargando archivo original...")
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: No se encontró {INPUT_FILE}")
        return
    
    ingredients = data.get('ingredients', {})
    print(f"✅ Cargados {len(ingredients)} ingredientes\n")
    
    # Crear backup
    print("💾 Creando backup...")
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Backup guardado en {BACKUP_FILE}\n")
    
    # Procesar cada ingrediente
    print("🔄 Analizando y corrigiendo ingredientes...")
    
    all_changes = []
    corrected_ingredients = {}
    
    for ing_id, ing_data in ingredients.items():
        original_data = json.loads(json.dumps(ing_data))  # Deep copy
        corrected_data = correct_ingredient_restrictions(ing_data)
        
        changes = analyze_changes(original_data, corrected_data)
        all_changes.extend(changes)
        
        corrected_ingredients[ing_id] = corrected_data
    
    # Actualizar datos
    data['ingredients'] = corrected_ingredients
    
    # Resumen de cambios
    print(f"\n📊 RESUMEN DE CORRECCIONES")
    print("="*70)
    print(f"Total de cambios realizados: {len(all_changes)}")
    
    # Agrupar por tipo de restricción
    changes_by_restriction = {}
    for change in all_changes:
        rest = change['restriction']
        if rest not in changes_by_restriction:
            changes_by_restriction[rest] = []
        changes_by_restriction[rest].append(change)
    
    print("\nCambios por restricción:")
    for rest, changes in sorted(changes_by_restriction.items()):
        true_to_false = len([c for c in changes if c['before'] == 'TRUE' and c['after'] == 'FALSE'])
        false_to_true = len([c for c in changes if c['before'] == 'FALSE' and c['after'] == 'TRUE'])
        print(f"  • {rest}: {len(changes)} cambios (TRUE→FALSE: {true_to_false}, FALSE→TRUE: {false_to_true})")
    
    # Mostrar ejemplos de cambios
    print("\n📝 Ejemplos de correcciones:")
    shown = set()
    for change in all_changes[:30]:
        ing = change['ingredient']
        if ing not in shown:
            print(f"  • {ing}: {change['restriction']} {change['before']} → {change['after']}")
            shown.add(ing)
    
    if len(all_changes) > 30:
        print(f"  ... y {len(all_changes) - 30} más")
    
    # Guardar archivo corregido
    print(f"\n💾 Guardando archivo corregido...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Archivo guardado: {OUTPUT_FILE}")
    
    # Regenerar archivo derivado
    print("\n🔄 Regenerando ingredientes_por_restriccion.json...")
    import subprocess
    result = subprocess.run(
        ['python', 'clasificar_ingredientes_por_restriccion.py'],
        cwd=os.path.join(BASE_DIR, 'Utils', 'Preproceso'),
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ Archivo derivado regenerado correctamente")
    else:
        print(f"⚠️ Error al regenerar: {result.stderr}")
    
    print("\n" + "="*70)
    print("✅ ¡CORRECCIÓN COMPLETADA!")
    print("="*70)


if __name__ == "__main__":
    main()
