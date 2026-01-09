"""
INTEGRATION TEMPLATE: Add Case Usefulness to Your CBR System
==============================================================

This is a template showing exactly where to add the usefulness evaluation
into your existing CBR pipeline. Copy and adapt this code to your main.py
or wherever your CBR cycle is implemented.
"""

# ============================================================================
# STEP 1: IMPORTS (Add these to your imports section)
# ============================================================================

from case_usefulness import (
    calculate_case_usefulness,
    evaluate_case_usefulness
)
from validacion_module import CBRValidator


# ============================================================================
# STEP 2: INITIALIZATION (Add this at the start of your CBR system)
# ============================================================================

def initialize_cbr_system():
    """Initialize your CBR system with validator"""
    
    # Your existing initialization code...
    # retriever = ...
    # adapter = ...
    
    # ADD THIS: Initialize the validator
    validator = CBRValidator(
        case_base_path='../Base_Casos/case_base_menus.json',  # Adjust path
        retention_threshold=0.5,      # Adjust as needed
        retention_strategy='threshold',  # Or 'conservative' or 'liberal'
        max_case_base_size=100        # Optional: limit case base size
    )
    
    return validator  # Return along with other components


# ============================================================================
# STEP 3: CBR CYCLE WITH USEFULNESS (Your main CBR workflow)
# ============================================================================

def cbr_cycle_with_usefulness(user_query, validator):
    """
    Complete CBR cycle including usefulness evaluation
    
    Parameters:
        user_query: The user's problem/query
        validator: CBRValidator instance
    """
    
    # -------------------------------------------------------------------------
    # RETRIEVE: Find similar cases (YOUR EXISTING CODE)
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("PHASE 1: RETRIEVE")
    print("="*70)
    
    # Your retrieval code here...
    # retrieved_case = retriever.retrieve(user_query)
    # similar_cases = retriever.get_k_most_similar(user_query, k=5)
    
    # Example placeholder:
    retrieved_case = {
        'case_id': 'example_case_1',
        'menu': {
            'starter': {'name': 'Salad', 'ingredients': ['lettuce', 'tomato']},
            'main': {'name': 'Chicken', 'ingredients': ['chicken', 'rice']},
            'dessert': {'name': 'Cake', 'ingredients': ['flour', 'sugar']}
        }
    }
    
    print(f"✅ Retrieved case: {retrieved_case['case_id']}")
    
    # -------------------------------------------------------------------------
    # REUSE: Adapt the retrieved case (YOUR EXISTING CODE)
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("PHASE 2: REUSE (ADAPT)")
    print("="*70)
    
    # IMPORTANT: Track adaptation steps for trace calculation!
    adaptation_steps = []
    
    # Your adaptation code here...
    # adapted_menu = adapter.adapt(retrieved_case, user_query)
    # adaptation_steps = adapter.get_adaptation_trace()
    
    # Example placeholder:
    adapted_menu = {
        'starter': {
            'name': 'Vegan Salad',
            'ingredients': ['lettuce', 'tomato', 'avocado', 'olive oil'],
            'cuisine': 'mediterranean',
            'cooking_style': 'healthy'
        },
        'main': {
            'name': 'Tofu Stir-Fry',
            'ingredients': ['tofu', 'vegetables', 'soy sauce', 'ginger'],
            'cuisine': 'asian',
            'cooking_style': 'healthy'
        },
        'dessert': {
            'name': 'Fruit Salad',
            'ingredients': ['mixed fruits', 'lemon juice', 'mint'],
            'cuisine': 'international',
            'cooking_style': 'healthy'
        }
    }
    
    # Example adaptation tracking
    adaptation_steps = [
        {
            'operator': 'substitute_ingredient',
            'course': 'main',
            'params': {'from': 'chicken', 'to': 'tofu'},
            'rationale': 'vegan diet requirement'
        },
        {
            'operator': 'add_ingredient',
            'course': 'starter',
            'params': {'ingredient': 'avocado'},
            'rationale': 'enhance nutrition'
        },
        {
            'operator': 'swap_recipe',
            'course': 'dessert',
            'params': {'from': 'Cake', 'to': 'Fruit Salad'},
            'rationale': 'healthier option'
        }
    ]
    
    print(f"✅ Adapted menu with {len(adaptation_steps)} modifications")
    
    # -------------------------------------------------------------------------
    # REVISE: Validate the solution (NEW - USEFULNESS INTEGRATION)
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("PHASE 3: REVISE (VALIDATE)")
    print("="*70)
    
    # ADD THIS: Get user feedback (optional but improves accuracy)
    # In a real system, this might come from user interface
    user_feedback = None  # Will be calculated from constraints if None
    
    # Optionally, get feedback from user:
    # user_feedback = get_user_satisfaction_rating()  # Implement this
    
    # Validate the adapted solution
    revision_results = validator.revise_case(
        adapted_menu=adapted_menu,
        user_query=user_query,
        adaptation_steps=adaptation_steps,
        user_feedback=user_feedback
    )
    
    # Check if solution is valid
    if not revision_results['is_valid']:
        print("\n⚠️ WARNING: Solution violates constraints!")
        for violation in revision_results['violations']:
            print(f"   - {violation}")
        
        # Decide what to do with invalid solutions
        # Option 1: Return error and ask for re-adaptation
        # Option 2: Still evaluate but mark as low performance
        # Option 3: Skip retention entirely
        
        # For this example, we'll continue but with low performance
        print("\n   → Continuing with low performance score...")
    
    # -------------------------------------------------------------------------
    # RETAIN: Decide whether to save (NEW - USEFULNESS INTEGRATION)
    # -------------------------------------------------------------------------
    print("\n" + "="*70)
    print("PHASE 4: RETAIN (SAVE DECISION)")
    print("="*70)
    
    # Evaluate usefulness and make retention decision
    retention_results = validator.retain_case(
        adapted_menu=adapted_menu,
        user_query=user_query,
        adaptation_steps=adaptation_steps,
        revision_results=revision_results,
        user_feedback=user_feedback
    )
    
    # Display results
    print("\n" + "─"*70)
    print("RETENTION DECISION:")
    print("─"*70)
    print(f"Usefulness:     {retention_results['usefulness']:.3f}")
    print(f"Performance:    {retention_results['performance']:.3f}")
    print(f"Similarity:     {retention_results['similarity']:.3f}")
    print(f"Novelty:        {retention_results['novelty']:.3f}")
    print(f"Trace:          {retention_results['trace']:.3f}")
    print()
    
    if retention_results['case_saved']:
        print(f"✅ CASE RETAINED")
        print(f"   Case ID: {retention_results['new_case_id']}")
        print(f"   {retention_results['rationale']}")
    else:
        print(f"❌ CASE DISCARDED")
        print(f"   {retention_results['rationale']}")
    
    # -------------------------------------------------------------------------
    # Return the adapted menu to the user
    # -------------------------------------------------------------------------
    return {
        'adapted_menu': adapted_menu,
        'revision_results': revision_results,
        'retention_results': retention_results,
        'case_saved': retention_results['case_saved']
    }


