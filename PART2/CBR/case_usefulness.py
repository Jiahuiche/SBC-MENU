"""
CASE USEFULNESS MODULE FOR CBR MENU SYSTEM
===========================================

This module calculates the usefulness of a case to determine whether it should
be retained in the case base. The usefulness is based on:
- Performance: How well it solved the problem
- Similarity: How similar to existing cases (inverse used - high similarity = redundant)
- Novelty: How unique/innovative the case is
- Trace: Adaptation effort (high trace = valuable learning)
"""

import numpy as np
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class CaseMetrics:
    """Metrics for evaluating a case"""
    performance: float  # 0-1: User satisfaction, constraint compliance
    similarity: float   # 0-1: Max similarity to existing cases
    novelty: float      # 0-1: Uniqueness of ingredients/combinations
    trace: float        # 0-1: Adaptation effort (# of modifications)
    
    def validate(self):
        """Ensure all metrics are in valid range"""
        for field in ['performance', 'similarity', 'novelty', 'trace']:
            value = getattr(self, field)
            if not 0 <= value <= 1:
                raise ValueError(f"{field} must be between 0 and 1, got {value}")


def calculate_case_usefulness(
    performance: float,
    similarity: float,
    novelty: float,
    trace: float,
    weights: Optional[Dict[str, float]] = None,
    use_similarity_penalty: bool = True
) -> float:
    """
    Calculate the usefulness of a case based on its attributes.
    
    Key insight: High similarity is BAD (redundant case), so we use (1 - similarity)
    to penalize cases that are too similar to existing ones.

    Parameters:
        performance (float): How well the case solved the problem (0 to 1).
            - 1.0 = Perfect solution (all constraints met, user satisfied)
            - 0.5 = Acceptable solution
            - 0.0 = Failed solution
            
        similarity (float): Max similarity to any existing case (0 to 1).
            - 1.0 = Identical to existing case (redundant!)
            - 0.5 = Moderately similar
            - 0.0 = Completely unique
            
        novelty (float): How unique the case is (0 to 1).
            - 1.0 = Highly innovative (new ingredient combinations, techniques)
            - 0.5 = Moderately novel
            - 0.0 = Standard/common combinations
            
        trace (float): The effort made in adapting the case (0 to 1).
            - 1.0 = Many adaptations (complex learning experience)
            - 0.5 = Some adaptations
            - 0.0 = No adaptations (case retrieved as-is)
            
        weights (dict, optional): Weights for each attribute.
            Default: performance=0.4, dissimilarity=0.15, novelty=0.25, trace=0.2
            
        use_similarity_penalty (bool): If True, use (1-similarity) to penalize
            redundant cases. If False, use similarity as-is.

    Returns:
        float: The usefulness score of the case (0 to 1).
            - Score > 0.7: Definitely save (high value)
            - Score 0.5-0.7: Consider saving (moderate value)
            - Score < 0.5: Discard (low value or redundant)
    """
    # Validate inputs
    metrics = CaseMetrics(performance, similarity, novelty, trace)
    metrics.validate()
    
    # Default weights emphasizing performance and novelty
    if weights is None:
        weights = {
            'performance': 0.4,    # Most important: did it work?
            'dissimilarity': 0.15, # Avoid redundancy
            'novelty': 0.25,       # Value innovation
            'trace': 0.2           # Value learning experiences
        }

    # Ensure weights sum to 1
    weight_sum = sum(weights.values())
    if not abs(weight_sum - 1.0) < 1e-6:
        raise ValueError(f"Weights must sum to 1, got {weight_sum}")

    # Convert similarity to dissimilarity (high similarity = bad)
    dissimilarity = (1 - similarity) if use_similarity_penalty else similarity
    
    # Calculate weighted usefulness
    usefulness = (
        performance * weights['performance'] +
        dissimilarity * weights['dissimilarity'] +
        novelty * weights['novelty'] +
        trace * weights['trace']
    )

    return usefulness


