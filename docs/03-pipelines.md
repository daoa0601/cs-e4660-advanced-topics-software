# Pipeline Implementations

**Version:** 3.0  
**Last Updated:** December 2025

## Pipeline Types

| Type | Structure | Use Case |
|------|-----------|----------|
| **Linear** | S1 → S2 → S3 | Standard generation with refinement |
| **ReAct** | Think ↔ Act (loop) | Agentic reasoning |
| **Multi-Turn** | T1 → T2 → ... → Tn | Conversations |
| **Self-Correcting** | Gen ↔ Validate (loop) | Quality assurance |
| **Document** | Extract → Analyze → Classify | Document processing |
| **RAG** | Query → Retrieve → Assemble → Generate → Verify | Retrieval-augmented generation |

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

### RAG (Retrieval-Augmented Generation)

```
[Query Understanding] → [Retrieval] → [Context Assembly] → [Generation] → [Verification]
```

5-stage pipeline with retrieval-augmented generation. Three variants available:

| Variant | Retrieval K | Verification | Model Strategy |
|---------|-------------|--------------|----------------|
| `rag_basic` | 5 | No | Flash/Flash |
| `rag_verified` | 10 | Yes | Flash/Flash |
| `rag_hybrid` | 10 | Yes | Flash/Pro |

> **Usage details**: See [06-new-workflows.md](06-new-workflows.md) for RAG workflow commands and cost analysis.

---

## Hybrid Model Strategy

Use Flash for early stages, Pro for critical stages:

```
[Flash: Generation] → [Flash: Critique] → [Pro: Refinement]
```

**Result**: 60% cost reduction, 96% quality retention

### RAG Hybrid Example

```
[Flash: Query Understanding] → [Flash: Retrieval] → [Flash: Context Assembly]
    → [Pro: Generation] → [Pro: Verification]
```

**Result**: Pro quality for generation/verification with Flash efficiency for retrieval stages

> See [06-new-workflows.md](06-new-workflows.md) for detailed RAG cost analysis.

---

## Domain Templates

The platform includes 8 domain-specific prompt templates for testing across different use cases:

| Domain | Templates | Difficulty | Description |
|--------|-----------|------------|-------------|
| `coding` | 5 | easy-hard | Programming tasks and code analysis |
| `biology` | 5 | medium-hard | Scientific reasoning and biology problems |
| `legal` | 5 | medium-hard | Legal document analysis and reasoning |
| `creative` | 5 | medium-hard | Creative writing and ideation |
| `finance` | 5 | medium-hard | Financial analysis and calculations |
| `medical` | 5 | hard | Medical diagnosis and clinical reasoning |
| `general` | 5 | easy-medium | General knowledge and reasoning |
| `complex_reasoning` | 10 | **all hard** | Pro-advantage tasks requiring deep reasoning |

### Using Domain Templates

```bash
# Run domain-specific experiments
python3 -m src.experiments.domain_experiment --domain complex_reasoning --compare-models

# Compare all domains
python3 -m src.experiments.domain_experiment --compare-domains

# Identify Pro-advantage scenarios
python3 -m src.experiments.domain_experiment --pro-advantage
```

---

## All Pipeline Instances

The platform provides 18 pre-configured pipeline instances:

| Pipeline | Type | Stages | Model Strategy |
|----------|------|--------|----------------|
| `verbosity_concise` | Linear | 3 | Flash/Pro |
| `verbosity_cot` | Linear | 3 | Flash/Pro |
| `context_short` | Linear | 3 | Flash/Pro |
| `context_long` | Linear | 3 | Flash/Pro |
| `react_basic` | Agentic | Loop (max 5) | Flash/Pro |
| `react_complex` | Agentic | Loop (max 5) | Flash/Pro |
| `multiturn_3` | Conversational | 3 turns | Flash/Pro |
| `multiturn_5` | Conversational | 5 turns | Flash/Pro |
| `self_correct_basic` | Agentic | Loop (max 3) | Flash/Pro |
| `self_correct_strict` | Agentic | Loop (max 3) | Flash/Pro |
| `document_basic` | Document | 4 | Flash/Pro |
| `document_advanced` | Document | 4 | Flash/Pro |
| `rag_basic` | RAG | 5 (no verify) | Flash/Flash |
| `rag_verified` | RAG | 5 | Flash/Flash |
| `rag_hybrid` | RAG | 5 | Flash/Pro |
| `hybrid_flash_pro` | Hybrid | 3 | Flash→Pro |
| `ab_control` | A/B Test | 3 | Flash/Pro |
| `ab_treatment` | A/B Test | 3 | Flash/Pro |

### Listing Pipelines

```bash
python3 -m src.experiment --list-pipelines
```

---

## Related Documentation

- [02-experiments.md](02-experiments.md) - Experiment results
- [04-recommendations.md](04-recommendations.md) - Cost optimization strategies
- [06-new-workflows.md](06-new-workflows.md) - RAG and analysis workflow details
- [01-architecture.md](01-architecture.md) - System architecture

