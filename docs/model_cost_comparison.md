# Model Cost Comparison for Full Hobbit Generation

**Scope:** 4,089 narrative blocks across all 95 canonical gaps  
**Estimated tokens:**
- Input: ~1,512,930 tokens (~370 tokens / block)
- Output: ~899,580 tokens (~220 tokens / block)

Prices fetched live from OpenRouter API on 2026-04-04.

---

## 25-Model Full-Batch Cost Table (sorted by total cost)

| Model ID | In $/1M | Out $/1M | Context | Total $ |
| :--- | ---: | ---: | ---: | ---: |
| nvidia/nemotron-3-nano-30b-a3b:free | 0.00 | 0.00 | 256,000 | **0.00** |
| nvidia/nemotron-3-super-120b-a12b:free | 0.00 | 0.00 | 262,144 | **0.00** |
| google/gemma-3n-e4b-it | 0.02 | 0.04 | 32,768 | **0.07** |
| mistralai/mistral-nemo | 0.02 | 0.04 | 131,072 | **0.07** |
| meta-llama/llama-3.1-8b-instruct | 0.02 | 0.05 | 16,384 | **0.08** |
| ibm-granite/granite-4.0-h-micro | 0.02 | 0.11 | 131,000 | **0.12** |
| qwen/qwen2.5-coder-7b-instruct | 0.03 | 0.09 | 32,768 | **0.13** |
| mistralai/mistral-small-3.1-24b-instruct | 0.03 | 0.11 | 131,072 | **0.14** |
| cohere/command-r7b-12-2024 | 0.04 | 0.15 | 128,000 | **0.19** |
| microsoft/phi-4 | 0.07 | 0.14 | 16,384 | **0.22** |
| allenai/olmo-2-0325-32b-instruct | 0.05 | 0.20 | 128,000 | **0.26** |
| google/gemma-3-27b-it | 0.08 | 0.16 | 131,072 | **0.26** |
| meta-llama/llama-3.3-70b-instruct | 0.10 | 0.32 | 131,072 | **0.44** |
| google/gemini-2.0-flash-001 | 0.10 | 0.40 | 1,048,576 | **0.51** |
| nvidia/llama-3.3-nemotron-super-49b-v1.5 | 0.10 | 0.40 | 131,072 | **0.51** |
| openai/gpt-4o-mini | 0.15 | 0.60 | 128,000 | **0.77** |
| meta-llama/llama-4-maverick | 0.15 | 0.60 | 1,048,576 | **0.77** |
| cohere/command-r-08-2024 | 0.15 | 0.60 | 128,000 | **0.77** |
| qwen/qwen2.5-vl-32b-instruct | 0.20 | 0.60 | 128,000 | **0.84** |
| deepseek/deepseek-chat-v3.1 | 0.15 | 0.75 | 32,768 | **0.90** |
| x-ai/grok-3-mini | 0.30 | 0.50 | 131,072 | **0.90** |
| openai/gpt-4.1-mini | 0.40 | 1.60 | 1,047,576 | **2.04** |
| anthropic/claude-3.5-haiku | 0.80 | 4.00 | 200,000 | **4.81** |
| google/gemini-2.5-pro-preview-05-06 | 1.25 | 10.00 | 1,048,576 | **10.89** |
| anthropic/claude-3.7-sonnet | 3.00 | 15.00 | 200,000 | **18.03** |

---

## Notes

- **Free models** (`:free` endpoints) are rate-limited and may not always be available or consistent.
- **OpenRouter purchase fee:** ~5.5% (with an $0.80 minimum on small purchases).
- **Current recommended models for this project:**
  - **Best value / quality trade-off:** `google/gemini-2.0-flash-001` (~$0.51)
  - **Best OpenAI alternative:** `openai/gpt-4o-mini` (~$0.77)
  - **Best premium quality:** `anthropic/claude-3.7-sonnet` (~$18.03) or `google/gemini-2.5-pro-preview-05-06` (~$10.89)
- **Claude 3.5 Sonnet** was not available on OpenRouter at the time of writing (returns 404); `anthropic/claude-3.7-sonnet` is used as the premium Anthropic option instead.

## Current Active Batches for Test Gap (`gap_canon_044_canon_045`)

| Batch ID | Model | Status |
| :--- | :--- | :--- |
| `84c7605b...` | `google/gemini-2.0-flash-001` | English, pure-dialogue prompts ✅ |
| `51abf064...` | `openai/gpt-4o-mini` | Older Spanish outputs — **regeneration pending** |

To regenerate a specific gap with a specific model:
```bash
python3 scripts/event_generator.py --gap-id gap_canon_044_canon_045 --days 2 --model openai/gpt-4o-mini
```
