# Future Improvements

Planned improvements and future work for the LLM Cost Decomposition Platform.

**Version:** 3.0
**Last Updated:** December 2025

---

## High Priority

### 1. Session System Fix (In Progress)
**Complexity:** Low-Medium | **Impact:** High

The session system creates folders but doesn't actually store data there. Database layer ignores session paths.

**Problem:**
- `get_session_db_path()` exists in `src/session.py` but is never called
- `src/db/connection.py` always uses hardcoded `DB_PATH`
- All data goes to `project-demo/data/experiments.db` regardless of session

**Implementation:**
- Modify `src/db/connection.py` to use `get_session_db_path()`
- Add `--session` CLI flag for session selection
- Add session comparison features

See [CURRENT_PLAN.md](../CURRENT_PLAN.md) for detailed implementation plan.

---

### 2. Analysis Chart PNG Conversion (In Progress)
**Complexity:** Low | **Impact:** Medium

Convert HTML analysis charts to combined PNG images for GitHub visibility.

**Current State:**
- `token_profiler.py` generates 18 HTML files
- `cost_quality_analysis.py` generates 2 HTML files
- HTML files not viewable on GitHub

**Target:** 3 combined PNG images using `make_subplots()`

See [CURRENT_PLAN.md](../CURRENT_PLAN.md) for detailed implementation plan.

---

### 3. Cost Budgets
**Complexity:** Low | **Impact:** High

Add `--max-cost` CLI flag to prevent runaway experiment costs.

```bash
python3 -m src.experiment --full-experiment --max-cost 10.00
```

**Implementation:**
- Add `--max-cost` argument to CLI
- Track cumulative cost in experiment loop
- Warn at 80%, hard stop at 100%
- Save partial results on budget termination

---

### 4. Prompt Caching Metrics
**Complexity:** Low-Medium | **Impact:** High

Track cache hit/miss rates from Gemini API to quantify caching benefits (50-90% savings potential).

**Implementation:**
- Parse `cached_content_token_count` from API responses
- Add `cached_tokens` field to StageResult and database
- Calculate cache hit rate in analysis

---

### 5. Real Tools for ReAct Pipeline
**Complexity:** Medium | **Impact:** Medium

Replace simulated tool responses with real tool calls.

**Current limitation:** ReAct pipeline returns mock responses when the model requests tool use.

**Implementation:**
- Integrate web search API (SerpAPI or Tavily)
- Add calculator/code execution tools
- Track tool costs and latency

---

## Medium Priority

### 6. Benchmark Integration (GSM8K, MATH)
**Complexity:** Medium | **Impact:** High

Integrate standardized benchmarks for objective quality measurement.

**Current limitation:** LLM-as-judge scores are subjective; ground truth dataset is only 30 problems.

**Proposed benchmarks:**
- **GSM8K**: 8.5K math word problems
- **MATH**: 12.5K competition-level problems
- **HumanEval**: 164 Python programming problems

**Benefits:**
- Objective, reproducible metrics
- Comparable to published model performance
- Better cost-quality tradeoff analysis

---

### 7. Adaptive Query Routing
**Complexity:** Medium-High | **Impact:** High (40-60% cost reduction)

Automatically route queries to Flash or Pro based on complexity.

**Current limitation:** Users manually choose models; Flash handles 80% of queries equally well at 7x lower cost.

**Implementation:**
1. Complexity classifier (heuristics or small model)
2. Route simple queries → Flash, complex → Pro
3. Configurable thresholds
4. Feedback loop for improvement

---

### 8. Cost Monitoring Dashboard
**Complexity:** Medium | **Impact:** Medium

Web dashboard for real-time cost monitoring during experiments.

**Features needed:**
- Real-time cost streaming
- Session comparison views
- Cost threshold alerts

**Implementation:** Streamlit or Flask dashboard with WebSocket updates.

---

## Lower Priority

### 9. Multi-Provider Support
**Complexity:** High | **Impact:** High

Add OpenAI and Anthropic support for cross-provider comparison.

**Providers to add:**
- OpenAI: GPT-4o, GPT-4o-mini
- Anthropic: Claude 3.5 Sonnet, Claude 3 Haiku
- Open-source: Llama 3.1, Mistral

**Challenges:** Multiple SDKs, different response formats, normalized pricing.

---

### 10. Multi-Region Latency Comparison
**Complexity:** Low | **Impact:** Low

Compare latency and pricing across GCP regions.

**Current limitation:** All experiments run in `us-central1`.

---

### 11. Expanded Ground Truth Dataset
**Complexity:** Low | **Impact:** Medium

Expand verifiable problems from 30 to 100+ across domains.

---

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Simulated ReAct tools | Can't measure real tool overhead | See #3 above |
| Single GCP region | No regional comparison | See #8 above |
| LLM-based quality scores | Subjective, non-deterministic | See #4, #9 above |

---

## Recently Completed

| Improvement | Completed |
|-------------|-----------|
| **full_run_v3 experiment** (2,444 runs, $30.70) | Dec 2025 |
| Report generation with --output-dir support | Dec 2025 |
| PNG figure generation for main reports | Dec 2025 |
| Live API for all experiments | Dec 2024 |
| RAG with FAISS + embedding costs | Dec 2024 |
| Academic corpus generator | Dec 2024 |
| Codebase cleanup (dead code removal) | Dec 2025 |
| Notebook updates (RAG, Pareto, Token Profiler) | Dec 2025 |

---

## Related Documentation

- [01-architecture.md](01-architecture.md) - System design
- [02-experiments.md](02-experiments.md) - Experiment history
- [IMPROVEMENTS.md](../project-demo/IMPROVEMENTS.md) - Detailed implementation guide
