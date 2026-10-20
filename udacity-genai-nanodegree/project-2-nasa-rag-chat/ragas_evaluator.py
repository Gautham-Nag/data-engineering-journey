"""
RAGAS evaluation for the NASA RAG chat system.

Real-time use (called by chat.py after every answer):
    evaluate_response_quality(question, answer, contexts)

Batch use (from the terminal, scores every question in the test set):
    python ragas_evaluator.py
    python ragas_evaluator.py --dataset evaluation_dataset.txt --n-results 5

Metrics:
    Always computed:          faithfulness, response_relevancy, context_precision
    With an expected answer:  bleu_score, rouge_score
    With reference contexts:  context_precision_with_reference
"""

import os
import json
import math
import asyncio
import argparse
import statistics
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

# RAGAS imports
try:
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas import SingleTurnSample
    from ragas.metrics import BleuScore, NonLLMContextPrecisionWithReference, ResponseRelevancy, Faithfulness, RougeScore
    from ragas import evaluate
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False

# Optional extra metric: judges whether the retrieved chunks were useful,
# without needing a hand-written reference answer.
try:
    from ragas.metrics import LLMContextPrecisionWithoutReference
except ImportError:
    LLMContextPrecisionWithoutReference = None

EVALUATOR_MODEL = "gpt-3.5-turbo"
EVALUATOR_EMBEDDING_MODEL = "text-embedding-3-small"
DATASET_FIELDS = ("CATEGORY", "MISSION", "QUESTION", "EXPECTED")


def _openai_settings() -> Tuple[str, Optional[str]]:
    """Return (api_key, base_url) from the environment.

    chat.py stores the key in CHROMA_OPENAI_API_KEY; OPENAI_API_KEY is the
    fallback when running from the terminal. Udacity/Vocareum keys
    ("voc-...") are routed to Vocareum's server.
    """
    api_key = os.getenv("CHROMA_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY first.")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url and api_key.startswith("voc-"):
        base_url = "https://openai.vocareum.com/v1"
    return api_key, base_url


def _validate_inputs(question: Any, answer: Any, contexts: Any) -> Tuple[List[str], Optional[str]]:
    """Check the (question, answer, contexts) triple.

    Returns (clean_contexts, error_message). error_message is None when valid.
    """
    if not isinstance(question, str) or not question.strip():
        return [], "Cannot evaluate: the question is empty or not text."
    if not isinstance(answer, str) or not answer.strip():
        return [], "Cannot evaluate: the answer is empty or not text."
    if contexts is None or not isinstance(contexts, (list, tuple)):
        return [], "Cannot evaluate: contexts must be a list of text passages."
    clean_contexts = [c for c in contexts if isinstance(c, str) and c.strip()]
    if not clean_contexts:
        return [], "Cannot evaluate: no documents were retrieved for this question."
    return clean_contexts, None


def _run_metric(metric, sample) -> float:
    """Score one sample with one metric (sync wrapper around the async API)."""
    if hasattr(metric, "single_turn_score"):
        return metric.single_turn_score(sample)
    return asyncio.run(metric.single_turn_ascore(sample))


def evaluate_response_quality(question: str, answer: str, contexts: List[str],
                              reference: Optional[str] = None,
                              reference_contexts: Optional[List[str]] = None) -> Dict[str, float]:
    """Evaluate response quality using RAGAS metrics

    Args:
        question: The user's question
        answer: The model's answer
        contexts: The retrieved document chunks given to the model
        reference: Optional expected answer (enables BLEU and ROUGE)
        reference_contexts: Optional ideal chunks (enables reference-based context precision)

    Returns:
        {metric_name: score between 0 and 1}. Metrics that fail are reported as
        "<metric_name>_error": message. If nothing can be scored, returns
        {"error": message} instead of raising.
    """
    if not RAGAS_AVAILABLE:
        return {"error": "RAGAS not available"}

    # Handle empty or malformed inputs with a clear message
    clean_contexts, error = _validate_inputs(question, answer, contexts)
    if error:
        return {"error": error}

    try:
        api_key, base_url = _openai_settings()

        # Create evaluator LLM with model gpt-3.5-turbo
        evaluator_llm = LangchainLLMWrapper(ChatOpenAI(
            model=EVALUATOR_MODEL,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
        ))

        # Create evaluator_embeddings with model text-embedding-3-small
        evaluator_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
            model=EVALUATOR_EMBEDDING_MODEL,
            api_key=api_key,
            base_url=base_url,
            check_embedding_ctx_length=False,
        ))
    except Exception as e:
        return {"error": f"Could not set up the evaluator: {e}"}

    # Define an instance for each metric to evaluate
    metric_factories = {
        "faithfulness": lambda: Faithfulness(llm=evaluator_llm),
        "response_relevancy": lambda: ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
    }
    if LLMContextPrecisionWithoutReference is not None:
        metric_factories["context_precision"] = lambda: LLMContextPrecisionWithoutReference(llm=evaluator_llm)
    if reference and reference.strip():
        metric_factories["bleu_score"] = lambda: BleuScore()
        metric_factories["rouge_score"] = lambda: RougeScore()
    if reference_contexts:
        metric_factories["context_precision_with_reference"] = lambda: NonLLMContextPrecisionWithReference()

    sample = SingleTurnSample(
        user_input=question,
        response=answer,
        retrieved_contexts=clean_contexts,
        reference=reference if reference and reference.strip() else None,
        reference_contexts=list(reference_contexts) if reference_contexts else None,
    )

    # Evaluate the response using the metrics (one failing metric does not stop the others)
    results: Dict[str, Any] = {}
    for name, make_metric in metric_factories.items():
        try:
            value = float(_run_metric(make_metric(), sample))
            if math.isnan(value):
                results[f"{name}_error"] = "metric returned no score"
                continue
            results[name] = max(0.0, min(1.0, value))
        except Exception as e:
            results[f"{name}_error"] = str(e)[:200]

    # Return the evaluation results
    if not any(isinstance(v, float) for v in results.values()):
        first_error = next(iter(results.values()), "unknown error")
        return {"error": f"All metrics failed: {first_error}"}
    return results


