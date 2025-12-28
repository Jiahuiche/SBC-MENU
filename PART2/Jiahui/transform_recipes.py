"""
Script para transformar filtered_recipes111.json a la estructura de cbr_recipes_database.json
Añade cultura y estilo_cocina basándose en análisis gastronómico de ingredientes y técnicas.

Basado en taxonomías culinarias de:
- The Oxford Companion to Food (Alan Davidson)
- On Food and Cooking (Harold McGee)
- Larousse Gastronomique
- UNESCO Intangible Cultural Heritage of Humanity (cuisines)
"""
import json
import re
from typing import Dict, List, Tuple

# =============================================================================
# TAXONOMÍA CULTURAL - Basada en ingredientes característicos
# =============================================================================

CULTURA_PATTERNS = {
    # ASIA
    "Japonesa": {
        "ingredients": ["miso", "soy sauce", "tofu", "sake", "wasabi", "nori", "dashi", 
                       "mirin", "sesame", "teriyaki", "shiitake", "edamame", "seaweed",
                       "rice vinegar", "pickled ginger", "green tea", "matcha", "udon",
                       "soba", "tempura", "panko"],
        "keywords": ["japanese", "sushi", "ramen", "teriyaki", "miso"]
    },
    "China": {
        "ingredients": ["soy sauce", "hoisin", "oyster sauce", "star anise", "five spice",
                       "sesame oil", "ginger", "bok choy", "water chestnuts", "bamboo shoots",
                       "rice wine", "black bean", "szechuan", "chili oil", "wonton"],
        "keywords": ["chinese", "stir fry", "dim sum", "wok", "szechuan", "cantonese"]
    },
    "Tailandesa": {
        "ingredients": ["fish sauce", "lemongrass", "galangal", "kaffir lime", "thai basil",
                       "coconut milk", "palm sugar", "tamarind", "bird's eye chili", 
                       "thai chili", "peanuts", "lime", "cilantro", "rice noodles"],
        "keywords": ["thai", "pad thai", "curry paste", "tom yum", "green curry"]
    },
    "India": {
        "ingredients": ["garam masala", "curry", "turmeric", "cumin", "coriander", "cardamom",
                       "fenugreek", "mustard seeds", "tamarind", "ghee", "paneer", "dal",
                       "basmati", "naan", "chutney", "masala", "tikka", "tandoori",
                       "chilli powder", "cloves", "cinnamon"],
        "keywords": ["indian", "curry", "masala", "tandoori", "biryani", "vindaloo", "korma"]
    },
    "Vietnamita": {
        "ingredients": ["fish sauce", "rice noodles", "rice paper", "mint", "thai basil",
                       "lime", "cilantro", "lemongrass", "star anise", "hoisin"],
        "keywords": ["vietnamese", "pho", "spring roll", "banh mi"]
    },
    "Coreana": {
        "ingredients": ["gochujang", "kimchi", "sesame", "soy sauce", "korean chili",
                       "doenjang", "rice wine", "perilla", "gochugaru"],
        "keywords": ["korean", "bibimbap", "bulgogi", "kimchi"]
    },
    
    # EUROPA
    "Italiana": {
        "ingredients": ["olive oil", "basil", "oregano", "parmesan", "mozzarella", 
                       "tomato", "garlic", "pasta", "risotto", "prosciutto", "pancetta",
                       "balsamic vinegar", "pine nuts", "capers", "anchovies", "pesto",
                       "ricotta", "mascarpone", "polenta", "focaccia", "ciabatta",
                       "marinara", "bolognese", "arrabiata", "penne", "spaghetti", "fettuccine",
                       "lasagna", "gnocchi", "ravioli", "cannoli", "tiramisu", "panna cotta"],
        "keywords": ["italian", "pizza", "pasta", "risotto", "antipasti", "antipasto", 
                    "bruschetta", "caprese", "carbonara", "parmigiana"]
    },
    "Francesa": {
        "ingredients": ["butter", "cream", "shallots", "tarragon", "thyme", "bay leaves",
                       "dijon mustard", "wine", "cognac", "brandy", "crème fraîche",
                       "herbes de provence", "lavender", "chervil", "leek", "gruyere",
                       "brie", "camembert", "duck", "foie gras", "escargot", "truffle"],
        "keywords": ["french", "provencal", "bouillabaisse", "ratatouille", "quiche",
                    "souffle", "bechamel", "hollandaise", "velouté", "bistro"]
    },
    "Española": {
        "ingredients": ["olive oil", "saffron", "paprika", "chorizo", "serrano",
                       "manchego", "sherry", "smoked paprika", "piquillo", "pimiento",
                       "almonds", "garlic", "tomato"],
        "keywords": ["spanish", "paella", "tapas", "gazpacho", "tortilla española"]
    },
    "Griega": {
        "ingredients": ["feta", "olive oil", "oregano", "lemon", "dill", "mint",
                       "yogurt", "cucumber", "olives", "phyllo", "honey", "lamb"],
        "keywords": ["greek", "gyro", "souvlaki", "moussaka", "tzatziki", "spanakopita"]
    },
    "Británica": {
        "ingredients": ["worcestershire", "malt vinegar", "clotted cream", "cheddar",
                       "stilton", "mint sauce", "horseradish", "brown sauce", "custard",
                       "marmalade", "treacle", "oats", "scones"],
        "keywords": ["british", "english", "fish and chips", "roast", "pie", "pudding",
                    "crumble", "scone", "trifle"]
    },
    "Alemana": {
        "ingredients": ["sauerkraut", "caraway", "beer", "rye", "pumpernickel",
                       "bratwurst", "schnitzel", "spätzle", "pretzel"],
        "keywords": ["german", "bavarian", "schnitzel", "strudel"]
    },
    "Húngara": {
        "ingredients": ["paprika", "sour cream", "caraway", "lard", "poppy seeds"],
        "keywords": ["hungarian", "goulash", "paprikash", "strudel"]
    },
    "Rusa/Eslava": {
        "ingredients": ["sour cream", "dill", "beets", "cabbage", "rye", "buckwheat",
                       "smetana", "kefir"],
        "keywords": ["russian", "borscht", "blini", "pierogi", "stroganoff"]
    },
    
    # MEDITERRÁNEO
    "Mediterránea": {
        "ingredients": ["olive oil", "lemon", "garlic", "oregano", "basil", "tomato",
                       "capers", "olives", "feta", "chickpeas", "eggplant", "zucchini",
                       "bell pepper", "artichoke", "sun-dried tomato"],
        "keywords": ["mediterranean", "mezze"]
    },
    "Turca/Medio Oriente": {
        "ingredients": ["pomegranate", "sumac", "za'atar", "tahini", "bulgur", "freekeh",
                       "rose water", "orange blossom", "pistachios", "dates", "figs",
                       "lamb", "chickpeas", "eggplant", "yogurt", "mint", "parsley",
                       "cumin", "coriander", "cinnamon", "allspice"],
        "keywords": ["turkish", "middle eastern", "lebanese", "persian", "falafel",
                    "hummus", "shawarma", "kebab", "baklava", "tabbouleh"]
    },
    "Israelí/Judía": {
        "ingredients": ["tahini", "za'atar", "sumac", "harissa", "preserved lemon",
                       "matzo", "challah"],
        "keywords": ["israeli", "jewish", "kosher", "falafel", "shakshuka"]
    },
    
    # AMÉRICAS
    "Mexicana/Tex-Mex": {
        "ingredients": ["cumin", "chili powder", "jalapeño", "chipotle", "cilantro",
                       "lime", "avocado", "corn", "beans", "tortilla", "tomatillo",
                       "adobo", "ancho", "guajillo", "pasilla", "poblano", "serrano",
                       "epazote", "mexican oregano", "queso fresco", "cotija"],
        "keywords": ["mexican", "tex-mex", "taco", "burrito", "enchilada", "salsa",
                    "guacamole", "quesadilla", "mole", "pozole", "tamale"]
    },
    "Americana": {
        "ingredients": ["corn syrup", "maple syrup", "peanut butter", "bacon",
                       "cheddar", "ranch", "buffalo sauce", "bbq sauce", "ketchup",
                       "mustard", "relish", "pickles", "buttermilk"],
        "keywords": ["american", "bbq", "burger", "mac and cheese", "pancakes",
                    "cornbread", "coleslaw", "buffalo"]
    },
    "Americana/Sureña": {
        "ingredients": ["buttermilk", "cornmeal", "pecans", "bourbon", "molasses",
                       "collard greens", "black-eyed peas", "grits", "okra", "catfish"],
        "keywords": ["southern", "cajun", "creole", "soul food", "fried chicken",
                    "biscuits", "pecan pie"]
    },
    "Caribeña": {
        "ingredients": ["allspice", "scotch bonnet", "jerk seasoning", "rum",
                       "plantain", "coconut", "mango", "papaya", "lime", "thyme",
                       "ginger", "nutmeg", "tamarind"],
        "keywords": ["caribbean", "jamaican", "cuban", "jerk", "mofongo"]
    },
    "Sudamericana/Andina": {
        "ingredients": ["quinoa", "amaranth", "ají", "chimichurri", "dulce de leche",
                       "empanada", "corn", "potato", "beans", "cilantro", "lime"],
        "keywords": ["peruvian", "brazilian", "argentinian", "andean", "ceviche",
                    "empanada", "chimichurri"]
    },
    
    # ÁFRICA
    "Africana/Norte de África": {
        "ingredients": ["harissa", "ras el hanout", "preserved lemon", "couscous",
                       "merguez", "dates", "almonds", "honey", "saffron", "cumin",
                       "coriander", "cinnamon", "ginger", "turmeric", "argan oil"],
        "keywords": ["moroccan", "tunisian", "egyptian", "tagine", "couscous",
                    "north african"]
    },
    "Africana/Subsahariana": {
        "ingredients": ["palm oil", "peanuts", "yam", "cassava", "plantain",
                       "okra", "black-eyed peas", "berbere", "injera"],
        "keywords": ["ethiopian", "west african", "nigerian", "ghanaian"]
    },
    
    # OCEANÍA
    "Australiana/Pacífico": {
        "ingredients": ["macadamia", "vegemite", "lemon myrtle", "finger lime",
                       "wattleseed", "bush tomato", "kangaroo", "barramundi"],
        "keywords": ["australian", "pacific", "polynesian", "hawaiian"]
    },
    
    # FUSIONES
    "Fusión Asiática": {
        "ingredients": ["soy sauce", "ginger", "sesame", "sriracha", "coconut milk",
                       "curry", "lemongrass", "fish sauce", "rice"],
        "keywords": ["asian fusion", "pan-asian"]
    },
    "Fusión Global": {
        "ingredients": [],  # Combinación de múltiples orígenes
        "keywords": ["fusion", "modern", "contemporary"]
    },
    "Internacional": {
        "ingredients": [],
        "keywords": []
    }
}

