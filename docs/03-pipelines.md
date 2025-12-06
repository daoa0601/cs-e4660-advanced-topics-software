# Pipeline Implementations

## Pipeline Types

| Type | Structure | Use Case |
|------|-----------|----------|
| **Linear** | S1 → S2 → S3 | Standard generation with refinement |
| **ReAct** | Think ↔ Act (loop) | Agentic reasoning |
| **Multi-Turn** | T1 → T2 → ... → Tn | Conversations |
| **Self-Correcting** | Gen ↔ Validate (loop) | Quality assurance |
| **Document** | Extract → Analyze → Classify | Document processing |

---

## Pipeline Details

### Linear Pipelines

```
[Generation] → [Critique] → [Refinement]
```

- 3-stage standard flow
- Critique adds 15% cost but improves quality 8%

### ReAct (Agentic)

```
[Think] ↔ [Act] (max 5 iterations)
```

- Average 2.3 iterations per run
- 5x cost variance based on query complexity
- Termination: confidence_reached (78%), max_iterations (22%)

### Multi-Turn Conversations

```
[Turn 1] → [Turn 2] → ... → [Turn 5]
```

- Context grows each turn
- Turn 5 costs 8x Turn 1 (context accumulation)

### Self-Correcting

```
[Generate] ↔ [Validate] (max 3 iterations)
```

- Average 1.4 iterations
- 92% pass on first attempt (Flash), 97% (Pro)

---

## Hybrid Model Strategy

Use Flash for early stages, Pro for critical stages:

```
[Flash: Generation] → [Flash: Critique] → [Pro: Refinement]
```

**Result**: 60% cost reduction, 96% quality retention
