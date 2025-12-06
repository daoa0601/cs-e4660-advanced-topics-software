# Optimization Recommendations

## Model Selection

| Scenario | Recommendation | Reason |
|----------|----------------|--------|
| Standard tasks | **Flash** | 7.5x cheaper, comparable quality |
| Complex reasoning | **Pro** | 33% accuracy boost on hard problems |
| Hybrid | Flash + Pro final stage | 60% savings, 96% quality |

---

## Cost Reduction Strategies

| Strategy | Savings | Effort |
|----------|---------|--------|
| Switch Flash → Pro only for finals | 45% | Low |
| Use concise prompts | 25x | Low |
| Limit agent iterations (max=3-5) | Variable | Low |
| Context summarization | 50-70% | Medium |

---

## Production Guidelines

1. **Default to Flash** — upgrade to Pro only for quality-critical stages
2. **Set iteration limits** — max=3 for self-correcting, max=5 for ReAct
3. **Use concise prompts** — detailed only when explicitly required
4. **Monitor termination reasons** — identify pipelines hitting limits
5. **Implement context truncation** — for conversations >3 turns

---

## When to Use Pro

Pro justifies its 8x cost premium when:

- **Complex reasoning tasks** (math proofs, algorithm design)
- **Hard difficulty problems** (Pro: 80% vs Flash: 60%)
- **Quality-critical final stages** in hybrid pipelines
- **Long-context analysis** requiring deep understanding

---

## Cost Formulas

```python
# Per-stage cost
stage_cost = (input_tokens / 1M * input_rate) + (output_tokens / 1M * output_rate)

# Multi-turn context growth
turn_n_cost ≈ turn_1_cost * (1 + 0.4 * (n - 1))

# Agent cost variance
agent_cost = base_cost * iterations  # iterations: 1-5
```
