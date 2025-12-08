# v2.1 Experiment Template

This directory serves as a template for the next experiment run.

## New Features in v2.1

- **Cost-Quality Frontier Analysis**: Pareto-optimal pipeline identification
- **RAG Agent Workflow**: Retrieval-augmented generation with citation tracking
- **Token Distribution Profiler**: Token usage analysis across workflows
- **Parallel Execution**: All new experiments support `--parallel` flag

## Quick Start

### 1. Pre-flight Checks

```bash
# Verify setup
python3 -m src.experiment --health-check

# Estimate costs
python3 -m src.experiment --full-experiment --estimate-cost
```

### 2. Run Experiments

```bash
# Full experiment suite (recommended)
python3 -m src.experiment --full-experiment

# Or run individual workflows
python3 -m src.experiment --workflow rag --model flash --iterations 10 --parallel
python3 -m src.experiment --workflow cost_quality
```

### 3. Generate Report

```bash
# Copy this template and generate report
cp -r reports/v2.1-template reports/v2.1-$(date +%Y%m%d)/
python3 notebooks/generate_report.py --output-dir reports/v2.1-$(date +%Y%m%d)/
```

## Experiment Configuration

See `experiment-config.json` for the full configuration template.

Key settings:
- **Iterations**: 20 per variant
- **Workers**: 16 parallel
- **Streaming**: Enabled (TTFT metrics)
- **LLM Eval**: Enabled (quality scoring)

## Expected Output

After running experiments:
- `summary.md` - Key metrics
- `figures/*.png` - Visualizations
- `experiment-config.json` - Actual config used (update after run)

## Workflows Included

| Workflow | Type | Description |
|----------|------|-------------|
| verbosity | Linear | Concise vs CoT comparison |
| context | Linear | Short vs long context |
| react | Agentic | ReAct reasoning loop |
| multiturn | Agentic | Multi-turn conversation |
| self_correcting | Agentic | Self-validation loop |
| document | Linear | Document analysis |
| rag | Agentic | RAG with retrieval (NEW) |
| cost_quality | Analysis | Pareto frontier analysis (NEW) |
