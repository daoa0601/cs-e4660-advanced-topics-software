# Experiment Results

**Version:** 3.0  
**Last Updated:** December 2025

## Overview

Two phases of experiments were conducted:

| Phase | Runs | Cost | Focus |
|-------|------|------|-------|
| MVP | 591 | $6.40 | Baseline cost metrics |
| Demo | 736 | $8.07 | Streaming, parallel, evaluation |

---

## MVP Phase Results

### Cost by Pipeline Type

| Pipeline Type | Flash Cost | Pro Cost | Cost Ratio |
|---------------|------------|----------|------------|
| Verbosity | $0.0010/run | $0.0075/run | 7.5x |
| Context Growth | $0.0025/run | $0.019/run | 7.6x |
| ReAct | $0.0032/run | $0.024/run | 7.5x |
| Multi-Turn (5) | $0.0045/run | $0.034/run | 7.6x |
| Self-Correcting | $0.0028/run | $0.021/run | 7.5x |

### Stage Cost Distribution

| Stage Type | % of Total Cost |
|------------|-----------------|
| Generation | 45% |
| Conversation | 25% |
| Thinking (ReAct) | 15% |
| Critique/Validation | 10% |
| Refinement | 5% |

---

## Demo Phase Results

### Streaming Metrics (TTFT)

| Model | Avg TTFT | Min | Max |
|-------|----------|-----|-----|
| Flash | 285ms | 180ms | 520ms |
| Pro | 420ms | 280ms | 890ms |

### Parallel Execution

| Workers | Throughput | Speedup |
|---------|------------|---------|
| 1 | 0.8 runs/s | 1x |
| 4 | 2.9 runs/s | 3.6x |
| 16 | 8.2 runs/s | 10.3x |

### Quality Scores

| Model | Avg Quality | Quality/$ |
|-------|-------------|-----------|
| Flash | 72.3 | 72,300 |
| Pro | 78.5 | 10,300 |
| Hybrid | 75.8 | 25,200 |

---

## v2.0 Results

Version 2.0 introduced reasoning-focused experiments and session-based isolation:

### New Features Tested
- **Session Management**: Isolated experiment runs with separate databases
- **Verified Experiments**: Ground truth accuracy testing (math, logic problems)
- **Extended A/B Testing**: Multiple prompt variants comparison

### Verified Experiment Results (Ground Truth)

These experiments use problems with known correct answers for objective accuracy measurement:

| Difficulty | Flash Accuracy | Pro Accuracy | Pro Advantage |
|------------|---------------|--------------|---------------|
| All | 95% | 100% | +5.3% |
| **Hard** | 60% | 80% | **+33.3%** |

> **Key Finding**: Pro's advantage increases dramatically on hard problems, justifying its cost premium for complex reasoning tasks.

```bash
# Run verified experiments
python3 -m src.experiments.verified_experiment --compare-models -n 20

# Hard problems only (where Pro shines)
python3 -m src.experiments.verified_experiment --compare-models -d hard -n 10
```

---

## full_run_v3 Results (Latest)

The most comprehensive experiment run with 2,444 pipeline executions.

### Summary Statistics

| Metric | Value |
|--------|-------|
| Pipeline Runs | **2,444** |
| Stage Executions | **5,947** |
| Total Cost | **$30.70** |

### Cost by Model

| Model | Runs | Total Cost | Avg Cost/Run |
|-------|------|------------|--------------|
| Flash | 1,268 | $7.14 | $0.0056 |
| Pro | 1,176 | $23.57 | $0.0200 |

**Cost Ratio**: Pro costs **3.6x** more than Flash

### Stage Cost Distribution

| Stage Type | Cost | % of Total |
|------------|------|------------|
| Conversation | $8.30 | 27% |
| Generation | $8.02 | 26% |
| Refinement | $4.36 | 14% |
| Critique | $3.52 | 12% |
| Extraction | $2.01 | 7% |
| Evaluation | $1.81 | 6% |

### Quality Comparison

| Model | Avg Quality |
|-------|-------------|
| Flash | 83.26 |
| Pro | 84.48 |

**Quality Difference**: Pro scores **+1.22** points higher

### Cost-Quality Analysis Highlights

| Configuration | Quality/$ | Notes |
|---------------|-----------|-------|
| verbosity_concise (Flash) | 2.47B | Best value |
| context_short (Flash) | 601M | Efficient |
| react_research (Flash) | 185M | Highest quality (92.2) |

### Reports and Figures

See [`project-demo/reports/full_run_v3/`](../project-demo/reports/full_run_v3/) for:
- 6 PNG visualizations
- `summary.md` with detailed metrics
- Analysis charts (HTML)

---

## v3.0 Architecture

Version 3.0 completed all 6 phases of development improvements.

