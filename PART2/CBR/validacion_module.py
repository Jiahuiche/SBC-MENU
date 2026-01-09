"""
VALIDATION AND RETENTION MODULE FOR CBR SYSTEM
================================================

This module implements the REVISE and RETAIN phases of the CBR cycle:
- REVISE: Validate that the adapted solution meets all requirements
- RETAIN: Decide whether to save the case in the case base

The retention decision is based on case usefulness, which considers:
- Performance (how well it solved the problem)
- Similarity (avoiding redundant cases)
- Novelty (valuing innovative solutions)
- Trace (valuing complex adaptations that represent learning)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from case_usefulness import (
    evaluate_case_usefulness,
    should_retain_case,
    calculate_performance_score
)


class ValidationError(Exception):
    """Raised when a case fails validation"""
    pass


class CBRValidator:
    """
    Validates adapted cases and manages case base retention.
    
    Implements the REVISE and RETAIN phases of the CBR cycle.
    """
    
    def __init__(
        self,
        case_base_path: str,
        retention_threshold: float = 0.5,
        retention_strategy: str = "threshold",
        max_case_base_size: Optional[int] = None
    ):
        """
        Initialize the validator.
        
        Parameters:
            case_base_path: Path to the case base JSON file
            retention_threshold: Minimum usefulness score to retain a case
            retention_strategy: Strategy for retention ("threshold", "conservative", "liberal")
            max_case_base_size: Maximum number of cases to keep (None = unlimited)
        """
        self.case_base_path = Path(case_base_path)
        self.retention_threshold = retention_threshold
        self.retention_strategy = retention_strategy
        self.max_case_base_size = max_case_base_size
        self.case_base = self._load_case_base()
    
    def _load_case_base(self) -> List[Dict[str, Any]]:
        """Load the case base from file"""
        if not self.case_base_path.exists():
            print(f"⚠️ Case base not found at {self.case_base_path}, starting with empty base")
            return []
        
        try:
            with open(self.case_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading case base: {e}")
            return []
    
    def _save_case_base(self):
        """Save the case base to file"""
        try:
            # Create directory if it doesn't exist
            self.case_base_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save with pretty printing
            with open(self.case_base_path, 'w', encoding='utf-8') as f:
                json.dump(self.case_base, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Case base saved: {len(self.case_base)} cases")
        except Exception as e:
            print(f"❌ Error saving case base: {e}")
            raise
    
    def validate_hard_constraints(
        self,
        menu: Dict[str, Dict[str, Any]],
        user_query: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that the menu meets all hard constraints.
        
        Parameters:
            menu: The adapted menu
            user_query: The original user query with constraints
        
        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []
        
        # Extract hard constraints
        hard = user_query.get('hard', {})
        forbidden = set(hard.get('forbidden_ingredients', []))
        required_diets = set(hard.get('required_diets', []))
        allergens = set(hard.get('allergens', []))
        
        # Check each course
        for course_name, course_data in menu.items():
            if not isinstance(course_data, dict):
                continue
            
            ingredients = set(
                ing.lower().strip() 
                for ing in course_data.get('ingredients', [])
            )
            
            # Check forbidden ingredients
            found_forbidden = ingredients & forbidden
            if found_forbidden:
                violations.append(
                    f"Course '{course_name}' contains forbidden ingredients: "
                    f"{', '.join(found_forbidden)}"
                )
            
            # Check allergens
            found_allergens = ingredients & allergens
            if found_allergens:
                violations.append(
                    f"Course '{course_name}' contains allergens: "
                    f"{', '.join(found_allergens)}"
                )
            
            # Check dietary restrictions (simplified)
            if 'vegan' in required_diets:
                non_vegan = {'meat', 'chicken', 'beef', 'pork', 'fish', 
                           'seafood', 'egg', 'eggs', 'dairy', 'cheese', 
                           'milk', 'cream', 'butter'}
                found_non_vegan = ingredients & non_vegan
                if found_non_vegan:
                    violations.append(
                        f"Course '{course_name}' not vegan: {', '.join(found_non_vegan)}"
                    )
        
        is_valid = len(violations) == 0
        return is_valid, violations
    
    def validate_soft_preferences(
        self,
        menu: Dict[str, Dict[str, Any]],
        user_query: Dict[str, Any]
    ) -> float:
        """
        Calculate how well the menu matches soft preferences.
        
        Parameters:
            menu: The adapted menu
            user_query: The original user query with preferences
        
        Returns:
            float: Satisfaction score (0-1)
        """
        soft = user_query.get('soft', {})
        preferred_cultura = set(soft.get('cultura', []))
        preferred_estilo = set(soft.get('estilo', []))
        preferred_season = soft.get('season', '')
        preferred_ingredients = set(soft.get('preferred_ingredients', []))
        
        scores = []
        
        # Check cultura match
        if preferred_cultura:
            menu_culturas = set()
            for course_data in menu.values():
                if isinstance(course_data, dict):
                    cuisine = course_data.get('cuisine', '').lower()
                    if cuisine:
                        menu_culturas.add(cuisine)
            
            if menu_culturas:
                cultura_match = len(menu_culturas & preferred_cultura) / len(preferred_cultura)
                scores.append(cultura_match)
        
        # Check estilo match
        if preferred_estilo:
            menu_estilos = set()
            for course_data in menu.values():
                if isinstance(course_data, dict):
                    estilo = course_data.get('cooking_style', '').lower()
                    if estilo:
                        menu_estilos.add(estilo)
            
            if menu_estilos:
                estilo_match = len(menu_estilos & preferred_estilo) / len(preferred_estilo)
                scores.append(estilo_match)
        
        # Check ingredient preferences
        if preferred_ingredients:
            menu_ingredients = set()
            for course_data in menu.values():
                if isinstance(course_data, dict):
                    ingredients = course_data.get('ingredients', [])
                    menu_ingredients.update(ing.lower() for ing in ingredients)
            
            if menu_ingredients:
                ing_match = len(menu_ingredients & preferred_ingredients) / len(preferred_ingredients)
                scores.append(ing_match)
        
        return sum(scores) / len(scores) if scores else 0.5
    
    def revise_case(
        self,
        adapted_menu: Dict[str, Dict[str, Any]],
        user_query: Dict[str, Any],
        adaptation_steps: List[Dict[str, Any]],
        user_feedback: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        REVISE phase: Validate and evaluate the adapted solution.
        
        Parameters:
            adapted_menu: The adapted menu
            user_query: The original user query
            adaptation_steps: List of adaptation operations performed
            user_feedback: Optional user satisfaction rating (0-1)
        
        Returns:
            dict: Revision results including validation and performance metrics
        """
        print("\n" + "="*70)
        print("🔍 REVISE PHASE: Validating adapted solution")
        print("="*70)
        
        # Validate hard constraints
        is_valid, violations = self.validate_hard_constraints(
            adapted_menu, user_query
        )
        
        if not is_valid:
            print("\n❌ Hard constraint violations detected:")
            for violation in violations:
                print(f"   - {violation}")
        else:
            print("\n✅ All hard constraints satisfied")
        
        # Evaluate soft preferences
        soft_satisfaction = self.validate_soft_preferences(
            adapted_menu, user_query
        )
        print(f"📊 Soft preference satisfaction: {soft_satisfaction:.2%}")
        
        # Calculate overall performance
        constraint_satisfaction = 1.0 if is_valid else 0.0
        performance = calculate_performance_score(
            user_feedback=user_feedback,
            constraint_satisfaction=constraint_satisfaction,
            dietary_compliance=constraint_satisfaction,
            seasonal_score=soft_satisfaction
        )
        
        print(f"🎯 Overall performance score: {performance:.3f}")
        
        return {
            'is_valid': is_valid,
            'violations': violations,
            'constraint_satisfaction': constraint_satisfaction,
            'soft_satisfaction': soft_satisfaction,
            'performance': performance,
            'adaptation_steps_count': len(adaptation_steps)
        }
    
    def retain_case(
        self,
        adapted_menu: Dict[str, Dict[str, Any]],
        user_query: Dict[str, Any],
        adaptation_steps: List[Dict[str, Any]],
        revision_results: Dict[str, Any],
        user_feedback: Optional[float] = None,
        similarity_function = None
    ) -> Dict[str, Any]:
        """
        RETAIN phase: Decide whether to save the case in the case base.
        
        Parameters:
            adapted_menu: The adapted menu
            user_query: The original user query
            adaptation_steps: List of adaptation operations
            revision_results: Results from the revise phase
            user_feedback: Optional user satisfaction rating
            similarity_function: Function to calculate similarity between cases
        
        Returns:
            dict: Retention decision and detailed metrics
        """
        print("\n" + "="*70)
        print("💾 RETAIN PHASE: Evaluating case usefulness")
        print("="*70)
        
        # Use simple similarity if none provided
        if similarity_function is None:
            similarity_function = self._simple_similarity
        
        # Evaluate usefulness
        evaluation = evaluate_case_usefulness(
            menu=adapted_menu,
            adaptation_steps=adaptation_steps,
            case_base=self.case_base,
            similarity_function=similarity_function,
            user_feedback=user_feedback,
            constraint_satisfaction=revision_results['constraint_satisfaction']
        )
        
        # Display evaluation
        print(f"\n📈 Usefulness Evaluation:")
        print(f"   Performance:    {evaluation['performance']:.3f}")
        print(f"   Similarity:     {evaluation['similarity']:.3f}")
        print(f"   Novelty:        {evaluation['novelty']:.3f}")
        print(f"   Trace:          {evaluation['trace']:.3f}")
        print(f"   → Usefulness:   {evaluation['usefulness']:.3f}")
        
        # Make retention decision
        should_save = evaluation['should_retain']
        
        if should_save:
            print(f"\n✅ DECISION: RETAIN CASE")
            print(f"   {evaluation['rationale']}")
            
            # Create new case
            new_case = self._create_case(
                adapted_menu, user_query, adaptation_steps, 
                evaluation, revision_results
            )
            
            # Add to case base
            self.case_base.append(new_case)
            
            # Check if we need to remove old cases
            if self.max_case_base_size and len(self.case_base) > self.max_case_base_size:
                self._prune_case_base()
            
            # Save case base
            self._save_case_base()
            
            evaluation['case_saved'] = True
            evaluation['new_case_id'] = new_case['case_id']
        else:
            print(f"\n❌ DECISION: DISCARD CASE")
            print(f"   {evaluation['rationale']}")
            evaluation['case_saved'] = False
        
        return evaluation
    
    def _create_case(
        self,
        menu: Dict[str, Dict[str, Any]],
        user_query: Dict[str, Any],
        adaptation_steps: List[Dict[str, Any]],
        evaluation: Dict[str, Any],
        revision_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new case entry for the case base"""
        
        # Generate unique case ID
        case_id = f"case_{len(self.case_base) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            'case_id': case_id,
            'menu': menu,
            'query': user_query,
            'adaptation_steps': adaptation_steps,
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'usefulness': evaluation['usefulness'],
                'performance': evaluation['performance'],
                'novelty': evaluation['novelty'],
                'trace': evaluation['trace'],
                'similarity': evaluation['similarity'],
                'adaptation_count': len(adaptation_steps),
                'constraint_satisfaction': revision_results['constraint_satisfaction'],
                'soft_satisfaction': revision_results['soft_satisfaction']
            }
        }
    
    def _simple_similarity(self, case1: Dict[str, Any], case2: Dict[str, Any]) -> float:
        """Simple Jaccard similarity on ingredients"""
        ing1 = set()
        ing2 = set()
        
        for course in case1.get('menu', {}).values():
            if isinstance(course, dict):
                ing1.update(ing.lower().strip() for ing in course.get('ingredients', []))
        
        for course in case2.get('menu', {}).values():
            if isinstance(course, dict):
                ing2.update(ing.lower().strip() for ing in course.get('ingredients', []))
        
        if not ing1 or not ing2:
            return 0.0
        
        intersection = len(ing1 & ing2)
        union = len(ing1 | ing2)
        return intersection / union if union > 0 else 0.0
    
    def _prune_case_base(self):
        """Remove least useful cases when case base is too large"""
        print(f"\n🔧 Pruning case base (current size: {len(self.case_base)})")
        
        # Sort by usefulness (descending)
        self.case_base.sort(
            key=lambda c: c.get('metadata', {}).get('usefulness', 0),
            reverse=True
        )
        
        # Keep only the most useful cases
        removed_count = len(self.case_base) - self.max_case_base_size
        self.case_base = self.case_base[:self.max_case_base_size]
        
        print(f"   Removed {removed_count} least useful cases")
        print(f"   New case base size: {len(self.case_base)}")
    
    def get_case_base_statistics(self) -> Dict[str, Any]:
        """Get statistics about the case base"""
        if not self.case_base:
            return {'size': 0, 'message': 'Case base is empty'}
        
        usefulness_scores = [
            c.get('metadata', {}).get('usefulness', 0)
            for c in self.case_base
        ]
        
        return {
            'size': len(self.case_base),
            'avg_usefulness': sum(usefulness_scores) / len(usefulness_scores),
            'min_usefulness': min(usefulness_scores),
            'max_usefulness': max(usefulness_scores),
            'cases_with_adaptations': sum(
                1 for c in self.case_base 
                if c.get('metadata', {}).get('adaptation_count', 0) > 0
            )
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def example_validation_workflow():
    """Complete example of the validation and retention workflow"""
    
    print("\n" + "="*70)
    print("VALIDATION AND RETENTION WORKFLOW EXAMPLE")
    print("="*70)
    
    # Initialize validator
    validator = CBRValidator(
        case_base_path='../Base_Casos/case_base_menus.json',
        retention_threshold=0.5,
        retention_strategy='threshold',
        max_case_base_size=100
    )
    
    # Example adapted menu
    adapted_menu = {
        'starter': {
            'name': 'Grilled Vegetable Platter',
            'ingredients': ['zucchini', 'eggplant', 'bell pepper', 'olive oil', 'herbs'],
            'cuisine': 'mediterranean',
            'cooking_style': 'healthy'
        },
        'main': {
            'name': 'Quinoa Buddha Bowl',
            'ingredients': ['quinoa', 'chickpeas', 'kale', 'avocado', 'tahini'],
            'cuisine': 'fusion',
            'cooking_style': 'modern'
        },
        'dessert': {
            'name': 'Coconut Chia Pudding',
            'ingredients': ['chia seeds', 'coconut milk', 'mango', 'honey'],
            'cuisine': 'tropical',
            'cooking_style': 'healthy'
        }
    }
    
    # Example user query
    user_query = {
        'hard': {
            'required_diets': ['vegan'],
            'forbidden_ingredients': ['meat', 'dairy'],
            'allergens': ['nuts']
        },
        'soft': {
            'cultura': ['mediterranean', 'fusion'],
            'estilo': ['healthy', 'modern'],
            'season': 'summer',
            'preferred_ingredients': ['quinoa', 'avocado', 'vegetables']
        }
    }
    
    # Example adaptation steps
    adaptation_steps = [
        {
            'operator': 'substitute_ingredient',
            'course': 'main',
            'params': {'from': 'chicken', 'to': 'chickpeas'},
            'rationale': 'vegan diet requirement'
        },
        {
            'operator': 'substitute_ingredient',
            'course': 'dessert',
            'params': {'from': 'cream', 'to': 'coconut milk'},
            'rationale': 'dairy-free requirement'
        },
        {
            'operator': 'add_ingredient',
            'course': 'main',
            'params': {'ingredient': 'tahini'},
            'rationale': 'enhance flavor and protein'
        }
    ]
    
    # REVISE phase
    revision_results = validator.revise_case(
        adapted_menu=adapted_menu,
        user_query=user_query,
        adaptation_steps=adaptation_steps,
        user_feedback=0.85  # User was satisfied
    )
    
    # RETAIN phase
    retention_results = validator.retain_case(
        adapted_menu=adapted_menu,
        user_query=user_query,
        adaptation_steps=adaptation_steps,
        revision_results=revision_results,
        user_feedback=0.85
    )
    
    # Display case base statistics
    print("\n" + "="*70)
    print("📊 CASE BASE STATISTICS")
    print("="*70)
    stats = validator.get_case_base_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    example_validation_workflow()
