# Project Plan (MVP)

**Project**: LLM Cost Decomposition Platform  
**Institution**: Aalto University — Advanced Topics in Software  
**Author**: Anh Dao  
**Date**: January 2025

---

## 1. Objective

Demonstrate that **multi-stage pipeline simulation with agentic patterns** provides granular, actionable LLM cost insights.

**Research Questions**:
1. Where is money spent within complex LLM pipelines?
2. What is the cost-quality tradeoff for different prompt strategies?
3. How do agentic loops (ReAct, self-correcting) affect cost predictability?
4. How does context growth in multi-turn conversations impact costs?

---

## 2. Scope

### In Scope

- **11 pipelines** across 4 patterns (linear, hybrid, agentic, multi-turn)
- **Per-stage cost tracking** with iteration/turn attribution
- **Streaming metrics** (Time-to-First-Token, throughput)
- **Quality evaluation** (automated + optional LLM-based)
- **Multi-model hybrid** pipelines
- **SQLite database** with 3 normalized tables

### Out of Scope (Future Work)

- RAG with embedding costs
- Document processing (PDF)
- Web UI / API endpoints
- Real tool execution in ReAct

---

## 3. Pipelines

### Linear Pipelines

| Pipeline | Stages | Description |
|----------|--------|-------------|
| `verbosity_concise` | 1 | Direct generation |
| `verbosity_cot` | 3 | Draft → Critique → Refine |
| `context_short` | 2 | Extract → Summarize |
| `context_long` | 3 | Extract → Summarize → Evaluate |

### Multi-Model Hybrid

| Pipeline | Models | Strategy |
|----------|--------|----------|
| `hybrid_cot` | Flash/Pro/Flash | Cheap draft, smart critique, cheap refine |

### Agentic Patterns

| Pipeline | Pattern | Max Iterations |
|----------|---------|----------------|
| `react_research` | ReAct Loop | 5 |
| `react_hybrid` | ReAct (Pro thinks, Flash acts) | 5 |
| `multiturn_3` | Conversation | 3 turns |
| `multiturn_5` | Conversation | 5 turns |
| `self_correcting` | Validate Loop | 3 retries |
| `self_correcting_hybrid` | Validate (Pro validates) | 3 retries |

---

## 4. Experimental Design

### Variables

| Type | Variables |
|------|-----------|
| Independent | Pipeline, Model, Streaming enabled |
| Dependent | Cost (per stage), TTFT, Iterations, Context growth |
| Controlled | API version, Region, Test inputs |

### Measurements

| Metric | Level | Precision |
|--------|-------|-----------|
| Cost | Per stage | $0.000001 |
| TTFT | Per stage | Milliseconds |
| Iterations | Per run | Count |
| Context tokens | Per turn | Exact |

---

## 5. Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Core Infrastructure | Days 1-2 | Vertex client, cost calculator, DB |
| Pipeline System | Days 3-4 | Linear + hybrid pipelines |
| Agentic Patterns | Days 5-6 | ReAct, multi-turn, self-correcting |
| Streaming | Day 7 | TTFT metrics |
| Analysis | Days 8-9 | Jupyter notebook |

**Total**: ~9 days

---

## 6. Key Analyses

1. **Cost Attribution**: Where is money spent by stage type?
2. **Hybrid Efficiency**: Does Pro-for-critique save money vs Pro-for-all?
3. **Iteration Analysis**: Cost variance in agentic loops
4. **Context Growth**: Cost escalation in multi-turn
5. **TTFT vs Total**: User-perceived vs actual latency
6. **Cost-Quality Frontier**: Pareto-optimal pipelines

---

## 7. Success Criteria

| Criterion | Target |
|-----------|--------|
| All pipelines execute | 11/11 working |
| Stage tracking | Per-stage costs logged |
| Streaming metrics | TTFT captured |
| Agentic metadata | Iterations/turns tracked |
| Statistical validity | 95% CIs calculable |
