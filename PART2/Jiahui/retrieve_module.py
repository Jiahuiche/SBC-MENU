from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np


# ----------------------------
# Utils: normalización robusta
# ----------------------------

def _norm_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def normalize_text(x: Any) -> str:
    if x is None:
        return ""
    return _norm_spaces(str(x).lower())

def normalize_restriction(x: Any) -> str:
    # "gluten-free" -> "gluten free"
    s = normalize_text(x).replace("-", " ")
    return _norm_spaces(s)

def split_taxonomy_tokens(x: Any) -> Set[str]:
    """
    Convierte taxonomías tipo:
      'Italiana/Mediterránea' -> {'italiana','mediterranea'}
      'Tradicional/Casero'    -> {'tradicional','casero'}
    """
    s = normalize_text(x)
    # opcional: normaliza tildes comunes si te interesa
    s = s.replace("fusión", "fusion")
    for ch in ["/", ",", ";", "|"]:
        s = s.replace(ch, " ")
    return {t for t in s.split() if t}

def ingredients_set(lst: Any) -> Set[str]:
    if not lst:
        return set()
    if isinstance(lst, str):
        return {normalize_text(lst)}
    return {normalize_text(i) for i in lst if i}

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def to_jsonable(obj: Any) -> Any:
    # para dump sin errores (np.float32, np.int64, etc.)
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
# Modelos de entrada/salida
# ----------------------------

@dataclass
class HardConstraints:
    required_diets: Set[str] = field(default_factory=set)       # {"vegan","gluten free"}
    forbidden_ingredients: Set[str] = field(default_factory=set) # {"peanut","shrimp"}
    allergens: Set[str] = field(default_factory=set)            # igual que forbidden

@dataclass
class SoftPreferences:
    cultura: Set[str] = field(default_factory=set)               # tokens
    estilo: Set[str] = field(default_factory=set)                # tokens
    season: Optional[str] = None                                 # "Summer"/"Fall"/"All"
    preferred_ingredients: Set[str] = field(default_factory=set) # tokens

@dataclass
class UserQuery:
    hard: HardConstraints = field(default_factory=HardConstraints)
    soft: SoftPreferences = field(default_factory=SoftPreferences)
    raw_text: Optional[str] = None  # opcional

@dataclass
class RetrievalResult:
    chosen_case_id: str
    chosen_cluster_id: int
    centroid_rank: List[Dict[str, Any]]
    rerank: List[Dict[str, Any]]
    mismatches: Dict[str, Any]
    suggested_swaps: List[Dict[str, Any]]
    chosen_menu: Dict[str, Any]


# ----------------------------
# Embedding (usa MISMO modelo que BERTopic)
# ----------------------------

class Embedder:
    def encode(self, texts: List[str]) -> np.ndarray:
        raise NotImplementedError

