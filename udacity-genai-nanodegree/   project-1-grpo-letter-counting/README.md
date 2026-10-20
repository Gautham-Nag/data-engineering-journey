# Project 1 — Teaching an LLM to Reason Step-by-Step with GRPO

Fine-tuning **Qwen2.5-3B-Instruct** with **Group Relative Policy Optimization (GRPO)** and a **LoRA** adapter so it reliably counts the occurrences of a letter in a word — a task LLMs often fail because of tokenization.

## Approach

1. **Model setup** — 4-bit quantized Qwen2.5-3B-Instruct with a rank-64 LoRA adapter on all seven attention and MLP projection layers (~120M trainable parameters, 3.7% of the model)
2. **Baseline** — one-shot Chain-of-Thought prompt: spell the word, check each letter, keep a running count, state the answer
3. **Reward design** — five reward functions (numbering, spelling, running count, output format, answer correctness), each validated before training
4. **Training** — 100 GRPO steps (~23 minutes on a single T4 GPU), monitored with a rolling-average reward plot
5. **Evaluation** — base vs. fine-tuned comparison and a catastrophic-forgetting check

## Results

| Metric | Before | After |
|---|---|---|
| Answer correctness (rolling avg.) | ~53% | ~88% |

The fine-tuned model counts letters correctly where the base model fails, and general knowledge was retained.

## Files

- `gen_ai_fundamentals_project_starter.ipynb` — the complete notebook with all training and evaluation outputs

## Tech stack

Python · Hugging Face TRL (GRPOTrainer) · PEFT / LoRA · Unsloth · vLLM · PyTorch
