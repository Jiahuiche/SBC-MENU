# 🍽️ Base de Datos CBR de Menús Completos

## 📋 Descripción General

Esta base de datos contiene **10 menús completos representativos** diseñados específicamente para **Case-Based Reasoning (CBR)** en sistemas de recomendación de menús.

Cada menú incluye:
- **Starter** (Entrante/Aperitivo)
- **Main Course** (Plato Principal)
- **Dessert** (Postre)

---

## 🎯 Objetivo

Proporcionar una **base de casos** diversa y representativa para:

1. **Recuperación de casos similares**: Encontrar menús parecidos a las preferencias del usuario
2. **Recomendación personalizada**: Sugerir menús basados en restricciones dietéticas, presupuesto, tiempo, etc.
3. **Adaptación de casos**: Modificar menús existentes según nuevos requisitos

---

## 📊 Estructura del Archivo JSON

### **Nivel 1: Metadata**

```json
{
  "metadata": {
    "version": "1.0",
    "created_date": "2025-12-01",
    "description": "CBR Menu Database",
    "total_menus": 10,
    "structure": "Each menu contains Starter + Main + Dessert"
  }
}
```

### **Nivel 2: Menus**

Cada menú tiene la siguiente estructura:

```json
{
  "menu_id": 1,
  "menu_name": "Menu 1: Corn Salsa",
  "description": "Complete menu featuring Corn Salsa as main course",
  
  "courses": { ... },      // Detalles de cada plato
  "features": { ... },     // Características del menú completo
  "similarity_features": { ... }  // Features para calcular similitud
}
```

---

## 🔍 Descripción de Campos

### **courses** (Detalles de cada plato)

Cada `course` (starter, main, dessert) contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `recipe_id` | integer | ID único de Spoonacular |
| `title` | string | Nombre del plato |
| `servings` | integer | Número de porciones |
| `price_per_serving` | float | Precio por porción (centavos) |
| `ready_in_minutes` | integer | Tiempo de preparación |
| `ingredients` | list<string> | Lista de ingredientes |
| `restrictions` | list<string> | Restricciones dietéticas cumplidas |

**Ejemplo:**
```json
"starter": {
  "recipe_id": 640062,
  "title": "Corn Avocado Salsa",
  "servings": 2,
  "price_per_serving": 130.73,
  "ready_in_minutes": 0,
  "ingredients": ["avocado", "balsamic vinegar", "cumin", ...],
  "restrictions": ["vegan", "gluten free", "vegetarian", "dairy free"]
}
```

---

### **features** (Características del menú completo)

Estos son los **features principales** para filtrado y matching:

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `total_price_per_serving` | float | Precio total del menú | 388.75 |
| `price_category` | string | Categoría de precio | "budget", "moderate", "premium", "luxury" |
| `avg_ready_time_minutes` | integer | Tiempo promedio | 25 |
| `time_category` | string | Categoría de tiempo | "quick", "moderate", "elaborate" |
| `season` | string | Estación recomendada | "Summer", "Winter", "Fall", "Spring", "Any season" |
| `wine_pairing` | string | Maridaje de vino | "White wine", "Red wine", "No wine pairing" |
| `is_kosher` | boolean | ¿Es kosher TODO el menú? | true/false |
| `is_halal` | boolean | ¿Es halal TODO el menú? | true/false |
| `common_dietary_restrictions` | list<string> | Restricciones comunes a TODO el menú | ["vegetarian", "gluten free"] |
| `is_vegetarian` | boolean | ¿Es vegetariano TODO el menú? | true/false |
| `is_vegan` | boolean | ¿Es vegano TODO el menú? | true/false |
| `is_gluten_free` | boolean | ¿Es gluten-free TODO el menú? | true/false |
| `is_dairy_free` | boolean | ¿Es dairy-free TODO el menú? | true/false |

**Ejemplo:**
```json
"features": {
  "total_price_per_serving": 388.75,
  "price_category": "moderate",
  "avg_ready_time_minutes": 0,
  "time_category": "quick",
  "season": "Summer",
  "wine_pairing": "No wine pairing",
  "is_kosher": true,
  "is_halal": true,
  "common_dietary_restrictions": ["vegetarian", "gluten free"],
  "is_vegetarian": true,
  "is_vegan": false,
  "is_gluten_free": true,
  "is_dairy_free": false
}
```

---

### **similarity_features** (Features para cálculo de similitud)

Estos campos se usan para **calcular distancia/similitud** entre menús:

| Campo | Tipo | Descripción | Rango |
|-------|------|-------------|-------|
| `total_ingredients_count` | integer | Total de ingredientes únicos en el menú | 5-50 |
| `complexity_score` | float | Complejidad del menú (0=simple, 100=complejo) | 0-100 |
| `health_factor` | float | Factor de salud (0=bajo, 100=muy saludable) | 0-100 |
| `cuisine_diversity` | integer | Número de cocinas diferentes en el menú | 0-5 |

**Ejemplo:**
```json
"similarity_features": {
  "total_ingredients_count": 22,
  "complexity_score": 52.0,
  "health_factor": 61.7,
  "cuisine_diversity": 0
}
```

---

## 🔢 Índice de Features (para CBR)

### **Features Numéricos** (usar distancia euclidiana o Manhattan)

```python
numerical_features = [
    "total_price_per_serving",
    "avg_ready_time_minutes",
    "total_ingredients_count",
    "complexity_score",
    "health_factor",
    "cuisine_diversity"
]
```

### **Features Categóricos** (usar coincidencia exacta o embedding)

