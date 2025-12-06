# LLM Cost Analysis Platform Enhancements

Enhanced modules for the LLM Cost Decomposition Platform:
1. **Domain-specific prompt templates** for topic-focused experiments
2. **Tiered token pricing** with long-context support (200K threshold)
3. **Domain experiment runner** for structured cost analysis

## File Locations

All enhancement modules are now integrated into the `src/` directory:

| Module | Location | Description |
|--------|----------|-------------|
| Prompt Templates | `src/config/prompt_templates.py` | Domain-specific prompts (coding, biology, legal, etc.) |
| Tiered Pricing | `src/pricing/tiered_pricing.py` | Accurate cost calculation with long-context tiers |
| Domain Experiments | `src/experiments/domain_experiment.py` | Run domain-focused experiments |
| GenAI Client | `src/clients/genai_client.py` | Google GenAI SDK with ADC authentication |

## Quick Start

### Generate Domain-Specific Prompts

```python
from src.config import list_domains, generate_experiment_prompts

# List available domains
domains = list_domains()  # ['coding', 'biology', 'legal', 'creative', 'finance', 'medical', 'general']

# Generate prompts
prompts = generate_experiment_prompts(domain="coding", n_prompts=20, seed=42)
```

### Calculate Costs with Tiered Pricing

```python
from src.pricing import calculate_cost, calculate_cost_detailed

# Standard context
cost = calculate_cost("flash", input_tokens=50000, output_tokens=1000)

# Long context (>200K tokens triggers higher rates)
details = calculate_cost_detailed("pro", input_tokens=50000, output_tokens=1000, context_tokens=250000)
print(f"Tier: {details['pricing_tier']}, Cost: ${details['total_cost']:.6f}")
```

### Run Domain Experiments

```bash
# Run a biology experiment
python -m src.experiments.domain_experiment --domain biology --iterations 20

# Compare Flash vs Pro on a domain
python -m src.experiments.domain_experiment --domain coding --compare-models

# Filter by difficulty
python -m src.experiments.domain_experiment --domain medical --difficulty hard
```

---

## Available Domains

| Domain | Description | Templates |
|--------|-------------|-----------|
| `coding` | Software development, debugging, code review, system design | 5 |
| `biology` | Molecular biology, genetics, biochemistry, experimental design | 5 |
| `legal` | Contract analysis, regulatory compliance, legal research | 5 |
| `creative` | Creative writing, storytelling, poetry, narrative craft | 5 |
| `finance` | Financial analysis, valuation, risk assessment, market analysis | 5 |
| `medical` | Clinical reasoning, diagnosis, treatment planning, patient education | 5 |
| `general` | General knowledge, reasoning, and problem-solving tasks | 5 |

---

## Pricing (December 2025)

### Google Gemini on Vertex AI

| Model | Tier | Input (/1M) | Output (/1M) |
|-------|------|-------------|--------------|
| **Gemini 2.5 Flash** | Standard (≤200K) | $0.15 | $0.60 |
| | Long Context (>200K) | $0.30 | $1.20 |
| **Gemini 2.5 Pro** | Standard (≤200K) | $1.25 | $10.00 |
| | Long Context (>200K) | $2.50 | $15.00 |

### When Long Context Pricing Applies

- If total context exceeds **200K tokens**, the higher rates apply to all tokens
- Critical for multi-turn conversations that accumulate context

---

## SDK Migration

The platform now uses the `google-genai` SDK with Vertex AI backend:

```python
from src.clients import call_model, call_model_with_history

# Simple call (uses ADC automatically)
response = call_model("Hello, world!", model="flash")

# Streaming with TTFT metrics
response = call_model("Count to 10", model="flash", streaming=True)
print(f"TTFT: {response.streaming_metrics.time_to_first_token_ms}ms")

# Multi-turn conversation
messages = [
    {"role": "user", "content": "What is Python?"},
    {"role": "model", "content": "Python is a programming language..."},
    {"role": "user", "content": "Give me an example"},
]
response = call_model_with_history(messages, model="pro")
```

**Authentication**: Uses Application Default Credentials (ADC) - no API key needed when running on GCP or after `gcloud auth application-default login`.
