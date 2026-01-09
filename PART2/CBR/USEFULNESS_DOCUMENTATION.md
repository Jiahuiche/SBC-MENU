# Case Usefulness Calculation - CBR System Documentation

## Overview

This module implements the **usefulness calculation** for the CBR (Case-Based Reasoning) menu recommendation system. It helps determine whether an adapted case should be retained in the case base for future use.

## Key Concept: Case Usefulness

The usefulness of a case is calculated based on **four key metrics**:

### 1. **Performance** (Weight: 0.4)
- **What it measures**: How well the case solved the problem
- **Range**: 0.0 (failed) to 1.0 (perfect)
- **Factors**:
  - User satisfaction/feedback
  - Hard constraint compliance (dietary restrictions, allergens)
  - Soft preference matching (cuisine, cooking style)

**Example**:
- Performance = 0.9: All constraints met, user very satisfied
- Performance = 0.5: Constraints met but user moderately satisfied
- Performance = 0.2: Some constraints violated or user unsatisfied

### 2. **Similarity** (Weight: 0.15, used as DISSIMILARITY)
- **What it measures**: How similar the case is to existing cases
- **Range**: 0.0 (completely unique) to 1.0 (identical to existing case)
- **Key insight**: HIGH similarity is BAD (redundant), so we use **(1 - similarity)**

**Why dissimilarity matters**:
- Similarity = 0.95 → Dissimilarity = 0.05 → **Redundant case, don't save**
- Similarity = 0.15 → Dissimilarity = 0.85 → **Unique case, valuable to save**

**Example**:
```
New Case: [salmon, asparagus, lemon, herbs]
Existing Case: [salmon, asparagus, lemon, butter] 
Similarity = 0.75 → Too similar, adds little value
```

### 3. **Novelty** (Weight: 0.25)
- **What it measures**: How innovative/unique the ingredients and combinations are
- **Range**: 0.0 (common ingredients) to 1.0 (highly innovative)
- **Calculation**: Based on ingredient rarity in the case base

**Example**:
- Novelty = 0.9: Uses rare ingredients like "saffron", "truffle", "exotic fruits"
- Novelty = 0.5: Mix of common and uncommon ingredients
- Novelty = 0.1: Only common ingredients like "chicken", "rice", "tomato"

### 4. **Trace** (Weight: 0.2)
- **What it measures**: The adaptation effort required
- **Range**: 0.0 (no adaptation) to 1.0 (extensive adaptation)
- **Key insight**: High trace = valuable learning experience

**Adaptation operations** (weighted by complexity):
- `swap_recipe` (1.0): Most complex - replaced entire recipe
- `substitute_ingredient` (0.8): Significant change
- `substitute_technique` (0.7): Cooking method change
- `add_ingredient` (0.6): Adding new element
- `remove_ingredient` (0.6): Removing element
- `adjust_portions` (0.3): Minor adjustment

**Example**:
```
Trace = 0.9: Case required 5 substitutions + 2 recipe swaps
            → Valuable learning about adaptation strategies
            
Trace = 0.1: Case retrieved and used as-is with no changes
            → Little learning value
```

## Usefulness Formula

```
Usefulness = (Performance × 0.4) + 
             (Dissimilarity × 0.15) + 
             (Novelty × 0.25) + 
             (Trace × 0.2)
```

**Retention threshold**: Usefulness ≥ 0.5 → Save the case

## Usage Examples

### Example 1: High-Value Case (Should RETAIN)
```python
performance = 0.9    # Excellent solution
similarity = 0.2     # Very different from existing cases
novelty = 0.8        # Innovative ingredients
trace = 0.7          # Complex adaptation

usefulness = calculate_case_usefulness(
    performance, similarity, novelty, trace
)
# Result: 0.82 → ✅ RETAIN
```

**Rationale**: Excellent performance, unique case that required significant adaptation. Valuable addition to case base.

### Example 2: Redundant Case (Should DISCARD)
```python
performance = 0.8    # Good solution
similarity = 0.95    # Almost identical to existing case
novelty = 0.3        # Common ingredients
trace = 0.2          # Little adaptation

usefulness = calculate_case_usefulness(
    performance, similarity, novelty, trace
)
# Result: 0.41 → ❌ DISCARD
```

**Rationale**: Good performance but too similar to existing cases. Adds little value to the case base.

### Example 3: Poor Performance (Should DISCARD)
```python
performance = 0.3    # Failed to meet constraints
similarity = 0.1     # Unique case
novelty = 0.9        # Very innovative
trace = 0.8          # High adaptation effort

usefulness = calculate_case_usefulness(
    performance, similarity, novelty, trace
)
# Result: 0.56 → Decision depends on strategy
```

**Rationale**: Despite uniqueness and complexity, poor performance makes it less valuable. Could be retained as a "what not to do" example.

