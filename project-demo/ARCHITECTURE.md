# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      Experiment Runner                          │
│       (CLI orchestration, workflow selection, parallel exec)    │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                        │
│                                                                 │
│  Linear:       [S1] ──▶ [S2] ──▶ [S3]                          │
│  ReAct:        [Think] ◀──▶ [Act] (loop until done)            │
│  Multi-Turn:   [T1] ──▶ [T2] ──▶ [T3] (growing context)        │
│  Self-Correct: [Gen] ◀──▶ [Validate] (loop until valid)        │
│  Document:     [Extract] ──▶ [Analyze] ──▶ [Recommend]         │
│                                                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌──────────────┐        ┌──────────────┐          ┌──────────────┐
│   Vertex AI  │        │   Quality    │          │    Cost      │
│   Client     │        │  Evaluator   │          │  Calculator  │
└──────────────┘        └──────────────┘          └──────────────┘
        │                       │                         │
        └───────────────────────┼─────────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │   SQLite Database   │
                    │   (WAL mode +       │
                    │   thread-safe)      │
                    │  ┌───────────────┐  │
                    │  │ runs          │  │
                    │  │ stages        │  │
                    │  │ quality_scores│  │
                    │  └───────────────┘  │
                    └─────────────────────┘
```

---

## Components

### 1. Experiment Runner (`experiment.py`)

**Purpose**: CLI entry point and workflow orchestration with parallel execution.

**Workflows**:
- `verbosity` — Compare concise vs CoT vs hybrid
- `context` — Compare short vs long context
- `react` — ReAct agent loops
- `multiturn` — Multi-turn conversations
- `self_correcting` — Generate-validate-fix loops
- `document` — Technical document analysis

**Key Functions**:
```python
run_experiment(workflow, model, iterations, streaming, parallel, workers)
run_full_suite(parallel=True, workers=8)  # All workflows, both models
run_parallel_iterations(tasks, execute_fn, workers)  # ThreadPoolExecutor
```

**Parallel Execution**:
- Uses `ThreadPoolExecutor` for concurrent API calls
- Thread-safe database writes with locks
- Configurable worker count (default: 4)
- Ignores `--delay` when running in parallel

---

### 2. Pipeline Orchestrator (`pipeline.py`)

**Purpose**: Execute different pipeline patterns with cost tracking.

**Pipeline Classes**:

```python
# Linear multi-stage
class Pipeline:
    stages: list[PipelineStage]
    def execute(input, model, streaming) -> PipelineResult

# ReAct agent loop
class ReActPipeline:
    max_iterations: int  # default: 5
    think_model: str
    act_model: str
    def execute(query, model, streaming) -> PipelineResult

# Multi-turn conversation
class MultiTurnPipeline:
    turns: list[str]  # Follow-up messages
    def execute(initial_query, model, streaming) -> PipelineResult

# Self-correcting loop
class SelfCorrectingPipeline:
    max_retries: int  # default: 3
    generate_model: str
    validate_model: str
    def execute(task, model, streaming) -> PipelineResult
```

**Total Pipelines: 15**

| Category | Count | Pipelines |
|----------|-------|-----------|
| Linear | 4 | verbosity_concise, verbosity_cot, context_short, context_long |
| Hybrid | 1 | hybrid_cot |
| ReAct | 2 | react_research, react_hybrid |
| Multi-turn | 2 | multiturn_3, multiturn_5 |
| Self-correcting | 2 | self_correcting, self_correcting_hybrid |
| Document | 4 | doc_analysis_simple, doc_analysis_thorough, doc_analysis_iterative, doc_analysis_hybrid |

**Stage Types**:
| Type | Description | Used In |
|------|-------------|---------|
| `generation` | Initial response | All |
| `critique` | Review previous output | CoT |
| `refinement` | Improve based on feedback | CoT, Self-correct |
| `extraction` | Pull out key info | Context, Document |
| `summarization` | Condense | Context |
| `thinking` | ReAct reasoning | ReAct |
| `action` | ReAct tool/action | ReAct |
| `validation` | Check correctness | Self-correct |
| `conversation` | Chat turn | Multi-turn |
| `analysis` | Security/quality analysis | Document |
| `classification` | Categorize issues | Document |
| `recommendation` | Remediation advice | Document |

---

### 3. Vertex AI Client (`vertex_client.py`)

**Purpose**: API wrapper with streaming support.

**Key Functions**:
```python
# Standard call
call_model(prompt, model, streaming=False) -> ModelResponse

# Multi-turn with history
call_model_with_history(messages, model, streaming=False) -> ModelResponse
```

**Streaming Metrics**:
```python
@dataclass
class StreamingMetrics:
    time_to_first_token_ms: int  # User-perceived start
    total_latency_ms: int        # Full response
    tokens_per_second: float     # Throughput
    chunk_count: int
```

**Models**:
| Model | ID | Input | Output |
|-------|-----|-------|--------|
| Flash | gemini-2.5-flash | $0.15/1M | $0.60/1M |
| Pro | gemini-2.5-pro | $1.25/1M | $5.00/1M |

---

### 4. Database (`db.py`)

**Purpose**: Thread-safe persistence with agentic metadata.

**Concurrency Features**:
- WAL (Write-Ahead Logging) mode for concurrent reads
- Thread locks on all write operations
- 30-second timeout for lock acquisition

**Schema**:

```sql
-- Runs table with agentic fields
CREATE TABLE runs (
    -- Standard
    id, timestamp, workflow, pipeline, model,
    total_cost, total_latency_ms, ...
    
    -- Agentic metadata
    pipeline_type TEXT,        -- linear/react/multiturn/self_correcting
    iterations INTEGER,        -- Loop count
    turns INTEGER,             -- Conversation turns
    termination_reason TEXT,   -- Why loop ended
    avg_ttft_ms FLOAT,         -- Average TTFT
    context_tokens_by_turn TEXT -- JSON array
);