# =============================================================================
# TAXONOMÍA DE ESTILOS DE COCINA
# =============================================================================

ESTILO_PATTERNS = {
    "Gourmet": {
        "ingredients": ["truffle", "foie gras", "saffron", "caviar", "lobster",
                       "duck", "veal", "filet mignon", "champagne", "shallots",
                       "reduction", "demi-glace", "microgreens"],
        "keywords": ["gourmet", "fine dining", "elegant", "sophisticated"],
        "complexity_threshold": 60
    },
    "Gourmet/Pastelería Clásica": {
        "ingredients": ["fondant", "ganache", "buttercream", "choux", "puff pastry",
                       "crème pâtissière", "meringue", "chocolate mousse", "génoise"],
        "keywords": ["pastry", "patisserie", "baking", "classic dessert"],
        "complexity_threshold": 70
    },
    "Tradicional": {
        "ingredients": [],
        "keywords": ["traditional", "classic", "authentic", "heritage", "rustic"],
        "complexity_threshold": 30
    },
    "Tradicional/Casero": {
        "ingredients": ["butter", "flour", "eggs", "milk", "sugar", "vanilla"],
        "keywords": ["homemade", "comfort food", "home-style", "grandma", "family"],
        "complexity_threshold": 25
    },
    "Moderno": {
        "ingredients": ["molecular", "foam", "gel", "spherification", "sous vide"],
        "keywords": ["modern", "contemporary", "innovative", "new"],
        "complexity_threshold": 45
    },
    "Moderno/Saludable": {
        "ingredients": ["quinoa", "kale", "avocado", "chia", "flaxseed", "hemp",
                       "spirulina", "acai", "goji", "matcha", "turmeric", "ginger",
                       "whole grain", "brown rice", "oats", "almonds", "walnuts"],
        "keywords": ["healthy", "superfood", "nutritious", "clean eating", "wellness",
                    "low-fat", "high-protein", "antioxidant"],
        "complexity_threshold": 30
    },
    "Moderno/Vegano": {
        "ingredients": ["tofu", "tempeh", "seitan", "nutritional yeast", "cashew cream",
                       "coconut cream", "aquafaba", "plant-based", "vegan cheese",
                       "flax egg", "chia egg", "oat milk", "almond milk", "coconut yogurt"],
        "keywords": ["vegan", "plant-based", "cruelty-free", "dairy-free alternative"],
        "complexity_threshold": 35
    },
    "Moderno/Sin Gluten": {
        "ingredients": ["rice flour", "almond flour", "coconut flour", "tapioca",
                       "arrowroot", "xanthan gum", "psyllium", "sorghum flour",
                       "buckwheat flour", "oat flour"],
        "keywords": ["gluten-free", "celiac-friendly", "grain-free"],
        "complexity_threshold": 40
    },
    "Moderno/Refrescante": {
        "ingredients": ["mint", "lime", "lemon", "watermelon", "cucumber", "basil",
                       "citrus", "sorbet", "granita", "ice"],
        "keywords": ["refreshing", "light", "summer", "cool", "iced"],
        "complexity_threshold": 20
    },
    "Street Food": {
        "ingredients": ["hot dog", "pretzel", "nachos", "fries", "wrap"],
        "keywords": ["street food", "food truck", "casual", "quick", "on-the-go"],
        "complexity_threshold": 20
    },
    "Rústico": {
        "ingredients": ["rustic bread", "olive oil", "herbs", "roasted vegetables",
                       "grains", "legumes", "root vegetables"],
        "keywords": ["rustic", "farmhouse", "country", "hearty", "wholesome"],
        "complexity_threshold": 30
    }
}