# ============================================================================
# STEP 4: EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Example of how to use the integrated system"""
    
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*15 + "CBR SYSTEM WITH USEFULNESS EVALUATION" + " "*16 + "║")
    print("╚" + "═"*68 + "╝")
    
    # Example user query
    user_query = {
        'hard': {
            'required_diets': ['vegan'],
            'forbidden_ingredients': ['meat', 'dairy', 'eggs'],
            'allergens': ['nuts', 'shellfish']
        },
        'soft': {
            'cultura': ['mediterranean', 'asian'],
            'estilo': ['healthy', 'modern'],
            'season': 'summer',
            'preferred_ingredients': ['vegetables', 'tofu', 'fruits']
        }
    }
    
    print("\nUser Query:")
    print(f"  Dietary requirements: {user_query['hard']['required_diets']}")
    print(f"  Forbidden: {user_query['hard']['forbidden_ingredients']}")
    print(f"  Preferred styles: {user_query['soft']['estilo']}")
    
    # Initialize system
    validator = initialize_cbr_system()
    
    # Run CBR cycle
    result = cbr_cycle_with_usefulness(user_query, validator)
    
    # Display final result
    print("\n" + "╔" + "═"*68 + "╗")
    print("║" + " "*25 + "FINAL RESULT" + " "*32 + "║")
    print("╚" + "═"*68 + "╝")
    print(f"\n✅ Menu successfully adapted!")
    print(f"   Performance: {result['retention_results']['performance']:.3f}")
    print(f"   Case saved: {result['case_saved']}")
    print(f"\nAdapted Menu:")
    for course, details in result['adapted_menu'].items():
        print(f"   {course.title()}: {details['name']}")