# ---------------------------------------------------------------------------
# Batch evaluation
# ---------------------------------------------------------------------------

def load_evaluation_dataset(path: str) -> List[Dict[str, str]]:
    """Load test questions from evaluation_dataset.txt.

    Format: blocks of "FIELD: value" lines separated by blank lines.
    Fields: CATEGORY, MISSION, QUESTION (required), EXPECTED.
    Lines starting with # are comments.
    """
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    entries: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    lines = dataset_path.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if line.startswith("#"):
            continue
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        if ":" not in line:
            raise ValueError(f"{dataset_path.name}, line {line_number}: expected 'FIELD: value'")
        key, value = line.split(":", 1)
        key = key.strip().upper()
        if key not in DATASET_FIELDS:
            raise ValueError(f"{dataset_path.name}, line {line_number}: unknown field '{key}'. "
                             f"Use one of {', '.join(DATASET_FIELDS)}")
        current[key.lower()] = value.strip()
    if current:
        entries.append(current)

    for number, entry in enumerate(entries, start=1):
        if not entry.get("question"):
            raise ValueError(f"{dataset_path.name}: entry {number} has no QUESTION")
    if not entries:
        raise ValueError(f"{dataset_path.name} contains no questions")
    return entries


def run_batch_evaluation(dataset_path: str, chroma_dir: str, collection_name: str,
                         n_results: int = 3, model: str = "gpt-3.5-turbo",
                         output_path: str = "evaluation_results.json") -> Dict[str, Any]:
    """Run every test question through retrieval -> generation -> RAGAS scoring,
    print a per-question summary and an aggregate for each metric."""
    import rag_client
    import llm_client

    api_key, _ = _openai_settings()
    entries = load_evaluation_dataset(dataset_path)
    print(f"Loaded {len(entries)} questions from {dataset_path}")

    collection, ok, error = rag_client.initialize_rag_system(chroma_dir, collection_name)
    if not ok:
        raise RuntimeError(f"Could not open ChromaDB collection: {error}")

    per_question = []
    for number, entry in enumerate(entries, start=1):
        question = entry["question"]
        mission = entry.get("mission") or "all"
        print("\n" + "=" * 70)
        print(f"[{number}/{len(entries)}] ({entry.get('category', 'general')}, mission: {mission})")
        print(f"Q: {question}")

        results = rag_client.retrieve_documents(collection, question, n_results, mission_filter=mission)
        documents = results["documents"][0] if results and results.get("documents") else []
        metadatas = results["metadatas"][0] if results and results.get("metadatas") else []
        context = rag_client.format_context(documents, metadatas)
        answer = llm_client.generate_response(api_key, question, context, [], model)
        scores = evaluate_response_quality(question, answer, documents, reference=entry.get("expected"))

        short_answer = answer if len(answer) <= 300 else answer[:300] + "..."
        print(f"A: {short_answer}")
        print("Scores:")
        for name, value in scores.items():
            shown = f"{value:.3f}" if isinstance(value, float) else value
            print(f"  {name}: {shown}")

        per_question.append({
            "category": entry.get("category", ""),
            "mission": mission,
            "question": question,
            "expected": entry.get("expected", ""),
            "answer": answer,
            "scores": scores,
        })

    # Aggregate: mean / min / max for each metric across all questions
    metric_names = sorted({name for row in per_question
                           for name, value in row["scores"].items() if isinstance(value, float)})
    aggregate = {}
    for name in metric_names:
        values = [row["scores"][name] for row in per_question if isinstance(row["scores"].get(name), float)]
        aggregate[name] = {
            "mean": round(statistics.mean(values), 3),
            "min": round(min(values), 3),
            "max": round(max(values), 3),
            "count": len(values),
        }

    print("\n" + "=" * 70)
    print("AGGREGATE RESULTS")
    print("=" * 70)
    print(f"{'metric':<28}{'mean':>8}{'min':>8}{'max':>8}{'n':>5}")
    for name, values in aggregate.items():
        print(f"{name:<28}{values['mean']:>8.3f}{values['min']:>8.3f}{values['max']:>8.3f}{values['count']:>5}")

    report = {"per_question": per_question, "aggregate": aggregate}
    Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nFull results saved to {output_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description="Batch RAGAS evaluation for the NASA RAG system")
    parser.add_argument("--dataset", default="evaluation_dataset.txt", help="Test question file")
    parser.add_argument("--chroma-dir", default="./chroma_db_openai", help="ChromaDB directory")
    parser.add_argument("--collection-name", default="nasa_space_missions_text", help="Collection name")
    parser.add_argument("--n-results", type=int, default=3, help="Chunks retrieved per question")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="Model used to generate answers")
    parser.add_argument("--output", default="evaluation_results.json", help="Where to save full results")
    args = parser.parse_args()

    if not RAGAS_AVAILABLE:
        parser.error("RAGAS is not available. Install it with: pip install -r requirements.txt")
    try:
        run_batch_evaluation(args.dataset, args.chroma_dir, args.collection_name,
                             args.n_results, args.model, args.output)
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()