# Demo Phase Enhancements

Improvements added in `project-demo/` over the MVP.

---

## New Features

| Feature | Description | Location |
|---------|-------------|----------|
| **SDK Migration** | `vertexai` → `google-genai` with ADC | `src/clients/genai_client.py` |
| **Tiered Pricing** | Long-context rates (>200K = 2x) | `src/pricing/tiered_pricing.py` |
| **Domain Prompts** | 8 domains (coding, legal, medical...) | `src/config/prompt_templates.py` |
| **Complex Reasoning** | Pro-advantage tasks | `complex_reasoning` domain |
| **Ground Truth** | 30 verifiable problems | `src/config/verifiable_problems.py` |
| **Verified Experiments** | Objective accuracy metrics | `src/experiments/verified_experiment.py` |

---

## Verified Experiment Results

| Difficulty | Flash | Pro | Pro Advantage |
|------------|-------|-----|---------------|
| All | 70% | 90% | +28.6% |
| Hard Only | 60% | 80% | +33.3% |

---

## Domain Templates

| Domain | Templates | Difficulty |
|--------|-----------|------------|
| coding | 5 | easy-hard |
| biology | 5 | medium-hard |
| legal | 5 | medium-hard |
| creative | 5 | medium-hard |
| finance | 5 | medium-hard |
| medical | 5 | hard |
| general | 5 | easy-medium |
| **complex_reasoning** | 10 | **all hard** |

---

## CLI Commands

```bash
# Domain experiments
python -m src.experiments.domain_experiment --domain complex_reasoning --compare-models

# Verified experiments (ground truth)
python -m src.experiments.verified_experiment --compare-models -n 20
python -m src.experiments.verified_experiment --compare-models -d hard

# Pro-advantage analysis
python -m src.experiments.domain_experiment --pro-advantage
```

---

## Future Work

1. Live API integration for verified experiments
2. RAG cost tracking (embeddings + retrieval)
3. Multi-provider support (OpenAI, Anthropic)
4. Real-time cost monitoring dashboard
5. Benchmark integration (GSM8K, MATH, HumanEval)
