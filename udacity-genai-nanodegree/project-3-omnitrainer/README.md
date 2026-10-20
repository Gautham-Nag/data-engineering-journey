# Project 3 — OmniTrainer: Multimodal Customer Service Trainer

An AI-powered training app for customer service agents. Trainees chat with a simulated angry customer (played by an LLM) who bought an ACME Power Widget Pro that stopped working. Every message and file the trainee sends is moderated before it reaches the customer.

## Architecture

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

## What was built

- **Structured moderation models** (`multimodal_moderation/types/moderation_result.py`) — Pydantic result types with a shared `rationale` and modality-specific boolean flags
- **Moderation agents** (`multimodal_moderation/agents/`) — Google Gemini via Pydantic AI; images and media sent as `BinaryContent`
- **Gradio chat app** (`multimodal_moderation/gradio_app.py`) — multimodal input, live moderation feedback panel, flagged content never sent to the customer agent
- **FastAPI backend** (`multimodal_moderation/fastapi_app.py`) — authenticated REST endpoints wrapping the agents
- **Observability** (`multimodal_moderation/tracing.py`) — `conversation` (with `session.id`), `chat_turn`, `moderate_*` and `feedback` spans in Arize Phoenix
- **Evaluation suite** (`evals/`) — Pydantic Evals with rule-based flag checks and an LLM-as-a-judge for rationale quality

## Results

| Check | Result |
|---|---|
| Unit tests | 45 / 45 passed |
| Text eval | 100% |
| Image eval | 83.3% |
| Audio eval | 80% |
| Video eval | 75% |

The eval misses (a low-quality image and a video with a face judged acceptable) show where the moderation prompts need more representative examples. Full test output, eval output and screenshots are in `RUN_EVIDENCE.pdf`.

## Running it

```bash
uv sync
cp env.example .env   # add your own GEMINI_API_KEY and a USER_API_KEY
uv run multimodal-moderation
```

Chat app: `http://localhost:7860` · API docs: `http://localhost:8000/docs` · Phoenix: `http://localhost:6006/projects`

## Tech stack

Python · Google Gemini · Pydantic AI · Gradio · FastAPI · OpenTelemetry · Arize Phoenix · Pydantic Evals · pytest · uv
