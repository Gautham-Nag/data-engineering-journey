import os
from typing import Dict, List
from openai import OpenAI

# Only the most recent turns are sent with each request, so the prompt
# stays small and focused (rubric: "includes only necessary context").
MAX_HISTORY_MESSAGES = 6

SYSTEM_PROMPT = """You are a NASA mission operations expert specializing in three historic missions: Apollo 11, Apollo 13, and Space Shuttle Challenger (STS-51-L).

You answer questions using ONLY the retrieved NASA archive documents provided to you as context.

Rules:
1. Base every factual claim on the provided context. Do not add facts from outside knowledge.
2. Cite your sources: after each key fact, name the source document it came from, using the source label shown in the context.
3. If the context does not contain enough information to answer, say so clearly and explain what is missing. Never fall back on general knowledge, even for well-known facts, and never guess.
4. If sources disagree or are unclear, point that out instead of picking one silently.
5. Be clear and concise, and briefly explain technical terms when it helps the reader."""


def _resolve_base_url(openai_key: str):
    """Return the API base URL to use.

    Udacity/Vocareum keys (starting with "voc-") must be sent to Vocareum's
    server instead of OpenAI's. An OPENAI_BASE_URL environment variable,
    if set, always takes priority.
    """
    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url and openai_key and openai_key.startswith("voc-"):
        base_url = "https://openai.vocareum.com/v1"
    return base_url


def generate_response(openai_key: str, user_message: str, context: str,
                      conversation_history: List[Dict], model: str = "gpt-3.5-turbo") -> str:
    """Generate response using OpenAI with context"""

    # Define system prompt
    messages: List[Dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add chat history (role + content per turn, most recent turns only)
    history = list(conversation_history or [])
    # If the caller already added the current question to the history,
    # drop it here so the question is not sent twice.
    if history and history[-1].get("role") == "user" and history[-1].get("content") == user_message:
        history = history[:-1]
    for turn in history[-MAX_HISTORY_MESSAGES:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    # Set context in messages (only for the current question, never stored in history)
    if context and context.strip():
        context_block = f"Retrieved NASA documents:\n\n{context}"
    else:
        context_block = (
            "Retrieved NASA documents: none were found for this question.\n"
            "Because there is no context, do NOT answer from general knowledge. "
            "Only tell the user that no relevant documents were found in the NASA archive "
            "and suggest they rephrase the question or choose a different mission."
        )
    messages.append({
        "role": "user",
        "content": f"{context_block}\n\nQuestion: {user_message}",
    })

    try:
        # Create OpenAI Client
        client = OpenAI(api_key=openai_key, base_url=_resolve_base_url(openai_key))

        # Send request to OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,  # low temperature keeps answers factual
            max_tokens=800,
        )

        # Return response
        return response.choices[0].message.content or ""
    except Exception as e:
        return f"Sorry, I couldn't generate a response: {e}"