def normalize_text(text: str) -> str:
    """Normaliza texto para comparación."""
    if not text:
        return ""
    return text.lower().strip()


def calculate_complexity(ingredients: List[str], instructions: str = "") -> int:
    """
    Calcula un score de complejidad basado en ingredientes e instrucciones.
    Escala: 0-100
    """
    base_score = 10
    
    # Factor por número de ingredientes
    num_ingredients = len(ingredients)
    if num_ingredients <= 5:
        ingredient_score = 10
    elif num_ingredients <= 10:
        ingredient_score = 25
    elif num_ingredients <= 15:
        ingredient_score = 40
    else:
        ingredient_score = min(60, 40 + (num_ingredients - 15) * 2)
    
    # Factor por ingredientes técnicos/especiales
    technical_ingredients = ["reduction", "stock", "demi-glace", "roux", "fond",
                            "clarified butter", "tempered chocolate", "meringue",
                            "caramel", "ganache", "mousse", "soufflé", "phyllo",
                            "puff pastry", "choux", "brioche"]
    
    tech_score = sum(5 for ing in ingredients 
                    if any(t in normalize_text(ing) for t in technical_ingredients))
    
    # Factor por longitud de instrucciones (si está disponible)
    instruction_score = 0
    if instructions:
        words = len(instructions.split())
        if words > 300:
            instruction_score = 20
        elif words > 150:
            instruction_score = 10
        elif words > 50:
            instruction_score = 5
    
    total = base_score + ingredient_score + tech_score + instruction_score
    return min(100, total)