-- Stages with streaming
CREATE TABLE stages (
    -- Standard
    run_id, stage_order, stage_name, stage_type, model, cost, ...
    
    -- Loop tracking
    iteration INTEGER,
    turn INTEGER,
    
    -- Streaming
    time_to_first_token_ms INTEGER,
    tokens_per_second FLOAT
);
```

**Query Functions**:
```python
get_iteration_analysis()      # ReAct/self-correct iteration stats
get_context_growth_analysis() # Multi-turn context escalation
get_streaming_analysis()      # TTFT and throughput stats
get_cost_by_model()           # For hybrid pipeline analysis
```

---

### 5. Quality Evaluator (`evaluator.py`)

**Purpose**: Assess output quality for cost-quality analysis.

**Metrics**:
- **Automated** (free): length, structure, vocabulary richness
- **LLM-based** (extra cost): relevance, completeness, clarity

---

## Pipeline Patterns

### Linear Pipeline
```
Input ──▶ [Stage 1] ──▶ [Stage 2] ──▶ [Stage 3] ──▶ Output
             │             │             │
             ▼             ▼             ▼
          $0.001        $0.002        $0.001     = $0.004 total
```

### Multi-Model Hybrid
```
Input ──▶ [Draft:Flash] ──▶ [Critique:Pro] ──▶ [Refine:Flash] ──▶ Output
              │                  │                  │
              ▼                  ▼                  ▼
           $0.0005            $0.003             $0.0005    = $0.004 total
                                 ↑
                    Pro only where it matters
```

### ReAct Loop
```
Query ──▶ [Think] ──▶ [Act] ──┐
             ↑                │
             └────────────────┘  (repeat until "FINAL ANSWER" or max iterations)
             
Iteration 1: $0.0008
Iteration 2: $0.0009
Iteration 3: $0.0007
Total:       $0.0024 (terminated: confidence_reached)
```

### Multi-Turn Conversation
```
[Turn 1] ──▶ [Turn 2] ──▶ [Turn 3] ──▶ [Turn 4] ──▶ [Turn 5]
  500 tok    1200 tok    2100 tok    3200 tok    4500 tok  ← Context grows!
  $0.0001    $0.0003     $0.0005     $0.0008     $0.0012   ← Cost escalates
```

### Self-Correcting Loop
```
[Generate] ──▶ [Validate] ──┬──▶ PASS ──▶ Output
                 │          │
                 NO         │
                 │          │
                 ▼          │
              [Fix] ───────┘

Attempt 1: Generate $0.001 + Validate $0.0005 = FAIL
Attempt 2: Fix $0.001 + Validate $0.0005 = FAIL  
Attempt 3: Fix $0.001 + Validate $0.0005 = PASS
Total: $0.0045
```

### Document Analysis
```
[Extract] ──▶ [Analyze] ──▶ [Classify] ──▶ [Recommend]
    │             │             │              │
    ▼             ▼             ▼              ▼
 $0.0003       $0.0015       $0.002         $0.0005    = $0.0043 total
  Flash          Pro           Pro           Flash
```

---

## Data Flow Example

```
User runs: python3 -m src.experiment --workflow react --model flash --streaming --parallel

1. Experiment Runner
   └─▶ Initializes ReActPipeline(max_iterations=5)
   └─▶ Creates ThreadPoolExecutor(max_workers=4)

2. Parallel Execution
   ├─▶ Thread 1: ReActPipeline.execute(query1)
   ├─▶ Thread 2: ReActPipeline.execute(query2)
   ├─▶ Thread 3: ReActPipeline.execute(query3)
   └─▶ Thread 4: ReActPipeline.execute(query4)

3. Each ReActPipeline.execute()
   ├─▶ Iteration 1:
   │   ├─▶ Think stage → Vertex AI (streaming)
   │   │   └─▶ Returns: text, tokens, TTFT=145ms
   │   └─▶ Act stage → Vertex AI (streaming)
   │       └─▶ Returns: observation, TTFT=98ms
   │
   ├─▶ Iteration 2:
   │   ├─▶ Think stage (with context) → "FINAL ANSWER: ..."
   │   └─▶ Terminated: confidence_reached
   │
   └─▶ Returns PipelineResult(iterations=2, stages=[...])

4. log_pipeline_result() [with thread lock]
   ├─▶ INSERT INTO runs (iterations=2, termination_reason='confidence_reached', ...)
   └─▶ INSERT INTO stages (iteration=1, time_to_first_token_ms=145, ...)
       INSERT INTO stages (iteration=1, time_to_first_token_ms=98, ...)
       INSERT INTO stages (iteration=2, time_to_first_token_ms=132, ...)

5. Analysis notebook queries (concurrent read OK with WAL):
   └─▶ get_iteration_analysis() → "Avg 2.3 iterations, $0.0018/run"
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Multiple pipeline classes | Different patterns need different orchestration |
| Streaming optional | Not all experiments need TTFT |
| Hybrid model support | Test cost optimization strategies |
| Loop tracking in schema | Essential for agentic cost analysis |
| Context growth as JSON | Flexible turn-by-turn tracking |
| Termination reasons | Understand why loops end |
| WAL mode + thread locks | Safe parallel execution |
| 4 default workers | Conservative to avoid API rate limits |
| Document analysis workflow | Real-world use case for security review |