def calculate_performance_score(
    user_feedback: Optional[float] = None,
    constraint_satisfaction: float = 0.0,
    dietary_compliance: float = 0.0,
    seasonal_score: float = 0.0
) -> float:
    """
    Calculate performance based on multiple factors.
    
    Parameters:
        user_feedback: Direct user rating (0-1), if available
        constraint_satisfaction: Fraction of hard constraints met (0-1)
        dietary_compliance: Fraction of dietary restrictions satisfied (0-1)
        seasonal_score: Score for seasonal ingredient usage (0-1)
    
    Returns:
        float: Overall performance score (0-1)
    """
    if user_feedback is not None:
        # If we have direct feedback, weight it heavily
        return 0.6 * user_feedback + 0.4 * constraint_satisfaction
    else:
        # Otherwise, use objective metrics
        return (constraint_satisfaction * 0.5 + 
                dietary_compliance * 0.3 + 
                seasonal_score * 0.2)


def calculate_similarity_to_case_base(
    new_case: Dict[str, Any],
    case_base: List[Dict[str, Any]],
    similarity_function=None
) -> float:
    """
    Calculate maximum similarity between new case and existing cases.
    Uses Jaccard similarity on ingredients if no function provided.
    
    Parameters:
        new_case: The case to evaluate
        case_base: List of existing cases
        similarity_function: Function that takes two cases and returns similarity (0-1)
                           If None, uses default ingredient-based Jaccard
    
    Returns:
        float: Maximum similarity to any existing case (0-1)
    """
    if not case_base:
        return 0.0
    
    # Use default Jaccard similarity on ingredients if no function provided
    if similarity_function is None:
        similarity_function = _jaccard_ingredient_similarity
    
    similarities = [similarity_function(new_case, existing_case) 
                   for existing_case in case_base]
    return max(similarities) if similarities else 0.0


