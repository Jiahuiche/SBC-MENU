# 🚀 GUÍA COMPLETA: PIPELINE DE CLUSTERING Y CBR PARA MENÚS

## 📋 ÍNDICE
1. [Visión General](#visión-general)
2. [Estructura de Archivos](#estructura-de-archivos)
3. [Pipeline Paso a Paso](#pipeline-paso-a-paso)
4. [Ventajas del Enfoque](#ventajas-del-enfoque)
5. [Próximos Pasos](#próximos-pasos)

---

## 🎯 VISIÓN GENERAL

Este pipeline transforma la base de datos de Spoonacular en una **estructura optimizada** para:
- ✅ **Clustering**: Agrupar recetas similares
- ✅ **CBR (Case-Based Reasoning)**: Recuperar menús similares a preferencias del usuario
- ✅ **Reducción de datos**: De 1602 recetas a ~50-100 representativas

### **Flujo Completo**

```
API Spoonacular
      ↓
[1. ExpandDatabase_Optimized.py]
      ↓
recipes_optimized.json (estructura organizada por features)
      ↓
[2. FeatureEngineering.py]
      ↓
recipe_features_normalized.csv (matriz de features)
      ↓
[3. ClusteringPipeline.py]
      ↓
representative_recipes.json (50-100 recetas representativas)
      ↓
[4. CBR_Engine.py] (futuro)
      ↓
Sistema de recomendación de menús
```

---

## 📁 ESTRUCTURA DE ARCHIVOS

### **Scripts Principales**

| Archivo | Propósito | Input | Output |
|---------|-----------|-------|--------|
| `ExpandDatabase_Optimized.py` | Obtiene recetas de API | API Spoonacular | `recipes_optimized.json` |
| `FeatureEngineering.py` | Transforma features | `recipes_optimized.json` | 3 CSVs de features |
| `ClusteringPipeline.py` | Clustering y selección | CSVs de features | `representative_recipes.json` |

### **Archivos de Datos**

| Archivo | Descripción | Tamaño aprox. |
|---------|-------------|---------------|
| `recipes_optimized.json` | Recetas en estructura optimizada | ~5-10 MB |
| `recipe_features_raw.csv` | Features sin normalizar | ~2-5 MB |
| `recipe_features_normalized.csv` | Features normalizadas (μ=0, σ=1) | ~2-5 MB |
| `recipe_features_pca.csv` | Features con PCA (~50 dims) | ~500 KB |
| `representative_recipes.json` | Recetas representativas finales | ~500 KB |
| `clustering_metrics.json` | Métricas de calidad del clustering | ~5 KB |

### **Visualizaciones**

| Archivo | Descripción |
|---------|-------------|
| `optimal_k_analysis.png` | Método del codo + Silhouette |
| `kmeans_clusters.png` | Visualización 2D de clusters |

---

## 🔄 PIPELINE PASO A PASO

### **PASO 1: Obtener Recetas Optimizadas**

```bash
# Configurar API Key
$env:API_KEY = "tu_api_key_aqui"

# Ejecutar script
python ExpandDatabase_Optimized.py
```

**Parámetros configurables** (editar en el script):
```python
diets = None          # 'vegan', 'vegetarian', etc.
intolerances = None   # 'dairy', 'gluten', etc.
meal_type = 'main course'  # 'dessert', 'appetizer', 'side dish'
num_recipes = 100
```

**Output**: `recipes_optimized.json`

**Estructura JSON**:
```json
{
  "id": 123,
  "title": "Recipe Name",
  
  "features_numeric": {
    "price_per_serving": 24.5,
    "ready_in_minutes": 35,
    "health_score": 72,
    "calories": 520
  },
  
  "features_categorical": {
    "vegan": false,
    "dish_class": "Main",
    "season": "spring"
  },
  
  "features_text": {
    "cuisines": ["Indian", "Asian"],
    "ingredients": ["chicken", "yogurt", ...]
  },
  
  "taste_profile": {
    "sweetness": 35.2,
    "saltiness": 62.8
  },
  
  "derived_features": {
    "complexity_score": 8.5,
    "value_score": 3.4,
    "price_category": "mid"
  },
  
  "metadata": {
    "wine_pairing": "Aromatic white wine",
    "kosher": false,
    "halal": true
  }
}
```

---

### **PASO 2: Feature Engineering**

```bash
python FeatureEngineering.py
```

**Proceso interno**:
1. ✅ Extrae 16 features numéricas
2. ✅ Codifica 9 features categóricas (One-Hot)
3. ✅ Vectoriza listas de texto (cuisines, diets, dish_types, occasions)
4. ✅ Aplica TF-IDF a ingredientes (50 features)
5. ✅ Normaliza con StandardScaler
6. ✅ Aplica PCA (reducción a 50 componentes)

**Outputs**:
- `recipe_features_raw.csv` - ~130-150 columnas
- `recipe_features_normalized.csv` - Mismas columnas normalizadas
- `recipe_features_pca.csv` - 50 componentes principales

**Dimensionalidad**:
```
Features numéricas:        16
Features categóricas:      ~20 (después de One-Hot)
Cuisines:                  ~15
Diets:                     ~10
Dish types:                ~15
Occasions:                 ~10
Ingredientes (TF-IDF):     50
─────────────────────────────
TOTAL:                     ~136 features

Después de PCA:            50 features (95% varianza)
```

---

### **PASO 3: Clustering y Selección de Representativos**

```bash
python ClusteringPipeline.py
```

**Proceso interno**:

#### **3.1 Búsqueda de K Óptimo**
- Prueba K desde 5 hasta 30
- Calcula Inertia (método del codo)
- Calcula Silhouette Score
- **Selecciona K con mejor Silhouette**

#### **3.2 K-Means Clustering**
```python
K = 15 (ejemplo)
→ 15 clusters
→ Silhouette: 0.45 (bueno si > 0.4)
→ Davies-Bouldin: 0.8 (bueno si < 1.0)
```

#### **3.3 Selección de Representativos**

**Método 1: Centroide** (recomendado)
- Calcula centroide de cada cluster
- Selecciona las 3 recetas más cercanas al centroide
- **Ventaja**: Recetas "promedio" del cluster

**Método 2: Top Scored**
- Selecciona las 3 recetas con mejor `spoonacular_score`
- **Ventaja**: Recetas de mejor calidad

**Output**:
```
15 clusters × 3 recetas = 45 recetas representativas
```

**Outputs**:
- `representative_recipes.json` - Recetas seleccionadas
- `clustering_metrics.json` - Métricas de calidad
- `optimal_k_analysis.png` - Gráficos de análisis
- `kmeans_clusters.png` - Visualización 2D

---

## 📊 MÉTRICAS DE CALIDAD

### **Silhouette Score** (0 a 1)
- **> 0.7**: Clustering excelente
- **0.5-0.7**: Clustering bueno
- **0.4-0.5**: Clustering aceptable
- **< 0.4**: Clustering pobre

### **Davies-Bouldin Index** (0 a ∞)
- **< 0.5**: Clustering excelente
- **0.5-1.0**: Clustering bueno
- **> 1.0**: Clusters poco separados

### **Calinski-Harabasz Score** (0 a ∞)
- **Mayor es mejor**
- Indica separación entre clusters

---

## ✅ VENTAJAS DEL ENFOQUE

### **1. Estructura Organizada**
```json
// Antes (ConstruirJSON.py)
{
  "id": 123,
  "vegan": true,
  "price": 24.5,
  "ingredients": [...],
  "cuisines": [...],
  ...  // 41 campos mezclados
}

// Después (ExpandDatabase_Optimized.py)
{
  "id": 123,
  "features_numeric": {...},      // Para clustering
  "features_categorical": {...},  // Para clustering
  "features_text": {...},         // Para vectorización
  "derived_features": {...},      // Features calculadas
  "metadata": {...}               // Solo para referencia
}
```

### **2. Reducción Dimensional Efectiva**
```
1602 recetas originales
  ↓ (Clustering K=15)
15 clusters
  ↓ (3 representativos por cluster)
45 recetas finales (97% reducción!)
```

### **3. Features Derivadas Inteligentes**
- `complexity_score`: ingredientes + tiempo
- `value_score`: calidad/precio
- `nutrient_density`: salud/calorías
- `price_category`: budget/mid/premium

### **4. Eliminación de Redundancia**
**Campos eliminados** (no aportan a clustering):
- ❌ `image`, `summary`, `instructions` (presentación)
- ❌ `credits_text`, `source_url` (metadata irrelevante)
- ❌ `low_fodmap`, `sustainable` (baja variabilidad)

**Campos mantenidos** (high-value):
- ✅ Numéricas: precio, tiempo, scores
- ✅ Categóricas: restricciones, tipo de plato
- ✅ Texto: ingredientes, cocinas, dietas
- ✅ Sabor: perfil de 5 dimensiones

---

## 🎯 PRÓXIMOS PASOS

### **Fase 1: Validación** ✅ (Completado)
- [x] Estructura optimizada
- [x] Feature engineering
- [x] Clustering pipeline

### **Fase 2: CBR Engine** (Siguiente)
```python
# CBR_Engine.py

def retrieve_similar_cases(user_preferences, representative_recipes):
    """
    Recupera menús similares a preferencias del usuario
    usando distancia en espacio de features
    """
    # 1. Convertir preferencias a vector de features
    user_vector = preferences_to_features(user_preferences)
    
    # 2. Calcular similitud con representativos
    similarities = []
    for recipe in representative_recipes:
        recipe_vector = recipe_to_features(recipe)
        distance = euclidean_distance(user_vector, recipe_vector)
        similarities.append((recipe, distance))
    
    # 3. Ordenar por similitud
    similarities.sort(key=lambda x: x[1])
    
    # 4. Retornar top-k más similares
    return similarities[:k]

def adapt_case(retrieved_recipe, user_constraints):
    """
    Adapta receta recuperada a restricciones específicas
    """
    # Ejemplo: Si usuario pide vegan, reemplazar ingredientes
    if user_constraints['vegan'] and not retrieved_recipe['vegan']:
        # Aplicar reglas de adaptación
        adapted = apply_veganization_rules(retrieved_recipe)
        return adapted
    
    return retrieved_recipe
```

### **Fase 3: Integración con CLIPS**
```clips
;; Cargar representativos en CLIPS
(definstances REPRESENTATIVES::recipes
  ([Rep_Recipe_1] of Recipe ...)
  ([Rep_Recipe_2] of Recipe ...)
  ...
  ([Rep_Recipe_45] of Recipe ...))

;; Regla de matching con CBR
(defrule match-with-cbr
  ?user <- (user-preferences ...)
  =>
  (bind ?similar-cases (python-call retrieve_similar_cases ?user))
  (assert (similar-recipes ?similar-cases)))
```

### **Fase 4: Evaluación**
- Precisión de clustering (validación manual)
- Calidad de recomendaciones CBR
- Tiempo de respuesta del sistema

---

## 📚 REFERENCIAS Y RECURSOS

### **Clustering**
- [Scikit-learn Clustering](https://scikit-learn.org/stable/modules/clustering.html)
- [K-Means Tutorial](https://realpython.com/k-means-clustering-python/)

### **CBR (Case-Based Reasoning)**
- [Introduction to CBR](https://en.wikipedia.org/wiki/Case-based_reasoning)
- [CBR Cycle](https://www.researchgate.net/publication/220605751_Case-Based_Reasoning_An_Introduction)

### **Feature Engineering**
- [Feature Engineering Guide](https://machinelearningmastery.com/discover-feature-engineering-how-to-engineer-features-and-how-to-get-good-at-it/)
- [TF-IDF Explained](https://monkeylearn.com/blog/what-is-tf-idf/)

---

## 🤝 CONTRIBUCIÓN

¿Mejoras sugeridas?
1. **Más features derivadas**: ratios, combinaciones
2. **Clustering híbrido**: combinar K-Means + DBSCAN
3. **Validación cruzada**: evaluar estabilidad de clusters
4. **UI**: dashboard para visualizar clusters

---

## 📧 CONTACTO

Para preguntas o sugerencias sobre este pipeline, contactar al equipo de desarrollo.

**¡Buena suerte con el clustering y CBR!** 🎉🍽️
