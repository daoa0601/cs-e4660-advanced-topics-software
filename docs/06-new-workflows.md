# Analysis & RAG Workflows

**Version:** 3.0  
**Last Updated:** December 2025

This document covers the three workflow types added in v3.0:
- RAG (Retrieval-Augmented Generation)
- Token Profiler
- Cost-Quality Analysis

---

## RAG Workflow (`--workflow rag`)

### Overview

The RAG (Retrieval-Augmented Generation) workflow simulates a full retrieval-augmented generation pipeline with 5 stages. It demonstrates the cost implications of document retrieval, context assembly, and optional verification steps.

### Pipeline Variants

| Variant | Description | Verification | Retrieval K | Multi-Model |
|---------|-------------|--------------|-------------|-------------|
| `rag_basic` | Basic RAG: 5 docs, no verification | No | 5 | No |
| `rag_verified` | Verified RAG: 10 docs with citation verification | Yes | 10 | No |
| `rag_hybrid` | Hybrid RAG: Flash retrieval, Pro generation | Yes | 10 | Yes |

### Pipeline Stages

1. **Query Understanding** - Analyzes the user query to extract key concepts and search terms
2. **Retrieval** - Simulates document retrieval (returns k mock documents with relevance scores)
3. **Context Assembly** - Assembles retrieved documents into a coherent context
4. **Generation** - Generates the final response using the assembled context
5. **Verification** (optional) - Verifies citations and fact-checks the response

### Usage

```bash
# Run RAG experiment with Flash model
python3 -m src.experiment --workflow rag --model flash --iterations 5

# Run with parallel execution
python3 -m src.experiment --workflow rag --model flash --iterations 20 --parallel --workers 8

# Run with Pro model and LLM evaluation
python3 -m src.experiment --workflow rag --model pro --iterations 5 --llm-eval
```

### Cost Implications

- **Basic RAG**: Lower cost, no verification overhead
- **Verified RAG**: ~30% more expensive due to verification stage
- **Hybrid RAG**: Higher quality at moderate cost (Flash for retrieval, Pro for generation)

---

## Token Profiler (`--workflow token_profile`)

### Overview

The Token Profiler is an **analysis-only** workflow that examines existing experiment data to understand token distribution patterns. It does not make API calls.

### Features

- **Token Distribution Histograms**: Visualizes input/output token distributions per workflow
- **Input vs Output Ratio Analysis**: Identifies workflows with high output amplification
- **Context Growth Patterns**: Tracks how context grows in multi-turn conversations
- **Per-Stage Analysis**: Breaks down token usage by pipeline stage

### Usage

```bash
# Analyze all workflows
python3 -m src.experiment --workflow token_profile

# Filter by model
python3 -m src.experiment --workflow token_profile --model flash
python3 -m src.experiment --workflow token_profile --model pro
```

### Output

The profiler generates:
1. Summary statistics table (mean, median, std for input/output tokens)
2. Token ratio analysis (output/input ratio per workflow)
3. Distribution histograms (if matplotlib available)
4. Context growth charts for multi-turn workflows

### Key Metrics

| Metric | Description |
|--------|-------------|
| `input_tokens` | Average input tokens per stage |
| `output_tokens` | Average output tokens per stage |
| `output_ratio` | output_tokens / input_tokens |
| `context_growth` | Token increase per conversation turn |

---

## Cost-Quality Analysis (`--workflow cost_quality`)

### Overview

The Cost-Quality Analysis is an **analysis-only** workflow that computes the Pareto frontier of cost vs quality trade-offs across all pipeline/model combinations. It helps identify the most cost-effective configurations.

### Features

- **Pareto Frontier Visualization**: Identifies pipeline configurations that offer the best trade-offs
- **Quality Efficiency Scoring**: Calculates "quality per dollar" for each configuration
- **Pipeline Ranking**: Ranks all configurations by cost-effectiveness
- **Actionable Recommendations**: Provides specific guidance based on analysis

### Usage

```bash
# Run cost-quality analysis
python3 -m src.experiment --workflow cost_quality

# Filter by model
python3 -m src.experiment --workflow cost_quality --model flash

# With parallel processing (for large datasets)
python3 -m src.experiment --workflow cost_quality --parallel --workers 4
```

### Understanding Results

#### Pareto-Optimal Pipelines

A configuration is **Pareto-optimal** if no other configuration has both:
- Lower cost AND
- Higher quality

Pareto-optimal configurations are marked with a star (★) in the output.

#### Quality Per Dollar

The key efficiency metric is calculated as:
```
quality_per_dollar = (avg_quality / avg_cost) * 1000
```

Higher values indicate better cost-effectiveness.

#### Recommendations

The analysis provides recommendations:
- **Best Value**: Highest quality per dollar
- **Highest Quality**: Best quality regardless of cost
- **Lowest Cost**: Cheapest option regardless of quality
- **Flash vs Pro comparison**: Which model is more cost-efficient

### Example Output

```
PARETO-OPTIMAL PIPELINES
----------------------------------------------------------------------
  ★ verbosity_concise (flash)
    Cost: $0.00012  Quality: 72.5  Efficiency Rank: #1
  ★ rag_hybrid (pro)
    Cost: $0.00089  Quality: 91.2  Efficiency Rank: #3

EFFICIENCY RANKINGS (Top 10)
----------------------------------------------------------------------
  ★ #1: verbosity_concise (flash)
      Quality/$ : 6042  |  Quality: 72.5  |  Cost: $0.00012

RECOMMENDATIONS
----------------------------------------------------------------------
  • Best Value: verbosity_concise (flash) - 6042 quality points per $0.001
  • Flash is 2.3x more cost-efficient than Pro on average
  • Highest Quality: rag_hybrid (pro) - Score: 91.2
  • Lowest Cost: verbosity_concise (flash) - $0.00012/run
```

---

## Comparison Table

| Workflow | Type | Makes API Calls | Parallel Support | Primary Use Case |
|----------|------|-----------------|------------------|------------------|
| `rag` | Experiment | Yes | Yes | Test RAG pipeline costs |
| `token_profile` | Analysis | No | No | Understand token patterns |
| `cost_quality` | Analysis | No | Yes | Find cost-effective configs |

---

## Related Commands

```bash
# List all available pipelines including RAG
python3 -m src.experiment --list-pipelines

# Estimate cost before running RAG experiment
python3 -m src.experiment --workflow rag --model flash --iterations 10 --estimate-cost

# Health check before running experiments
python3 -m src.experiment --health-check
```

---

## Related Documentation

- [03-pipelines.md](03-pipelines.md) - All pipeline implementations
- [04-recommendations.md](04-recommendations.md) - Cost optimization strategies
- [02-experiments.md](02-experiments.md) - Experiment results