def _jaccard_ingredient_similarity(case1: Dict[str, Any], case2: Dict[str, Any]) -> float:
    """
    Similarity function based on USER QUERY (input problem), not menu.
    Compares the problems being solved, not the solutions.
    
    This is more appropriate for CBR case retention:
    - High similarity = solving the SAME problem = redundant case
    - Low similarity = solving DIFFERENT problem = valuable diversity
    
    Compatible with retrieve_module structure.
    """
    # Extract user queries (the input problems) - use P from case base
    query1 = case1.get('query', case1.get('P', {}))
    query2 = case2.get('query', case2.get('P', {}))
    
    # If no queries, fall back to ingredient comparison
    if not query1 or not query2:
        return _fallback_ingredient_similarity(case1, case2)
    
    # Extract hard constraints - support both 'hard' and 'restricciones_duras'
    hard1 = query1.get('hard', query1.get('restricciones_duras', []))
    hard2 = query2.get('hard', query2.get('restricciones_duras', []))
    
    # For restricciones_duras (list format), extract as restrictions
    if isinstance(hard1, list):
        hard1_restrictions = set(str(r).lower().strip() for r in hard1)
        diets1 = hard1_restrictions
        forbidden1 = hard1_restrictions
    else:
        # Required diets
        diets1 = set(str(d).lower().strip() for d in hard1.get('required_diets', []))
        # Forbidden ingredients + allergens
        forbidden1 = set(str(f).lower().strip() for f in hard1.get('forbidden_ingredients', []))
        forbidden1.update(str(a).lower().strip() for a in hard1.get('allergens', []))
    
    if isinstance(hard2, list):
        hard2_restrictions = set(str(r).lower().strip() for r in hard2)
        diets2 = hard2_restrictions
        forbidden2 = hard2_restrictions
    else:
        diets2 = set(str(d).lower().strip() for d in hard2.get('required_diets', []))
        forbidden2 = set(str(f).lower().strip() for f in hard2.get('forbidden_ingredients', []))
        forbidden2.update(str(a).lower().strip() for a in hard2.get('allergens', []))
    
    # Extract soft preferences - support both 'soft' and 'preferencias_blandas'
    soft1 = query1.get('soft', query1.get('preferencias_blandas', {}))
    soft2 = query2.get('soft', query2.get('preferencias_blandas', {}))
    
    # Cultura preferences
    cultura1_raw = soft1.get('cultura', [])
    cultura1 = set([str(cultura1_raw).lower().strip()]) if isinstance(cultura1_raw, str) else set(str(c).lower().strip() for c in cultura1_raw if c)
    
    cultura2_raw = soft2.get('cultura', [])
    cultura2 = set([str(cultura2_raw).lower().strip()]) if isinstance(cultura2_raw, str) else set(str(c).lower().strip() for c in cultura2_raw if c)
    
    # Estilo preferences (can be string or list)
    estilo1_raw = soft1.get('estilo', [])
    estilo1 = set([str(estilo1_raw).lower().strip()]) if isinstance(estilo1_raw, str) else set(str(e).lower().strip() for e in estilo1_raw if e)
    
    estilo2_raw = soft2.get('estilo', [])
    estilo2 = set([str(estilo2_raw).lower().strip()]) if isinstance(estilo2_raw, str) else set(str(e).lower().strip() for e in estilo2_raw if e)
    
    # Season preferences (from evento.estacion_mes)
    season1 = str(soft1.get('season', '')).lower().strip()
    if not season1 and isinstance(query1, dict):
        evento1 = query1.get('evento', {})
        season1 = str(evento1.get('estacion_mes', '')).lower().strip()
    
    season2 = str(soft2.get('season', '')).lower().strip()
    if not season2 and isinstance(query2, dict):
        evento2 = query2.get('evento', {})
        season2 = str(evento2.get('estacion_mes', '')).lower().strip()
    
    # Calculate Jaccard similarity for each component
    similarities = []
    
    # Hard constraints similarity (most important)
    if diets1 or diets2:
        diet_sim = _jaccard_set(diets1, diets2)
        similarities.append(diet_sim * 3)  # Weight more heavily
    
    if forbidden1 or forbidden2:
        forbidden_sim = _jaccard_set(forbidden1, forbidden2)
        similarities.append(forbidden_sim * 2)  # Weight moderately
    
    # Soft preferences similarity
    if cultura1 or cultura2:
        cultura_sim = _jaccard_set(cultura1, cultura2)
        similarities.append(cultura_sim)
    
    if estilo1 or estilo2:
        estilo_sim = _jaccard_set(estilo1, estilo2)
        similarities.append(estilo_sim)
    
    # Season similarity (exact match or both empty)
    if season1 or season2:
        season_sim = 1.0 if (season1 == season2 or season1 == 'all' or season2 == 'all') else 0.0
        similarities.append(season_sim)
    
    # Return weighted average
    if similarities:
        return sum(similarities) / len(similarities)
    else:
        # If no query information, fall back to ingredient similarity
        return _fallback_ingredient_similarity(case1, case2)


