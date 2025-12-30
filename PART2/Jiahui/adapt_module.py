from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import retrieve_module as rm  # reusar normalización + evaluate_menu + scoring


# ----------------------------
# Matching robusto (evita 'corn' dentro de 'acorn')
# ----------------------------
def word_boundary_match(needle: str, hay: str) -> bool:
    needle = rm.normalize_text(needle)
    hay = rm.normalize_text(hay)
    if not needle or not hay:
        return False
    pattern = r"\b" + re.escape(needle) + r"\b"
    return re.search(pattern, hay) is not None


# ----------------------------
# Técnicas: extracción ligera desde instrucciones (si existen)
# ----------------------------
TECH_KEYWORDS = [
    "deep fry", "fry", "fried",
    "bake", "roast", "grill", "broil",
    "steam", "boil", "simmer",
    "saute", "sauté", "sear",
    "poach", "blend", "mix",
    "marinate", "ferment", "smoke",
    "raw", "no bake"
]

def extract_techniques(instructions: Optional[str]) -> Set[str]:
    if not instructions:
        return set()
    txt = rm.normalize_text(instructions)
    txt = re.sub(r"<[^>]+>", " ", txt)  # quita html simple
    txt = re.sub(r"\s+", " ", txt)

    found = set()
    for k in TECH_KEYWORDS:
        if word_boundary_match(k, txt):
            found.add(k)
    return found


# ----------------------------
# Operadores / trazas
# ----------------------------
@dataclass
class AdaptationStep:
    operator: str
    course: str
    params: Dict[str, Any]
    rationale: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None

@dataclass
class AdaptationResult:
    adapted_menu: Dict[str, Dict[str, Any]]
    steps: List[AdaptationStep]
    final_eval: Dict[str, Any]
    unresolved: List[Dict[str, Any]]


@dataclass
class MenuState:
    menu: Dict[str, Dict[str, Any]]
    steps: List[AdaptationStep] = field(default_factory=list)

    def copy(self) -> "MenuState":
        return MenuState(menu=copy.deepcopy(self.menu), steps=list(self.steps))


