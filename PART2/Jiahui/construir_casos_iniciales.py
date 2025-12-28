import json
from pathlib import Path
from collections import Counter
from math import isfinite

RECIPES_PATH = Path("cbr_recipes_database.json")
METACASES_PATH = Path("meta_cases_cultura_estilo.json")
OUT_PATH = Path("case_base_menus.json")

COURSES = ["starter", "main", "dessert"]

# -------------------------
# Utils
# -------------------------
def split_taxonomy(value: str):
    """'Italiana/Toscana' -> {'italiana','toscana'} ; 'Fusión Americana-India' -> {'fusion','americana','india'}"""
    if value is None:
        return set()
    v = str(value).lower().strip()
    v = v.replace("fusión", "fusion")
    for ch in ["/", "-", ","]:
        v = v.replace(ch, " ")
    toks = {t for t in v.split() if t}
    # añade token fusion explícito si aparece
    if "fusion" in toks:
        toks.add("fusion")
    return toks

def dominant_key(count_dict: dict, default=""):
    if not count_dict:
        return default
    # max por count, estable por orden alfabético para reproducibilidad
    return sorted(count_dict.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

def safe_num(x, default=0.0):
    try:
        v = float(x)
        return v if isfinite(v) else default
    except Exception:
        return default

def to_jsonable(x):
    # evita el error int64/float32/etc.
    import numpy as np
    if isinstance(x, (np.integer,)): return int(x)
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, (np.ndarray,)): return x.tolist()
    if isinstance(x, dict): return {k: to_jsonable(v) for k, v in x.items()}
    if isinstance(x, list): return [to_jsonable(v) for v in x]
    return x

# -------------------------
# Load data
# -------------------------
with RECIPES_PATH.open("r", encoding="utf-8") as f:
    recipes_db = json.load(f)
recipes = recipes_db["recipes"]  # estructura real del fichero :contentReference[oaicite:2]{index=2}

with METACASES_PATH.open("r", encoding="utf-8") as f:
    meta_cases = json.load(f)     # lista de metacasos :contentReference[oaicite:3]{index=3}

# index rápido por recipe_id
recipe_by_id = {r["recipe_id"]: r for r in recipes}

# -------------------------
# Scoring para elegir platos
# (prioriza cultura/estilo del cluster + luego salud/tiempo/coste/complexidad)
# -------------------------
def dish_score(dish: dict, dom_cultura: str, dom_estilo: str, preferred_season: str = None):
    score = 0.0

    dish_c = split_taxonomy(dish.get("cultura", ""))
    dish_s = split_taxonomy(dish.get("estilo_cocina", ""))

    dom_c = split_taxonomy(dom_cultura)
    dom_s = split_taxonomy(dom_estilo)

    # coherencia cultural/estilo (muy importante)
    score += 8.0 * (len(dish_c & dom_c) > 0)
    score += 8.0 * (len(dish_s & dom_s) > 0)

    # season match (suave)
    if preferred_season:
        score += 2.0 * (str(dish.get("season", "")).lower() == str(preferred_season).lower())

    # trade-offs suaves
    health = safe_num(dish.get("health_factor", 0))
    time_m = safe_num(dish.get("ready_in_minutes", 0))
    price  = safe_num(dish.get("price_per_serving", 0))
    compl  = safe_num(dish.get("complexity_score", 0))

    score += 0.05 * health
    score -= 0.01 * time_m
    score -= 0.003 * price
    score -= 0.02 * compl

    return score

