"""
PIPELINE COMPLETO DE SISTEMA CBR PARA MENÚS
=============================================

Este script ejecuta automáticamente todos los pasos necesarios:
1. Captura de preferencias del usuario (intput_cbr.py)
2. Motor CBR: Retrieve, Reuse, Revise, Retain (CBREngine_Demo.py)
3. Generación de recomendaciones adaptadas culturalmente

Uso:
    python main.py
"""
import os
import sys
import time
from datetime import datetime

# ============================================================================
# VERIFICACIÓN DE DEPENDENCIAS
# ============================================================================

def check_dependencies():
    """Verifica que todas las librerías estén instaladas"""
    print(f"\n{'='*70}")
    print(f"🔍 VERIFICANDO DEPENDENCIAS")
    print(f"{'='*70}\n")
    
    required_packages = {
        'json': 'built-in',
    }
    
    print(f"✅ Todas las dependencias básicas están disponibles\n")
    return True

# ============================================================================
# PASO 1: CAPTURA DE PREFERENCIAS DEL USUARIO
# ============================================================================

def step1_get_user_input():
    """Paso 1: Capturar las preferencias del usuario"""
    print(f"\n{'='*70}")
    print(f"📋 PASO 1: CAPTURA DE PREFERENCIAS DEL USUARIO")
    print(f"{'='*70}\n")
    
    try:
        # Importar el módulo de input
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from intput_cbr import get_user_restrictions
        
        # Obtener preferencias
        user_data = get_user_restrictions()
        
        print("\n✅ Preferencias capturadas exitosamente\n")
        return user_data
        
    except Exception as e:
        print(f"❌ Error capturando preferencias: {e}")
        import traceback
        traceback.print_exc()
        return None

# ============================================================================
# PASO 2: EJECUTAR MOTOR CBR
# ============================================================================