# ----------------------------
# Adapter (adaptation as search: beam search)
# ----------------------------
class CBRAdapter:
    """
    - Consistente con retrieve_module.py:
      usa retriever.evaluate_menu() para medir hard/soft.
    - Decide operadores (ing/tech add/remove/substitute) y usa swap receta como fallback.
    """

    def __init__(
        self,
        retriever: rm.CBRRetriever,
        beam_width: int = 6,
        max_steps: int = 6,
        step_penalty: float = 0.8,
        hard_penalty: float = 100.0,
    ):
        self.retriever = retriever
        self.recipe_by_id = retriever.recipe_by_id or {}

        self.beam_width = beam_width
        self.max_steps = max_steps
        self.step_penalty = step_penalty
        self.hard_penalty = hard_penalty

        # Sustituciones seed (amplíalas con taxonomía/ontología/diccionarios)
        self.sub_ing = {
            "milk": "soy milk",
            "butter": "olive oil",
            "cream": "coconut cream",
            "cheese": "vegan cheese",
            "yogurt": "soy yogurt",
            "egg": "flax egg",
            "beef": "mushrooms",
            "chicken": "tofu",
            "pork": "chicken",
            "bacon": "smoked tofu",
            "shrimp": "mushrooms",
            "flour": "almond flour",
            "wheat flour": "rice flour",
            "peanut": "sunflower seeds",
        }

        self.sub_tech = {
            "deep fry": "bake",
            "fry": "bake",
            "fried": "baked",
            "saute": "steam",
            "sauté": "steam",
        }

    # ---------- scoring estado ----------
    def _score_state(self, st: MenuState, q: rm.UserQuery) -> float:
        ev = self.retriever.evaluate_menu(st.menu, q)
        hard_pen = self.hard_penalty * ev["hard_violation_count"]
        soft = float(ev["soft_score"])
        steps_pen = self.step_penalty * len(st.steps)
        return soft - hard_pen - steps_pen

    # ---------- helpers dish ----------
    def _dish_is_essential(self, dish: Dict[str, Any], ingredient: str) -> bool:
        title = rm.normalize_text(dish.get("title", ""))
        if word_boundary_match(ingredient, title):
            return True
        for ing in (dish.get("ingredients", []) or []):
            if rm.normalize_text(ing) == rm.normalize_text(ingredient):
                return True
        return False

    def _apply_remove_ingredient(self, dish: Dict[str, Any], bad: str) -> Dict[str, Any]:
        new = copy.deepcopy(dish)
        keep = []
        for ing in (new.get("ingredients", []) or []):
            if word_boundary_match(bad, ing) or rm.normalize_text(ing) == rm.normalize_text(bad):
                continue
            keep.append(ing)
        new["ingredients"] = keep
        return new

    def _apply_add_ingredient(self, dish: Dict[str, Any], ing: str) -> Dict[str, Any]:
        new = copy.deepcopy(dish)
        ings = new.get("ingredients", []) or []
        if all(not word_boundary_match(ing, x) and rm.normalize_text(x) != rm.normalize_text(ing) for x in ings):
            ings.append(ing)
        new["ingredients"] = ings
        return new

    def _apply_substitute_ingredient(self, dish: Dict[str, Any], old: str, new_ing: str) -> Dict[str, Any]:
        new = copy.deepcopy(dish)
        ings = new.get("ingredients", []) or []
        out = []
        replaced = False
        for ing in ings:
            if (not replaced) and (word_boundary_match(old, ing) or rm.normalize_text(ing) == rm.normalize_text(old)):
                out.append(new_ing)
                replaced = True
            else:
                out.append(ing)
        if not replaced:
            out.append(new_ing)

        # dedup manteniendo orden
        seen = set()
        ded = []
        for x in out:
            k = rm.normalize_text(x)
            if k not in seen:
                seen.add(k)
                ded.append(x)
        new["ingredients"] = ded
        return new

    def _ensure_techniques(self, dish: Dict[str, Any]) -> Dict[str, Any]:
        new = copy.deepcopy(dish)
        if "techniques" in new:
            return new
        rid = int(new.get("recipe_id"))
        r = self.recipe_by_id.get(rid)
        tech = extract_techniques(r.get("instructions")) if r else set()
        new["techniques"] = sorted(tech)
        return new

    def _apply_remove_technique(self, dish: Dict[str, Any], tech: str) -> Dict[str, Any]:
        new = self._ensure_techniques(dish)
        new["techniques"] = [t for t in (new.get("techniques", []) or []) if rm.normalize_text(t) != rm.normalize_text(tech)]
        return new

    def _apply_add_technique(self, dish: Dict[str, Any], tech: str) -> Dict[str, Any]:
        new = self._ensure_techniques(dish)
        t = new.get("techniques", []) or []
        if rm.normalize_text(tech) not in {rm.normalize_text(x) for x in t}:
            t.append(tech)
        new["techniques"] = t
        return new

    def _apply_substitute_technique(self, dish: Dict[str, Any], old: str, new_tech: str) -> Dict[str, Any]:
        new = self._ensure_techniques(dish)
        t = new.get("techniques", []) or []
        out = []
        replaced = False
        for x in t:
            if (not replaced) and rm.normalize_text(x) == rm.normalize_text(old):
                out.append(new_tech)
                replaced = True
            else:
                out.append(x)
        if not replaced:
            out.append(new_tech)

        seen = set()
        ded = []
        for x in out:
            k = rm.normalize_text(x)
            if k not in seen:
                seen.add(k)
                ded.append(x)
        new["techniques"] = ded
        return new

    def _recipe_to_dish(self, r: Dict[str, Any]) -> Dict[str, Any]:
        keys = [
            "recipe_id","title","course_type","cultura","estilo_cocina","season",
            "ingredients","restrictions","ready_in_minutes","price_per_serving",
            "complexity_score","health_factor"
        ]
        d = {k: r.get(k) for k in keys}
        d["recipe_id"] = int(d["recipe_id"])
        return d

    def _swap_recipe(self, st: MenuState, course: str, to_recipe_id: int, why: str) -> Optional[MenuState]:
        r = self.recipe_by_id.get(int(to_recipe_id))
        if not r:
            return None
        ns = st.copy()
        before = ns.menu[course]
        after = self._recipe_to_dish(r)
        ns.menu[course] = after
        ns.steps.append(AdaptationStep(
            operator="swap_recipe",
            course=course,
            params={"to_recipe_id": int(to_recipe_id)},
            rationale=why,
            before=before,
            after=after
        ))
        return ns

    def _best_swap_candidate(self, case: Dict[str, Any], course: str, q: rm.UserQuery) -> Optional[int]:
        """
        1) intenta dentro del cluster (misma lógica que retrieve)
        2) fallback global
        """
        member_ids = case.get("cluster_member_recipe_ids", [])
        if member_ids and hasattr(self.retriever, "_best_recipe_for_course"):
            best = self.retriever._best_recipe_for_course(member_ids, course, q)
            if best:
                _, r = best
                return int(r["recipe_id"])

        cand = []
        for r in self.recipe_by_id.values():
            if rm.normalize_text(r.get("course_type")) != rm.normalize_text(course):
                continue
            if self.retriever.dish_violations(r, q.hard):
                continue
            sc, _ = self.retriever.dish_soft_score(r, q.soft)
            cand.append((sc, r))
        if not cand:
            return None
        cand.sort(key=lambda x: x[0], reverse=True)
        return int(cand[0][1]["recipe_id"])

    # ---------- generación de candidatos (decide operador) ----------
    def _expand(self, st: MenuState, case: Dict[str, Any], q: rm.UserQuery) -> List[MenuState]:
        ev = self.retriever.evaluate_menu(st.menu, q)
        out: List[MenuState] = []

        # A) Si hay hard violations: reparar primero (prioridad absoluta)
        if ev["hard_violation_count"] > 0:
            hv = ev["hard_violations"][0]
            course = hv["course"]
            dish = st.menu[course]

            for vio in hv["violations"]:
                if vio["type"] == "forbidden_ingredient_present":
                    for bad in vio["hits"]:
                        essential = self._dish_is_essential(dish, bad)

                        # Regla: si es esencial, NO “remove” (preferimos substitute o swap)
                        if essential:
                            if bad in self.sub_ing:
                                ns = st.copy()
                                before = ns.menu[course]
                                after = self._apply_substitute_ingredient(before, bad, self.sub_ing[bad])
                                ns.menu[course] = after
                                ns.steps.append(AdaptationStep(
                                    operator="substitute_ingredient",
                                    course=course,
                                    params={"old": bad, "new": self.sub_ing[bad]},
                                    rationale="Hard violation: ingrediente prohibido esencial -> sustituir por alternativa.",
                                    before=before,
                                    after=after
                                ))
                                out.append(ns)

                            # swap como alternativa coherente
                            rid = self._best_swap_candidate(case, course, q)
                            if rid is not None:
                                ns2 = self._swap_recipe(st, course, rid, "Hard violation (esencial) -> swap receta (mínimo cambio coherente).")
                                if ns2: out.append(ns2)
                            continue

                        # Si NO es esencial: remove (mínimo cambio) + substitute opcional
                        ns = st.copy()
                        before = ns.menu[course]
                        after = self._apply_remove_ingredient(before, bad)
                        ns.menu[course] = after
                        ns.steps.append(AdaptationStep(
                            operator="remove_ingredient",
                            course=course,
                            params={"ingredient": bad},
                            rationale="Hard violation: ingrediente prohibido no esencial -> eliminar (mínimo cambio).",
                            before=before,
                            after=after
                        ))
                        out.append(ns)

                        if bad in self.sub_ing:
                            ns2 = st.copy()
                            before2 = ns2.menu[course]
                            after2 = self._apply_substitute_ingredient(before2, bad, self.sub_ing[bad])
                            ns2.menu[course] = after2
                            ns2.steps.append(AdaptationStep(
                                operator="substitute_ingredient",
                                course=course,
                                params={"old": bad, "new": self.sub_ing[bad]},
                                rationale="Hard violation: alternativa válida -> sustituir en lugar de eliminar.",
                                before=before2,
                                after=after2
                            ))
                            out.append(ns2)

                elif vio["type"] == "missing_required_restriction":
                    # Micro-edición aquí es frágil sin un modelo nutricional -> swap
                    rid = self._best_swap_candidate(case, course, q)
                    if rid is not None:
                        ns = self._swap_recipe(st, course, rid, "Falta restricción requerida -> swap receta (cluster->global).")
                        if ns: out.append(ns)

            return out

        # B) Si ya no hay hard violations: mejoras soft baratas (add/substitute/remove)
        # Añadir ingredientes preferidos (starter/main por defecto)
        if q.soft.preferred_ingredients:
            for course in ["starter", "main"]:
                dish = st.menu.get(course)
                if not dish:
                    continue
                dish_ings = dish.get("ingredients", []) or []
                for pref in list(q.soft.preferred_ingredients)[:2]:
                    if any(word_boundary_match(pref, x) for x in dish_ings):
                        continue
                    ns = st.copy()
                    before = ns.menu[course]
                    after = self._apply_add_ingredient(before, pref)
                    ns.menu[course] = after
                    ns.steps.append(AdaptationStep(
                        operator="add_ingredient",
                        course=course,
                        params={"ingredient": pref},
                        rationale="Soft preference: añadir ingrediente deseado (mínimo cambio).",
                        before=before,
                        after=after
                    ))
                    out.append(ns)

        # Cultura/estilo muy lejos: swap es más coherente que micro-edición
        for course, det in ev.get("soft_details", {}).items():
            c_j = det.get("cultura_jaccard", 1.0)
            e_j = det.get("estilo_jaccard", 1.0)
            if (q.soft.cultura and c_j < 0.10) or (q.soft.estilo and e_j < 0.10):
                rid = self._best_swap_candidate(case, course, q)
                if rid is not None:
                    ns = self._swap_recipe(st, course, rid, "Global mismatch cultura/estilo -> swap receta (coherencia).")
                    if ns: out.append(ns)

        return out

    # ---------- API ----------
    def adapt(self, case: Dict[str, Any], q: rm.UserQuery) -> AdaptationResult:
        init = MenuState(menu=copy.deepcopy(case["S"]["menu"]), steps=[])
        beam = [init]

        best = init
        best_score = self._score_state(best, q)

        for _ in range(self.max_steps):
            candidates: List[Tuple[float, MenuState]] = []

            for st in beam:
                next_states = self._expand(st, case, q)
                if not next_states:
                    candidates.append((self._score_state(st, q), st))
                else:
                    for ns in next_states:
                        candidates.append((self._score_state(ns, q), ns))

            candidates.sort(key=lambda x: x[0], reverse=True)
            beam = [s for _, s in candidates[: self.beam_width]]

            if candidates and candidates[0][0] > best_score:
                best_score = candidates[0][0]
                best = candidates[0][1]

        final_eval = self.retriever.evaluate_menu(best.menu, q)
        unresolved = final_eval["hard_violations"] if final_eval["hard_violation_count"] > 0 else []
        return AdaptationResult(
            adapted_menu=best.menu,
            steps=best.steps,
            final_eval=final_eval,
            unresolved=unresolved
        )


# ----------------------------
# Ejemplo de uso (sin necesidad de sentence-transformers)
# ----------------------------
if __name__ == "__main__":
    retriever = rm.CBRRetriever(
        case_base_path="case_base_menus.json",
        recipes_db_path="cbr_recipes_database.json",
        embedder=None
    )

    # Si vienes del Retrieve:
    # result = retriever.retrieve(q)
    # case = next(c for c in retriever.cases if c["case_id"] == result.chosen_case_id)

    # Demo: usa el primer caso
    case = retriever.cases[0]

    q = rm.UserQuery(
        hard=rm.HardConstraints(
            required_diets=set(),
            forbidden_ingredients={"pumpkin"},
            allergens=set(),
        ),
        soft=rm.SoftPreferences(
            preferred_ingredients=rm.ingredients_set(["garlic"])
        )
    )

    adapter = CBRAdapter(retriever, beam_width=6, max_steps=6)
    out = adapter.adapt(case, q)

    print("Hard violations after adapt:", out.final_eval["hard_violation_count"])
    print("Steps:", [s.operator for s in out.steps])
