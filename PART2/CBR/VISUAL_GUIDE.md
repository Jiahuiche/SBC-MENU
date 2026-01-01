# Visual Guide: Case Usefulness System

## 📊 Decision Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    ADAPTED MENU CASE                        │
│  (After RETRIEVE, REUSE, and REVISE phases)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Calculate 4 Metrics  │
         └───────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │Perform- │  │Dissimi- │  │Novelty  │  │Trace    │
   │ance     │  │larity   │  │         │  │         │
   │0.0-1.0  │  │0.0-1.0  │  │0.0-1.0  │  │0.0-1.0  │
   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
        │            │            │            │
        │  × 0.4     │  × 0.15    │  × 0.25    │  × 0.2
        │            │            │            │
        └────────────┴────────────┴────────────┘
                     │
                     ▼
              ┌─────────────┐
              │ USEFULNESS  │
              │   SCORE     │
              │  0.0-1.0    │
              └──────┬──────┘
                     │
                     ▼
              ┌─────────────┐
              │  Compare    │
              │  Threshold  │
              │   (0.5)     │
              └──────┬──────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │ ≥ 0.5    │          │ < 0.5    │
    │ RETAIN   │          │ DISCARD  │
    └────┬─────┘          └────┬─────┘
         │                     │
         ▼                     ▼
   ┌──────────┐          ┌──────────┐
   │ Add to   │          │ Don't    │
   │ Case Base│          │ Save     │
   └──────────┘          └──────────┘
```

---

## 🎯 The Four Metrics - Visual Representation

### Performance (Weight: 40%)
```
┌────────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░  0.4               │
│                                            │
│ Did the solution work well?                │
│ • All constraints met?                     │
│ • User satisfied?                          │
│ • Dietary rules followed?                  │
└────────────────────────────────────────────┘
```

### Dissimilarity (Weight: 15%)
```
┌────────────────────────────────────────────┐
│ ▓▓▓▓▓▓░░░░░░░░░░░░░░  0.15              │
│                                            │
│ Is it unique? (1 - Similarity)             │
│ • Different from existing cases?           │
│ • Adds diversity to case base?             │
│ • Not a duplicate?                         │
└────────────────────────────────────────────┘
```

### Novelty (Weight: 25%)
```
┌────────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░  0.25              │
│                                            │
│ Is it innovative?                          │
│ • Rare ingredients?                        │
│ • Creative combinations?                   │
│ • Unique flavor profiles?                  │
└────────────────────────────────────────────┘
```

### Trace (Weight: 20%)
```
┌────────────────────────────────────────────┐
│ ▓▓▓▓▓▓▓▓░░░░░░░░░░░░  0.20              │
│                                            │
│ Was adaptation complex?                    │
│ • Many modifications?                      │
│ • Complex operations?                      │
│ • Valuable learning?                       │
└────────────────────────────────────────────┘
```

---

## 📈 Score Interpretation Guide

```
USEFULNESS SCALE
│
1.0 ├─────────────────────────────────────────────
    │ ✨ Exceptional Case
0.9 │    • Perfect performance
    │    • Highly unique
    │    • Very innovative
0.8 ├────────────── [Definitely Retain] ──────────
    │ 🌟 High-Value Case
0.7 │    • Excellent solution
    │    • Good diversity
    │    • Worth keeping
0.6 ├────────────── [Should Retain] ─────────────
    │
0.5 ├═════════════ THRESHOLD ═══════════════════
    │ ⚖️  Borderline Case
0.4 │    • Acceptable but...
    │    • Low uniqueness or
    │    • Moderate performance
0.3 ├────────────── [Should Discard] ────────────
    │ ⚠️  Low-Value Case
0.2 │    • Poor performance or
    │    • Very similar to existing
    │    • Little learning value
0.1 ├────────────── [Definitely Discard] ────────
    │ ❌ Problematic Case
0.0 │    • Failed solution
    └─────────────────────────────────────────────