def calculate_health_factor(ingredients: List[str], restrictions: List[str]) -> int:
    """
    Calcula un factor de salud basado en ingredientes y restricciones.
    Escala: 0-100
    """
    base_score = 50
    
    # Ingredientes saludables (+)
    healthy_ingredients = ["vegetables", "fruit", "whole grain", "legumes", "nuts",
                          "seeds", "olive oil", "fish", "lean", "kale", "spinach",
                          "broccoli", "quinoa", "avocado", "berries", "citrus",
                          "herbs", "garlic", "ginger", "turmeric", "tomato", "carrot",
                          "zucchini", "squash", "beans", "lentils", "chickpeas"]
    
    # Ingredientes menos saludables (-)
    unhealthy_ingredients = ["sugar", "corn syrup", "butter", "cream", "fried",
                            "bacon", "processed", "white flour", "shortening",
                            "lard", "margarine", "candy", "syrup", "frosting",
                            "deep-fried", "batter"]
    
    # Calcular scores
    healthy_score = sum(3 for ing in ingredients 
                       if any(h in normalize_text(ing) for h in healthy_ingredients))
    
    unhealthy_score = sum(4 for ing in ingredients 
                         if any(u in normalize_text(ing) for u in unhealthy_ingredients))
    
    # Bonus por restricciones dietéticas saludables
    restriction_bonus = 0
    if "vegan" in [r.lower() for r in restrictions]:
        restriction_bonus += 10
    if "vegetarian" in [r.lower() for r in restrictions]:
        restriction_bonus += 5
    if "gluten free" in [r.lower() for r in restrictions]:
        restriction_bonus += 3
    if "dairy free" in [r.lower() for r in restrictions]:
        restriction_bonus += 3
    
    total = base_score + healthy_score - unhealthy_score + restriction_bonus
    return max(10, min(100, total))