# -------------------------
# Selección de menú por cluster
# -------------------------
def select_menu_for_cluster(meta_case: dict):
    member_ids = set(meta_case.get("member_recipe_ids", []))
    cluster_recipes = [recipe_by_id[rid] for rid in member_ids if rid in recipe_by_id]

    # dominantes desde el perfil del metacaso (si existe)
    profile = meta_case.get("profile", {}) or {}
    dom_cultura = dominant_key(profile.get("cultura_top", {}), default=meta_case.get("representative_recipe", {}).get("cultura", ""))
    dom_estilo  = dominant_key(profile.get("estilo_cocina_top", {}), default=meta_case.get("representative_recipe", {}).get("estilo_cocina", ""))

    # season “preferida” = moda dentro del cluster (si hay)
    season_counts = Counter([r.get("season", "") for r in cluster_recipes if r.get("season")])
    preferred_season = season_counts.most_common(1)[0][0] if season_counts else None

    trace = []
    menu = {}

    for course in COURSES:
        # 1) candidatos dentro del cluster
        candidates = [r for r in cluster_recipes if str(r.get("course_type", "")).lower() == course]

        source = "cluster"
        if not candidates:
            # 2) fallback: buscar globalmente (prioriza cultura/estilo del cluster)
            source = "global_fallback"
            global_same = []
            for r in recipes:
                if str(r.get("course_type", "")).lower() != course:
                    continue
                if len(split_taxonomy(r.get("cultura", "")) & split_taxonomy(dom_cultura)) > 0 or \
                   len(split_taxonomy(r.get("estilo_cocina", "")) & split_taxonomy(dom_estilo)) > 0:
                    global_same.append(r)
            candidates = global_same if global_same else [r for r in recipes if str(r.get("course_type", "")).lower() == course]

        # rank
        ranked = sorted(
            candidates,
            key=lambda r: dish_score(r, dom_cultura, dom_estilo, preferred_season),
            reverse=True
        )
        chosen = ranked[0]

        menu[course] = {
            "recipe_id": int(chosen["recipe_id"]),
            "title": chosen.get("title"),
            "course_type": chosen.get("course_type"),
            "cultura": chosen.get("cultura"),
            "estilo_cocina": chosen.get("estilo_cocina"),
            "season": chosen.get("season"),
            "ingredients": chosen.get("ingredients", []),
            "restrictions": chosen.get("restrictions", []),
            "ready_in_minutes": chosen.get("ready_in_minutes"),
            "price_per_serving": chosen.get("price_per_serving"),
            "complexity_score": chosen.get("complexity_score"),
            "health_factor": chosen.get("health_factor"),
        }

        trace.append({
            "step": f"select_{course}",
            "source": source,
            "dominant_cultura": dom_cultura,
            "dominant_estilo": dom_estilo,
            "preferred_season": preferred_season,
            "chosen_recipe_id": int(chosen["recipe_id"]),
            "chosen_title": chosen.get("title"),
            "why": "max score = cultura/estilo match + (health - time - cost - complexity)"
        })

    return menu, dom_cultura, dom_estilo, preferred_season, trace, cluster_recipes

# -------------------------
# Utility inicial ==> constante 1 (no feedback aún)
# -------------------------
def initial_utility(menu: dict):
    return {
        "utility_score": 1,
        "components": {},
        "note": "Inicializado a 1 (sin feedback)."
    }

# -------------------------
# Build case base (1 caso por cluster)
# -------------------------
case_base = []
for mc in meta_cases:
    cluster_id = int(mc["topic_id"])
    menu, dom_cultura, dom_estilo, pref_season, trace, cluster_recipes = select_menu_for_cluster(mc)

    # problema “plantilla” del cluster (no es el input real del usuario todavía)
    P = {
        "evento": {
            "tipo": None,
            "formalidad": None,
            "hora": None,
            "estacion_mes": pref_season
        },
        "comensales": {
            "n": None,
            "perfil": None,
            "formato": None
        },
        "restricciones_duras": [],
        "preferencias_blandas": {
            "cocina_cultura": dom_cultura,
            "estilo": dom_estilo
        },
        "presupuesto_tiempo": {
            "budget_total": None,
            "prep_time_limit": None
        }
    }

    S = {
        "menu": {
            "starter": menu["starter"],
            "main": menu["main"],
            "dessert": menu["dessert"],
        },
        "menu_stats": {
            "supported_restrictions_intersection": sorted(
                list(set(menu["starter"]["restrictions"]) &
                     set(menu["main"]["restrictions"]) &
                     set(menu["dessert"]["restrictions"]))
            )
        }
    }

    U = initial_utility(menu)

    T = {
        "construction_trace": trace,
        "adaptation_steps": []  # vacío por ahora; lo llenarás cuando adaptes desde el caso
    }

    case = {
        "case_id": f"cluster_menu_{cluster_id}",
        "cluster_id": cluster_id,

        # índice para retrieve “macro”
        "index_vector": mc.get("centroid_embedding", []),    # <- centroide del cluster :contentReference[oaicite:4]{index=4}
        "cluster_keywords": mc.get("keywords", []),
        "cluster_profile": mc.get("profile", {}),
        "cluster_member_recipe_ids": mc.get("member_recipe_ids", []),

        # tu estructura
        "P": P,
        "S": S,
        "U": U,
        "T": T
    }

    case_base.append(case)

with OUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(to_jsonable(case_base), f, ensure_ascii=False, indent=2)

print(f"OK -> guardado {OUT_PATH} | num_cases={len(case_base)}")
for c in case_base:
    m = c["S"]["menu"]
    print(c["case_id"], "=>", m["starter"]["title"], "|", m["main"]["title"], "|", m["dessert"]["title"])