```

---

## 🔄 CBR Cycle Integration

```
┌──────────────────────────────────────────────────────────┐
│                    CBR CYCLE WITH                        │
│              USEFULNESS EVALUATION                       │
└──────────────────────────────────────────────────────────┘

    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  1. RETRIEVE                        ┃
    ┃  Find similar cases from case base  ┃
    ┗━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┛
                  │
                  ▼
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  2. REUSE                           ┃
    ┃  Adapt retrieved case to problem    ┃
    ┃  Track: adaptation_steps            ┃
    ┗━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┛
                  │
                  ▼
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  3. REVISE                          ┃  ← validator.revise_case()
    ┃  Validate hard constraints          ┃
    ┃  Evaluate soft preferences          ┃
    ┗━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┛
                  │
                  ▼
    ┌─────────────────────────────────────┐
    │  🎯 EVALUATE USEFULNESS             │
    │  • Calculate performance            │  ← NEW!
    │  • Calculate similarity             │  ← NEW!
    │  • Calculate novelty                │  ← NEW!
    │  • Calculate trace                  │  ← NEW!
    └─────────────┬───────────────────────┘
                  │
                  ▼
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃  4. RETAIN                          ┃  ← validator.retain_case()
    ┃  Decide: Save or Discard?           ┃
    ┃  • usefulness >= 0.5 → SAVE         ┃
    ┃  • usefulness < 0.5  → DISCARD      ┃
    ┗━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┛
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
   ┌─────────┐         ┌─────────┐
   │ SAVE    │         │ DISCARD │
   │ to Case │         │ Case    │
   │ Base    │         └─────────┘
   └─────────┘
```

---

## 🎨 Example Cases - Visual Comparison

### Case A: High-Value Wedding Menu ✅
```
┌──────────────────────────────────────────┐
│ Performance:    ████████████████░░ 0.90  │  Excellent
│ Dissimilarity:  ████████████████░░ 0.80  │  Very unique
│ Novelty:        ████████████████░░ 0.80  │  Innovative
│ Trace:          ██████████████░░░░ 0.70  │  Complex
├──────────────────────────────────────────┤
│ USEFULNESS:     ████████████████░░ 0.82  │
│ DECISION:       ✅ RETAIN                │
└──────────────────────────────────────────┘
Rationale: Excellent performance, unique case with 
innovative ingredients and complex adaptation.
```

### Case B: Redundant Birthday Menu ❌
```
┌──────────────────────────────────────────┐
│ Performance:    ████████████████░░ 0.80  │  Good but...
│ Dissimilarity:  ░░░░░░░░░░░░░░░░░░ 0.05  │  Almost duplicate
│ Novelty:        ██████░░░░░░░░░░░░ 0.30  │  Common
│ Trace:          ████░░░░░░░░░░░░░░ 0.20  │  Little effort
├──────────────────────────────────────────┤
│ USEFULNESS:     ████████░░░░░░░░░░ 0.41  │
│ DECISION:       ❌ DISCARD               │
└──────────────────────────────────────────┘
Rationale: Too similar to existing cases, adds 
little value despite good performance.
```

### Case C: Learning-Rich Corporate Menu ✅
```
┌──────────────────────────────────────────┐
│ Performance:    ███████████████░░░ 0.75  │  Good
│ Dissimilarity:  ████████████░░░░░░ 0.60  │  Moderately unique
│ Novelty:        ████████████░░░░░░ 0.60  │  Some innovation
│ Trace:          ██████████████████ 0.90  │  Very complex!
├──────────────────────────────────────────┤
│ USEFULNESS:     ██████████████░░░░ 0.70  │
│ DECISION:       ✅ RETAIN                │
└──────────────────────────────────────────┘
Rationale: Valuable learning case with extensive
adaptations. Represents complex problem-solving.
```

---

## 🎯 When to Use Different Strategies

### Strategy Matrix

```
                    Low Diversity         High Diversity
                    in Case Base         in Case Base
                  ┌──────────────┬──────────────┐
Performance       │              │              │
Focus            │ Performance- │   Quality +   │
(Quality         │   Focused    │   Diversity   │
Important)       │   0.6/0.1/   │   0.5/0.3/    │
                 │   0.2/0.1    │   0.15/0.05   │
                  ├──────────────┼──────────────┤
Learning          │              │              │
Focus            │  Learning-   │  Innovation-  │
(Education       │   Focused    │   Focused     │
Important)       │   0.3/0.1/   │   0.3/0.2/    │
                 │   0.2/0.4    │   0.4/0.1     │
                  └──────────────┴──────────────┘

         Weights format: Performance/Dissimilarity/Novelty/Trace
```

---

## 🔍 Metric Calculation Examples

### Performance Calculation
```
Input:
  user_feedback = 0.85
  constraint_satisfaction = 1.0
  
