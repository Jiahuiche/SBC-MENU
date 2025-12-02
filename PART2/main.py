"""
PIPELINE COMPLETO DE CLUSTERING Y CBR PARA MENÚS
==================================================

Este script ejecuta automáticamente todos los pasos necesarios:
1. Conversión de formato antiguo a optimizado (si es necesario)
2. Feature Engineering (extracción y transformación)
3. Clustering (K-Means) y selección de representativos
4. Generación de visualizaciones y métricas

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
        'pandas': 'pandas',
        'numpy': 'numpy',
        'sklearn': 'scikit-learn',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NO INSTALADO")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️ Faltan {len(missing)} paquetes:")
        print(f"   Instalar con: pip install {' '.join(missing)}\n")
        return False
    
    print(f"\n✅ Todas las dependencias están instaladas\n")
    return True

# ============================================================================
# PASO 1: CONVERSIÓN DE FORMATO
# ============================================================================

def step1_convert_format():
    """Paso 1: Convertir formato antiguo a optimizado"""
    print(f"\n{'='*70}")
    print(f"📋 PASO 1: CONVERSIÓN DE FORMATO")
    print(f"{'='*70}\n")
    
    # Verificar si ya existe recipes_optimized.json
    if os.path.exists('recipes_optimized.json'):
        print(f"✅ recipes_optimized.json ya existe")
        user_input = input("¿Deseas reconvertir desde filtered_recipes111.json? (s/N): ")
        if user_input.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("⏭️  Saltando conversión...\n")
            return True
    
    # Ejecutar conversión
    try:
        from ConvertOldToOptimized import convert_old_to_optimized
        
        success = convert_old_to_optimized()
                
        
        if not success:
            print("❌ Error en la conversión. Abortando pipeline.")
            return False
        
        print("✅ Paso 1 completado\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en conversión: {e}")
        return False

# ============================================================================
# PASO 2: FEATURE ENGINEERING
# ============================================================================

def step2_feature_engineering():
    """Paso 2: Extracción y transformación de features"""
    print(f"\n{'='*70}")
    print(f"📋 PASO 2: FEATURE ENGINEERING")
    print(f"{'='*70}\n")
    
    # Verificar si ya existen los archivos
    files_exist = all([
        os.path.exists('recipe_features_raw.csv'),
        os.path.exists('recipe_features_normalized.csv'),
        os.path.exists('recipe_features_pca.csv')
    ])
    
    if files_exist:
        print(f"✅ Archivos de features ya existen:")
        print(f"   - recipe_features_raw.csv")
        print(f"   - recipe_features_normalized.csv")
        print(f"   - recipe_features_pca.csv")
        user_input = input("¿Deseas regenerar las features? (s/N): ")
        if user_input.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("⏭️  Saltando feature engineering...\n")
            return True
    
    # Ejecutar feature engineering
    try:
        from FeatureEngineering import main as feature_main
        feature_main()
        
        print("✅ Paso 2 completado\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en feature engineering: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# PASO 3: CLUSTERING
# ============================================================================

def step3_clustering():
    """Paso 3: Clustering y selección de representativos"""
    print(f"\n{'='*70}")
    print(f"📋 PASO 3: CLUSTERING Y SELECCIÓN DE REPRESENTATIVOS")
    print(f"{'='*70}\n")
    
    # Verificar si ya existen resultados
    files_exist = all([
        os.path.exists('representative_recipes.json'),
        os.path.exists('clustering_metrics.json')
    ])
    
    if files_exist:
        print(f"✅ Archivos de clustering ya existen:")
        print(f"   - representative_recipes.json")
        print(f"   - clustering_metrics.json")
        user_input = input("¿Deseas regenerar el clustering? (s/N): ")
        if user_input.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("⏭️  Saltando clustering...\n")
            return True
    
    # Ejecutar clustering
    try:
        from ClusteringPipeline import main as clustering_main
        clustering_main()
        
        print("✅ Paso 3 completado\n")
        return True
        
    except Exception as e:
        print(f"❌ Error en clustering: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# RESUMEN FINAL
# ============================================================================

def generate_summary():
    """Genera resumen final de los resultados"""
    print(f"\n{'='*70}")
    print(f"📊 RESUMEN FINAL DEL PIPELINE")
    print(f"{'='*70}\n")
    
    # Leer métricas
    import json
    
    try:
        with open('clustering_metrics.json', 'r') as f:
            metrics = json.load(f)
        
        print(f"✅ CLUSTERING COMPLETADO CON ÉXITO")
        print(f"\n📈 Métricas:")
        print(f"   - Recetas totales: {metrics['total_recipes']}")
        print(f"   - K óptimo: {metrics['optimal_k']}")
        print(f"   - Recetas representativas: {metrics['total_representatives']}")
        print(f"   - Silhouette Score: {metrics['kmeans_metrics']['silhouette']:.3f}")
        print(f"   - Davies-Bouldin Index: {metrics['kmeans_metrics']['davies_bouldin']:.3f}")
        
        reduction_pct = (1 - metrics['total_representatives'] / metrics['total_recipes']) * 100
        print(f"\n🎯 Reducción de datos: {reduction_pct:.1f}%")
        print(f"   ({metrics['total_recipes']} → {metrics['total_representatives']} recetas)")
        
        print(f"\n📁 Archivos generados:")
        print(f"   1. recipes_optimized.json - Recetas en formato optimizado")
        print(f"   2. recipe_features_normalized.csv - Features normalizadas")
        print(f"   3. representative_recipes.json - Recetas representativas")
        print(f"   4. clustering_metrics.json - Métricas de calidad")
        print(f"   5. kmeans_clusters.png - Visualización de clusters")
        print(f"   6. optimal_k_analysis.png - Análisis de K óptimo")
        
        print(f"\n{'='*70}")
        print(f"🎉 PIPELINE COMPLETADO EXITOSAMENTE")
        print(f"{'='*70}\n")
        
        print(f"🔜 PRÓXIMOS PASOS:")
        print(f"   1. Revisar representative_recipes.json")
        print(f"   2. Validar clustering en kmeans_clusters.png")
        print(f"   3. Implementar CBR Engine para recuperación de casos")
        print(f"   4. Crear sistema de composición de menús (Starter + Main + Dessert)\n")
        
    except FileNotFoundError:
        print("⚠️ No se encontró clustering_metrics.json")
        print("   El clustering puede no haberse ejecutado correctamente.\n")
    except Exception as e:
        print(f"⚠️ Error leyendo métricas: {e}\n")

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def main():
    """Ejecuta el pipeline completo"""
    
    start_time = time.time()
    
    print(f"\n{'#'*70}")
    print(f"# PIPELINE COMPLETO DE CLUSTERING Y CBR PARA MENÚS")
    print(f"# Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n❌ Pipeline abortado: Dependencias faltantes\n")
        return
    
    # Paso 1: Conversión de formato
    if not step1_convert_format():
        print("\n❌ Pipeline abortado en Paso 1\n")
        return
    
    # Paso 2: Feature Engineering
    if not step2_feature_engineering():
        print("\n❌ Pipeline abortado en Paso 2\n")
        return
    
    # Paso 3: Clustering
    if not step3_clustering():
        print("\n❌ Pipeline abortado en Paso 3\n")
        return
    
    # Resumen final
    generate_summary()
    
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