def _jaccard_set(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets"""
    if not set1 and not set2:
        return 1.0  # Both empty = similar
    if not set1 or not set2:
        return 0.0  # One empty, one not = dissimilar
    
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def _fallback_ingredient_similarity(case1: Dict[str, Any], case2: Dict[str, Any]) -> float:
    """
    Fallback: Compare based on menu ingredients if no query information available.
    """
    ing1 = set()
    ing2 = set()
    
    # Extract ingredients from menu
    menu1 = case1.get('menu', case1.get('S', {}).get('menu', {}))
    menu2 = case2.get('menu', case2.get('S', {}).get('menu', {}))
    
    for course in menu1.values():
        if isinstance(course, dict):
            ingredients = course.get('ingredients', [])
            if isinstance(ingredients, list):
                ing1.update(ing.lower().strip() for ing in ingredients)
    
    for course in menu2.values():
        if isinstance(course, dict):
            ingredients = course.get('ingredients', [])
            if isinstance(ingredients, list):
                ing2.update(ing.lower().strip() for ing in ingredients)
    
    return _jaccard_set(ing1, ing2)


def calculate_novelty_score(
    menu: Dict[str, Dict[str, Any]],
    case_base: List[Dict[str, Any]],
    ingredient_frequency: Optional[Dict[str, int]] = None
) -> float:
    """
    Calculate novelty based on ingredient combinations and uniqueness.
    
    Parameters:
        menu: The menu dictionary with courses and ingredients
        case_base: List of existing cases
        ingredient_frequency: Optional dict mapping ingredients to their frequency in case base
    
    Returns:
        float: Novelty score (0-1)
    """
    # Extract all ingredients from menu
    all_ingredients = set()
    for course_data in menu.values():
        if isinstance(course_data, dict) and 'ingredients' in course_data:
            ingredients = course_data['ingredients']
            if isinstance(ingredients, list):
                all_ingredients.update([ing.lower().strip() for ing in ingredients])
    
    if not all_ingredients:
        return 0.0
    
    # Calculate ingredient rarity
    if ingredient_frequency is None:
        # Build frequency from case base (support both 'menu' and 'S.menu')
        ingredient_frequency = {}
        for case in case_base:
            # Try 'menu' first, then 'S' (solution)
            case_menu = case.get('menu', {})
            if not case_menu and 'S' in case:
                case_menu = case['S'].get('menu', {})
            
            for course_data in case_menu.values():
                if isinstance(course_data, dict) and 'ingredients' in course_data:
                    ingredients = course_data['ingredients']
                    if isinstance(ingredients, list):
                        for ing in ingredients:
                            ing = ing.lower().strip()
                            ingredient_frequency[ing] = ingredient_frequency.get(ing, 0) + 1
    
    # Calculate average rarity (rare ingredients = high novelty)
    total_cases = len(case_base) if case_base else 1
    rarity_scores = []
    
    for ing in all_ingredients:
        frequency = ingredient_frequency.get(ing, 0)
        rarity = 1.0 - (frequency / total_cases)  # Rare = high score
        rarity_scores.append(rarity)
    
    novelty = np.mean(rarity_scores) if rarity_scores else 0.5
    return float(novelty)


def calculate_trace_score(
    adaptation_steps: List[Dict[str, Any]],
    max_steps: int = 10
) -> float:
    """
    Calculate trace score based on adaptation effort.
    SIMPLIFIED: Only counts the number of operations, no complexity weighting.
    
    Parameters:
        adaptation_steps: List of adaptation operations performed
        max_steps: Maximum expected number of steps (for normalization)
    
    Returns:
        float: Trace score (0-1), higher means more adaptations
    """
    if not adaptation_steps:
        return 0.0
    
    num_steps = len(adaptation_steps)
    
    # Simple normalization: just count the operations
    trace = min(num_steps / max_steps, 1.0)
    
    return float(trace)


def should_retain_case(
    usefulness: float,
    threshold: float = 0.5,
    strategy: str = "threshold"
) -> bool:
    """
    Decide whether to retain a case based on its usefulness.
    
    Parameters:
        usefulness: The usefulness score (0-1)
        threshold: Minimum usefulness required to retain
        strategy: Retention strategy:
            - "threshold": Simple threshold comparison
            - "conservative": Higher threshold (0.6)
            - "liberal": Lower threshold (0.4)
            - "adaptive": Adjust based on case base size
    
    Returns:
        bool: True if case should be retained
    """
    if strategy == "threshold":
        return usefulness >= threshold
    elif strategy == "conservative":
        return usefulness >= 0.6
    elif strategy == "liberal":
        return usefulness >= 0.4
    elif strategy == "adaptive":
        # Could be extended to adjust based on case base size
        return usefulness >= threshold
    else:
        raise ValueError(f"Unknown strategy: {strategy}")


def evaluate_case_usefulness(
    menu: Dict[str, Dict[str, Any]],
    adaptation_steps: List[Dict[str, Any]],
    case_base: List[Dict[str, Any]],
    similarity_function,
    user_feedback: Optional[float] = None,
    constraint_satisfaction: float = 1.0,
    weights: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Complete evaluation of a case's usefulness.
    
    Parameters:
        menu: The adapted menu
        adaptation_steps: List of adaptation operations
        case_base: Existing case base
        similarity_function: Function to calculate similarity between cases
        user_feedback: Optional user satisfaction rating (0-1)
        constraint_satisfaction: How well constraints were met (0-1)
        weights: Optional custom weights for usefulness calculation
    
    Returns:
        dict: Detailed evaluation results including:
            - usefulness: Overall usefulness score
            - performance: Performance metric
            - similarity: Max similarity to existing cases
            - novelty: Novelty score
            - trace: Adaptation effort score
            - recommendation: Whether to retain the case
            - rationale: Explanation of the decision
    """
    # Calculate individual metrics
    performance = calculate_performance_score(
        user_feedback=user_feedback,
        constraint_satisfaction=constraint_satisfaction
    )
    
    # Wrap new case with both formats for compatibility
    new_case = {
        'menu': menu,
        'S': {'menu': menu}
    }
    similarity = calculate_similarity_to_case_base(
        new_case, case_base, similarity_function
    )
    
    novelty = calculate_novelty_score(menu, case_base)
    trace = calculate_trace_score(adaptation_steps)
    
    # Calculate overall usefulness
    usefulness = calculate_case_usefulness(
        performance, similarity, novelty, trace, weights
    )
    
    # Determine retention recommendation
    should_retain = should_retain_case(usefulness, threshold=0.5)
    
    # Generate rationale
    rationale = _generate_rationale(
        usefulness, performance, similarity, novelty, trace, should_retain
    )
    
    return {
        'usefulness': round(usefulness, 3),
        'performance': round(performance, 3),
        'similarity': round(similarity, 3),
        'novelty': round(novelty, 3),
        'trace': round(trace, 3),
        'should_retain': should_retain,
        'rationale': rationale,
        'metrics': {
            'dissimilarity': round(1 - similarity, 3),
            'adaptation_steps': len(adaptation_steps)
        }
    }


def _generate_rationale(
    usefulness: float,
    performance: float,
    similarity: float,
    novelty: float,
    trace: float,
    should_retain: bool
) -> str:
    """Generate human-readable rationale for retention decision"""
    parts = []
    
    if should_retain:
        parts.append(f"✅ RETAIN - Usefulness: {usefulness:.2f}")
    else:
        parts.append(f"❌ DISCARD - Usefulness: {usefulness:.2f}")
    
    # Performance analysis
    if performance >= 0.8:
        parts.append(f"Excellent performance ({performance:.2f})")
    elif performance >= 0.6:
        parts.append(f"Good performance ({performance:.2f})")
    else:
        parts.append(f"Low performance ({performance:.2f}) - needs improvement")
    
    # Similarity analysis
    if similarity >= 0.8:
        parts.append(f"Very similar to existing cases ({similarity:.2f}) - redundant")
    elif similarity >= 0.5:
        parts.append(f"Moderately similar ({similarity:.2f})")
    else:
        parts.append(f"Unique case ({similarity:.2f}) - adds diversity")
    
    # Novelty analysis
    if novelty >= 0.7:
        parts.append(f"Highly novel ({novelty:.2f}) - valuable innovation")
    elif novelty >= 0.4:
        parts.append(f"Moderately novel ({novelty:.2f})")
    else:
        parts.append(f"Common ingredients ({novelty:.2f})")
    
    # Trace analysis
    if trace >= 0.7:
        parts.append(f"Complex adaptation ({trace:.2f}) - valuable learning")
    elif trace >= 0.4:
        parts.append(f"Moderate adaptation ({trace:.2f})")
    else:
        parts.append(f"Minimal adaptation ({trace:.2f})")
    
    return " | ".join(parts)


# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

def test_case_usefulness_scenarios():
    """Test different scenarios to understand the usefulness calculation"""
    
    print("\n" + "="*70)
    print("CASE USEFULNESS EVALUATION - TEST SCENARIOS")
    print("="*70 + "\n")
    
    scenarios = [
        {
            'name': '🌟 Scenario 1: High-Value Case (Should RETAIN)',
            'description': 'Excellent performance, unique, complex adaptation',
            'performance': 0.9,
            'similarity': 0.2,  # Low similarity = unique
            'novelty': 0.8,
            'trace': 0.7
        },
        {
            'name': '🔄 Scenario 2: Redundant Case (Should DISCARD)',
            'description': 'Good performance but almost identical to existing case',
            'performance': 0.8,
            'similarity': 0.95,  # Very similar = redundant
            'novelty': 0.3,
            'trace': 0.2
        },
        {
            'name': '⚠️ Scenario 3: Poor Performance (Should DISCARD)',
            'description': 'Unique case but failed to meet constraints',
            'performance': 0.3,
            'similarity': 0.1,
            'novelty': 0.9,
            'trace': 0.8
        },
        {
            'name': '💡 Scenario 4: Valuable Learning Case (Should RETAIN)',
            'description': 'Good performance, moderate uniqueness, high adaptation effort',
            'performance': 0.75,
            'similarity': 0.4,
            'novelty': 0.6,
            'trace': 0.9  # High trace = valuable learning
        },
        {
            'name': '📋 Scenario 5: Retrieved As-Is (Should DISCARD)',
            'description': 'Retrieved case with no modifications',
            'performance': 0.8,
            'similarity': 0.6,
            'novelty': 0.4,
            'trace': 0.0  # No adaptation = no learning value
        },
        {
            'name': '🎨 Scenario 6: Innovative Recipe (Should RETAIN)',
            'description': 'Very novel ingredients and techniques',
            'performance': 0.85,
            'similarity': 0.15,
            'novelty': 0.95,  # Highly innovative
            'trace': 0.5
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Inputs: P={scenario['performance']:.2f}, "
              f"S={scenario['similarity']:.2f}, "
              f"N={scenario['novelty']:.2f}, "
              f"T={scenario['trace']:.2f}")
        
        usefulness = calculate_case_usefulness(
            scenario['performance'],
            scenario['similarity'],
            scenario['novelty'],
            scenario['trace']
        )
        
        should_retain = should_retain_case(usefulness)
        decision = "✅ RETAIN" if should_retain else "❌ DISCARD"
        
        print(f"   → Usefulness: {usefulness:.3f} → {decision}")
        print(f"   → Dissimilarity bonus: {(1 - scenario['similarity']):.2f}")


def example_complete_evaluation():
    """Complete example with a realistic menu case"""
    
    print("\n" + "="*70)
    print("COMPLETE CASE EVALUATION EXAMPLE")
    print("="*70 + "\n")
    
    # Example adapted menu
    example_menu = {
        'starter': {
            'name': 'Roasted Beet and Goat Cheese Salad',
            'ingredients': ['beet', 'goat cheese', 'arugula', 'walnuts', 'balsamic'],
            'cuisine': 'mediterranean',
            'cooking_style': 'modern'
        },
        'main': {
            'name': 'Pan-Seared Sea Bass with Cauliflower Puree',
            'ingredients': ['sea bass', 'cauliflower', 'garlic', 'white wine', 'herbs'],
            'cuisine': 'french',
            'cooking_style': 'gourmet'
        },
        'dessert': {
            'name': 'Lavender Panna Cotta with Berry Compote',
            'ingredients': ['cream', 'lavender', 'mixed berries', 'honey', 'gelatin'],
            'cuisine': 'italian',
            'cooking_style': 'modern'
        }
    }
    
    # Example adaptation steps (complex case)
    adaptation_steps = [
        {'operator': 'substitute_ingredient', 'from': 'beef', 'to': 'sea bass', 
         'rationale': 'pescatarian diet'},
        {'operator': 'add_ingredient', 'ingredient': 'lavender', 
         'rationale': 'seasonal herb'},
        {'operator': 'substitute_technique', 'from': 'grill', 'to': 'pan-sear',
         'rationale': 'better for fish'},
        {'operator': 'remove_ingredient', 'ingredient': 'butter',
         'rationale': 'dairy-light preference'}
    ]
    
    # Mock case base (simplified)
    mock_case_base = [
        {
            'menu': {
                'starter': {'ingredients': ['tomato', 'mozzarella', 'basil']},
                'main': {'ingredients': ['chicken', 'pasta', 'tomato']},
                'dessert': {'ingredients': ['chocolate', 'cream', 'sugar']}
            }
        },
        {
            'menu': {
                'starter': {'ingredients': ['salmon', 'cucumber', 'dill']},
                'main': {'ingredients': ['steak', 'potato', 'asparagus']},
                'dessert': {'ingredients': ['vanilla', 'cream', 'berries']}
            }
        }
    ]
    
    # Simple similarity function (Jaccard on ingredients)
    def simple_similarity(case1, case2):
        ing1 = set()
        ing2 = set()
        for course in case1.get('menu', {}).values():
            if isinstance(course, dict):
                ing1.update(course.get('ingredients', []))
        for course in case2.get('menu', {}).values():
            if isinstance(course, dict):
                ing2.update(course.get('ingredients', []))
        
        if not ing1 or not ing2:
            return 0.0
        intersection = len(ing1 & ing2)
        union = len(ing1 | ing2)
        return intersection / union if union > 0 else 0.0
    
    # Evaluate the case
    print("Evaluating adapted menu case...")
    print(f"Menu courses: {list(example_menu.keys())}")
    print(f"Adaptation steps: {len(adaptation_steps)}")
    print(f"Case base size: {len(mock_case_base)}\n")
    
    evaluation = evaluate_case_usefulness(
        menu=example_menu,
        adaptation_steps=adaptation_steps,
        case_base=mock_case_base,
        similarity_function=simple_similarity,
        user_feedback=0.85,  # User was satisfied
        constraint_satisfaction=1.0  # All constraints met
    )
    
    # Display results
    print("EVALUATION RESULTS:")
    print("-" * 70)
    print(f"Usefulness Score:     {evaluation['usefulness']:.3f}")
    print(f"  - Performance:      {evaluation['performance']:.3f}")
    print(f"  - Similarity:       {evaluation['similarity']:.3f} "
          f"(dissimilarity: {evaluation['metrics']['dissimilarity']:.3f})")
    print(f"  - Novelty:          {evaluation['novelty']:.3f}")
    print(f"  - Trace:            {evaluation['trace']:.3f}")
    print(f"\nDecision: {'✅ RETAIN' if evaluation['should_retain'] else '❌ DISCARD'}")
    print(f"\n{evaluation['rationale']}")


def example_custom_weights():
    """Example showing different weighting strategies"""
    
    print("\n" + "="*70)
    print("CUSTOM WEIGHT STRATEGIES")
    print("="*70 + "\n")
    
    # Case attributes
    performance = 0.75
    similarity = 0.5
    novelty = 0.6
    trace = 0.7
    
    strategies = [
        {
            'name': 'Default (Balanced)',
            'weights': None  # Will use defaults
        },
        {
            'name': 'Performance-Focused',
            'weights': {
                'performance': 0.6,
                'dissimilarity': 0.1,
                'novelty': 0.2,
                'trace': 0.1
            }
        },
        {
            'name': 'Innovation-Focused',
            'weights': {
                'performance': 0.3,
                'dissimilarity': 0.2,
                'novelty': 0.4,
                'trace': 0.1
            }
        },
        {
            'name': 'Learning-Focused',
            'weights': {
                'performance': 0.3,
                'dissimilarity': 0.1,
                'novelty': 0.2,
                'trace': 0.4
            }
        }
    ]
    
    print(f"Case: P={performance:.2f}, S={similarity:.2f}, "
          f"N={novelty:.2f}, T={trace:.2f}\n")
    
    for strategy in strategies:
        usefulness = calculate_case_usefulness(
            performance, similarity, novelty, trace,
            weights=strategy['weights']
        )
        print(f"{strategy['name']:25s} → Usefulness: {usefulness:.3f}")


if __name__ == "__main__":
    # Run all examples
    test_case_usefulness_scenarios()
    example_complete_evaluation()
    example_custom_weights()
    
    print("\n" + "="*70)
    print("✅ All examples completed!")
    print("="*70 + "\n")