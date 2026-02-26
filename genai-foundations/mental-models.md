# GenAI Foundations — Engineering Mental Models

This document captures core system-level mental models required to design, evaluate, and deploy enterprise-grade Generative AI systems.

The focus is not definitions, but decision intelligence.

---

## 1️⃣ Tokenization — Cost & Context Control Layer

**What it is**
Process of converting raw text into tokens that transformers operate on.

**Why it matters**
- Token count drives API cost.
- Token count impacts latency.
- Context window is a hard architectural constraint.

**Production Insight**
Chunking strategy in RAG must be designed based on token size, not word count.

**Failure Mode**
Poor chunking → irrelevant retrieval → hallucination amplification.

---

## 2️⃣ Foundation Model vs Adaptation Layer

**Foundation Model**
- Trained on massive, diverse corpus.
- General reasoning ability.
- Not domain-aware by default.

**Adaptation happens through:**
- Prompt engineering
- RAG (external knowledge injection)
- Fine-tuning (behavior specialization)
- RLHF (alignment)

**Engineering Insight**
Enterprise intelligence is built on top of foundation models — not by retraining them.

---

## 3️⃣ RAG (Retrieval-Augmented Generation)

**Purpose**
Inject external knowledge at runtime without modifying model weights.

**When to Use**
- Knowledge changes frequently.
- Documents are large and dynamic.
- Factual grounding is required.
- Compliance requires traceability.

**Tradeoff**
Answer quality depends on:
- Chunking strategy
- Embedding quality
- Retrieval ranking

**Production Insight**
RAG is often preferred over fine-tuning in enterprise systems due to agility and lower operational risk.

---

## 4️⃣ Fine-Tuning — Behavioral Specialization

**Purpose**
Adjust model behavior, style, and task performance using curated data.

**When to Use**
- Output format must be consistent (e.g., SQL generation patterns).
- Domain reasoning must be deeply internalized.
- Prompt-only control is insufficient.

**Tradeoff**
- Higher cost.
- Slower iteration cycle.
- Governance complexity increases.

---

## 5️⃣ RLHF — Alignment Mechanism

**Purpose**
Optimize model outputs toward human preference.

Improves:
- Helpfulness
- Safety
- Tone control
- Brand alignment

**Does NOT**
- Add new knowledge.
- Replace retrieval mechanisms.

**Production Insight**
Critical for large-scale public-facing deployment.

---

## 6️⃣ Transformer Architecture — Scaling Engine

Modern LLMs are based on transformers using self-attention.

**Why it matters**
- Handles long-range dependencies.
- Enables parallel training.
- Scales effectively with data and compute.

**Engineering Insight**
Understanding transformer limits helps in context window planning and memory optimization.

---

## 7️⃣ Model Size & Infrastructure Awareness

Model size ≈ Parameters × Bytes per parameter

Example:
- 70B parameters (FP16) ≈ ~140 GB weight size.

**Production Implications**
- GPU memory requirements
- Quantization tradeoffs
- Inference latency
- Cost per request

---

## 8️⃣ Prompt Engineering — Fastest Control Lever

Crafting structured prompts to guide output behavior.

**Use When**
- Rapid experimentation needed.
- Behavior tuning without retraining.
- Low-cost iteration required.

**Limitation**
Cannot permanently encode domain knowledge.

---

## 9️⃣ Zero-shot / One-shot / Few-shot

- Zero-shot: Instruction only.
- One-shot: Single example.
- Few-shot: Small example set to guide pattern learning.

**Engineering Insight**
Few-shot prompting can sometimes reduce need for fine-tuning.

---

## 10️⃣ Model Ecosystem Awareness

Understand model providers and their positioning:

- OpenAI → GPT series
- Meta → LLaMA
- Google → Gemini
- Anthropic → Claude

**Architectural Consideration**
Model selection depends on:
- Context window
- Cost
- Latency
- Compliance constraints
- Deployment environment

---

# Guiding Principle

Enterprise GenAI systems are built by combining:

Foundation Model  
+ Retrieval Layer  
+ Prompt Layer  
+ Orchestration  
+ Evaluation  
+ Governance  

Not by training models from scratch.
