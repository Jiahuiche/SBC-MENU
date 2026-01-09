"""
CBR Adapt Module - Modulo de Adaptacion para Sistema de Recomendacion de Menus.

Este modulo implementa la fase de adaptacion del ciclo CBR, aplicando operadores
de transformacion para ajustar el menu recuperado a las restricciones del usuario.

Utiliza:
- Beam search para explorar el espacio de adaptaciones
- Bases de conocimiento para sustituciones inteligentes
- Ontologia de ingredientes para validar compatibilidad
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import retrieve_module as rm


# ----------------------------
# Paths a Bases de Conocimiento
# ----------------------------
BASE_DIR = Path(__file__).parent.parent
KB_DIR = BASE_DIR / "Bases_Conocimientos"


# ----------------------------
# Cargador de Sustituciones
# ----------------------------

class SubstitutionDatabase:
    """Base de datos de sustituciones de ingredientes."""
    
    _instance = None
    _loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not SubstitutionDatabase._loaded:
            self._substitutions: Dict[str, List[str]] = {}
            self._load_substitutions()
            SubstitutionDatabase._loaded = True
    
    def _load_substitutions(self) -> None:
        """Carga sustituciones desde el archivo JSON."""
        sub_path = KB_DIR / "ingredients_substitude.json"
        if sub_path.exists():
            try:
                with open(sub_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    ing = rm.normalize_text(entry.get("ingredient", ""))
                    sub = entry.get("substitution", "")
                    if ing and sub and len(sub) > 2:
                        sub_norm = rm.normalize_text(sub)
                        if ing not in self._substitutions:
                            self._substitutions[ing] = []
                        if sub_norm not in self._substitutions[ing]:
                            self._substitutions[ing].append(sub_norm)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Sustituciones predeterminadas (fallback)
        defaults = {
            "milk": ["soy milk", "almond milk", "oat milk"],
            "butter": ["olive oil", "margarine", "coconut oil"],
            "cream": ["coconut cream", "cashew cream"],
            "cheese": ["vegan cheese", "nutritional yeast"],
            "yogurt": ["soy yogurt", "coconut yogurt"],
            "egg": ["flax egg", "chia egg", "applesauce"],
            "beef": ["mushrooms", "seitan", "jackfruit"],
            "chicken": ["tofu", "tempeh", "seitan"],
            "pork": ["jackfruit", "seitan"],
            "bacon": ["smoked tofu", "tempeh bacon"],
            "shrimp": ["hearts of palm", "king oyster mushroom"],
            "flour": ["almond flour", "oat flour"],
            "wheat flour": ["rice flour", "gluten free flour"],
            "peanut": ["sunflower seeds", "soy butter"],
            "corn syrup": ["honey", "maple syrup", "agave"],
        }
        for ing, subs in defaults.items():
            if ing not in self._substitutions:
                self._substitutions[ing] = subs
            else:
                for s in subs:
                    if s not in self._substitutions[ing]:
                        self._substitutions[ing].append(s)
    
    def get_substitutions(self, ingredient: str) -> List[str]:
        """Obtiene posibles sustituciones para un ingrediente."""
        ing_norm = rm.normalize_text(ingredient)
        
        # Busqueda exacta
        if ing_norm in self._substitutions:
            return self._substitutions[ing_norm]
        
        # Busqueda parcial
        for key in self._substitutions:
            if key in ing_norm or ing_norm in key:
                return self._substitutions[key]
        
        return []
    
    def get_best_substitution(
        self, 
        ingredient: str, 
        cultura: Set[str] = None,
        kb: rm.KnowledgeBaseLoader = None
    ) -> Optional[str]:
        """
        Obtiene la mejor sustitucion para un ingrediente,
        priorizando ingredientes culturalmente apropiados.
        """
        subs = self.get_substitutions(ingredient)
        if not subs:
            return None
        
        if not cultura or not kb:
            return subs[0]
        
        # Priorizar sustituciones culturalmente apropiadas
        valid_cultural = kb.get_ingredients_for_context(cultura, set())
        for sub in subs:
            sub_norm = rm.normalize_text(sub)
            if any(sub_norm in v or v in sub_norm for v in valid_cultural):
                return sub
        
        # Priorizar por similitud ontologica
        ing_families = kb.get_ingredient_families(ingredient)
        if ing_families:
            best_sim = 0.0
            best_sub = subs[0]
            for sub in subs:
                sim = kb.get_family_depth_similarity(ingredient, sub)
                if sim > best_sim:
                    best_sim = sim
                    best_sub = sub
            return best_sub
        
        return subs[0]


# ----------------------------
# Matching robusto
# ----------------------------

def word_boundary_match(needle: str, hay: str) -> bool:
    """Match con limites de palabra para evitar falsos positivos."""
    needle = rm.normalize_text(needle)
    hay = rm.normalize_text(hay)
    if not needle or not hay:
        return False
    pattern = r"\b" + re.escape(needle) + r"\b"
    return re.search(pattern, hay) is not None


# ----------------------------
# Tecnicas de cocina
# ----------------------------

TECH_KEYWORDS = [
    "deep fry", "fry", "fried", "bake", "roast", "grill", "broil",
    "steam", "boil", "simmer", "saute", "sear", "poach", "blend",
    "mix", "marinate", "ferment", "smoke", "raw", "no bake"
]

TECH_SUBSTITUTIONS = {
    "deep fry": "bake",
    "fry": "bake",
    "fried": "baked",
    "saute": "steam",
}


def extract_techniques(instructions: Optional[str]) -> Set[str]:
    """Extrae tecnicas de cocina de las instrucciones."""
    if not instructions:
        return set()
    txt = rm.normalize_text(instructions)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt)
    
    found = set()
    for k in TECH_KEYWORDS:
        if word_boundary_match(k, txt):
            found.add(k)
    return found


# ----------------------------
# Operadores / Trazas
# ----------------------------

@dataclass
class AdaptationStep:
    """Representa un paso de adaptacion aplicado."""
    operator: str
    course: str
    params: Dict[str, Any]
    rationale: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None


@dataclass
class AdaptationResult:
    """Resultado del proceso de adaptacion."""
    adapted_menu: Dict[str, Dict[str, Any]]
    steps: List[AdaptationStep]
    final_eval: Dict[str, Any]
    unresolved: List[Dict[str, Any]]


@dataclass
class MenuState:
    """Estado del menu durante el proceso de adaptacion."""
    menu: Dict[str, Dict[str, Any]]
    steps: List[AdaptationStep] = field(default_factory=list)
    
    def copy(self) -> "MenuState":
        return MenuState(menu=copy.deepcopy(self.menu), steps=list(self.steps))


# ----------------------------
# Adapter Principal (Beam Search)
# ----------------------------

class CBRAdapter:
    """
    Adaptador CBR que utiliza beam search para explorar
    el espacio de adaptaciones posibles.
    
    Integra:
    - Base de sustituciones de ingredientes
    - Ontologia para validar compatibilidad
    - Ingredientes por contexto cultural
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
        self.kb = retriever.kb
        
        self.beam_width = beam_width
        self.max_steps = max_steps
        self.step_penalty = step_penalty
        self.hard_penalty = hard_penalty
        
        # Cargar base de sustituciones
        self.sub_db = SubstitutionDatabase()
    
    # ----------------------------
    # Scoring de estados
    # ----------------------------
    
    def _score_state(self, st: MenuState, q: rm.UserQuery) -> float:
        """Calcula puntuacion de un estado del menu."""
        ev = self.retriever.evaluate_menu(st.menu, q)
        hard_pen = self.hard_penalty * ev["hard_violation_count"]
        soft = float(ev["soft_score"])
        steps_pen = self.step_penalty * len(st.steps)
        return soft - hard_pen - steps_pen
    
    # ----------------------------
    # Helpers para operaciones sobre platos
    # ----------------------------
    
    def _dish_is_essential(self, dish: Dict[str, Any], ingredient: str) -> bool:
        """Determina si un ingrediente es esencial para el plato."""
        title = rm.normalize_text(dish.get("title", ""))
        if word_boundary_match(ingredient, title):
            return True
        for ing in (dish.get("ingredients", []) or []):
            if rm.normalize_text(ing) == rm.normalize_text(ingredient):
                return True
        return False
    
    def _apply_remove_ingredient(self, dish: Dict[str, Any], bad: str) -> Dict[str, Any]:
        """Elimina un ingrediente de un plato."""
        new = copy.deepcopy(dish)
        keep = []
        for ing in (new.get("ingredients", []) or []):
            if word_boundary_match(bad, ing) or rm.normalize_text(ing) == rm.normalize_text(bad):
                continue
            keep.append(ing)
        new["ingredients"] = keep
        return new
    
    def _apply_add_ingredient(self, dish: Dict[str, Any], ing: str) -> Dict[str, Any]:
        """Agrega un ingrediente a un plato."""
        new = copy.deepcopy(dish)
        ings = new.get("ingredients", []) or []
        if all(not word_boundary_match(ing, x) and rm.normalize_text(x) != rm.normalize_text(ing) for x in ings):
            ings.append(ing)
        new["ingredients"] = ings
        return new
    
    def _apply_substitute_ingredient(self, dish: Dict[str, Any], old: str, new_ing: str) -> Dict[str, Any]:
        """Sustituye un ingrediente por otro."""
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
        
        # Deduplicar manteniendo orden
        seen = set()
        ded = []
        for x in out:
            k = rm.normalize_text(x)
            if k not in seen:
                seen.add(k)
                ded.append(x)
        new["ingredients"] = ded
        return new
    
    def _get_smart_substitution(
        self, 
        ingredient: str, 
        q: rm.UserQuery,
        forbidden: Set[str] = None
    ) -> Optional[str]:
        """
        Obtiene una sustitucion inteligente validando:
        1. Compatibilidad ontologica
        2. Coherencia cultural
        3. No esta prohibido
        """
        forbidden = forbidden or set()
        
        # Obtener sustituciones de la base de datos
        subs = self.sub_db.get_substitutions(ingredient)
        if not subs:
            return None
        
        cultura = q.soft.cultura if q.soft else set()
        
        for sub in subs:
            sub_norm = rm.normalize_text(sub)
            
            # Verificar que no esta prohibido
            if any(sub_norm in f or f in sub_norm for f in forbidden):
                continue
            
            # Verificar compatibilidad ontologica
            if self.kb.ingredients_share_family(ingredient, sub):
                # Verificar coherencia cultural si aplica
                if not cultura or self.kb.is_ingredient_valid_for_culture(sub, cultura):
                    return sub
        
        # Si no hay match ontologico, intentar solo cultural
        for sub in subs:
            sub_norm = rm.normalize_text(sub)
            if any(sub_norm in f or f in sub_norm for f in forbidden):
                continue
            if not cultura or self.kb.is_ingredient_valid_for_culture(sub, cultura):
                return sub
        
        # Fallback: primer sustitucion no prohibida
        for sub in subs:
            sub_norm = rm.normalize_text(sub)
            if not any(sub_norm in f or f in sub_norm for f in forbidden):
                return sub
        
        return None
    
    def _recipe_to_dish(self, r: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte una receta a formato de plato del menu."""
        keys = [
            "recipe_id", "title", "course_type", "cultura", "estilo_cocina", "season",
            "ingredients", "restrictions", "ready_in_minutes", "price_per_serving",
            "complexity_score", "health_factor"
        ]
        d = {k: r.get(k) for k in keys}
        d["recipe_id"] = int(d["recipe_id"])
        return d
    
    def _swap_recipe(self, st: MenuState, course: str, to_recipe_id: int, why: str) -> Optional[MenuState]:
        """Intercambia un plato completo por otra receta."""
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
        """Encuentra el mejor candidato para swap dentro del cluster o global."""
        # Intentar dentro del cluster
        member_ids = case.get("cluster_member_recipe_ids", [])
        if member_ids and hasattr(self.retriever, "_best_recipe_for_course"):
            best = self.retriever._best_recipe_for_course(member_ids, course, q)
            if best:
                _, r = best
                return int(r["recipe_id"])
        
        # Fallback global
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
    
    # ----------------------------
    # Expansion de estados (generacion de candidatos)
    # ----------------------------
    
    def _expand(self, st: MenuState, case: Dict[str, Any], q: rm.UserQuery) -> List[MenuState]:
        """Genera estados candidatos aplicando operadores."""
        ev = self.retriever.evaluate_menu(st.menu, q)
        out: List[MenuState] = []
        
        forbidden = {rm.normalize_text(x) for x in (q.hard.forbidden_ingredients | q.hard.allergens) if x}
        
        # A) Hard violations: reparar primero
        if ev["hard_violation_count"] > 0:
            hv = ev["hard_violations"][0]
            course = hv["course"]
            dish = st.menu[course]
            
            for vio in hv["violations"]:
                if vio["type"] == "forbidden_ingredient_present":
                    for bad in vio["hits"]:
                        essential = self._dish_is_essential(dish, bad)
                        
                        # Buscar sustitucion inteligente
                        smart_sub = self._get_smart_substitution(bad, q, forbidden)
                        
                        if essential:
                            # Ingrediente esencial: preferir sustitucion o swap
                            if smart_sub:
                                ns = st.copy()
                                before = ns.menu[course]
                                after = self._apply_substitute_ingredient(before, bad, smart_sub)
                                ns.menu[course] = after
                                ns.steps.append(AdaptationStep(
                                    operator="substitute_ingredient",
                                    course=course,
                                    params={"old": bad, "new": smart_sub},
                                    rationale=f"Hard violation: ingrediente esencial '{bad}' -> sustituir por '{smart_sub}' (validado ontologicamente).",
                                    before=before,
                                    after=after
                                ))
                                out.append(ns)
                            
                            # Swap como alternativa
                            rid = self._best_swap_candidate(case, course, q)
                            if rid is not None:
                                ns2 = self._swap_recipe(st, course, rid, "Hard violation (esencial) -> swap receta.")
                                if ns2:
                                    out.append(ns2)
                        else:
                            # No esencial: eliminar o sustituir
                            ns = st.copy()
                            before = ns.menu[course]
                            after = self._apply_remove_ingredient(before, bad)
                            ns.menu[course] = after
                            ns.steps.append(AdaptationStep(
                                operator="remove_ingredient",
                                course=course,
                                params={"ingredient": bad},
                                rationale=f"Hard violation: ingrediente prohibido '{bad}' -> eliminar.",
                                before=before,
                                after=after
                            ))
                            out.append(ns)
                            
                            if smart_sub:
                                ns2 = st.copy()
                                before2 = ns2.menu[course]
                                after2 = self._apply_substitute_ingredient(before2, bad, smart_sub)
                                ns2.menu[course] = after2
                                ns2.steps.append(AdaptationStep(
                                    operator="substitute_ingredient",
                                    course=course,
                                    params={"old": bad, "new": smart_sub},
                                    rationale=f"Hard violation: '{bad}' -> sustituir por '{smart_sub}'.",
                                    before=before2,
                                    after=after2
                                ))
                                out.append(ns2)
                
                elif vio["type"] == "missing_required_restriction":
                    # Swap es la mejor opcion sin modelo nutricional
                    rid = self._best_swap_candidate(case, course, q)
                    if rid is not None:
                        ns = self._swap_recipe(st, course, rid, "Falta restriccion requerida -> swap receta.")
                        if ns:
                            out.append(ns)
            
            return out
        
        # B) Sin hard violations: mejoras soft
        if q.soft.preferred_ingredients:
            for course in ["starter", "main"]:
                dish = st.menu.get(course)
                if not dish:
                    continue
                dish_ings = dish.get("ingredients", []) or []
                for pref in list(q.soft.preferred_ingredients)[:2]:
                    if any(word_boundary_match(pref, x) for x in dish_ings):
                        continue
                    
                    # Verificar coherencia cultural antes de agregar
                    if q.soft.cultura and not self.kb.is_ingredient_valid_for_culture(pref, q.soft.cultura):
                        continue
                    
                    ns = st.copy()
                    before = ns.menu[course]
                    after = self._apply_add_ingredient(before, pref)
                    ns.menu[course] = after
                    ns.steps.append(AdaptationStep(
                        operator="add_ingredient",
                        course=course,
                        params={"ingredient": pref},
                        rationale=f"Soft preference: agregar ingrediente preferido '{pref}'.",
                        before=before,
                        after=after
                    ))
                    out.append(ns)
        
        # Mismatch cultural severo: swap
        for course, det in ev.get("soft_details", {}).items():
            c_j = det.get("cultura_jaccard", 1.0)
            e_j = det.get("estilo_jaccard", 1.0)
            if (q.soft.cultura and c_j < 0.10) or (q.soft.estilo and e_j < 0.10):
                rid = self._best_swap_candidate(case, course, q)
                if rid is not None:
                    ns = self._swap_recipe(st, course, rid, "Mismatch cultura/estilo severo -> swap receta.")
                    if ns:
                        out.append(ns)
        
        return out
    
    # ----------------------------
    # API Principal
    # ----------------------------
    
    def adapt(self, case: Dict[str, Any], q: rm.UserQuery) -> AdaptationResult:
        """
        Adapta un caso recuperado a las restricciones del usuario
        usando beam search.
        """
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
            beam = [s for _, s in candidates[:self.beam_width]]
            
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
# Ejemplo de uso
# ----------------------------

if __name__ == "__main__":
    retriever = rm.CBRRetriever(
        case_base_path="../Base_Casos/case_base_menus.json",
        recipes_db_path="../Bases_Conocimientos/cbr_recipes_database.json",
        embedder=None
    )
    
    case = retriever.cases[0]
    
    q = rm.UserQuery(
        hard=rm.HardConstraints(
            forbidden_ingredients={"pumpkin"},
        ),
        soft=rm.SoftPreferences(
            cultura=rm.split_taxonomy_tokens("Italiana"),
            preferred_ingredients=rm.ingredients_set(["garlic"])
        )
    )
    
    adapter = CBRAdapter(retriever, beam_width=6, max_steps=6)
    out = adapter.adapt(case, q)
    
    print(f"Hard violations after adapt: {out.final_eval['hard_violation_count']}")
    print(f"Steps applied: {[s.operator for s in out.steps]}")