class SentenceTransformerEmbedder(Embedder):
    """
    Requiere:
      pip install sentence-transformers
    """
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def dim(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def encode(self, texts: List[str]) -> np.ndarray:
        emb = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(emb, dtype=np.float32)


# ----------------------------
# Retriever
# ----------------------------

class CBRRetriever:
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

        # pesos razonables (ajústalos cuando tengas feedback real)
        self.w = {
            "centroid": 1.0,
            "soft": 0.20,
            "hard_penalty": 2.0,     # penaliza violaciones duras
            "swap_cost": 0.20,       # coste de reemplazar plato
        }
        if weights:
            self.w.update(weights)

        # carga
        self.cases = self._load_json(case_base_path)
        self.centroid_matrix, self.case_ids, self.cluster_ids = self._build_centroid_index(self.cases)

        # recetas (para sugerir swaps dentro del cluster)
        self.recipe_by_id = {}
        if recipes_db_path:
            db = self._load_json(recipes_db_path)
            for r in db.get("recipes", []):
                self.recipe_by_id[int(r["recipe_id"])] = r

        # sanity
        d = self.centroid_matrix.shape[1]
        if self.embedder and hasattr(self.embedder, "dim"):
            emb_dim = self.embedder.dim()
            if emb_dim != d:
                raise ValueError(
                    f"Dimensión embedding mismatch: centroid={d} vs embedder={emb_dim}. "
                    f"Debes usar el MISMO modelo que generó los centroides."
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
        # renormaliza por seguridad
        M = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-12)
        return M, ids, cids

    def build_query_doc(self, q: UserQuery) -> str:
        """
        Construye texto “controlado” para embedding.
        Repite cultura/estilo para dar más peso semántico (truco simple pero efectivo).
        """
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
    # Hard/Soft scoring + mismatches
    # ----------------------------

    def dish_violations(self, dish: Dict[str, Any], hard: HardConstraints) -> List[Dict[str, Any]]:
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
        score = 0.0
        det: Dict[str, Any] = {}

        dish_c = split_taxonomy_tokens(dish.get("cultura"))
        dish_s = split_taxonomy_tokens(dish.get("estilo_cocina"))

        if soft.cultura:
            c = jaccard(dish_c, soft.cultura)
            score += 3.0 * c
            det["cultura_jaccard"] = c
            det["cultura_exact"] = normalize_text(dish.get("cultura")) in {normalize_text(" ".join(soft.cultura))}
        if soft.estilo:
            s = jaccard(dish_s, soft.estilo)
            score += 3.0 * s
            det["estilo_jaccard"] = s
            det["estilo_exact"] = normalize_text(dish.get("estilo_cocina")) in {normalize_text(" ".join(soft.estilo))}

        if soft.season:
            ds = normalize_text(dish.get("season"))
            qs = normalize_text(soft.season)
            det["season_match"] = (ds == qs) or (ds == "all")
            score += 1.0 if det["season_match"] else 0.0

        if soft.preferred_ingredients:
            dish_ings = ingredients_set(dish.get("ingredients", []))
            hits = sum(1 for p in soft.preferred_ingredients if any(p in ing for ing in dish_ings))
            det["preferred_ing_hits"] = hits
            score += 0.2 * hits

        return score, det

    def evaluate_menu(self, menu: Dict[str, Any], q: UserQuery) -> Dict[str, Any]:
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
    # Matching “dentro del cluster”: sugerir swaps por plato
    # ----------------------------

    def _best_recipe_for_course(
        self,
        recipe_ids: List[int],
        course_type: str,
        q: UserQuery
    ) -> Optional[Tuple[float, Dict[str, Any]]]:
        """
        Devuelve (score, recipe) del mejor candidato dentro del cluster
        que NO viole hard constraints. Si no hay, devuelve None.
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

            # tie-breakers suaves (opcionales)
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

    def suggest_swaps_within_cluster(self, case: Dict[str, Any], q: UserQuery) -> List[Dict[str, Any]]:
        """
        Para cada course, sugiere reemplazo dentro del cluster si mejora
        hard constraints o soft preferences.
        """
        if not self.recipe_by_id:
            return []

        swaps = []
        menu = case["S"]["menu"]
        member_ids = case.get("cluster_member_recipe_ids", [])

        for course, dish in menu.items():
            current_id = int(dish["recipe_id"])
            current_v = self.dish_violations(dish, q.hard)

            best = self._best_recipe_for_course(member_ids, course, q)
            if not best:
                continue
            best_sc, best_r = best
            best_id = int(best_r["recipe_id"])

            if best_id == current_id:
                continue

            swaps.append({
                "course": course,
                "from_recipe_id": current_id,
                "from_title": dish.get("title"),
                "to_recipe_id": best_id,
                "to_title": best_r.get("title"),
                "why": "mejor match dentro del cluster (filtrando hard constraints, optimizando soft prefs)",
                "hard_violations_current": current_v,
            })

        return swaps

    # ----------------------------
    # Retrieve: Stage 1 + Stage 2
    # ----------------------------

    def retrieve(
        self,
        q: UserQuery,
        top_k_centroids: int = 3
    ) -> RetrievalResult:

        # 1) embedding query
        query_doc = self.build_query_doc(q)
        if not self.embedder:
            raise RuntimeError(
                "No embedder configurado. Usa SentenceTransformerEmbedder (mismo modelo que BERTopic) "
                "o pásame tu embedding de query si lo prefieres."
            )
        q_vec = self.embedder.encode([query_doc])[0]

        # 2) Stage 1: centroid similarity
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

        # 3) Stage 2: re-rank con matching exacto + mismatches
        rerank = []
        best = None

        for case, sim in candidates:
            menu = case["S"]["menu"]

            eval_menu = self.evaluate_menu(menu, q)
            swaps = self.suggest_swaps_within_cluster(case, q)

            # scoring final (ajusta pesos)
            hard_pen = eval_menu["hard_violation_count"] * self.w["hard_penalty"]
            swap_cost = len(swaps) * self.w["swap_cost"]
            total = (self.w["centroid"] * sim) + (self.w["soft"] * eval_menu["soft_score"]) - hard_pen - swap_cost

            row = {
                "case_id": case["case_id"],
                "cluster_id": int(case["cluster_id"]),
                "centroid_sim": sim,
                "soft_score": float(eval_menu["soft_score"]),
                "hard_violation_count": int(eval_menu["hard_violation_count"]),
                "swap_suggestions": int(len(swaps)),
                "final_score": float(total),
            }
            rerank.append(row)

            if best is None or total > best[0]:
                best = (total, case, eval_menu, swaps)

        rerank.sort(key=lambda x: x["final_score"], reverse=True)

        assert best is not None
        _, best_case, best_eval, best_swaps = best

        # 4) mismatches “para Adapt”
        mismatches = {
            "hard_violations": best_eval["hard_violations"],
            "soft_details": best_eval["soft_details"],
            "what_to_adapt": self._summarize_adaptation_targets(best_eval, best_swaps),
        }

        return RetrievalResult(
            chosen_case_id=best_case["case_id"],
            chosen_cluster_id=int(best_case["cluster_id"]),
            centroid_rank=centroid_rank,
            rerank=rerank,
            mismatches=mismatches,
            suggested_swaps=best_swaps,
            chosen_menu=best_case["S"]["menu"]
        )

    @staticmethod
    def _summarize_adaptation_targets(best_eval: Dict[str, Any], swaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        targets = []

        for hv in best_eval.get("hard_violations", []):
            targets.append({
                "severity": "hard",
                "course": hv["course"],
                "recipe_id": hv["recipe_id"],
                "issues": hv["violations"],
                "suggested_operator": "replace_dish_or_remove_ingredient"
            })

        for s in swaps:
            targets.append({
                "severity": "soft_or_hard_fix",
                "course": s["course"],
                "suggested_operator": "swap_recipe_within_cluster",
                "from": s["from_recipe_id"],
                "to": s["to_recipe_id"],
                "why": s["why"]
            })

        return targets


# ----------------------------
# Ejemplo de uso
# ----------------------------

if __name__ == "__main__":
    # Ajusta al MISMO modelo que usaste para generar embeddings/centroides
    MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    retriever = CBRRetriever(
        case_base_path="case_base_menus.json",
        recipes_db_path="cbr_recipes_database.json",
        embedder=SentenceTransformerEmbedder(MODEL_ID),
        weights={
            "centroid": 1.0,
            "soft": 0.20,
            "hard_penalty": 2.0,
            "swap_cost": 0.20,
        }
    )

    # Ejemplo: usuario quiere Italiana Tradicional, sin gluten y vegetariano, evita "corn syrup"
    q = UserQuery(
        hard=HardConstraints(
            required_diets={normalize_restriction("gluten free"), normalize_restriction("vegetarian")},
            forbidden_ingredients={"corn syrup"},
            allergens=set(),
        ),
        soft=SoftPreferences(
            cultura=split_taxonomy_tokens("Italiana"),
            estilo=split_taxonomy_tokens("Tradicional"),
            season="Summer",
            preferred_ingredients=ingredients_set(["garlic", "lemon"]),
        ),
        raw_text=None
    )

    res = retriever.retrieve(q, top_k_centroids=3)

    # imprime resumen
    print("\n--- Stage 1 (centroid) ---")
    print(json.dumps(to_jsonable(res.centroid_rank), ensure_ascii=False, indent=2))

    print("\n--- Stage 2 (rerank) ---")
    print(json.dumps(to_jsonable(res.rerank), ensure_ascii=False, indent=2))

    print("\n--- CHOSEN ---")
    out = {
        "chosen_case_id": res.chosen_case_id,
        "chosen_cluster_id": res.chosen_cluster_id,
        "menu": res.chosen_menu,
        "mismatches": res.mismatches,
        "suggested_swaps": res.suggested_swaps,
    }
    print(json.dumps(to_jsonable(out), ensure_ascii=False, indent=2))
