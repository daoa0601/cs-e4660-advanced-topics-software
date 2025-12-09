# Future Improvements

This document tracks planned improvements and future work for the LLM Cost Decomposition Platform, with detailed reasoning for each item.

**Version:** 3.0  
**Last Updated:** December 2025

---

## Research Directions

### 1. Benchmark Integration

**Current Gap:** The platform uses LLM-based quality evaluation and a small set of 30 ground truth problems. While functional, this approach has limitations:
- LLM-as-judge scores are subjective and can vary between runs
- The ground truth dataset is small and domain-specific
- Results are not directly comparable to published model benchmarks

**Proposed Solution:** Integrate standardized evaluation benchmarks:
- **GSM8K** (Grade School Math): 8.5K math word problems for reasoning evaluation
- **MATH**: 12.5K competition-level math problems with difficulty levels
- **HumanEval**: 164 Python programming problems for code generation

**Expected Impact:**
- Objective, reproducible quality metrics
- Direct comparison with published model performance
- Standardized reporting for academic publications
- Better understanding of cost-quality tradeoffs on specific task types

**Implementation Complexity:** Medium — requires parsing benchmark formats, implementing answer extraction, and creating scoring logic

---

### 2. Multi-Provider Cost Analysis

**Current Gap:** The platform only supports Google Vertex AI (Gemini 2.5 Flash/Pro). This limits:
- Understanding of relative pricing across providers
- Ability to recommend optimal provider for specific use cases
- Cross-provider cost-quality comparisons

**Proposed Solution:** Add support for:
- **OpenAI**: GPT-4o, GPT-4o-mini (API integration)
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Haiku (API integration)
- **Open-source**: Llama 3.1, Mistral via Hugging Face or local deployment

**Expected Impact:**
- Comprehensive cost comparison tables (e.g., "GPT-4o is 2x more expensive than Gemini Pro but 15% better on MATH")
- Provider-agnostic recommendations
- Insights into when cheaper providers suffice

**Implementation Complexity:** High — requires multiple SDK integrations, unified response parsing, and normalized pricing

---

### 3. Prompt Caching Optimization

**Current Gap:** Modern LLM APIs (Gemini, Claude, GPT-4) offer prompt caching that can reduce costs by 50-90% for repeated prefixes. Currently:
- The platform doesn't measure cache hit rates
- No optimization for cache-friendly prompt structures
- Unknown savings from caching in production scenarios

**Proposed Solution:**
- Add cache hit/miss tracking to API responses
- Implement metrics: cache hit rate, cached tokens, cache savings
- Optimize prompt templates for consistent prefixes
- A/B test cache-optimized vs standard prompts

**Expected Impact:**
- Quantify actual caching benefits (potentially 50%+ cost reduction)
- Guidelines for cache-optimized prompt design
- More accurate cost predictions for production workloads

**Implementation Complexity:** Low-Medium — requires API response parsing and metrics aggregation

---

### 4. Adaptive Query Routing

**Current Gap:** Users must manually choose between Flash and Pro models. Our data shows:
- Flash performs equally well on 80% of queries (7x cheaper)
- Pro is justified only for complex reasoning (hard problems show +33% accuracy)
- No automated way to route queries to the optimal model

**Proposed Solution:** Implement a query complexity classifier:
1. **Difficulty Estimation**: Use a lightweight model to score query complexity (0-1)
2. **Routing Rules**: Route simple queries to Flash, complex to Pro
3. **Confidence Thresholds**: Configurable routing thresholds
4. **Feedback Loop**: Track routing decisions and outcomes for improvement

**Expected Impact:**
- Automated cost optimization without quality loss
- Estimated 40-60% cost reduction for mixed workloads
- Self-improving routing based on actual outcomes

**Implementation Complexity:** Medium-High — requires training a classifier or using heuristics, plus routing infrastructure

---

## Engineering Improvements

### 1. ~~Live API for Verified Experiments~~ ✅ COMPLETED

**Status:** Implemented in December 2024

**What Was Done:**
- Replaced `simulate_llm_response()` with `call_llm()` using real Gemini API
- Removed `--live` flag - all experiments now use real API by default
- Implemented answer extraction and verification logic
- Quality scores now extracted from actual LLM responses

**Files Changed:**
- `src/experiments/verified_experiment.py` - Real API calls only
- `src/experiments/domain_experiment.py` - Real API calls only

---

### 2. ~~RAG Embedding Costs~~ ✅ COMPLETED

**Status:** Implemented in December 2024

**What Was Done:**
- Created `src/rag/` module with:
  - `embedding_client.py` - Google GenAI `text-embedding-004` integration
  - `vector_store.py` - FAISS with disk persistence
  - `chunker.py` - Document chunking utilities
  - `cost_tracker.py` - Embedding cost tracking