def detect_cultura(title: str, ingredients: List[str]) -> str:
    """
    Detecta la cultura culinaria basándose en el título e ingredientes.
    Utiliza un sistema de puntuación para determinar la mejor coincidencia.
    """
    title_lower = normalize_text(title)
    ingredients_lower = [normalize_text(ing) for ing in ingredients]
    ingredients_text = " ".join(ingredients_lower)
    
    scores = {}
    
    for cultura, patterns in CULTURA_PATTERNS.items():
        score = 0
        
        # Buscar keywords en el título
        for keyword in patterns.get("keywords", []):
            if keyword in title_lower:
                score += 15  # Alta prioridad para keywords en título
        
        # Buscar ingredientes característicos
        for ingredient in patterns.get("ingredients", []):
            ingredient_lower = ingredient.lower()
            # Coincidencia exacta o parcial en la lista de ingredientes
            for ing in ingredients_lower:
                if ingredient_lower in ing or ing in ingredient_lower:
                    score += 3
                    break
        
        if score > 0:
            scores[cultura] = score
    
    # Seleccionar la cultura con mayor puntuación
    if scores:
        # Ordenar por puntuación descendente
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_match = sorted_scores[0]
        
        # Si hay empate o puntuación baja, verificar si es fusión
        if len(sorted_scores) >= 2:
            if sorted_scores[0][1] == sorted_scores[1][1] and sorted_scores[0][1] < 10:
                return "Internacional"
            elif sorted_scores[0][1] < 6 and sorted_scores[1][1] >= 4:
                return "Fusión Global"
        
        return best_match[0]
    
    # Análisis de respaldo basado en ingredientes comunes
    if any(ing in ingredients_text for ing in ["olive oil", "garlic", "lemon", "oregano"]):
        return "Mediterránea"
    elif any(ing in ingredients_text for ing in ["soy sauce", "ginger", "sesame"]):
        return "Fusión Asiática"
    elif any(ing in ingredients_text for ing in ["butter", "cream", "vanilla"]):
        return "Europea"
    
    return "Internacional"


