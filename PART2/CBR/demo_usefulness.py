"""
DEMONSTRATION: Case Usefulness Integration with CBR System
===========================================================

This script demonstrates how to integrate the case usefulness calculation
into your complete CBR workflow for menu recommendations.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from case_usefulness import (
    calculate_case_usefulness,
    evaluate_case_usefulness,
    CaseMetrics
)
from validacion_module import CBRValidator


def demo_scenario_analysis():
    """
    Demonstrate different retention scenarios with detailed analysis
    """
    print("\n" + "="*80)
    print("CASE USEFULNESS SCENARIOS - DETAILED ANALYSIS")
    print("="*80 + "\n")
    
    scenarios = [
        {
            'name': '🎯 SCENARIO 1: Perfect Case',
            'description': 'Wedding menu - all constraints met, innovative, complex adaptation',
            'menu': {
                'starter': {
                    'name': 'Smoked Salmon Rillettes with Fennel',
                    'ingredients': ['smoked salmon', 'fennel', 'capers', 'dill', 'cream cheese'],
                    'cuisine': 'french',
                    'cooking_style': 'gourmet'
                },
                'main': {
                    'name': 'Herb-Crusted Rack of Lamb',
                    'ingredients': ['lamb', 'herbs', 'garlic', 'dijon mustard', 'breadcrumbs'],
                    'cuisine': 'french',
                    'cooking_style': 'traditional'
                },
                'dessert': {
                    'name': 'Lavender Crème Brûlée',
                    'ingredients': ['cream', 'eggs', 'sugar', 'lavender', 'vanilla'],
                    'cuisine': 'french',
                    'cooking_style': 'gourmet'
                }
            },
            'adaptations': [
                {'operator': 'substitute_ingredient', 'rationale': 'seasonal preference'},
                {'operator': 'add_ingredient', 'rationale': 'enhance flavor profile'},
                {'operator': 'substitute_technique', 'rationale': 'optimize cooking method'}
            ],
            'user_feedback': 0.95,
            'expected_decision': 'RETAIN'
        },
        {
            'name': '⚠️ SCENARIO 2: Redundant Case',
            'description': 'Birthday party - very similar to existing popular menu',
            'menu': {
                'starter': {
                    'name': 'Classic Caesar Salad',
                    'ingredients': ['romaine', 'parmesan', 'croutons', 'caesar dressing'],
                    'cuisine': 'american',
                    'cooking_style': 'traditional'
                },
                'main': {
                    'name': 'Grilled Chicken Breast',
                    'ingredients': ['chicken', 'olive oil', 'herbs', 'lemon'],
                    'cuisine': 'american',
                    'cooking_style': 'traditional'
                },
                'dessert': {
                    'name': 'Chocolate Cake',
                    'ingredients': ['chocolate', 'flour', 'eggs', 'butter', 'sugar'],
                    'cuisine': 'american',
                    'cooking_style': 'traditional'
                }
            },
            'adaptations': [],  # Retrieved as-is
            'user_feedback': 0.75,
            'expected_decision': 'DISCARD'
        },
        {
            'name': '🚨 SCENARIO 3: Constraint Violation',
            'description': 'Vegan event - but contains dairy in one course',
            'menu': {
                'starter': {
                    'name': 'Roasted Vegetable Medley',
                    'ingredients': ['zucchini', 'eggplant', 'tomato', 'olive oil'],
                    'cuisine': 'mediterranean',
                    'cooking_style': 'healthy'
                },
                'main': {
                    'name': 'Mushroom Risotto',
                    'ingredients': ['arborio rice', 'mushrooms', 'onion', 'parmesan', 'butter'],
                    'cuisine': 'italian',
                    'cooking_style': 'traditional'
                },
                'dessert': {
                    'name': 'Fruit Sorbet',
                    'ingredients': ['mixed fruits', 'sugar', 'water', 'lemon'],
                    'cuisine': 'fusion',
                    'cooking_style': 'modern'
                }
            },
            'adaptations': [
                {'operator': 'substitute_ingredient', 'rationale': 'vegan requirement'},
                {'operator': 'substitute_ingredient', 'rationale': 'vegan requirement'}
            ],
            'user_feedback': 0.4,  # User noticed dairy
            'expected_decision': 'DISCARD'
        },
        {
            'name': '💡 SCENARIO 4: Learning-Rich Case',
            'description': 'Corporate event - many dietary restrictions, complex adaptation',
            'menu': {
                'starter': {
                    'name': 'Quinoa Tabbouleh with Herbs',
                    'ingredients': ['quinoa', 'parsley', 'mint', 'tomato', 'lemon', 'olive oil'],
                    'cuisine': 'middle eastern',
                    'cooking_style': 'healthy'
                },
                'main': {
                    'name': 'Baked Salmon with Almond Crust',
                    'ingredients': ['salmon', 'almonds', 'herbs', 'lemon', 'olive oil'],
                    'cuisine': 'fusion',
                    'cooking_style': 'modern'
                },
                'dessert': {
                    'name': 'Coconut Panna Cotta',
                    'ingredients': ['coconut milk', 'agar agar', 'vanilla', 'mango'],
                    'cuisine': 'tropical',
                    'cooking_style': 'modern'
                }
            },
            'adaptations': [
                {'operator': 'swap_recipe', 'rationale': 'gluten-free requirement'},
                {'operator': 'substitute_ingredient', 'rationale': 'dairy-free requirement'},
                {'operator': 'substitute_ingredient', 'rationale': 'nut allergy for one guest'},
                {'operator': 'substitute_technique', 'rationale': 'optimize for batch cooking'},
                {'operator': 'add_ingredient', 'rationale': 'enhance nutritional value'}
            ],
            'user_feedback': 0.8,
            'expected_decision': 'RETAIN'
        },
        {
            'name': '🌟 SCENARIO 5: Innovative Menu',
            'description': 'Fusion wedding - rare ingredients, creative combinations',
            'menu': {
                'starter': {
                    'name': 'Seared Scallops with Yuzu Foam',
                    'ingredients': ['scallops', 'yuzu', 'microgreens', 'sea salt', 'olive oil'],
                    'cuisine': 'fusion',
                    'cooking_style': 'molecular'
                },
                'main': {
                    'name': 'Miso-Glazed Black Cod with Edamame Puree',
                    'ingredients': ['black cod', 'miso', 'edamame', 'sake', 'mirin'],
                    'cuisine': 'japanese',
                    'cooking_style': 'gourmet'
                },
                'dessert': {
                    'name': 'Matcha Tiramisu with Sake-Poached Pear',
                    'ingredients': ['matcha', 'mascarpone', 'sake', 'pear', 'ladyfingers'],
                    'cuisine': 'fusion',
                    'cooking_style': 'modern'
                }
            },
            'adaptations': [
                {'operator': 'substitute_ingredient', 'rationale': 'fusion style preference'},
                {'operator': 'add_ingredient', 'rationale': 'enhance presentation'}
            ],
            'user_feedback': 0.9,
            'expected_decision': 'RETAIN'
        }
    ]
    
    # Simple case base for comparison
    simple_case_base = [
        {
            'menu': {
                'starter': {'ingredients': ['salad', 'tomato', 'cucumber']},
                'main': {'ingredients': ['chicken', 'rice', 'vegetables']},
                'dessert': {'ingredients': ['cake', 'chocolate', 'cream']}
            }
        }
    ]
    
    def simple_similarity(case1, case2):
        """Calculate Jaccard similarity on ingredients"""
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
    
    # Analyze each scenario
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{scenario['name']}")
        print(f"{'─'*80}")
        print(f"Description: {scenario['description']}")
        print(f"\nMenu: {list(scenario['menu'].keys())}")
        print(f"Adaptations: {len(scenario['adaptations'])} operations")
        print(f"User Feedback: {scenario['user_feedback']:.2f}")
        
        # Evaluate usefulness
        evaluation = evaluate_case_usefulness(
            menu=scenario['menu'],
            adaptation_steps=scenario['adaptations'],
            case_base=simple_case_base,
            similarity_function=simple_similarity,
            user_feedback=scenario['user_feedback'],
            constraint_satisfaction=1.0 if scenario['user_feedback'] > 0.5 else 0.0
        )
        
        # Display results
        print(f"\n📊 Usefulness Breakdown:")
        print(f"   Performance:    {evaluation['performance']:.3f}")
        print(f"   Similarity:     {evaluation['similarity']:.3f}")
        print(f"   Novelty:        {evaluation['novelty']:.3f}")
        print(f"   Trace:          {evaluation['trace']:.3f}")
        print(f"   ───────────────────────────")
        print(f"   USEFULNESS:     {evaluation['usefulness']:.3f}")
        
        decision = "✅ RETAIN" if evaluation['should_retain'] else "❌ DISCARD"
        expected = f"(Expected: {scenario['expected_decision']})"
        match = "✓" if decision.split()[1] == scenario['expected_decision'] else "✗"
        
        print(f"\n{decision} {expected} {match}")
        print(f"\n💭 Rationale: {evaluation['rationale']}")


def demo_weight_comparison():
    """
    Compare different weighting strategies on the same case
    """
    print("\n\n" + "="*80)
    print("WEIGHT STRATEGY COMPARISON")
    print("="*80 + "\n")
    
    # A case with moderate scores across all metrics
    performance = 0.7
    similarity = 0.5
    novelty = 0.6
    trace = 0.8
    
    print(f"Case Metrics: P={performance:.2f}, S={similarity:.2f}, "
          f"N={novelty:.2f}, T={trace:.2f}\n")
    
    strategies = [
        {
            'name': 'Default (Balanced)',
            'weights': None,
            'description': 'Balanced approach valuing all factors'
        },
        {
            'name': 'Performance-Focused',
            'weights': {
                'performance': 0.6,
                'dissimilarity': 0.1,
                'novelty': 0.2,
                'trace': 0.1
            },
            'description': 'Prioritizes successful solutions over innovation'
        },
        {
            'name': 'Innovation-Focused',
            'weights': {
                'performance': 0.3,
                'dissimilarity': 0.2,
                'novelty': 0.4,
                'trace': 0.1
            },
            'description': 'Prioritizes novel and unique cases'
        },
        {
            'name': 'Learning-Focused',
            'weights': {
                'performance': 0.3,
                'dissimilarity': 0.1,
                'novelty': 0.2,
                'trace': 0.4
            },
            'description': 'Prioritizes cases with complex adaptations'
        },
        {
            'name': 'Quality + Diversity',
            'weights': {
                'performance': 0.5,
                'dissimilarity': 0.3,
                'novelty': 0.15,
                'trace': 0.05
            },
            'description': 'Balance between quality and avoiding redundancy'
        }
    ]
    
    results = []
    for strategy in strategies:
        usefulness = calculate_case_usefulness(
            performance, similarity, novelty, trace,
            weights=strategy['weights']
        )
        decision = "RETAIN" if usefulness >= 0.5 else "DISCARD"
        results.append({
            'strategy': strategy['name'],
            'usefulness': usefulness,
            'decision': decision,
            'description': strategy['description']
        })
    
    # Display comparison table
    print(f"{'Strategy':<25} {'Usefulness':<12} {'Decision':<10} {'Description'}")
    print("─" * 80)
    
    for result in results:
        decision_emoji = "✅" if result['decision'] == "RETAIN" else "❌"
        print(f"{result['strategy']:<25} {result['usefulness']:.3f}        "
              f"{decision_emoji} {result['decision']:<10}")
        print(f"{'':25} {result['description']}")
        print()
    
    print("\n💡 Insight: The same case can be retained or discarded depending on")
    print("   your retention strategy. Choose weights based on your goals:")
    print("   • Performance-focused: For established restaurants with quality standards")
    print("   • Innovation-focused: For experimental/creative culinary projects")
    print("   • Learning-focused: For training systems or complex problem domains")


def demo_integration_workflow():
    """
    Show complete integration with CBR cycle
    """
    print("\n\n" + "="*80)
    print("COMPLETE CBR INTEGRATION WORKFLOW")
    print("="*80 + "\n")
    
    print("This demonstrates integrating usefulness calculation into a full CBR cycle:\n")
    
    workflow_steps = [
        "1️⃣  RETRIEVE: Find similar cases from case base",
        "2️⃣  REUSE: Adapt retrieved case to current problem",
        "3️⃣  REVISE: Validate adapted solution (hard constraints)",
        "4️⃣  EVALUATE: Calculate usefulness metrics",
        "5️⃣  RETAIN: Decide whether to save case",
        "6️⃣  UPDATE: Add case to base (if usefulness ≥ threshold)"
    ]
    
    for step in workflow_steps:
        print(f"   {step}")
    
    print("\n" + "─"*80)
    print("Example Code:")
    print("─"*80)
    
    example_code = '''
# Initialize validator with your case base
validator = CBRValidator(
    case_base_path='case_base_menus.json',
    retention_threshold=0.5,
    retention_strategy='threshold'
)

# After retrieval and adaptation...
# (Assuming you have: adapted_menu, adaptation_steps, user_query)

# STEP 3: REVISE - Validate the solution
revision_results = validator.revise_case(
    adapted_menu=adapted_menu,
    user_query=user_query,
    adaptation_steps=adaptation_steps,
    user_feedback=user_rating  # Optional: from user
)

# Check if solution is valid
if not revision_results['is_valid']:
    print("❌ Solution violates constraints, not saving")
else:
    # STEP 4-6: EVALUATE & RETAIN
    retention_results = validator.retain_case(
        adapted_menu=adapted_menu,
        user_query=user_query,
        adaptation_steps=adaptation_steps,
        revision_results=revision_results,
        user_feedback=user_rating
    )
    
    # Check decision
    if retention_results['case_saved']:
        print(f"✅ Case retained: {retention_results['new_case_id']}")
        print(f"   Usefulness: {retention_results['usefulness']:.3f}")
    else:
        print(f"❌ Case discarded")
        print(f"   Reason: {retention_results['rationale']}")
'''
    print(example_code)


def main():
    """Run all demonstrations"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "CASE USEFULNESS DEMONSTRATION" + " "*28 + "║")
    print("║" + " "*15 + "CBR Menu Recommendation System" + " "*32 + "║")
    print("╚" + "═"*78 + "╝")
    
    try:
        demo_scenario_analysis()
        demo_weight_comparison()
        demo_integration_workflow()
        
        print("\n\n" + "="*80)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*80)
        print("\nNext Steps:")
        print("   1. Run 'python case_usefulness.py' for detailed examples")
        print("   2. Run 'python validacion_module.py' for validation workflow")
        print("   3. Read 'USEFULNESS_DOCUMENTATION.md' for full documentation")
        print("   4. Integrate into your CBR main.py workflow")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
