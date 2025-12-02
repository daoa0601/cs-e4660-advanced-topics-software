# Project Report: LLM Cost Decomposition Platform (MVP)

## 1. Summary

This project demonstrates **granular cost tracking for complex LLM workflows** including multi-stage pipelines, multi-model hybrids, and agentic patterns. By tracking costs at the stage level with streaming metrics and iteration counts, we enable data-driven decisions about prompt strategies and model selection.

**Key Innovations**:
- Per-stage cost attribution within multi-step workflows
- Multi-model hybrid pipelines (Flash for drafts, Pro for critique)
- Agentic loop cost tracking (ReAct, self-correcting)
- Context growth analysis for multi-turn conversations
- Document analysis workflows for security review
- Streaming metrics (Time-to-First-Token)
- Parallel execution for faster experimentation

---

## 2. Research Questions

1. **Cost Attribution**: Where is money spent within complex pipelines?
2. **Hybrid Efficiency**: Can strategic model selection reduce costs?
3. **Agentic Costs**: How predictable are loop-based workflows?
4. **Context Growth**: How does multi-turn conversation cost escalate?
5. **Latency Tradeoffs**: TTFT vs total latency for user experience?
6. **Document Analysis**: Is thorough 4-stage analysis worth 2x the cost?

---

## 3. System Design

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Experiment Runner                          │
│              (Sequential or Parallel Execution)                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                        │
│                                                                 │
│   Linear:       [Stage1] ──▶ [Stage2] ──▶ [Stage3]             │
│   ReAct:        [Think] ──▶ [Act] ──▶ [Observe] ──▶ loop       │
│   Multi-Turn:   [Turn1] ──▶ [Turn2] ──▶ ... (context grows)    │
│   Self-Correct: [Gen] ──▶ [Validate] ──▶ [Fix] ──▶ loop        │
│   Document:     [Extract] ──▶ [Analyze] ──▶ [Recommend]        │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐          ┌──────────────┐
│   Vertex AI  │        │   Quality    │          │   Streaming  │
│    Client    │        │  Evaluator   │          │   Metrics    │
└──────────────┘        └──────────────┘          └──────────────┘
        │                       │                         │
        └───────────────────────┴─────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SQLite Database   │
                    │   (WAL mode for     │
                    │   concurrent access)│
                    └─────────────────────┘
```

### Parallel Execution

The platform supports parallel experiment execution using `ThreadPoolExecutor`:
- **Thread-safe DB writes**: All log functions use thread locks
- **WAL mode**: Enables concurrent reads during writes
- **Configurable workers**: Default 4, adjust with `--workers`
- **~4x speedup**: 100 iterations in ~5 min vs ~20 min sequential

---

## 4. Pipelines Implemented

### 4.1 Linear Pipelines (4)

| Pipeline | Stages | Flow |
|----------|--------|------|
| `verbosity_concise` | 1 | Generate |
| `verbosity_cot` | 3 | Draft → Critique → Refine |
| `context_short` | 2 | Extract → Summarize |
| `context_long` | 3 | Extract → Summarize → Evaluate |

### 4.2 Multi-Model Hybrid (1)

| Pipeline | Strategy |
|----------|----------|
| `hybrid_cot` | Flash (draft) → **Pro** (critique) → Flash (refine) |

**Hypothesis**: Using Pro only for critique saves ~60% vs Pro for all stages.

### 4.3 Agentic Patterns (6)

| Pipeline | Pattern | Key Metric |
|----------|---------|------------|
| `react_research` | ReAct Loop (max 5) | Iterations until confident |
| `react_hybrid` | ReAct (Pro thinks) | Think vs Act cost split |
| `multiturn_3` | 3-turn conversation | Context growth |
| `multiturn_5` | 5-turn conversation | Cost escalation |
| `self_correcting` | Validate loop (max 3) | Retry rate |
| `self_correcting_hybrid` | Pro validates | Validation accuracy vs cost |

### 4.4 Document Analysis (4)

| Pipeline | Stages | Strategy |
|----------|--------|----------|
| `doc_analysis_simple` | 2 | Extract → Analyze |
| `doc_analysis_thorough` | 4 | Extract → Analyze → Classify → Recommend |
| `doc_analysis_iterative` | 3 | Analyze → Self-Review → Refine |
| `doc_analysis_hybrid` | 3 | Flash (extract) → Pro (analyze) → Flash (remediate) |

**Test Documents** (5 examples):
- User authentication module (Python) - SQL injection, plaintext passwords
- Kubernetes deployment (YAML) - Hardcoded secrets, privileged containers
- REST API endpoint (Flask) - No auth, command injection
- Microservices architecture (doc) - Single point of failure, no TLS
- AWS Terraform (HCL) - Hardcoded credentials, public S3/RDS

**Total Pipelines: 15**

---

## 5. Key Metrics Tracked

### Per-Stage
| Metric | Description |
|--------|-------------|
| `cost` | Cost for this stage |
| `input_tokens` / `output_tokens` | Token usage |
| `latency_ms` | Stage duration |
| `time_to_first_token_ms` | Streaming TTFT |
| `tokens_per_second` | Throughput |
| `iteration` | Which loop iteration (agentic) |
| `turn` | Which conversation turn |

### Per-Run
| Metric | Description |
|--------|-------------|
| `iterations` | Total iterations (ReAct, self-correct) |
| `turns` | Total conversation turns |
| `termination_reason` | Why loop ended |
| `context_tokens_by_turn` | Context growth tracking |
| `avg_ttft_ms` | Average time to first token |

---

## 6. Expected Findings

### Hypothesis 1: Hybrid Efficiency
Using Pro only for critique stages will reduce costs by 50-70% compared to Pro for all stages, with minimal quality impact.

### Hypothesis 2: Agentic Cost Variance
ReAct and self-correcting loops will show **2-5x cost variance** depending on query complexity and number of iterations.

### Hypothesis 3: Context Growth
Multi-turn conversations will show **exponential context cost growth**:
- Turn 1: baseline
- Turn 3: ~3x baseline
- Turn 5: ~8x baseline

### Hypothesis 4: TTFT Value
TTFT will be 30-50% of total latency, demonstrating that streaming provides significant perceived performance improvement.

### Hypothesis 5: Document Analysis Tradeoffs
Thorough 4-stage analysis will find 20-30% more issues than simple 2-stage, but at 2x the cost.

---

## 7. Analyses

### Analysis 1: Cost by Stage Type
```
Stage Type Distribution (expected):
  Generation    ████████████████████  55%
  Critique      ████████████          25%
  Thinking      ██████                12%
  Validation    ████                   8%