- RAG pipeline now uses real semantic retrieval
- Embedding costs tracked per retrieval stage
- Added scripts for corpus generation and index building:
  - `scripts/generate_academic_corpus.py` - Generate knowledge base
  - `scripts/build_rag_index.py` - Build FAISS index

**Files Changed:**
- `src/pipeline/rag.py` - Real FAISS retrieval
- `requirements.txt` - Added `faiss-cpu`

---

### 3. Cost Monitoring Dashboard (Medium Priority)

**Current Gap:** Cost visualization is only available after experiments complete. Users can't:
- Monitor costs in real-time during long experiments
- Set alerts for unexpected cost spikes
- Compare multiple sessions visually

**What's Missing:**
- Real-time cost streaming
- Web-based dashboard
- Session comparison views
- Cost alerting

**Proposed Solution:**
- Create a simple web dashboard (Flask/Streamlit)
- WebSocket streaming for real-time updates
- Historical session comparison
- Cost threshold alerts (email/Slack)

**Expected Impact:**
- Improved experiment monitoring
- Early detection of cost anomalies
- Better experiment planning through visual comparison

---

### 4. Cost Budgets (Medium Priority)

**Current Gap:** Experiments run until completion with no cost guardrails. This is risky because:
- A misconfigured experiment could run up large costs
- No way to say "stop if cost exceeds $5"
- No soft warnings as budgets approach

**What's Missing:**
```bash
# Desired capability
python3 -m src.experiment --full-experiment --max-cost 10.00
```

**Proposed Solution:**
- Add `--max-cost` CLI flag
- Track cumulative cost in experiment loop
- Implement soft warning at 80% and hard stop at 100%
- Save partial results when budget exceeded

**Expected Impact:**
- Safer experimentation, especially for new users
- Predictable cost control for budget-constrained projects
- Partial results preserved even on budget termination

---

### 5. Multi-Region Pricing (Low Priority)

**Current Gap:** All experiments run in a single GCP region. However:
- Pricing may vary slightly by region
- Latency differs significantly by region
- Some models may only be available in specific regions

**Proposed Solution:**
- Add region configuration to experiments
- Compare latency and availability across regions
- Document any pricing differences

**Expected Impact:**
- Optimized region selection for latency-sensitive applications
- Understanding of regional availability constraints

---

## Known Limitations

### 1. Simulated Tools in ReAct Pipeline

**Current State:** The ReAct (Reasoning + Acting) pipeline simulates tool calls rather than executing real tools. When the model says "I'll search for X", we return a mock response.

**Why This Matters:**
- Real tool calls have latency and cost implications
- Tool reliability affects overall pipeline success
- Can't measure actual tool integration overhead

**Planned Mitigation:**
- Integrate real web search API (SerpAPI, Tavily)
- Add calculator/code execution tools
- Implement tool cost and latency tracking

---

### 2. ~~No Embedding Cost Tracking~~ ✅ RESOLVED

**Resolution:** RAG pipeline now tracks embedding costs via `text-embedding-004` integration. See "RAG Embedding Costs" above.

---

### 3. Single GCP Region

**Current State:** All experiments run in `us-central1`.

**Why This Matters:**
- Can't compare regional pricing or latency
- May not reflect user's production environment
- Limited availability testing

**Planned Mitigation:** See "Multi-Region Pricing" in Engineering Improvements above.

---

### 4. LLM-Based Quality Scores

**Current State:** Quality is evaluated by asking an LLM to score responses 0-100.

**Why This Matters:**
- LLM-as-judge has known biases (verbosity preference, self-preference)
- Scores vary between runs (not deterministic)
- May not correlate with human preferences

**Planned Mitigation:**
- Expand ground truth dataset to 100+ problems across domains
- Add human evaluation for calibration
- Implement multiple evaluation strategies (BLEU, ROUGE for summarization)
- Use consensus scoring (multiple LLM judges)

---

## Completed Improvements

### December 2024
- **Live API Integration**: All experiments now use real Gemini API calls (no simulation)
- **RAG Embedding Costs**: FAISS vector store with `text-embedding-004` embeddings and cost tracking
- **Academic Corpus Generator**: Script to generate 200 research chunks for RAG testing

For earlier improvements, see [02-experiments.md](02-experiments.md).

---

## Contributing

To propose additional improvements:
1. Open an issue describing the enhancement
2. Reference this document for context
3. Provide expected impact and priority assessment
4. Estimate implementation complexity (Low/Medium/High)

---

## Related Documentation

- [01-architecture.md](01-architecture.md) - Current system design
- [02-experiments.md](02-experiments.md) - Experiment results and development history
- [06-new-workflows.md](06-new-workflows.md) - Current workflow implementations