def detect_estilo_cocina(title: str, ingredients: List[str], restrictions: List[str],
                         complexity: int) -> str:
    """
    Detecta el estilo de cocina basándose en múltiples factores.
    """
    title_lower = normalize_text(title)
    ingredients_lower = [normalize_text(ing) for ing in ingredients]
    ingredients_text = " ".join(ingredients_lower)
    restrictions_lower = [r.lower() for r in restrictions]
    
    # Prioridad 1: Estilos específicos por restricciones
    if "vegan" in restrictions_lower:
        # Verificar si es moderno/saludable o tradicional vegano
        healthy_count = sum(1 for ing in ingredients_lower 
                          if any(h in ing for h in ["quinoa", "kale", "chia", "superfood"]))
        if healthy_count >= 2 or any(k in title_lower for k in ["healthy", "superfood"]):
            return "Moderno/Saludable"
        return "Moderno/Vegano"
    
    # Prioridad 2: Gluten-free moderno
    if "gluten free" in restrictions_lower:
        gf_flours = ["rice flour", "almond flour", "coconut flour", "tapioca", "sorghum"]
        if any(f in ingredients_text for f in gf_flours):
            return "Moderno/Sin Gluten"
    
    # Prioridad 3: Detectar por keywords en título
    for estilo, patterns in ESTILO_PATTERNS.items():
        for keyword in patterns.get("keywords", []):
            if keyword in title_lower:
                return estilo
    
    # Prioridad 4: Detectar por ingredientes especiales
    scores = {}
    for estilo, patterns in ESTILO_PATTERNS.items():
        score = 0
        for ingredient in patterns.get("ingredients", []):
            if ingredient.lower() in ingredients_text:
                score += 2
        if score > 0:
            scores[estilo] = score
    
    if scores:
        best_match = max(scores.items(), key=lambda x: x[1])
        if best_match[1] >= 4:
            return best_match[0]
    
    # Prioridad 5: Basarse en complejidad
    if complexity >= 70:
        return "Gourmet"
    elif complexity >= 50:
        return "Moderno"
    elif complexity >= 35:
        return "Tradicional"
    else:
        return "Tradicional/Casero"


def map_meal_type(meal_types: str) -> str:
    """
    Mapea los tipos de comida originales a starter/main/dessert.
    """
    meal_lower = normalize_text(meal_types)
    
    # Dessert patterns
    dessert_keywords = ["dessert", "sweet", "cake", "pie", "cookie", "brownie",
                       "pudding", "ice cream", "sorbet", "candy", "chocolate",
                       "pastry", "tart", "mousse", "fudge", "truffle", "brittle"]
    
    # Starter patterns
    starter_keywords = ["starter", "appetizer", "antipasti", "antipasto", "hor d'oeuvre",
                       "hors d'oeuvre", "snack", "finger food", "fingerfood", "salad",
                       "soup", "bite", "dip", "spread"]
    
    # Main course patterns
    main_keywords = ["main course", "main dish", "dinner", "lunch", "entree", "entrée",
                    "roast", "steak", "chicken", "fish", "pasta", "rice dish"]
    
    # Check for dessert first
    if any(kw in meal_lower for kw in dessert_keywords):
        return "dessert"
    
    # Check for starter
    if any(kw in meal_lower for kw in starter_keywords):
        return "starter"
    
    # Check for main
    if any(kw in meal_lower for kw in main_keywords):
        return "main"
    
    # Default based on additional analysis
    return "main"