```python
categorical_features = [
    "price_category",      # budget, moderate, premium, luxury
    "time_category",       # quick, moderate, elaborate
    "season",              # Spring, Summer, Fall, Winter, Any season
    "wine_pairing"         # White wine, Red wine, No wine pairing, etc.
]
```

### **Features Booleanos** (usar coincidencia binaria)

```python
boolean_features = [
    "is_kosher",
    "is_halal",
    "is_vegetarian",
    "is_vegan",
    "is_gluten_free",
    "is_dairy_free"
]
```

### **Features de Lista** (usar Jaccard similarity o intersección)

```python
list_features = [
    "common_dietary_restrictions"
]
```

---

## 📈 Uso en CBR

### **1. Recuperación de Casos (Retrieve)**

Calcular similitud entre el **caso nuevo** (preferencias del usuario) y los **casos almacenados** (menús en la BD).

**Ejemplo de función de similitud:**

```python
def calculate_similarity(user_prefs, menu):
    """
    Calcula similitud entre preferencias del usuario y un menú
    
    Parámetros:
        user_prefs: dict con preferencias (e.g., {"is_vegan": True, "max_price": 400})
        menu: dict del menú de la BD
    
    Returns:
        float: similarity score (0-1)
    """
    score = 0
    weights = {
        'dietary': 0.4,      # 40% peso
        'price': 0.3,        # 30% peso
        'time': 0.2,         # 20% peso
        'season': 0.1        # 10% peso
    }
    
    # Similitud dietética (restricciones)
    if user_prefs.get('is_vegan') == menu['features']['is_vegan']:
        score += weights['dietary']
    elif user_prefs.get('is_vegetarian') == menu['features']['is_vegetarian']:
        score += weights['dietary'] * 0.5
    
    # Similitud de precio
    price_diff = abs(user_prefs.get('max_price', 500) - menu['features']['total_price_per_serving'])
    price_score = max(0, 1 - (price_diff / 500))  # Normalizar
    score += weights['price'] * price_score
    
    # Similitud de tiempo
    time_diff = abs(user_prefs.get('max_time', 60) - menu['features']['avg_ready_time_minutes'])
    time_score = max(0, 1 - (time_diff / 60))
    score += weights['time'] * time_score
    
    # Similitud de estación
    if user_prefs.get('season') == menu['features']['season']:
        score += weights['season']
    
    return score
```

### **2. Reutilización (Reuse)**

Adaptar el menú más similar a las necesidades exactas del usuario.

**Ejemplo:**
- Si el menú es vegetariano pero el usuario es vegano → Reemplazar dessert por opción vegana
- Si el presupuesto es menor → Sugerir ingredientes alternativos más baratos

### **3. Revisión (Revise)**

Validar si el menú adaptado cumple con todas las restricciones.

```python
def validate_menu(menu, user_prefs):
    """Valida si el menú cumple las restricciones del usuario"""
    checks = []
    
    # Check dietético
    if user_prefs.get('is_vegan') and not menu['features']['is_vegan']:
        checks.append("❌ Menu is not vegan")
    
    # Check precio
    if menu['features']['total_price_per_serving'] > user_prefs.get('max_price', 1000):
        checks.append("❌ Menu exceeds budget")
    
    # Check tiempo
    if menu['features']['avg_ready_time_minutes'] > user_prefs.get('max_time', 120):
        checks.append("❌ Menu takes too long")
    
    return len(checks) == 0, checks
```

### **4. Retención (Retain)**

Almacenar nuevos menús exitosos en la base de datos para futuras consultas.

---

## 🎯 Ejemplos de Menús en la Base de Datos

### **Menu 1: Corn Salsa** (Vegetariano, Gluten-Free, Summer)
- **Starter**: Corn Avocado Salsa
- **Main**: Corn Salsa
- **Dessert**: Peanut Brittle
- **Precio**: $388.75 (moderate)
- **Restricciones**: Vegetarian, Gluten-Free, Kosher, Halal

### **Menu 2: Simple Squash Salad** (Vegano, Summer)
- **Starter**: Maple & Curry Acorn Squash
- **Main**: Simple Squash Salad
- **Dessert**: Wild Blackberry Sorbet
- **Precio**: $217.41 (moderate)
- **Restricciones**: Vegan, Gluten-Free, Kosher, Halal

### **Menu 5: Monastery soup** (Winter, con maridaje)
- **Starter**: Stuffed Buttercup Squash
- **Main**: Monastery soup
- **Dessert**: Pecan Pie
- **Precio**: $596.93 (premium)
- **Vino**: Light Red wine or White wine

---

## 📦 Archivos

| Archivo | Descripción |
|---------|-------------|
| `cbr_menu_database.json` | Base de datos de 10 menús completos |
| `CreateCBRMenuDatabase.py` | Script generador (análisis + selección diversa) |
| `README_CBR_DATABASE.md` | Esta documentación |

---

## 🚀 Próximos Pasos

1. **Implementar motor CBR** que use esta base de datos
2. **Expandir a 50-100 menús** usando clustering del pipeline principal
3. **Añadir features adicionales**: calorías, macros, alergias específicas
4. **Interfaz de consulta**: Sistema que permita queries tipo:
   - "Quiero un menú vegano para verano con presupuesto medio"
   - "Dame un menú kosher rápido de preparar"
   - "Necesito un menú gluten-free para invierno con maridaje de vino"

---

## 📚 Referencias

- **Spoonacular API**: Fuente de recetas originales
- **CBR Methodology**: Retrieve → Reuse → Revise → Retain
- **Similarity Metrics**: Euclidean distance (numerical), Jaccard similarity (categorical), Hamming distance (boolean)

---

**Autor**: Sistema de Generación Automática CBR  
**Fecha**: 2025-12-01  
**Versión**: 1.0
