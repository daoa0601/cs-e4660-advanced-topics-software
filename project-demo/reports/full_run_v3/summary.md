# Experiment Results Summary - full_run_v3

Generated: 2025-12-10

## Overview

| Metric | Value |
|--------|-------|
| Total Runs | 2,444 |
| Total Stages | 5,947 |
| Total Cost | $30.70 |

## Model Comparison

| Model | Runs | Total Cost | Avg Cost |
|-------|------|------------|----------|
| Flash | 1,268 | $7.14 | $0.0056 |
| Pro | 1,176 | $23.57 | $0.0200 |

**Cost Ratio**: Pro costs 3.6x more than Flash

## Quality Comparison

| Model | Avg Quality |
|-------|-------------|
| Flash | 83.26 |
| Pro | 84.48 |

**Quality Difference**: Pro scores +1.22 points higher

## Stage Cost Distribution

| Stage Type | Cost | % |
|------------|------|---|
| Conversation | $8.30 | 27% |
| Generation | $8.02 | 26% |
| Refinement | $4.36 | 14% |
| Critique | $3.52 | 12% |
| Extraction | $2.01 | 7% |
| Evaluation | $1.81 | 6% |

## Figures Generated

1. `01_cost_by_model.png` - Overall cost comparison
2. `02_cost_by_pipeline.png` - Cost by pipeline
3. `03_quality_by_model.png` - Quality comparison
4. `04_cost_quality_scatter.png` - Cost vs quality
5. `05_stage_cost_distribution.png` - Stage costs
6. `06_pro_vs_flash_advantage.png` - Pro advantage by pipeline

## Analysis Charts (HTML)

- `pareto_frontier.html` - Pareto-optimal configurations
- `efficiency_rankings.html` - Quality per dollar rankings
- `token_ratios.html` - Token I/O ratios by workflow
- `context_growth.html` - Context growth analysis
- `token_histogram_*.html` - Token distributions by workflow/model

## Key Insights

### Pareto-Optimal Configurations
- **verbosity_concise (Flash)** - Best value: 2.47B quality/$
- **context_short (Flash)** - Efficient: 601M quality/$
- **react_research (Flash)** - Highest quality: 92.2

### Recommendations
- Default to Flash for standard tasks (3.6x cheaper)
- Use Pro for complex reasoning (33% better on hard problems)
- Hybrid approach: Flash + Pro final stage for best cost/quality