def determine_course_from_title(title: str, ingredients: List[str] = None) -> str:
    """
    Determina el tipo de plato basándose en el título e ingredientes.
    """
    title_lower = normalize_text(title)
    ingredients_lower = [normalize_text(ing) for ing in (ingredients or [])]
    ingredients_text = " ".join(ingredients_lower)
    
    # Dessert indicators
    dessert_words = ["cake", "pie", "cookie", "brownie", "pudding", "ice cream",
                    "sorbet", "candy", "fudge", "truffle", "brittle",
                    "custard", "mousse", "tart", "crumble", "cobbler",
                    "cheesecake", "tiramisu", "panna cotta", "macaroon", "biscuit",
                    "dessert", "caramel", "frosting", "cupcake", "muffin",
                    "donut", "doughnut", "parfait", "sundae", "gelato",
                    "popsicle", "granita", "compote", "meringue", "pavlova",
                    "soufflé", "souffle", "éclair", "eclair", "macaron",
                    "scone", "pastry", "danish", "croissant", "strudel",
                    "baklava", "halva", "flan", "crème brûlée", "creme brulee"]
    
    # Ingredients that strongly indicate dessert
    dessert_ingredients = ["sugar", "chocolate", "cocoa", "vanilla extract", 
                          "powdered sugar", "confectioner", "icing", "frosting",
                          "maple syrup", "honey", "brown sugar", "molasses",
                          "whipped cream", "ice cream"]
    
    # Starter indicators
    starter_words = ["salad", "soup", "dip", "spread", "bruschetta", "crostini",
                    "appetizer", "starter", "bite", "roll", "spring roll", "dumpling",
                    "samosa", "empanada", "toast", "tartare", "ceviche", "carpaccio",
                    "antipasti", "antipasto", "tapas", "mezze", "finger food",
                    "canapé", "canape", "amuse", "hors d'oeuvre", "croquette",
                    "fritter", "pakora", "tempura", "gyoza", "wonton", "dim sum",
                    "trifolati", "funghetti", "mushroom", "hummus", "guacamole",
                    "tzatziki", "baba ganoush", "edamame", "satay", "skewer"]
    
    # Main course indicators
    main_words = ["roast", "steak", "grilled", "braised", "stew", "curry",
                 "pasta", "risotto", "lasagna", "casserole", "tagine",
                 "chicken", "beef", "pork", "lamb", "fish", "salmon", "tuna",
                 "shrimp", "lobster", "crab", "paella", "biryani", "kebab",
                 "burger", "sandwich", "wrap", "enchilada", "burrito", "taco",
                 "pizza", "noodle", "fried rice", "lo mein", "pad thai",
                 "simmered", "linefish", "fillet"]
    
    # Check for savory main course indicators first
    if any(word in title_lower for word in main_words):
        return "main"
    
    # Check for starter indicators
    if any(word in title_lower for word in starter_words):
        return "starter"
    
    # Check for dessert by title
    if any(word in title_lower for word in dessert_words):
        return "dessert"
    
    # Check ingredients for dessert indicators (requires many sweet ingredients)
    if ingredients:
        dessert_ing_count = sum(1 for ing in dessert_ingredients 
                               if any(ing in i for i in ingredients_lower))
        savory_indicators = ["garlic", "onion", "salt", "pepper", "olive oil",
                            "chicken", "beef", "fish", "vegetable", "broth"]
        savory_count = sum(1 for ing in savory_indicators 
                          if any(ing in i for i in ingredients_lower))
        
        if dessert_ing_count >= 3 and savory_count < 2:
            return "dessert"
        elif savory_count >= 2:
            return "main"
    
    return "main"


def map_season(season_text: str) -> str:
    """Mapea el texto de temporada al formato estándar."""
    season_lower = normalize_text(season_text)
    
    if "spring" in season_lower:
        return "Spring"
    elif "summer" in season_lower:
        return "Summer"
    elif "fall" in season_lower or "autumn" in season_lower:
        return "Fall"
    elif "winter" in season_lower:
        return "Winter"
    else:
        return "All"


def transform_recipe(recipe: Dict) -> Dict:
    """
    Transforma una receta del formato original al formato CBR.
    """
    title = recipe.get("title", "")
    ingredients = recipe.get("ingredients", [])
    restrictions = recipe.get("restrictions", [])
    meal_types = recipe.get("mealTypes", "")
    
    # Determinar course_type
    course_from_meals = map_meal_type(meal_types)
    course_from_title = determine_course_from_title(title, ingredients)
    
    # Lógica mejorada para determinar course_type
    # Priorizar análisis del título e ingredientes sobre mealTypes genéricos
    if course_from_title in ["starter", "dessert"]:
        course_type = course_from_title
    elif course_from_meals in ["starter", "dessert"]:
        course_type = course_from_meals
    else:
        course_type = course_from_title
    
    # Calcular métricas
    complexity = calculate_complexity(ingredients)
    health_factor = calculate_health_factor(ingredients, restrictions)
    
    # Detectar cultura y estilo
    cultura = detect_cultura(title, ingredients)
    estilo = detect_estilo_cocina(title, ingredients, restrictions, complexity)
    
    # Mapear temporada
    season = map_season(recipe.get("seasonText", "Any season"))
    
    # Construir receta transformada
    transformed = {
        "recipe_id": recipe.get("id"),
        "title": title,
        "course_type": course_type,
        "servings": recipe.get("servings"),
        "price_per_serving": recipe.get("pricePerServing"),
        "ready_in_minutes": recipe.get("readyInMinutes", 0),
        "ingredients": ingredients,
        "restrictions": restrictions,
        "instructions": recipe.get("instructions", ""),
        "cultura": cultura,
        "estilo_cocina": estilo,
        "season": season,
        "complexity_score": complexity,
        "health_factor": health_factor
    }
    
    return transformed


