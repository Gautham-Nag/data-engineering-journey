# Generative AI Nanodegree — Project Portfolio

![Udacity](https://img.shields.io/badge/Udacity-Generative_AI-02B3E4?logo=udacity&logoColor=white)
![Projects](https://img.shields.io/badge/Projects-3%2F3_Passed-brightgreen)
![Certificate](https://img.shields.io/badge/Certificate-Verified-brightgreen)

This repository contains the three project submissions completed as part of the **Udacity Generative AI Nanodegree** (completed October 2026). The program covers the generative AI engineering lifecycle — from fine-tuning LLMs with reinforcement learning, to retrieval-augmented generation, to multimodal AI agents with evaluation and observability.

---

## 📋 Program Overview

| Domain | Technologies Covered |
|---|---|
| LLM Fine-Tuning | Qwen2.5-3B-Instruct, GRPO, LoRA / PEFT, Hugging Face TRL, Unsloth, vLLM |
| Retrieval-Augmented Generation | ChromaDB, OpenAI embeddings, metadata filtering, Streamlit |
| Multimodal AI Agents | Google Gemini, Pydantic AI, structured outputs, Gradio, FastAPI |
| Evaluation & Observability | RAGAS, BLEU / ROUGE, Pydantic Evals, LLM-as-a-judge, OpenTelemetry, Arize Phoenix |

---

## 🗂️ Projects

### Project 1 — Teaching an LLM to Reason Step-by-Step with GRPO

**Objective:** Teach an instruction-tuned LLM to reliably count the occurrences of a letter in a word — a task LLMs typically fail because of tokenization — using reinforcement learning.

**What was built:**

- **LoRA adapter on Qwen2.5-3B-Instruct** — 4-bit quantized base model with a rank-64 LoRA adapter targeting all seven attention and MLP projection layers (~120M trainable parameters, 3.7% of the model)
- **Chain-of-Thought baseline** — one-shot system prompt that makes the model spell the word, check each letter, keep a running count and state the answer
- **Five reward functions** — numbering, spelling, running count, output format and answer correctness, each validated against test cases before training
- **GRPO training run** — 100 steps (~23 minutes on a single T4 GPU) with reward monitoring via a rolling-average plot

**Results:**

- Answer correctness rose from **~53% to ~88%** over 100 training steps
- Fine-tuned model counts letters correctly where the base model fails
- A catastrophic-forgetting check confirmed general knowledge was retained

**Tech stack:** Python, Hugging Face TRL (GRPOTrainer), PEFT / LoRA, Unsloth, vLLM, PyTorch

---

### Project 2 — NASA Mission Intelligence: RAG-Based Chat System

**Objective:** Build a question-answering system over NASA mission documents that gives grounded, cited answers and measures its own answer quality.

**What was built:**

- **Embedding pipeline** (`embedding_pipeline.py`) — configurable chunk size and overlap, per-chunk metadata (source file and mission), persistent ChromaDB storage, `skip` / `update` / `replace` update modes and a `--stats-only` inspection option
- **Retrieval client** (`rag_client.py`) — semantic search with configurable top-k, mission metadata filtering, de-duplicated context with source labels
- **LLM client** (`llm_client.py`) — scoped system prompt (NASA expert, cites sources, says when the context lacks the answer) with conversation history management
- **Evaluator** (`ragas_evaluator.py`) — RAGAS faithfulness and response relevancy plus BLEU and ROUGE, with per-question and aggregate batch results
- **Chat interface** (`chat.py`) — Streamlit app with a mission filter and live answer scoring

**Key design decisions:**

- Re-chunked at 1500 characters / 300 overlap after small default chunks produced unhelpful retrieval context
- Added mission-level filtering to prevent cross-mission retrieval errors
- Evaluation dataset of mission questions spanning overview, emergency, crew, technical and timeline categories

**Tech stack:** Python, OpenAI API, ChromaDB, RAGAS, Streamlit

---

### Project 3 — OmniTrainer: Multimodal Customer Service Trainer

**Objective:** Build an AI-powered training app where trainee customer service agents handle a simulated angry customer, with every outgoing message and file moderated before it reaches the customer.

**Architecture:**

```
Trainee agent (Gradio chat: text, image, video, audio)
        │
        ▼
FastAPI moderation backend
   ├── Text agent   → PII · unfriendly · unprofessional
   ├── Image agent  → PII · disturbing · low quality
   ├── Video agent  → PII · disturbing · low quality
   └── Audio agent  → transcription · PII · unfriendly · unprofessional
        │
        ├── flagged → blocked, rationale shown to trainee
        └── safe    → LLM customer agent (keeps conversation history)

All steps traced with OpenTelemetry → Arize Phoenix
```

**What was built:**

- **Structured moderation models** — Pydantic result types with a shared `rationale` and modality-specific boolean flags
- **Moderation agents** — Google Gemini via Pydantic AI; images and media sent as `BinaryContent`
- **Gradio multimodal chat** — text and file uploads, live moderation feedback panel, flagged content never sent to the customer agent
- **Observability** — `conversation` (with `session.id`), `chat_turn`, `moderate_*` and `feedback` spans in Arize Phoenix
- **Evaluation suite** — Pydantic Evals with rule-based flag checks and an LLM-as-a-judge for rationale quality

**Results:**

- 45 / 45 unit tests passing
- Eval scores: text 100%, image 83.3%, audio 80%, video 75% — the misses (a low-quality image and a video with a face judged acceptable) highlight where the prompts need more representative examples

**Tech stack:** Python, Google Gemini, Pydantic AI, Gradio, FastAPI, OpenTelemetry, Arize Phoenix, Pydantic Evals

---

## 🔭 Next Steps

Ideas for extending these projects, drawn from reviewer feedback:

- **GRPO:** compare LoRA ranks (8–64), try a few-shot baseline, weight the correctness reward higher, extend training and test on out-of-distribution words
- **RAG:** hybrid search (dense vectors + BM25), cross-encoder re-ranking and query rewriting for
