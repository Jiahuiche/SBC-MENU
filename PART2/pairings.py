import pandas as pd
import json
from collections import defaultdict

# --- CONFIGURACIÓN DE ARCHIVOS ---
FILE_INFO = 'food_info.csv'             # Tu diccionario de ingredientes
FILE_PAIRINGS = 'flavour_pairings.csv'   # Tu archivo de relaciones moleculares
OUTPUT_FILE = 'molecular_pairing_db.json'

# Categorías a excluir (Bebidas)
CATEGORIAS_IGNORADAS = {'beverage', 'beverage alcoholic'}

def generar_base_molecular():
    print("🔬 Iniciando proceso de Pairing Molecular...")

    # ---------------------------------------------------------
    # PASO 1: Crear el mapa ID -> Nombre (Filtrando bebidas)
    # ---------------------------------------------------------
    print(f"📚 Cargando mapa de IDs desde {FILE_INFO}...")
    
    # Cargamos solo las columnas necesarias
    try:
        df_info = pd.read_csv(FILE_INFO, usecols=['id', 'food_name', 'category'])
    except ValueError:
        # Por si las columnas tienen nombres ligeramente distintos (ej: mayúsculas)
        df_info = pd.read_csv(FILE_INFO)
    
    # Diccionario: id (int) -> nombre (str)
    id_to_name = {}
    bebidas_count = 0
    
    for _, row in df_info.iterrows():
        cat = str(row['category']).lower().strip()
        
        # Filtro de bebidas
        if cat in CATEGORIAS_IGNORADAS:
            bebidas_count += 1
            continue
            
        # Guardamos el ID y el nombre
        try:
            ing_id = int(row['id'])
            ing_name = str(row['food_name']).lower().strip()
            id_to_name[ing_id] = ing_name
        except ValueError:
            continue # Si hay algún ID corrupto

    print(f"✅ Mapa cargado. {len(id_to_name)} ingredientes válidos.")
    print(f"🚫 Se han ignorado {bebidas_count} bebidas.")

    # ---------------------------------------------------------
    # PASO 2: Cruzar con la tabla de Pairings
    # ---------------------------------------------------------
    print(f"⚗️  Procesando relaciones moleculares desde {FILE_PAIRINGS}...")
    
    try:
        df_pairs = pd.read_csv(FILE_PAIRINGS)
    except FileNotFoundError:
        print("❌ Error: No encuentro el archivo flavor_pairings.csv")
        return

    # Estructura final:
    # { "tomato": [ {"pair": "basil", "score": 15}, ... ] }
    pairing_db = defaultdict(list)
    count_relaciones = 0

    # Iteramos sobre el CSV de pairings
    # Asumimos columnas: entity1, entity2, overlapping_molecules
    for _, row in df_pairs.iterrows():
        try:
            id1 = int(row['entity1'])
            id2 = int(row['entity2'])
            score = int(row['overlapping_molecules']) # Número de moléculas compartidas
            
            # Verificamos si AMBOS ingredientes son válidos (existen y no son bebidas)
            name1 = id_to_name.get(id1)
            name2 = id_to_name.get(id2)
            
            if name1 and name2:
                # Añadimos la relación bidireccional
                # (FlavorDB suele traer solo una dirección, así que aseguramos ambas)
                pairing_db[name1].append({"pair": name2, "score": score})
                pairing_db[name2].append({"pair": name1, "score": score})
                count_relaciones += 1
                
        except (ValueError, KeyError):
            continue

    # ---------------------------------------------------------
    # PASO 3: Ordenar y Guardar
    # ---------------------------------------------------------
    print("💾 Ordenando y guardando resultados...")
    
    final_json = {}
    
    for main_ing, pairs in pairing_db.items():
        # Ordenamos: primero los que tienen MAS moléculas en común (mejor pairing)
        # Nota: A veces hay duplicados en el CSV original, los limpiamos con el set
        unique_pairs = {p['pair']: p for p in pairs}.values()
        sorted_pairs = sorted(list(unique_pairs), key=lambda x: x['score'], reverse=True)
        
        # Opcional: Quedarnos solo con los top 50 para no hacer el archivo enorme
        final_json[main_ing] = sorted_pairs[:50]

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, indent=4)

    print(f"✨ ¡Éxito! Base de datos molecular generada en: {OUTPUT_FILE}")
    print(f"   Se han procesado {count_relaciones} conexiones entre ingredientes.")

if __name__ == "__main__":
    generar_base_molecular()