Calculation:
  performance = (0.6 × 0.85) + (0.4 × 1.0)
              = 0.51 + 0.4
              = 0.91
  
Result: 0.91 (Excellent!) ✅
```

### Novelty Calculation
```
Case ingredients: [yuzu, scallops, microgreens]

Frequency in case base:
  yuzu: appears in 2/100 cases = frequency 0.02
  scallops: appears in 15/100 cases = frequency 0.15
  microgreens: appears in 5/100 cases = frequency 0.05

Rarity scores:
  yuzu: 1 - 0.02 = 0.98
  scallops: 1 - 0.15 = 0.85
  microgreens: 1 - 0.05 = 0.95

Novelty = average(0.98, 0.85, 0.95) = 0.93

Result: 0.93 (Highly innovative!) 🌟
```

### Trace Calculation
```
Adaptation steps:
  1. swap_recipe (weight: 1.0)
  2. substitute_ingredient (weight: 0.8)
  3. add_ingredient (weight: 0.6)
  4. substitute_technique (weight: 0.7)

Total weighted complexity = 1.0 + 0.8 + 0.6 + 0.7 = 3.1

Normalized:
  step_score = 4 / 10 = 0.4
  complexity_score = 3.1 / 7.0 = 0.44
  trace = (0.4 × 0.4) + (0.6 × 0.44) = 0.42

Result: 0.42 (Moderate adaptation) 💡
```

---

## 📊 Case Base Health Indicators

### Healthy Case Base
```
Size: 85 cases
Average usefulness: 0.72 ✅
Min usefulness: 0.51 ✅
Max usefulness: 0.95 ✅
Cases with adaptations: 68 (80%) ✅

Status: Healthy, diverse, high-quality case base
```

### Needs Attention
```
Size: 150 cases
Average usefulness: 0.48 ⚠️
Min usefulness: 0.20 ⚠️
Max usefulness: 0.98 ✅
Cases with adaptations: 30 (20%) ⚠️

Status: Too many low-quality cases, consider:
- Increasing retention threshold
- Pruning low-usefulness cases
- Reviewing adaptation tracking
```

---

## 🚀 Quick Action Guide

```
┌─────────────────────────────────────────────┐
│ I want to...                                │
├─────────────────────────────────────────────┤
│ ☐ Calculate usefulness for one case        │
│   → Use calculate_case_usefulness()        │
│                                             │
│ ☐ Validate and save a case                 │
│   → Use CBRValidator.revise_case() +       │
│     CBRValidator.retain_case()             │
│                                             │
│ ☐ Get only high-quality cases              │
│   → Set retention_threshold=0.6            │
│                                             │
│ ☐ Build diverse case base                  │
│   → Increase novelty weight to 0.4         │
│                                             │
│ ☐ Preserve learning experiences            │
│   → Increase trace weight to 0.4           │
│                                             │
│ ☐ Limit case base size                     │
│   → Set max_case_base_size=100             │
│                                             │
│ ☐ Monitor case base quality                │
│   → Use get_case_base_statistics()         │
│                                             │
│ ☐ Test the system                          │
│   → Run demo_usefulness.py                 │
└─────────────────────────────────────────────┘
```

---

## 📖 Learning Path

```
1. Start Here ━━━━━━━━━━━━━━━━━━━━┓
   Read: SUMMARY.md              │
   Time: 5 minutes               │
                                 │
2. Quick Reference ━━━━━━━━━━━━━━┫
   Read: QUICK_REFERENCE.md      │
   Time: 10 minutes              │
                                 │
3. Try It Out ━━━━━━━━━━━━━━━━━━┫
   Run: demo_usefulness.py       │
   Time: 5 minutes               │
                                 │
4. Deep Dive ━━━━━━━━━━━━━━━━━━━┫
   Read: USEFULNESS_DOCUMENTATION.md
   Time: 20 minutes              │
                                 │
5. Integrate ━━━━━━━━━━━━━━━━━━━┫
   Modify: Your main.py          │
   Time: 30 minutes              │
                                 │
6. Master It ━━━━━━━━━━━━━━━━━━━┛
   Experiment with weights
   Monitor your case base
   Tune parameters
```

---

**Visual Guide Complete!** 🎨

For more details, see:
- SUMMARY.md - Overview
- QUICK_REFERENCE.md - Quick lookup
- USEFULNESS_DOCUMENTATION.md - Detailed docs