# ============================================================================
# STEP 5: INTEGRATION INTO YOUR EXISTING main.py
# ============================================================================

"""
HOW TO INTEGRATE INTO YOUR EXISTING CODE:

1. Import the modules (see STEP 1)

2. In your main() function, add:
   
   validator = CBRValidator(
       case_base_path='path/to/your/case_base.json',
       retention_threshold=0.5
   )

3. After your adaptation phase, add:
   
   # Validate
   revision_results = validator.revise_case(
       adapted_menu=adapted_menu,
       user_query=user_query,
       adaptation_steps=adaptation_steps,
       user_feedback=user_rating  # Optional
   )
   
   # Retain
   retention_results = validator.retain_case(
       adapted_menu=adapted_menu,
       user_query=user_query,
       adaptation_steps=adaptation_steps,
       revision_results=revision_results,
       user_feedback=user_rating
   )

4. Check the retention decision:
   
   if retention_results['case_saved']:
       print(f"Case saved: {retention_results['new_case_id']}")
   else:
       print("Case discarded")

5. That's it! The case base will be automatically updated.
"""


# ============================================================================
# STEP 6: OPTIONAL - CUSTOM CONFIGURATION
# ============================================================================

def custom_configuration_example():
    """
    Example of custom configuration for specific use cases
    """
    
    # Configuration 1: Quality-focused (restaurants, professional use)
    validator_quality = CBRValidator(
        case_base_path='case_base_quality.json',
        retention_threshold=0.6,  # Higher threshold
        retention_strategy='conservative',
        max_case_base_size=50  # Keep only best cases
    )
    
    # Configuration 2: Innovation-focused (experimental, creative)
    validator_innovation = CBRValidator(
        case_base_path='case_base_innovation.json',
        retention_threshold=0.4,  # Lower threshold
        retention_strategy='liberal',
        max_case_base_size=200  # Allow more cases
    )
    
    # Configuration 3: Learning-focused (training, education)
    validator_learning = CBRValidator(
        case_base_path='case_base_learning.json',
        retention_threshold=0.5,
        max_case_base_size=100
    )
    
    # Use custom weights when evaluating
    custom_weights = {
        'performance': 0.3,
        'dissimilarity': 0.1,
        'novelty': 0.2,
        'trace': 0.4  # Emphasize learning
    }
    
    # Then when calling calculate_case_usefulness, pass weights:
    # usefulness = calculate_case_usefulness(..., weights=custom_weights)


# ============================================================================
# STEP 7: MONITORING AND MAINTENANCE
# ============================================================================

def monitor_case_base(validator):
    """Monitor case base quality and health"""
    
    print("\n" + "="*70)
    print("CASE BASE STATISTICS")
    print("="*70)
    
    stats = validator.get_case_base_statistics()
    
    print(f"\nSize: {stats['size']} cases")
    print(f"Average usefulness: {stats.get('avg_usefulness', 0):.3f}")
    print(f"Min usefulness: {stats.get('min_usefulness', 0):.3f}")
    print(f"Max usefulness: {stats.get('max_usefulness', 0):.3f}")
    print(f"Cases with adaptations: {stats.get('cases_with_adaptations', 0)}")
    
    # Health check
    avg_usefulness = stats.get('avg_usefulness', 0)
    if avg_usefulness >= 0.7:
        print("\n✅ Case base health: EXCELLENT")
    elif avg_usefulness >= 0.6:
        print("\n✅ Case base health: GOOD")
    elif avg_usefulness >= 0.5:
        print("\n⚠️ Case base health: FAIR - Consider reviewing retention strategy")
    else:
        print("\n❌ Case base health: POOR - Needs attention!")
        print("   Suggestions:")
        print("   - Increase retention threshold")
        print("   - Review case quality")
        print("   - Check adaptation tracking")


# ============================================================================
# RUN EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Run the example
    example_usage()
    
    print("\n\n" + "="*70)
    print("INTEGRATION TEMPLATE COMPLETE")
    print("="*70)
    print("\nTo integrate into your system:")
    print("1. Copy relevant sections to your main.py")
    print("2. Adjust paths and parameters")
    print("3. Ensure adaptation_steps are tracked")
    print("4. Test with your existing cases")
    print("\nFor more help, see:")
    print("- SUMMARY.md for overview")
    print("- QUICK_REFERENCE.md for quick lookup")
    print("- USEFULNESS_DOCUMENTATION.md for details")