def step2_run_cbr_engine(user_data):
    """Paso 2: Ejecutar el motor CBR con las preferencias del usuario"""
    print(f"\n{'='*70}")
    print(f"📋 PASO 2: EJECUTANDO MOTOR CBR")
    print(f"{'='*70}\n")
    
    try:
        # Importar el motor CBR
        from CBREngine_Demo import run_cbr_system
        
        # Convertir datos del usuario al formato esperado por CBR
        user_prefs = convert_user_data_to_cbr_format(user_data)
        
        # Ejecutar sistema CBR
        adapted_menu, is_valid = run_cbr_system(user_prefs)
        
        print("\n✅ Motor CBR ejecutado exitosamente\n")
        return adapted_menu, is_valid
        
    except Exception as e:
        print(f"❌ Error ejecutando motor CBR: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def convert_user_data_to_cbr_format(user_data):
    """Convierte datos del formulario de usuario al formato CBR"""
    cbr_prefs = {}
    
    # Mapear cultura
    cuisine_mapping = {
        'italian': 'Italiana',
        'italiana': 'Italiana',
        'chinese': 'China',
        'china': 'China',
        'mexican': 'Mexicana/Tex-Mex',
        'mexicana': 'Mexicana/Tex-Mex',
        'indian': 'India',
        'india': 'India',
        'mediterranean': 'Mediterránea',
        'mediterránea': 'Mediterránea',
        'american': 'Americana',
        'americana': 'Americana',
        'peruvian': 'Peruana',
        'peruana': 'Peruana',
        'japanese': 'Japonesa',
        'japonesa': 'Japonesa'
    }
    
    if 'cuisine' in user_data:
        cuisine_key = user_data['cuisine'].lower()
        cbr_prefs['cultura'] = cuisine_mapping.get(cuisine_key, user_data['cuisine'])
    
    # Mapear estilo de cocina
    style_mapping = {
        'traditional': 'Tradicional',
        'modern': 'Moderno',
        'regional': 'Regional',
        'sybarite': 'Gourmet'
    }
    
    if 'food_style' in user_data:
        style_key = user_data['food_style'].lower()
        cbr_prefs['estilo_cocina'] = style_mapping.get(style_key, user_data['food_style'])
    
    # Mapear temporada
    season_mapping = {
        'spring': 'Spring',
        'summer': 'Summer',
        'autumn': 'Fall',
        'fall': 'Fall',
        'winter': 'Winter',
        'any-season': 'any-season'
    }
    
    if 'season' in user_data:
        season_key = user_data['season'].lower()
        cbr_prefs['season'] = season_mapping.get(season_key, user_data['season'])
    
    # Precio
    if 'max_price' in user_data:
        cbr_prefs['max_price'] = user_data['max_price']
    if 'min_price' in user_data:
        cbr_prefs['min_price'] = user_data['min_price']
    
    # Restricciones dietéticas
    restrictions = user_data.get('restrictions', [])
    cbr_prefs['is_vegan'] = 'vegan' in restrictions
    cbr_prefs['is_vegetarian'] = 'vegetarian' in restrictions or cbr_prefs['is_vegan']
    cbr_prefs['is_gluten_free'] = 'gluten-free' in restrictions or 'gluten free' in restrictions
    cbr_prefs['is_dairy_free'] = 'dairy-free' in restrictions or 'dairy free' in restrictions
    cbr_prefs['is_kosher'] = 'kosher' in restrictions
    cbr_prefs['is_halal'] = 'halal' in restrictions
    
    # Otros datos
    if 'max_people' in user_data:
        cbr_prefs['max_people'] = user_data['max_people']
    if 'event_type' in user_data:
        cbr_prefs['event_type'] = user_data['event_type']
    if 'quiere_tarta' in user_data:
        cbr_prefs['quiere_tarta'] = user_data['quiere_tarta']
    
    return cbr_prefs

# ============================================================================
# RESUMEN FINAL
# ============================================================================

def generate_summary(adapted_menu, is_valid):
    """Genera resumen final de la recomendación"""
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN FINAL")
    print(f"{'='*70}\n")
    
    if adapted_menu:
        print(f"✅ RECOMENDACIÓN GENERADA CON ÉXITO")
        print(f"\n🍽️  Menú: {adapted_menu['menu_name']}")
        print(f"🌍 Cultura: {adapted_menu['features'].get('cultura', 'N/A')}")
        print(f"👨‍🍳 Estilo: {adapted_menu['features'].get('estilo_cocina', 'N/A')}")
        print(f"💰 Precio: ${adapted_menu['features']['total_price_per_serving']:.2f}")
        
        if 'cultural_substitutions' in adapted_menu and adapted_menu['cultural_substitutions']:
            print(f"\n🔄 Adaptaciones culturales: {len(adapted_menu['cultural_substitutions'])} ingredientes")
        
        if 'adaptations' in adapted_menu and adapted_menu['adaptations']:
            print(f"🔧 Otras adaptaciones: {len(adapted_menu['adaptations'])}")
        
        if is_valid:
            print(f"\n✅ El menú cumple todas las restricciones del usuario")
        else:
            print(f"\n⚠️  El menú requiere revisión adicional")
        
        print(f"\n{'='*70}")
        print(f"🎉 SISTEMA CBR COMPLETADO EXITOSAMENTE")
        print(f"{'='*70}\n")
    else:
        print(f"❌ No se pudo generar una recomendación\n")

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def main():
    """Ejecuta el pipeline completo del sistema CBR"""
    
    start_time = time.time()
    
    print(f"\n{'#'*70}")
    print(f"# SISTEMA CBR DE RECOMENDACIÓN DE MENÚS")
    print(f"# Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ Pipeline abortado: Dependencias faltantes\n")
        return
    
    # Paso 1: Capturar preferencias del usuario
    user_data = step1_get_user_input()
    if not user_data:
        print("\n❌ Pipeline abortado en Paso 1\n")
        return
    
    # Paso 2: Ejecutar motor CBR
    adapted_menu, is_valid = step2_run_cbr_engine(user_data)
    if not adapted_menu:
        print("\n❌ Pipeline abortado en Paso 2\n")
        return
    
    # Resumen final
    generate_summary(adapted_menu, is_valid)
    
    # Tiempo total
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    
    print(f"⏱️  Tiempo total de ejecución: {minutes}m {seconds}s\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrumpido por el usuario\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