### Development Phases Overview

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| 1 | Critical Fixes | Retry logic, 26 unit tests, exception handling |
| 2 | Code Quality | Consolidated runners (~200 lines saved), structured logging |
| 3 | UX Improvements | CLI validation, cost estimation, progress tracking, health checks |
| 4 | Performance | Database indexes, environment configuration |
| 5 | New Features | Token Profiler, Cost-Quality Analysis, RAG pipeline, visualization module |
| 6 | Refactoring | Modular package architecture (5,824 lines refactored) |

### Phase Details

<details>
<summary><b>Phase 1-2: Foundation</b></summary>

**Phase 1 - Critical Fixes:**
- Added retry decorator with exponential backoff in `genai_client.py`
- Fixed bare `except:` exceptions
- Added 26 unit tests for core functionality

**Phase 2 - Code Quality:**
- Consolidated 6 duplicated `_run_single_*_iteration()` into generic `_run_single_iteration()`
- Created generic `run_workflow_experiment()` runner
- Removed unused legacy files
- Added structured logging with `--log-level` CLI flag

</details>

<details>
<summary><b>Phase 3-4: UX & Performance</b></summary>

**Phase 3 - UX Improvements:**
- Added CLI error validation with `parser.error()`
- Added `--estimate-cost` flag for pre-experiment cost preview
- Added real-time progress tracking (variant cost, cumulative cost, ETA)
- Added `--health-check` command

**Phase 4 - Performance:**
- Added compound database indexes:
  - `idx_runs_workflow_model` on runs(workflow, model)
  - `idx_stages_run_turn` on stages(run_id, turn)
  - `idx_runs_timestamp` on runs(timestamp)
- Environment configuration for GCP, gRPC, TensorFlow

</details>

<details>
<summary><b>Phase 5-6: Features & Refactoring</b></summary>

**Phase 5 - New Features:**
- Token Distribution Profiler (`--workflow token_profile`)
- Cost-Quality Frontier Analysis (`--workflow cost_quality`)
- RAG Pipeline with 3 variants (`--workflow rag`)
- Visualization module with shared utilities

**Phase 6 - Codebase Refactoring:**

| Original File | New Package | Lines |
|---------------|-------------|-------|
| `pipeline.py` | `src/pipeline/` | 1,404 |
| `experiment.py` | `src/experiment/` | 1,281 |
| `prompt_templates.py` | `src/config/prompt_domains/` | 1,310 |
| `vulnerability_ground_truth.py` | `src/evaluation/vulnerabilities/` | 1,829 |

</details>

### New Workflows Added

| Workflow | Description | API Calls |
|----------|-------------|-----------|
| `rag` | Retrieval-Augmented Generation (3 variants) | Yes |
| `token_profile` | Token distribution analysis | No |
| `cost_quality` | Pareto frontier cost-quality analysis | No |

### RAG Pipeline Variants
- **rag_basic**: 5 docs, no verification (lowest cost)
- **rag_verified**: 10 docs with citation verification
- **rag_hybrid**: Flash retrieval + Pro generation (best quality)

### Infrastructure Improvements
- Visualization module (`src/visualization/`) with shared utilities
- Parallel support for cost-quality analysis
- Comprehensive troubleshooting guide ([05-troubleshooting.md](05-troubleshooting.md))
- Health check and cost estimation CLI commands
- Structured logging with configurable levels

### December 2025 Cleanup
- Removed dead code: `src/config.py`, `src/pipelines/`, `src/vertex_client.py`
- Migrated `verified_experiment.py` to use `genai_client`
- Updated analysis notebook with RAG, Token Profiler, Pareto Frontier, Domain, and Verified Experiments sections
- Consolidated RAG documentation between `03-pipelines.md` and `06-new-workflows.md`

### Running v3.0 Experiments
```bash
# Full suite including RAG
python3 -m src.experiment --full-experiment

# RAG-specific experiments
python3 -m src.experiment --workflow rag --model flash --iterations 10

# Analysis workflows (no API cost)
python3 -m src.experiment --workflow cost_quality --parallel
python3 -m src.experiment --workflow token_profile
```

Results are saved to `figures/summary.md` in your session directory.

---

## Key Insight

**Flash provides 7x better quality-per-dollar** for most tasks. Pro justified only for complex reasoning where quality improvement exceeds cost premium.

For detailed analysis of cost-quality tradeoffs, use:
```bash
python3 -m src.experiment --workflow cost_quality
```

---

## Related Documentation

- [03-pipelines.md](03-pipelines.md) - Pipeline configurations
- [04-recommendations.md](04-recommendations.md) - Optimization strategies
- [06-new-workflows.md](06-new-workflows.md) - RAG and analysis workflow details

