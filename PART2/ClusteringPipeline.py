"""
Pipeline de Clustering para Selección de Recetas Representativas
- Lee features normalizadas de recetas
- Aplica K-Means, DBSCAN y Hierarchical Clustering
- Selecciona recetas representativas por cluster
- Genera visualizaciones y métricas de calidad
- Exporta recetas representativas para CBR
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CARGA DE DATOS
# ============================================================================

def load_features(filepath='recipe_features_normalized.csv'):
    """Carga matriz de features normalizada"""
    print(f"\n{'='*70}")
    print(f"📂 CARGANDO FEATURES DESDE {filepath}")
    print(f"{'='*70}\n")
    
    df = pd.read_csv(filepath)
    print(f"✅ Cargadas {df.shape[0]} recetas con {df.shape[1]-1} features\n")
    
    return df

def load_original_recipes(filepath='recipes_optimized.json'):
    """Carga recetas originales para referencia"""
    with open(filepath, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    
    # Crear diccionario ID -> recipe
    recipe_dict = {recipe['id']: recipe for recipe in recipes}
    return recipe_dict

# ============================================================================
# CLUSTERING: K-MEANS
# ============================================================================

def perform_kmeans(X, n_clusters=15, random_state=42):
    """Aplica K-Means clustering"""
    print(f"🔵 K-Means Clustering (k={n_clusters})...")
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # Métricas
    silhouette = silhouette_score(X, labels)
    davies_bouldin = davies_bouldin_score(X, labels)
    calinski = calinski_harabasz_score(X, labels)
    
    print(f"   ✓ Silhouette Score: {silhouette:.3f} (mejor si cercano a 1)")
    print(f"   ✓ Davies-Bouldin Index: {davies_bouldin:.3f} (mejor si cercano a 0)")
    print(f"   ✓ Calinski-Harabasz Score: {calinski:.1f} (mejor si alto)")
    
    # Distribución de clusters
    unique, counts = np.unique(labels, return_counts=True)
    print(f"   ✓ Distribución de clusters:")
    for cluster_id, count in zip(unique, counts):
        print(f"      Cluster {cluster_id}: {count} recetas")
    
    return kmeans, labels, {
        'silhouette': silhouette,
        'davies_bouldin': davies_bouldin,
        'calinski_harabasz': calinski
    }

# ============================================================================
# CLUSTERING: DBSCAN
# ============================================================================

def perform_dbscan(X, eps=0.5, min_samples=5):
    """Aplica DBSCAN clustering"""
    print(f"\n🟢 DBSCAN Clustering (eps={eps}, min_samples={min_samples})...")
    
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    labels = dbscan.fit_predict(X)
    
    # Contar clusters (excluyendo ruido -1)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)
    
    print(f"   ✓ Clusters encontrados: {n_clusters}")
    print(f"   ✓ Puntos de ruido: {n_noise}")
    
    # Métricas (solo si hay al menos 2 clusters)
    if n_clusters >= 2:
        # Filtrar ruido para métricas
        mask = labels != -1
        X_filtered = X[mask]
        labels_filtered = labels[mask]
        
        silhouette = silhouette_score(X_filtered, labels_filtered)
        davies_bouldin = davies_bouldin_score(X_filtered, labels_filtered)
        calinski = calinski_harabasz_score(X_filtered, labels_filtered)
        
        print(f"   ✓ Silhouette Score: {silhouette:.3f}")
        print(f"   ✓ Davies-Bouldin Index: {davies_bouldin:.3f}")
        print(f"   ✓ Calinski-Harabasz Score: {calinski:.1f}")
        
        metrics = {
            'silhouette': silhouette,
            'davies_bouldin': davies_bouldin,
            'calinski_harabasz': calinski
        }
    else:
        print(f"   ⚠️  No hay suficientes clusters para calcular métricas")
        metrics = None
    
    return dbscan, labels, metrics

# ============================================================================
# CLUSTERING: HIERARCHICAL
# ============================================================================

def perform_hierarchical(X, n_clusters=15, linkage='ward'):
    """Aplica Hierarchical Clustering"""
    print(f"\n🟣 Hierarchical Clustering (k={n_clusters}, linkage={linkage})...")
    
    hierarchical = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
    labels = hierarchical.fit_predict(X)
    
    # Métricas
    silhouette = silhouette_score(X, labels)
    davies_bouldin = davies_bouldin_score(X, labels)
    calinski = calinski_harabasz_score(X, labels)
    
    print(f"   ✓ Silhouette Score: {silhouette:.3f}")
    print(f"   ✓ Davies-Bouldin Index: {davies_bouldin:.3f}")
    print(f"   ✓ Calinski-Harabasz Score: {calinski:.1f}")
    
    # Distribución
    unique, counts = np.unique(labels, return_counts=True)
    print(f"   ✓ Distribución de clusters:")
    for cluster_id, count in zip(unique, counts):
        print(f"      Cluster {cluster_id}: {count} recetas")
    
    return hierarchical, labels, {
        'silhouette': silhouette,
        'davies_bouldin': davies_bouldin,
        'calinski_harabasz': calinski
    }

# ============================================================================
# SELECCIÓN DE REPRESENTATIVOS
# ============================================================================

def select_representatives(X, labels, df_ids, recipe_dict, n_per_cluster=3, method='centroid'):
    """
    Selecciona recetas representativas de cada cluster
    
    method: 'centroid' (más cercano al centroide) o 'top_scored' (mejor spoonacular_score)
    """
    print(f"\n🎯 Seleccionando representativos ({method}, {n_per_cluster} por cluster)...")
    
    representatives = []
    
    unique_clusters = sorted(set(labels))
    if -1 in unique_clusters:
        unique_clusters.remove(-1)  # Ignorar ruido de DBSCAN
    
    for cluster_id in unique_clusters:
        # Obtener índices de recetas en este cluster
        cluster_mask = labels == cluster_id
        cluster_indices = np.where(cluster_mask)[0]
        cluster_points = X[cluster_mask]
        
        if method == 'centroid':
            # Calcular centroide del cluster
            centroid = cluster_points.mean(axis=0)
            
            # Calcular distancias al centroide
            distances = np.linalg.norm(cluster_points - centroid, axis=1)
            
            # Ordenar por distancia (más cercanos primero)
            sorted_indices = np.argsort(distances)[:n_per_cluster]
            selected_indices = cluster_indices[sorted_indices]
        
        elif method == 'top_scored':
            # Ordenar por spoonacular_score (mejor calificados)
            cluster_recipe_ids = df_ids.iloc[cluster_indices].values
            cluster_scores = []
            
            for idx in cluster_indices:
                recipe_id = df_ids.iloc[idx]
                if recipe_id in recipe_dict:
                    score = recipe_dict[recipe_id]['features_numeric']['spoonacular_score']
                    cluster_scores.append((idx, score))
            
            # Ordenar por score descendente
            cluster_scores.sort(key=lambda x: x[1], reverse=True)
            selected_indices = [idx for idx, score in cluster_scores[:n_per_cluster]]
        
        # Guardar representativos
        for idx in selected_indices:
            recipe_id = df_ids.iloc[idx]
            if recipe_id in recipe_dict:
                recipe = recipe_dict[recipe_id]
                representatives.append({
                    'cluster_id': int(cluster_id),
                    'recipe_id': int(recipe_id),
                    'recipe': recipe
                })
    
    print(f"   ✓ Seleccionados {len(representatives)} recetas representativas")
    print(f"   ✓ De {len(unique_clusters)} clusters")
    
    return representatives

# ============================================================================
# VISUALIZACIÓN
# ============================================================================

def visualize_clusters(X, labels, title='Clustering Visualization', save_path=None):
    """Visualiza clusters en 2D usando PCA"""
    print(f"\n📊 Generando visualización...")
    
    # Reducir a 2D con PCA
    pca = PCA(n_components=2)
    X_2d = pca.fit_transform(X)
    
    # Crear figura
    plt.figure(figsize=(12, 8))
    
    # Plotear clusters
    unique_labels = sorted(set(labels))
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    
    for label, color in zip(unique_labels, colors):
        if label == -1:
            # Ruido en negro
            color = 'black'
            marker = 'x'
        else:
            marker = 'o'
        
        mask = labels == label
        plt.scatter(X_2d[mask, 0], X_2d[mask, 1], 
                   c=[color], label=f'Cluster {label}',
                   alpha=0.6, s=50, marker=marker)
    
    plt.title(title, fontsize=16, fontweight='bold')
    plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% var)', fontsize=12)
    plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% var)', fontsize=12)
    plt.legend(loc='best', fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"   ✓ Visualización guardada en: {save_path}")
    else:
        plt.show()
    
    plt.close()

# ============================================================================
# BÚSQUEDA DEL MEJOR K (Método del Codo)
# ============================================================================

def find_optimal_k(X, k_range=range(5, 31), plot=True):
    """Encuentra el K óptimo usando método del codo y Silhouette"""
    print(f"\n🔍 Buscando K óptimo (rango: {k_range.start}-{k_range.stop-1})...")
    
    inertias = []
    silhouettes = []
    
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        
        inertias.append(kmeans.inertia_)
        silhouettes.append(silhouette_score(X, labels))
        
        print(f"   k={k}: Inertia={kmeans.inertia_:.1f}, Silhouette={silhouettes[-1]:.3f}")
    
    # Encontrar el K con mejor Silhouette
    best_k = k_range[np.argmax(silhouettes)]
    print(f"\n   ✅ Mejor K según Silhouette: {best_k}")
    
    if plot:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Método del codo
        ax1.plot(k_range, inertias, 'bo-')
        ax1.set_xlabel('Número de Clusters (K)', fontsize=12)
        ax1.set_ylabel('Inertia', fontsize=12)
        ax1.set_title('Método del Codo', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Silhouette Score
        ax2.plot(k_range, silhouettes, 'ro-')
        ax2.axvline(best_k, color='green', linestyle='--', label=f'Mejor K={best_k}')
        ax2.set_xlabel('Número de Clusters (K)', fontsize=12)
        ax2.set_ylabel('Silhouette Score', fontsize=12)
        ax2.set_title('Silhouette Score por K', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('optimal_k_analysis.png', dpi=300, bbox_inches='tight')
        print(f"   ✓ Gráficos guardados en: optimal_k_analysis.png")
        plt.close()
    
    return best_k

# ============================================================================
# PIPELINE PRINCIPAL
# ============================================================================

def main():
    """Pipeline principal de clustering"""
    
    # 1. Cargar datos
    df_features = load_features('recipe_features_normalized.csv')
    recipe_dict = load_original_recipes('recipes_optimized.json')
    
    # Separar IDs y features
    ids = df_features['id']
    X = df_features.drop('id', axis=1).values
    
    # 2. Encontrar K óptimo
    optimal_k = find_optimal_k(X, k_range=range(5, 11), plot=True)
    
    # 3. Aplicar K-Means con K óptimo
    print(f"\n{'='*70}")
    kmeans_model, kmeans_labels, kmeans_metrics = perform_kmeans(X, n_clusters=optimal_k)
    
    # 4. Aplicar DBSCAN (opcional)
    # dbscan_model, dbscan_labels, dbscan_metrics = perform_dbscan(X, eps=3.0, min_samples=5)
    
    # 5. Aplicar Hierarchical (opcional)
    # hierarchical_model, hierarchical_labels, hierarchical_metrics = perform_hierarchical(X, n_clusters=optimal_k)
    
    # 6. Seleccionar representativos (usando K-Means)
    representatives = select_representatives(
        X, kmeans_labels, ids, recipe_dict, 
        n_per_cluster=3, method='centroid'
    )
    
    # 7. Visualizar clusters
    visualize_clusters(X, kmeans_labels, 
                      title=f'K-Means Clustering (k={optimal_k})',
                      save_path='kmeans_clusters.png')
    
    # 8. Guardar representativos
    output_file = 'representative_recipes.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(representatives, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Recetas representativas guardadas en: {output_file}")
    
    # 9. Guardar métricas
    metrics_summary = {
        'optimal_k': int(optimal_k),
        'total_recipes': int(len(X)),
        'total_representatives': len(representatives),
        'kmeans_metrics': kmeans_metrics,
        'representatives_per_cluster': 3
    }
    
    with open('clustering_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(metrics_summary, f, indent=2)
    
    print(f"💾 Métricas guardadas en: clustering_metrics.json")
    
    # 10. Resumen final
    print(f"\n{'='*70}")
    print(f"✅ CLUSTERING COMPLETADO")
    print(f"{'='*70}")
    print(f"📊 Resumen:")
    print(f"   - Total de recetas: {len(X)}")
    print(f"   - K óptimo: {optimal_k}")
    print(f"   - Recetas representativas: {len(representatives)}")
    print(f"   - Silhouette Score: {kmeans_metrics['silhouette']:.3f}")
    print(f"\n📁 Archivos generados:")
    print(f"   1. {output_file} - Recetas representativas")
    print(f"   2. clustering_metrics.json - Métricas del clustering")
    print(f"   3. kmeans_clusters.png - Visualización de clusters")
    print(f"   4. optimal_k_analysis.png - Análisis del K óptimo")
    print(f"{'='*70}\n")
    
    print("🎯 Próximo paso: Implementar CBR Engine para recuperación de casos")

if __name__ == "__main__":
    main()
