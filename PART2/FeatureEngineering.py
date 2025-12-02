"""
Feature Engineering Pipeline para Clustering de Recetas
- Lee recipes_optimized.json
- Transforma features a formato numérico
- Normaliza y codifica variables
- Genera matriz de features lista para clustering
- Exporta a CSV para scikit-learn
"""

import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MultiLabelBinarizer, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CARGA DE DATOS
# ============================================================================

def load_recipes(filepath='recipes_optimized.json'):
    """Carga recetas desde JSON optimizado"""
    print(f"\n{'='*70}")
    print(f"📂 CARGANDO RECETAS DESDE {filepath}")
    print(f"{'='*70}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    
    print(f"✅ Cargadas {len(recipes)} recetas\n")
    return recipes

# ============================================================================
# EXTRACCIÓN DE FEATURES NUMÉRICAS
# ============================================================================

def extract_numeric_features(recipes):
    """Extrae features numéricas directas"""
    print("🔢 Extrayendo features numéricas...")
    
    numeric_data = []
    for recipe in recipes:
        fn = recipe['features_numeric']
        df = recipe['derived_features']
        
        row = {
            'id': recipe['id'],
            'price_per_serving': fn['price_per_serving'],
            'ready_in_minutes': fn['ready_in_minutes'],
            'servings': fn['servings'],
            'health_score': fn['health_score'],
            'spoonacular_score': fn['spoonacular_score'],
            'calories': fn['calories'],
            'complexity_score': df['complexity_score'],
            'value_score': df['value_score'],
            'nutrient_density': df['nutrient_density'],
            'restriction_count': df['restriction_count']
        }
        
        # Añadir taste profile si existe
        if recipe['taste_profile']:
            tp = recipe['taste_profile']
            row['taste_sweetness'] = tp['sweetness']
            row['taste_saltiness'] = tp['saltiness']
            row['taste_sourness'] = tp['sourness']
            row['taste_bitterness'] = tp['bitterness']
            row['taste_savoriness'] = tp['savoriness']
        else:
            row['taste_sweetness'] = 0
            row['taste_saltiness'] = 0
            row['taste_sourness'] = 0
            row['taste_bitterness'] = 0
            row['taste_savoriness'] = 0
        
        numeric_data.append(row)
    
    df_numeric = pd.DataFrame(numeric_data)
    print(f"   ✓ {df_numeric.shape[1]-1} features numéricas extraídas")
    return df_numeric

# ============================================================================
# EXTRACCIÓN DE FEATURES CATEGÓRICAS
# ============================================================================

def extract_categorical_features(recipes):
    """Extrae y codifica features categóricas"""
    print("🏷️  Extrayendo features categóricas...")
    
    categorical_data = []
    for recipe in recipes:
        fc = recipe['features_categorical']
        df = recipe['derived_features']
        
        row = {
            'id': recipe['id'],
            'vegan': int(fc['vegan']),
            'vegetarian': int(fc['vegetarian']),
            'gluten_free': int(fc['gluten_free']),
            'dairy_free': int(fc['dairy_free']),
            'very_healthy': int(fc['very_healthy']),
            'cheap': int(fc['cheap']),
            'dish_class': fc['dish_class'],
            'season': fc['season'],
            'price_category': df['price_category']
        }
        categorical_data.append(row)
    
    df_categorical = pd.DataFrame(categorical_data)
    
    # One-Hot Encoding para dish_class, season, price_category
    df_encoded = pd.get_dummies(df_categorical, 
                                 columns=['dish_class', 'season', 'price_category'],
                                 prefix=['dish', 'season', 'price'])
    
    print(f"   ✓ {df_encoded.shape[1]-1} features categóricas codificadas")
    return df_encoded

# ============================================================================
# EXTRACCIÓN DE FEATURES DE TEXTO
# ============================================================================

def extract_text_features(recipes, max_features_per_field=10):
    """Extrae features de campos de texto usando multi-label binarization"""
    print("📝 Extrayendo features de texto...")
    
    # Preparar listas
    all_cuisines = []
    all_diets = []
    all_dish_types = []
    all_occasions = []
    
    for recipe in recipes:
        ft = recipe['features_text']
        all_cuisines.append(ft['cuisines'])
        all_diets.append(ft['diets'])
        all_dish_types.append(ft['dish_types'])
        all_occasions.append(ft['occasions'])
    
    # Multi-Label Binarization
    mlb_cuisines = MultiLabelBinarizer()
    mlb_diets = MultiLabelBinarizer()
    mlb_dish_types = MultiLabelBinarizer()
    mlb_occasions = MultiLabelBinarizer()
    
    cuisines_encoded = mlb_cuisines.fit_transform(all_cuisines)
    diets_encoded = mlb_diets.fit_transform(all_diets)
    dish_types_encoded = mlb_dish_types.fit_transform(all_dish_types)
    occasions_encoded = mlb_occasions.fit_transform(all_occasions)
    
    # Crear DataFrames
    df_cuisines = pd.DataFrame(
        cuisines_encoded,
        columns=[f'cuisine_{c}' for c in mlb_cuisines.classes_]
    )
    df_diets = pd.DataFrame(
        diets_encoded,
        columns=[f'diet_{d}' for d in mlb_diets.classes_]
    )
    df_dish_types = pd.DataFrame(
        dish_types_encoded,
        columns=[f'dishtype_{dt}' for dt in mlb_dish_types.classes_]
    )
    df_occasions = pd.DataFrame(
        occasions_encoded,
        columns=[f'occasion_{o}' for o in mlb_occasions.classes_]
    )
    
    # Añadir IDs
    ids = [recipe['id'] for recipe in recipes]
    df_cuisines['id'] = ids
    df_diets['id'] = ids
    df_dish_types['id'] = ids
    df_occasions['id'] = ids
    
    print(f"   ✓ Cuisines: {len(mlb_cuisines.classes_)} categorías")
    print(f"   ✓ Diets: {len(mlb_diets.classes_)} categorías")
    print(f"   ✓ Dish Types: {len(mlb_dish_types.classes_)} categorías")
    print(f"   ✓ Occasions: {len(mlb_occasions.classes_)} categorías")
    
    return df_cuisines, df_diets, df_dish_types, df_occasions

# ============================================================================
# EXTRACCIÓN DE FEATURES DE INGREDIENTES (TF-IDF)
# ============================================================================

def extract_ingredient_features(recipes, max_features=50):
    """Extrae features de ingredientes usando TF-IDF"""
    print(f"🥘 Extrayendo features de ingredientes (TF-IDF, max={max_features})...")
    
    # Preparar corpus de ingredientes
    ingredient_docs = []
    for recipe in recipes:
        ingredients = recipe['features_text']['ingredients']
        # Unir ingredientes en un solo documento
        doc = ' '.join(ingredients)
        ingredient_docs.append(doc)
    
    # TF-IDF Vectorization
    tfidf = TfidfVectorizer(
        max_features=max_features,
        ngram_range=(1, 2),  # Unigrams y bigrams
        min_df=2,            # Ignorar términos que aparecen en menos de 2 documentos
        max_df=0.8           # Ignorar términos que aparecen en más del 80%
    )
    
    ingredient_matrix = tfidf.fit_transform(ingredient_docs)
    
    # Crear DataFrame
    df_ingredients = pd.DataFrame(
        ingredient_matrix.toarray(),
        columns=[f'ing_{term}' for term in tfidf.get_feature_names_out()]
    )
    df_ingredients['id'] = [recipe['id'] for recipe in recipes]
    
    print(f"   ✓ {ingredient_matrix.shape[1]} features de ingredientes extraídas")
    return df_ingredients

# ============================================================================
# CONSOLIDACIÓN Y NORMALIZACIÓN
# ============================================================================

def consolidate_features(*dfs):
    """Consolida todos los DataFrames en uno solo"""
    print("\n🔗 Consolidando todas las features...")
    
    # Merge por ID
    df_final = dfs[0]
    for df in dfs[1:]:
        df_final = df_final.merge(df, on='id', how='inner')
    
    print(f"   ✓ Dimensiones finales: {df_final.shape}")
    print(f"   ✓ Total de features: {df_final.shape[1] - 1} (sin contar ID)")
    
    return df_final

def normalize_features(df, exclude_cols=['id']):
    """Normaliza features numéricas usando StandardScaler"""
    print("\n📏 Normalizando features numéricas...")
    
    # Separar ID
    ids = df['id'].copy()
    
    # Obtener columnas a normalizar
    cols_to_normalize = [col for col in df.columns if col not in exclude_cols]
    
    # Normalizar
    scaler = StandardScaler()
    df_normalized = pd.DataFrame(
        scaler.fit_transform(df[cols_to_normalize]),
        columns=cols_to_normalize
    )
    df_normalized['id'] = ids
    
    print(f"   ✓ {len(cols_to_normalize)} features normalizadas")
    print(f"   ✓ Media: 0, Desviación estándar: 1")
    
    return df_normalized, scaler

# ============================================================================
# REDUCCIÓN DIMENSIONAL (PCA)
# ============================================================================

def apply_pca(df, n_components=50, exclude_cols=['id']):
    """Aplica PCA para reducción dimensional"""
    print(f"\n🎯 Aplicando PCA (reducción a {n_components} componentes)...")
    
    # Separar ID
    ids = df['id'].copy()
    
    # Obtener features
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    X = df[feature_cols].values
    
    # Aplicar PCA
    pca = PCA(n_components=min(n_components, X.shape[1]))
    X_pca = pca.fit_transform(X)
    
    # Crear DataFrame
    df_pca = pd.DataFrame(
        X_pca,
        columns=[f'PC{i+1}' for i in range(X_pca.shape[1])]
    )
    df_pca['id'] = ids
    
    # Varianza explicada
    explained_var = pca.explained_variance_ratio_.sum() * 100
    
    print(f"   ✓ Reducido de {X.shape[1]} a {X_pca.shape[1]} dimensiones")
    print(f"   ✓ Varianza explicada: {explained_var:.2f}%")
    
    return df_pca, pca, explained_var

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def main():
    """Pipeline principal de Feature Engineering"""
    
    # 1. Cargar datos
    recipes = load_recipes('recipes_optimized.json')
    
    # 2. Extraer features numéricas
    df_numeric = extract_numeric_features(recipes)
    
    # 3. Extraer features categóricas
    df_categorical = extract_categorical_features(recipes)
    
    # 4. Extraer features de texto
    df_cuisines, df_diets, df_dish_types, df_occasions = extract_text_features(recipes)
    
    # 5. Extraer features de ingredientes
    df_ingredients = extract_ingredient_features(recipes, max_features=50)
    
    # 6. Consolidar todas las features
    df_all = consolidate_features(
        df_numeric,
        df_categorical,
        df_cuisines,
        df_diets,
        df_dish_types,
        df_occasions,
        df_ingredients
    )
    
    # 7. Guardar features completas (sin normalizar)
    output_raw = 'recipe_features_raw.csv'
    df_all.to_csv(output_raw, index=False, encoding='utf-8')
    print(f"\n💾 Features sin normalizar guardadas en: {output_raw}")
    
    # 8. Normalizar features
    df_normalized, scaler = normalize_features(df_all)
    
    # 9. Guardar features normalizadas
    output_normalized = 'recipe_features_normalized.csv'
    df_normalized.to_csv(output_normalized, index=False, encoding='utf-8')
    print(f"💾 Features normalizadas guardadas en: {output_normalized}")
    
    # 10. Aplicar PCA (opcional, para reducción dimensional)
    df_pca, pca_model, explained_var = apply_pca(df_normalized, n_components=50)
    
    # 11. Guardar features con PCA
    output_pca = 'recipe_features_pca.csv'
    df_pca.to_csv(output_pca, index=False, encoding='utf-8')
    print(f"💾 Features con PCA guardadas en: {output_pca}")
    
    # 12. Resumen final
    print(f"\n{'='*70}")
    print(f"✅ FEATURE ENGINEERING COMPLETADO")
    print(f"{'='*70}")
    print(f"📊 Resumen:")
    print(f"   - Recetas procesadas: {len(recipes)}")
    print(f"   - Features totales (raw): {df_all.shape[1] - 1}")
    print(f"   - Features después de PCA: {df_pca.shape[1] - 1}")
    print(f"   - Varianza explicada (PCA): {explained_var:.2f}%")
    print(f"\n📁 Archivos generados:")
    print(f"   1. {output_raw} - Features completas sin normalizar")
    print(f"   2. {output_normalized} - Features normalizadas")
    print(f"   3. {output_pca} - Features con PCA aplicado")
    print(f"{'='*70}\n")
    
    print("🎯 Próximo paso: Clustering (K-Means, DBSCAN, Hierarchical)")
    print("   Usa 'recipe_features_normalized.csv' o 'recipe_features_pca.csv'\n")

if __name__ == "__main__":
    main()
