"""
Script para clasificar ingredientes por restricción alimentaria
================================================================
Genera una base de datos similar a ingredientes_por_contexto.json
pero organizada por restricciones alimentarias.

Restricciones posibles:
- gluten-free
- vegetarian
- vegan
- dairy-free
- kosher
- halal
- shellfish-free
- soy-free
- nut-free
"""

import json
import os
from collections import defaultdict

# Rutas de archivos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..', '..')
INPUT_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ingredientes_restricciones.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'Bases_Conocimientos', 'ingredientes_por_restriccion.json')


def load_ingredients_data(filepath):
    """Carga el archivo de ingredientes con restricciones."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('ingredients', {})
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo {filepath}")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Error: El archivo {filepath} no es un JSON válido")
        return {}


def classify_by_restriction(ingredients_data):
    """
    Clasifica los ingredientes por restricción alimentaria.
    
    Args:
        ingredients_data (dict): Diccionario con todos los ingredientes
        
    Returns:
        dict: Diccionario organizado por restricción
    """
    # Mapeo de claves internas a nombres de restricción
    restriction_mapping = {
        'gluten_free': 'gluten-free',
        'vegetarian': 'vegetarian',
        'vegan': 'vegan',
        'dairy_free': 'dairy-free',
        'kosher': 'kosher',
        'halal': 'halal',
        'shellfish_free': 'shellfish-free',
        'soy_free': 'soy-free',
        'nut_free': 'nut-free'
    }
    
    # Estructura de salida
    result = {}
    
    for restriction_key, restriction_name in restriction_mapping.items():
        result[restriction_name] = {
            "restriction": restriction_name,
            "description": get_restriction_description(restriction_name),
            "total_ingredients": 0,
            "ingredients_allowed": [],      # TRUE - pueden consumir
            "ingredients_forbidden": [],    # FALSE - no pueden consumir
            "ingredients_unknown": []       # UNKNOWN - verificar
        }
    
    # Procesar cada ingrediente
    for ingredient_id, ingredient_data in ingredients_data.items():
        restrictions = ingredient_data.get('restrictions', {})
        canonical_name = ingredient_data.get('canonical_name', ingredient_id)
        
        for restriction_key, restriction_name in restriction_mapping.items():
            value = restrictions.get(restriction_key, 'UNKNOWN').upper()
            
            if value == 'TRUE':
                result[restriction_name]['ingredients_allowed'].append(canonical_name)
            elif value == 'FALSE':
                result[restriction_name]['ingredients_forbidden'].append(canonical_name)
            else:
                result[restriction_name]['ingredients_unknown'].append(canonical_name)
    
    # Ordenar listas y calcular totales
    for restriction_name in result:
        # Eliminar duplicados y asegurar consistencia
        allowed_set = set(result[restriction_name]['ingredients_allowed'])
        forbidden_set = set(result[restriction_name]['ingredients_forbidden'])
        unknown_set = set(result[restriction_name]['ingredients_unknown'])
        
        # Si un ingrediente está tanto en allowed como en forbidden, 
        # priorizar allowed (es más probable que sea correcto)
        forbidden_set -= allowed_set
        unknown_set -= allowed_set
        unknown_set -= forbidden_set
        
        result[restriction_name]['ingredients_allowed'] = sorted(list(allowed_set))
        result[restriction_name]['ingredients_forbidden'] = sorted(list(forbidden_set))
        result[restriction_name]['ingredients_unknown'] = sorted(list(unknown_set))
        
        result[restriction_name]['total_ingredients'] = len(result[restriction_name]['ingredients_allowed'])
        result[restriction_name]['total_forbidden'] = len(result[restriction_name]['ingredients_forbidden'])
        result[restriction_name]['total_unknown'] = len(result[restriction_name]['ingredients_unknown'])
    
    return result


def get_restriction_description(restriction_name):
    """Devuelve una descripción de cada restricción alimentaria."""
    descriptions = {
        'gluten-free': 'Ingredientes aptos para personas con celiaquía o sensibilidad al gluten. No contienen trigo, cebada, centeno ni sus derivados.',
        'vegetarian': 'Ingredientes aptos para vegetarianos. No contienen carne ni pescado, pero pueden incluir lácteos y huevos.',
        'vegan': 'Ingredientes aptos para veganos. No contienen ningún producto de origen animal.',
        'dairy-free': 'Ingredientes sin lácteos. Aptos para personas con intolerancia a la lactosa o alergia a la proteína de la leche.',
        'kosher': 'Ingredientes que cumplen con las leyes dietéticas judías (kashrut).',
        'halal': 'Ingredientes que cumplen con las leyes dietéticas islámicas.',
        'shellfish-free': 'Ingredientes sin mariscos. Aptos para personas con alergia a crustáceos y moluscos.',
        'soy-free': 'Ingredientes sin soja. Aptos para personas con alergia a la soja.',
        'nut-free': 'Ingredientes sin frutos secos. Aptos para personas con alergia a los frutos secos.'
    }
    return descriptions.get(restriction_name, '')


def generate_summary_report(result):
    """Genera un resumen estadístico de la clasificación."""
    print("\n" + "="*70)
    print("📊 RESUMEN DE CLASIFICACIÓN POR RESTRICCIÓN ALIMENTARIA")
    print("="*70 + "\n")
    
    for restriction_name, data in result.items():
        total_allowed = data['total_ingredients']
        total_forbidden = data['total_forbidden']
        total_unknown = data['total_unknown']
        total = total_allowed + total_forbidden + total_unknown
        
        pct_allowed = (total_allowed / total * 100) if total > 0 else 0
        
        print(f"🏷️  {restriction_name.upper()}")
        print(f"   ✅ Permitidos: {total_allowed} ({pct_allowed:.1f}%)")
        print(f"   ❌ Prohibidos: {total_forbidden}")
        print(f"   ❓ Desconocidos: {total_unknown}")
        print()
    
    print("="*70 + "\n")


def save_output(result, filepath):
    """Guarda el resultado en un archivo JSON."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ Archivo guardado en: {filepath}")


def create_compact_version(result):
    """
    Crea una versión compacta similar a ingredientes_por_contexto.json
    Solo incluye los ingredientes permitidos por cada restricción.
    """
    compact = {}
    
    for restriction_name, data in result.items():
        compact[restriction_name] = {
            "restriction": restriction_name,
            "description": data['description'],
            "ingredients": data['ingredients_allowed']
        }
    
    return compact


def main():
    """Función principal."""
    print("\n🔄 Cargando archivo de ingredientes...")
    ingredients_data = load_ingredients_data(INPUT_FILE)
    
    if not ingredients_data:
        print("❌ No se pudo cargar el archivo de ingredientes.")
        return
    
    print(f"✅ Se cargaron {len(ingredients_data)} ingredientes.\n")
    
    print("🔄 Clasificando ingredientes por restricción alimentaria...")
    result = classify_by_restriction(ingredients_data)
    
    # Mostrar resumen
    generate_summary_report(result)
    
    # Guardar versión completa
    save_output(result, OUTPUT_FILE)
    
    # Guardar versión compacta (similar a ingredientes_por_contexto.json)
    compact_output = OUTPUT_FILE.replace('.json', '_compacto.json')
    compact_result = create_compact_version(result)
    save_output(compact_result, compact_output)
    
    print("\n✅ ¡Proceso completado exitosamente!")
    print(f"   📁 Versión completa: {OUTPUT_FILE}")
    print(f"   📁 Versión compacta: {compact_output}")


if __name__ == "__main__":
    main()
