"""
CBR Retrieve Module - Modulo de Recuperacion para Sistema de Recomendacion de Menus.

Este modulo implementa la fase de recuperacion del ciclo CBR, encontrando el menu
mas similar dentro de la base de casos usando embeddings semanticos y matching exacto.

Integra bases de conocimiento:
- ingredientes_por_contexto.json: Ingredientes validos por cultura/estilo
- ontologia_ingredientes_cultura.json: Ontologia jerarquica de ingredientes
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


# ----------------------------
# Paths a Bases de Conocimiento
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
KB_DIR = BASE_DIR / "Bases_Conocimientos"


# ----------------------------
# Utils: normalizacion robusta
# ----------------------------

def _norm_spaces(s: str) -> str:
    """Normaliza espacios multiples a uno solo."""
    return re.sub(r"\s+", " ", s).strip()


def normalize_text(x: Any) -> str:
    """Normaliza texto a minusculas y espacios simples."""
    if x is None:
        return ""
    return _norm_spaces(str(x).lower())


def normalize_restriction(x: Any) -> str:
    """Normaliza restricciones dieteticas (ej: 'gluten-free' -> 'gluten free')."""
    s = normalize_text(x).replace("-", " ")
    return _norm_spaces(s)


def normalize_ingredient_key(x: str) -> str:
    """Normaliza nombre de ingrediente para comparacion en ontologia."""
    return normalize_text(x).replace(" ", "-").replace("_", "-")


def split_taxonomy_tokens(x: Any) -> Set[str]:
    """
    Convierte taxonomias tipo:
      'Italiana/Mediterranea' -> {'italiana','mediterranea'}
      'Tradicional/Casero'    -> {'tradicional','casero'}
    """
    s = normalize_text(x)
    s = s.replace("fusion", "fusion")
    for ch in ["/", ",", ";", "|"]:
        s = s.replace(ch, " ")
    return {t for t in s.split() if t}


def ingredients_set(lst: Any) -> Set[str]:
    """Convierte lista de ingredientes a set normalizado."""
    if not lst:
        return set()
    if isinstance(lst, str):
        return {normalize_text(lst)}
    return {normalize_text(i) for i in lst if i}


def jaccard(a: Set[str], b: Set[str]) -> float:
    """Calcula similitud Jaccard entre dos conjuntos."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def to_jsonable(obj: Any) -> Any:
    """Convierte objetos numpy a tipos serializables JSON."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_jsonable(v) for v in obj]
    return obj


# ----------------------------
# Cargador de Bases de Conocimiento
# ----------------------------

class KnowledgeBaseLoader:
    """Gestor centralizado de bases de conocimiento (Singleton)."""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not KnowledgeBaseLoader._loaded:
            self._ingredientes_contexto: Dict[str, Any] = {}
            self._ontologia: Dict[str, Any] = {}
            self._ingredient_to_family: Dict[str, List[str]] = {}
            self._culture_ingredients: Dict[str, Set[str]] = {}
            self._load_knowledge_bases()
            KnowledgeBaseLoader._loaded = True
    
    def _load_knowledge_bases(self) -> None:
        """Carga todas las bases de conocimiento necesarias."""
        # Cargar ingredientes por contexto
        ing_ctx_path = KB_DIR / "ingredientes_por_contexto.json"
        if ing_ctx_path.exists():
            with open(ing_ctx_path, "r", encoding="utf-8") as f:
                self._ingredientes_contexto = json.load(f)
            self._build_culture_ingredients_index()
        
        # Cargar ontologia de ingredientes
        onto_path = KB_DIR / "ontologia_ingredientes_cultura.json"
        if onto_path.exists():
            with open(onto_path, "r", encoding="utf-8") as f:
                self._ontologia = json.load(f)
            self._build_ingredient_family_index()
    
    def _build_culture_ingredients_index(self) -> None:
        """Construye indice de ingredientes validos por cultura/estilo."""
        for key, data in self._ingredientes_contexto.items():
            culture = normalize_text(data.get("culture", ""))
            style = normalize_text(data.get("style", ""))
            ingredients = set(normalize_text(i) for i in data.get("ingredients", []))
            
            if culture:
                for c in split_taxonomy_tokens(culture):
                    if c not in self._culture_ingredients:
                        self._culture_ingredients[c] = set()
                    self._culture_ingredients[c].update(ingredients)
            
            combo_key = f"{culture}_{style}" if culture and style else ""
            if combo_key:
                self._culture_ingredients[combo_key] = ingredients
    
    def _build_ingredient_family_index(self) -> None:
        """Construye indice inverso: ingrediente -> familias ontologicas."""
        ontology_tree = self._ontologia.get("ontology_tree", {})
        
        def traverse(node: Dict, path: List[str]) -> None:
            for key, value in node.items():
                if key == "__ingredients":
                    for ing in value:
                        normalized = normalize_ingredient_key(ing)
                        if normalized not in self._ingredient_to_family:
                            self._ingredient_to_family[normalized] = []
                        self._ingredient_to_family[normalized].append("/".join(path))
                elif isinstance(value, dict):
                    traverse(value, path + [key])
        
        for culture, categories in ontology_tree.items():
            if isinstance(categories, dict):
                traverse(categories, [culture])
    
    def get_ingredients_for_context(self, cultura: Set[str], estilo: Set[str]) -> Set[str]:
        """Obtiene ingredientes validos para un contexto cultura/estilo."""
        result = set()
        
        for c in cultura:
            c_norm = normalize_text(c)
            if c_norm in self._culture_ingredients:
                result.update(self._culture_ingredients[c_norm])
        
        for c in cultura:
            for e in estilo:
                combo = f"{normalize_text(c)}_{normalize_text(e)}"
                if combo in self._culture_ingredients:
                    result.update(self._culture_ingredients[combo])
        
        return result
    
    def get_ingredient_families(self, ingredient: str) -> List[str]:
        """Obtiene las familias ontologicas a las que pertenece un ingrediente."""
        normalized = normalize_ingredient_key(ingredient)
        return self._ingredient_to_family.get(normalized, [])
    
    def ingredients_share_family(self, ing1: str, ing2: str) -> bool:
        """Verifica si dos ingredientes comparten familia ontologica."""
        families1 = set(self.get_ingredient_families(ing1))
        families2 = set(self.get_ingredient_families(ing2))
        
        if not families1 or not families2:
            return False
        
        for f1 in families1:
            for f2 in families2:
                if f1 == f2:
                    return True
                if f1.startswith(f2) or f2.startswith(f1):
                    return True
                parts1 = f1.split("/")
                parts2 = f2.split("/")
                common_depth = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
                if common_depth >= 2:
                    return True
        
        return False
    
    def get_family_depth_similarity(self, ing1: str, ing2: str) -> float:
        """Calcula similitud basada en profundidad compartida en ontologia."""
        families1 = self.get_ingredient_families(ing1)
        families2 = self.get_ingredient_families(ing2)
        
        if not families1 or not families2:
            return 0.0
        
        max_similarity = 0.0
        for f1 in families1:
            parts1 = f1.split("/")
            for f2 in families2:
                parts2 = f2.split("/")
                common = sum(1 for p1, p2 in zip(parts1, parts2) if p1 == p2)
                max_depth = max(len(parts1), len(parts2))
                if max_depth > 0:
                    max_similarity = max(max_similarity, common / max_depth)
        
        return max_similarity
    
    def is_ingredient_valid_for_culture(self, ingredient: str, cultura: Set[str]) -> bool:
        """Verifica si un ingrediente es valido para una cultura dada."""
        if not cultura:
            return True
        
        valid_ingredients = set()
        for c in cultura:
            c_norm = normalize_text(c)
            if c_norm in self._culture_ingredients:
                valid_ingredients.update(self._culture_ingredients[c_norm])
        
        if not valid_ingredients:
            return True
        
        ing_norm = normalize_text(ingredient)
        return any(ing_norm in valid or valid in ing_norm for valid in valid_ingredients)


# ----------------------------
# Modelos de entrada/salida
# ----------------------------

@dataclass
class HardConstraints:
    """Restricciones duras que DEBEN cumplirse."""
    required_diets: Set[str] = field(default_factory=set)
    forbidden_ingredients: Set[str] = field(default_factory=set)
    allergens: Set[str] = field(default_factory=set)


@dataclass
class SoftPreferences:
    """Preferencias blandas que se optimizan pero no son obligatorias."""
    cultura: Set[str] = field(default_factory=set)
    estilo: Set[str] = field(default_factory=set)
    season: Optional[str] = None
    preferred_ingredients: Set[str] = field(default_factory=set)


@dataclass
class UserQuery:
    """Query del usuario con restricciones y preferencias."""
    hard: HardConstraints = field(default_factory=HardConstraints)
    soft: SoftPreferences = field(default_factory=SoftPreferences)
    raw_text: Optional[str] = None


@dataclass
class RetrievalResult:
    """Resultado del proceso de recuperacion."""
    chosen_case_id: str
    chosen_cluster_id: int
    centroid_rank: List[Dict[str, Any]]
    rerank: List[Dict[str, Any]]
    mismatches: Dict[str, Any]
    chosen_menu: Dict[str, Any]


# ----------------------------
# Embedding
# ----------------------------

class Embedder:
    """Interfaz base para embedders."""
    
    def encode(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError


class SentenceTransformerEmbedder(Embedder):
    """Embedder usando SentenceTransformers."""
    
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def dim(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def encode(self, texts: List[str]) -> np.ndarray:
        emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(emb, dtype=np.float32)


# ----------------------------
# Retriever Principal
# ----------------------------

class CBRRetriever:
    """
    Recuperador CBR que combina:
    - Similitud semantica (embeddings)
    - Matching exacto de restricciones
    - Validacion con bases de conocimiento
    """
    
    def __init__(
        self,
        case_base_path: str,
        recipes_db_path: Optional[str] = None,
        embedder: Optional[Embedder] = None,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.case_base_path = case_base_path
        self.recipes_db_path = recipes_db_path
        self.embedder = embedder
        
        # Cargar bases de conocimiento
        self.kb = KnowledgeBaseLoader()
        
        # Pesos para scoring
        self.w = {
            "centroid": 1.0,
            "soft": 0.25,
            "hard_penalty": 3.0,
            "cultural_fit": 0.15,
        }
        if weights:
            self.w.update(weights)
        
        # Cargar casos y recetas
        self.cases = self._load_json(case_base_path)
        self.centroid_matrix, self.case_ids, self.cluster_ids = self._build_centroid_index(self.cases)
        
        self.recipe_by_id: Dict[int, Dict[str, Any]] = {}
        if recipes_db_path:
            db = self._load_json(recipes_db_path)
            for r in db.get("recipes", []):
                self.recipe_by_id[int(r["recipe_id"])] = r
        
        # Validar dimensiones
        d = self.centroid_matrix.shape[1]
        if self.embedder and hasattr(self.embedder, "dim"):
            emb_dim = self.embedder.dim()
            if emb_dim != d:
                raise ValueError(
                    f"Dimension embedding mismatch: centroid={d} vs embedder={emb_dim}. "
                    f"Debe usar el MISMO modelo que genero los centroides."
                )
    
    @staticmethod
    def _load_json(path: str) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    @staticmethod
    def _build_centroid_index(cases: List[Dict[str, Any]]) -> Tuple[np.ndarray, List[str], List[int]]:
        ids = []
        cids = []
        vecs = []
        for c in cases:
            ids.append(c["case_id"])
            cids.append(int(c["cluster_id"]))
            vecs.append(np.asarray(c["index_vector"], dtype=np.float32))
        M = np.vstack(vecs)
        M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-12)
        return M, ids, cids
    
    def build_query_doc(self, q: UserQuery) -> str:
        """Construye documento de texto para embedding de la query."""
        parts = []
        
        if q.soft.cultura:
            parts.append(("cultura " + " ".join(sorted(q.soft.cultura)) + " ") * 3)
        if q.soft.estilo:
            parts.append(("estilo " + " ".join(sorted(q.soft.estilo)) + " ") * 3)
        
        if q.soft.season:
            parts.append(f"season {normalize_text(q.soft.season)} ")
        
        if q.hard.required_diets:
            parts.append(" ".join(f"diet {r}" for r in sorted(q.hard.required_diets)))
        
        if q.hard.forbidden_ingredients or q.hard.allergens:
            bad = sorted(q.hard.forbidden_ingredients | q.hard.allergens)
            parts.append(" ".join(f"avoid {b}" for b in bad))
        
        if q.soft.preferred_ingredients:
            parts.append(" ".join(f"ingredient {i}" for i in sorted(q.soft.preferred_ingredients)))
        
        if q.raw_text:
            parts.append(q.raw_text)
        
        return _norm_spaces(" ".join(parts))
    
    def _cosine_to_centroids(self, q_vec: np.ndarray) -> np.ndarray:
        q_vec = q_vec.astype(np.float32)
        q_vec = q_vec / (np.linalg.norm(q_vec) + 1e-12)
        return self.centroid_matrix @ q_vec
    
    # ----------------------------
    # Evaluacion de platos y menus
    # ----------------------------
    
    def dish_violations(self, dish: Dict[str, Any], hard: HardConstraints) -> List[Dict[str, Any]]:
        """Detecta violaciones de restricciones duras en un plato."""
        vios = []
        
        dish_restr = {normalize_restriction(r) for r in dish.get("restrictions", [])}
        dish_ings = ingredients_set(dish.get("ingredients", []))
        
        missing = [r for r in hard.required_diets if r and r not in dish_restr]
        if missing:
            vios.append({"type": "missing_required_restriction", "missing": sorted(missing)})
        
        forbid = {normalize_text(x) for x in (hard.forbidden_ingredients | hard.allergens) if x}
        hits = []
        for bad in forbid:
            if any(bad in ing for ing in dish_ings):
                hits.append(bad)
        if hits:
            vios.append({"type": "forbidden_ingredient_present", "hits": sorted(set(hits))})
        
        return vios
    
    def dish_soft_score(self, dish: Dict[str, Any], soft: SoftPreferences) -> Tuple[float, Dict[str, Any]]:
        """Calcula puntuacion de preferencias blandas con validacion cultural."""
        score = 0.0
        det: Dict[str, Any] = {}
        
        dish_c = split_taxonomy_tokens(dish.get("cultura"))
        dish_s = split_taxonomy_tokens(dish.get("estilo_cocina"))
        dish_ings = ingredients_set(dish.get("ingredients", []))
        
        # Similitud cultural
        if soft.cultura:
            c = jaccard(dish_c, soft.cultura)
            score += 3.0 * c
            det["cultura_jaccard"] = c
            
            # Bonus por ingredientes culturalmente apropiados (usando KB)
            valid_ings = self.kb.get_ingredients_for_context(soft.cultura, soft.estilo)
            if valid_ings and dish_ings:
                cultural_match = len(dish_ings & valid_ings) / len(dish_ings) if dish_ings else 0
                score += self.w["cultural_fit"] * cultural_match
                det["cultural_ingredient_fit"] = cultural_match
        
        # Similitud de estilo
        if soft.estilo:
            s = jaccard(dish_s, soft.estilo)
            score += 3.0 * s
            det["estilo_jaccard"] = s
        
        # Temporada
        if soft.season:
            ds = normalize_text(dish.get("season"))
            qs = normalize_text(soft.season)
            det["season_match"] = (ds == qs) or (ds == "all")
            score += 1.0 if det["season_match"] else 0.0
        
        # Ingredientes preferidos
        if soft.preferred_ingredients:
            hits = sum(1 for p in soft.preferred_ingredients if any(p in ing for ing in dish_ings))
            det["preferred_ing_hits"] = hits
            score += 0.2 * hits
        
        return score, det
    
    def evaluate_menu(self, menu: Dict[str, Any], q: UserQuery) -> Dict[str, Any]:
        """Evalua un menu completo contra las restricciones y preferencias."""
        hard_vios = []
        soft_total = 0.0
        soft_details = {}
        
        for course, dish in menu.items():
            v = self.dish_violations(dish, q.hard)
            if v:
                hard_vios.append({
                    "course": course,
                    "recipe_id": dish.get("recipe_id"),
                    "title": dish.get("title"),
                    "violations": v
                })
            sc, det = self.dish_soft_score(dish, q.soft)
            soft_total += sc
            soft_details[course] = det
        
        return {
            "hard_violations": hard_vios,
            "hard_violation_count": len(hard_vios),
            "soft_score": soft_total,
            "soft_details": soft_details,
        }
    
    # ----------------------------
    # Matching dentro del cluster
    # ----------------------------
    
    def _best_recipe_for_course(
        self,
        recipe_ids: List[int],
        course_type: str,
        q: UserQuery
    ) -> Optional[Tuple[float, Dict[str, Any]]]:
        """
        Encuentra la mejor receta para un curso dentro de un conjunto de IDs.
        Devuelve (score, recipe) o None si no hay candidato valido.
        """
        best = None
        for rid in recipe_ids:
            r = self.recipe_by_id.get(int(rid))
            if not r:
                continue
            if normalize_text(r.get("course_type")) != normalize_text(course_type):
                continue
            
            if self.dish_violations(r, q.hard):
                continue
            
            sc, _ = self.dish_soft_score(r, q.soft)
            
            tie = (
                float(r.get("health_factor", 0)),
                -float(r.get("ready_in_minutes", 0)),
                -float(r.get("price_per_serving", 0)),
                -float(r.get("complexity_score", 0)),
            )
            key = (sc, tie)
            
            if best is None or key > best[0]:
                best = (key, r)
        
        if best is None:
            return None
        return float(best[0][0]), best[1]
    
    # ----------------------------
    # Retrieve: Stage 1 + Stage 2
    # ----------------------------
    
    def retrieve(self, q: UserQuery, top_k_centroids: int = 3) -> RetrievalResult:
        """
        Proceso de recuperacion en dos etapas:
        1. Ranking por similitud semantica a centroides
        2. Re-ranking con matching exacto y evaluacion de mismatches
        """
        query_doc = self.build_query_doc(q)
        if not self.embedder:
            raise RuntimeError(
                "No embedder configurado. Use SentenceTransformerEmbedder con el mismo modelo que BERTopic."
            )
        q_vec = self.embedder.encode([query_doc])[0]
        
        sims = self._cosine_to_centroids(q_vec)
        order = np.argsort(-sims)[:top_k_centroids]
        
        centroid_rank = []
        candidates = []
        for idx in order:
            case = self.cases[int(idx)]
            sim = float(sims[int(idx)])
            centroid_rank.append({
                "case_id": case["case_id"],
                "cluster_id": int(case["cluster_id"]),
                "centroid_sim": sim
            })
            candidates.append((case, sim))
        
        rerank = []
        best = None
        
        for case, sim in candidates:
            menu = case["S"]["menu"]
            eval_menu = self.evaluate_menu(menu, q)
            
            hard_pen = eval_menu["hard_violation_count"] * self.w["hard_penalty"]
            total = (
                self.w["centroid"] * sim + 
                self.w["soft"] * eval_menu["soft_score"] - 
                hard_pen
            )
            
            row = {
                "case_id": case["case_id"],
                "cluster_id": int(case["cluster_id"]),
                "centroid_sim": sim,
                "soft_score": float(eval_menu["soft_score"]),
                "hard_violation_count": int(eval_menu["hard_violation_count"]),
                "final_score": float(total),
            }
            rerank.append(row)
            
            if best is None or total > best[0]:
                best = (total, case, eval_menu)
        
        rerank.sort(key=lambda x: x["final_score"], reverse=True)
        
        assert best is not None
        _, best_case, best_eval = best
        
        mismatches = {
            "hard_violations": best_eval["hard_violations"],
            "soft_details": best_eval["soft_details"],
        }
        
        return RetrievalResult(
            chosen_case_id=best_case["case_id"],
            chosen_cluster_id=int(best_case["cluster_id"]),
            centroid_rank=centroid_rank,
            rerank=rerank,
            mismatches=mismatches,
            chosen_menu=best_case["S"]["menu"]
        )


# ----------------------------
# Ejemplo de uso
# ----------------------------

if __name__ == "__main__":
    MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    
    retriever = CBRRetriever(
        case_base_path="../Base_Casos/case_base_menus.json",
        recipes_db_path="../Bases_Conocimientos/cbr_recipes_database.json",
        embedder=SentenceTransformerEmbedder(MODEL_ID),
    )
    
    q = UserQuery(
        hard=HardConstraints(
            required_diets={normalize_restriction("gluten free"), normalize_restriction("vegetarian")},
            forbidden_ingredients={"corn syrup"},
        ),
        soft=SoftPreferences(
            cultura=split_taxonomy_tokens("Italiana"),
            estilo=split_taxonomy_tokens("Tradicional"),
            season="Summer",
            preferred_ingredients=ingredients_set(["garlic", "lemon"]),
        ),
    )
    
    res = retriever.retrieve(q, top_k_centroids=3)
    
    out = {
        "chosen_case_id": res.chosen_case_id,
        "chosen_cluster_id": res.chosen_cluster_id,
        "menu": res.chosen_menu,
        "mismatches": res.mismatches,
    }
    print(json.dumps(to_jsonable(out), ensure_ascii=False, indent=2))