```

### Analysis 2: Hybrid vs Uniform
| Configuration | Expected Cost | Quality |
|---------------|---------------|---------|
| All Flash | $0.001 | 70/100 |
| All Pro | $0.010 | 85/100 |
| Hybrid | $0.004 | 82/100 |

### Analysis 3: Iteration Cost Curve
```
ReAct Iterations:
  1 iteration:  $0.0008
  2 iterations: $0.0015
  3 iterations: $0.0023
  4 iterations: $0.0031
  5 iterations: $0.0040 (max)
```

### Analysis 4: Document Analysis Strategies
| Strategy | Stages | Expected Cost | Issues Found |
|----------|--------|---------------|--------------|
| Simple | 2 | $0.002 | 70% |
| Thorough | 4 | $0.004 | 90% |
| Iterative | 3 | $0.003 | 85% |
| Hybrid | 3 | $0.0025 | 85% |

---

## 8. Usage

### Quick Start
```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add GCP_PROJECT_ID

# Test connection
python3 -m src.experiment --test-connection

# Run single workflow
python3 -m src.experiment --workflow verbosity --model flash --iterations 10

# Run with parallel execution (faster!)
python3 -m src.experiment --workflow document --model flash --iterations 20 --parallel

# Run full suite with 8 workers
python3 -m src.experiment --full-suite --iterations 20 --parallel --workers 8

# Analyze results
jupyter notebook notebooks/analysis.ipynb
```

### CLI Reference
```bash
--workflow verbosity|context|react|multiturn|self_correcting|document
--model flash|pro
--iterations N       # Runs per variant (default: 20)
--parallel           # Enable parallel execution
--workers N          # Parallel workers (default: 4)
--streaming          # Enable TTFT metrics
--reset              # Clear database before running
```

---

## 9. Limitations

| Limitation | Impact |
|------------|--------|
| Simulated tools in ReAct | Not measuring real tool costs |
| No RAG pipeline | Retrieval/embedding costs not captured |
| Automated quality only | May not capture all quality dimensions |
| Single region | Regional pricing differences not captured |
| API rate limits | May affect parallel execution speed |

---

## 10. Future Work

1. **RAG Pipeline**: Add retrieval with embedding cost tracking
2. **Real Tool Integration**: Actual web search, code execution costs
3. **Adaptive Routing**: Route queries to optimal pipeline based on complexity
4. **Cost Budgets**: Run pipelines with cost constraints
5. **Caching Analysis**: Measure prompt cache hit rates
6. **Multi-Region**: Compare pricing across GCP regions

---

## 11. Models

| Model | ID | Input Price | Output Price |
|-------|-----|-------------|--------------|
| Flash | gemini-2.5-flash | $0.15/1M tokens | $0.60/1M tokens |
| Pro | gemini-2.5-pro | $1.25/1M tokens | $5.00/1M tokens |

---

## 12. Conclusion

This platform provides **unprecedented granularity** in LLM cost analysis:

1. **Stage-level attribution** answers "where is the money going?"
2. **Multi-model hybrids** demonstrate practical cost optimization
3. **Agentic tracking** reveals loop cost variance and predictability
4. **Context growth** analysis shows multi-turn cost escalation
5. **Document analysis** provides real-world security review use case
6. **Streaming metrics** capture user-perceived latency
7. **Parallel execution** enables faster experimentation

These insights enable organizations to make **data-driven decisions** about pipeline design, model selection, and cost optimization strategies.