def transform_database(input_path: str, output_path: str):
    """
    Transforma la base de datos completa.
    """
    print(f"📖 Cargando recetas desde: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)
    
    print(f"   Encontradas {len(recipes)} recetas")
    
    # Transformar cada receta
    transformed_recipes = []
    cultura_stats = {}
    estilo_stats = {}
    course_stats = {"starter": 0, "main": 0, "dessert": 0}
    
    for i, recipe in enumerate(recipes):
        if (i + 1) % 50 == 0:
            print(f"   Procesando receta {i + 1}/{len(recipes)}...")
        
        transformed = transform_recipe(recipe)
        transformed_recipes.append(transformed)
        
        # Estadísticas
        cultura = transformed["cultura"]
        estilo = transformed["estilo_cocina"]
        course = transformed["course_type"]
        
        cultura_stats[cultura] = cultura_stats.get(cultura, 0) + 1
        estilo_stats[estilo] = estilo_stats.get(estilo, 0) + 1
        course_stats[course] = course_stats.get(course, 0) + 1
    
    # Construir estructura final
    output_data = {
        "metadata": {
            "version": "2.0",
            "created_date": "2025-12-28",
            "description": "CBR Recipe Database - Individual dishes for Case-Based Reasoning with cultural and cooking style attributes per dish",
            "total_recipes": len(transformed_recipes),
            "structure": "Each recipe contains complete features including cultura and estilo_cocina for similarity matching"
        },
        "recipes": transformed_recipes,
        "cbr_features_index": {
            "numerical_features": [
                "price_per_serving",
                "ready_in_minutes",
                "servings",
                "complexity_score",
                "health_factor"
            ],
            "categorical_features": [
                "course_type",
                "season",
                "cultura",
                "estilo_cocina"
            ],
            "list_features": [
                "ingredients",
                "restrictions"
            ]
        },
        "cultura_taxonomy": {
            "description": "Clasificación cultural de los platos basada en origen geográfico, ingredientes típicos y técnicas culinarias tradicionales",
            "categories": sorted(list(set(r["cultura"] for r in transformed_recipes)))
        },
        "estilo_cocina_taxonomy": {
            "description": "Clasificación del estilo de cocina basada en técnicas, presentación y filosofía culinaria",
            "categories": sorted(list(set(r["estilo_cocina"] for r in transformed_recipes)))
        }
    }
    
    # Guardar resultado
    print(f"\n💾 Guardando base de datos transformada en: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Imprimir estadísticas
    print("\n" + "="*60)
    print("📊 ESTADÍSTICAS DE TRANSFORMACIÓN")
    print("="*60)
    
    print(f"\n🍽️  Distribución por tipo de plato:")
    for course, count in sorted(course_stats.items()):
        print(f"   {course}: {count} ({100*count/len(recipes):.1f}%)")
    
    print(f"\n🌍 Top 10 Culturas detectadas:")
    for cultura, count in sorted(cultura_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {cultura}: {count}")
    
    print(f"\n👨‍🍳 Estilos de cocina detectados:")
    for estilo, count in sorted(estilo_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {estilo}: {count}")
    
    print(f"\n✅ Transformación completada: {len(transformed_recipes)} recetas procesadas")
    
    return output_data


if __name__ == "__main__":
    INPUT_PATH = "filtered_recipes111.json"
    OUTPUT_PATH = "filtered_recipes_cbr.json"
    
    transform_database(INPUT_PATH, OUTPUT_PATH)
