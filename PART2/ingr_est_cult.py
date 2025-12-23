import json
import os
from collections import defaultdict

def generar_bd_ingredientes(archivo_origen, archivo_destino):
    """
    Lee una base de casos de recetas y crea una base de conocimiento
    de ingredientes clasificados por intersección de (Cultura, Estilo).
    """
    
    # 1. Cargar la base de datos de menús/recetas
    try:
        with open(archivo_origen, 'r', encoding='utf-8') as f:
            recetas = json.load(f)
        print(f"✅ Cargadas {len(recetas)} recetas de {archivo_origen}")
    except FileNotFoundError:
        print(f"❌ No se encuentra el archivo: {archivo_origen}")
        return

    # 2. Diccionario para almacenar ingredientes únicos por combinación
    # Estructura: clave=(cultura, estilo), valor=set(ingredientes)
    # Usamos 'set' para evitar ingredientes duplicados automáticamente
    knowledge_base = defaultdict(set)

    # 3. Recorrer recetas y extraer datos
    for receta in recetas:
        # IMPORTANTE: Ajusta las claves ('cuisine', 'style', 'ingredients') 
        # según los nombres exactos que uses en tu JSON.
        
        # Obtenemos cultura y estilo, normalizamos a minúsculas
        cultura = receta.get('cuisine', 'unknown').lower().strip()
        estilo = receta.get('style', 'unknown').lower().strip()
        
        # Obtenemos la lista de ingredientes
        ingredientes = receta.get('ingredients', [])
        
        # Clave compuesta
        clave = (cultura, estilo)
        
        # Añadimos los ingredientes al set correspondiente
        for ingrediente in ingredientes:
            # Normalizamos el nombre del ingrediente
            ing_limpio = ingrediente.lower().strip()
            if ing_limpio:
                knowledge_base[clave].add(ing_limpio)

    # 4. Convertir a formato exportable (JSON no soporta tuplas como claves ni sets)
    # Formato final: Un diccionario de strings o una lista de objetos
    output_data = {}
    
    for (cultura, estilo), lista_ingredientes in knowledge_base.items():
        # Creamos una clave de texto legible, ej: "italian_traditional"
        key_str = f"{cultura}_{estilo}"
        
        # Convertimos el set a lista y la ordenamos alfabéticamente
        output_data[key_str] = {
            "culture": cultura,
            "style": estilo,
            "ingredients": sorted(list(lista_ingredientes))
        }

    # 5. Guardar el resultado
    with open(archivo_destino, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print(f"✨ Base de datos de ingredientes generada en: {archivo_destino}")
    print(f"   Se han encontrado {len(output_data)} combinaciones de Cultura/Estilo.")

# --- EJECUCIÓN ---
if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con el tuyo
    INPUT_FILE = "cbr_menu_database.json" 

    OUTPUT_FILE = "ingredientes_por_contexto.json"
    
    generar_bd_ingredientes(INPUT_FILE, OUTPUT_FILE)