### Example 4: Valuable Learning Case (Should RETAIN)
```python
performance = 0.75   # Good solution
similarity = 0.4     # Moderately unique
novelty = 0.6        # Some innovation
trace = 0.9          # Very complex adaptation

usefulness = calculate_case_usefulness(
    performance, similarity, novelty, trace
)
# Result: 0.70 → ✅ RETAIN
```

**Rationale**: Required extensive adaptation, representing valuable problem-solving experience worth saving.

## Custom Weight Strategies

You can customize weights based on your priorities:

### Strategy 1: Performance-Focused
```python
weights = {
    'performance': 0.6,      # Prioritize successful solutions
    'dissimilarity': 0.1,
    'novelty': 0.2,
    'trace': 0.1
}
```
**Use when**: Quality is more important than diversity

### Strategy 2: Innovation-Focused
```python
weights = {
    'performance': 0.3,
    'dissimilarity': 0.2,
    'novelty': 0.4,          # Prioritize innovative cases
    'trace': 0.1
}
```
**Use when**: Building a diverse case base with novel solutions

### Strategy 3: Learning-Focused
```python
weights = {
    'performance': 0.3,
    'dissimilarity': 0.1,
    'novelty': 0.2,
    'trace': 0.4             # Prioritize complex adaptations
}
```
**Use when**: Learning from adaptation experiences is most important

## Integration with CBR Cycle

### Complete CBR Workflow

```python
from validacion_module import CBRValidator

# 1. Initialize validator
validator = CBRValidator(
    case_base_path='case_base_menus.json',
    retention_threshold=0.5,
    retention_strategy='threshold'
)

# 2. REVISE: Validate the adapted solution
revision_results = validator.revise_case(
    adapted_menu=my_menu,
    user_query=original_query,
    adaptation_steps=adaptation_history,
    user_feedback=0.85
)

# 3. RETAIN: Decide whether to save
retention_results = validator.retain_case(
    adapted_menu=my_menu,
    user_query=original_query,
    adaptation_steps=adaptation_history,
    revision_results=revision_results,
    user_feedback=0.85
)

# Check if case was saved
if retention_results['case_saved']:
    print(f"✅ Case saved: {retention_results['new_case_id']}")
else:
    print(f"❌ Case discarded: {retention_results['rationale']}")
```

## Running the Examples

### Test the usefulness calculation:
```bash
cd PART2/CBR
python case_usefulness.py
```

This will run comprehensive tests showing:
- 6 different scenarios (high-value, redundant, poor performance, etc.)
- Complete case evaluation example
- Custom weight strategies

### Test the validation workflow:
```bash
python validacion_module.py
```

This demonstrates:
- REVISE phase: Constraint validation
- RETAIN phase: Usefulness evaluation and retention decision
- Case base management

## Key Decisions in the Design

### Why Dissimilarity Instead of Similarity?
Traditional CBR values similar cases, but for **retention**, we want to avoid redundancy. A case identical to one already stored adds no value.

### Why High Weight on Performance?
A case must first **work well** before other factors matter. Low-performing cases shouldn't be retained even if they're unique.

### Why Value Trace/Adaptation Effort?
Complex adaptations represent **learning experiences**. They show how to solve difficult problems and are worth preserving.

### Why Consider Novelty?
Novel cases add **diversity** to the case base, improving coverage of the solution space and enabling creativity.

## Case Base Management

### Automatic Pruning
When the case base reaches max size, least useful cases are removed:
```python
validator = CBRValidator(
    case_base_path='case_base.json',
    max_case_base_size=100  # Keep only top 100 cases
)
```

### Statistics
```python
stats = validator.get_case_base_statistics()
print(f"Case base size: {stats['size']}")
print(f"Average usefulness: {stats['avg_usefulness']:.3f}")
print(f"Cases with adaptations: {stats['cases_with_adaptations']}")
```

## Troubleshooting

### Problem: Too many cases being retained
**Solution**: Increase retention threshold or use "conservative" strategy
```python
validator = CBRValidator(
    retention_threshold=0.6,
    retention_strategy='conservative'
)
```

### Problem: No cases being retained
**Solution**: Lower threshold or check if adaptation_steps are being tracked
```python
validator = CBRValidator(
    retention_threshold=0.4,
    retention_strategy='liberal'
)
```

### Problem: All cases look similar
**Solution**: Increase novelty weight to favor diverse cases
```python
weights = {
    'performance': 0.3,
    'dissimilarity': 0.2,
    'novelty': 0.4,  # Higher novelty weight
    'trace': 0.1
}
```

## References

- Smyth, B., & Keane, M. T. (1995). "Remembering to forget: A competence-preserving case deletion policy for case-based reasoning systems"
- Leake, D. B., & Wilson, D. C. (2000). "Remembering why to remember: Performance-guided case-base maintenance"
- Zhu, J., & Yang, Q. (1999). "Remembering to add: Competence-preserving case-addition policies for case base maintenance"

## Author

Created for SBC-MENU CBR System
Date: January 2026
