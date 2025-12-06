# Experiment Results

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

## Key Insight

**Flash provides 7x better quality-per-dollar** for most tasks. Pro justified only for complex reasoning where quality improvement exceeds cost premium.
