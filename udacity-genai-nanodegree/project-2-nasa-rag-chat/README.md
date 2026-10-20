# NASA Mission Intelligence: RAG-Based Chat System

A Retrieval-Augmented Generation (RAG) chat system that answers questions about Apollo 11, Apollo 13, and Space Shuttle Challenger (STS-51-L) using NASA's own mission transcripts and technical documents, with real-time answer quality scoring using RAGAS.

## Project Structure

```
/
├── chat.py                  # Streamlit chat app (mission selector, sources, live scores)
├── embedding_pipeline.py    # Chunks NASA text files, embeds them with OpenAI, stores them in ChromaDB
├── rag_client.py            # Finds the ChromaDB collection, semantic search, context formatting
├── llm_client.py            # OpenAI chat client: NASA-expert system prompt, conversation history
├── ragas_evaluator.py       # RAGAS metrics (real-time and batch evaluation)
├── evaluation_dataset.txt   # 7 test questions with expected answers
├── evaluation_results.json  # Output of the last batch evaluation
├── setup_env.sh             # Reinstalls packages and applies the RAGAS 0.4.3 fix
├── REPORT.md                # Challenges faced, solutions, and results
├── requirements.txt
└── data_text/               # NASA source documents (apollo11/, apollo13/, challenger/)
```

## Setup

1. **Install packages and apply the RAGAS fix** (run again after every workspace restart):
   ```bash
   bash setup_env.sh
   ```
   RAGAS 0.4.3 imports `ChatVertexAI` from an old `langchain-community` path. The script installs `requirements.txt` and points those imports to `langchain_google_vertexai`, then prints `RAGAS OK: 0.4.3`.

2. **Set your OpenAI API key** (never commit it):
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```
   Udacity/Vocareum keys (starting with `voc-`) are detected automatically and sent to `https://openai.vocareum.com/v1`. To use a different server, set `OPENAI_BASE_URL`.

## How to Run

### 1. Build the vector database

```bash
python embedding_pipeline.py --chunk-size 1500 --chunk-overlap 300
```

| Option | Default | Purpose |
|---|---|---|
| `--data-path` | `./data_text` | Folder containing `apollo11/`, `apollo13/`, `challenger/` |
| `--chunk-size` | `500` | Maximum chunk length in characters |
| `--chunk-overlap` | `100` | Characters shared by consecutive chunks |
| `--chroma-dir` | `./chroma_db_openai` | Where ChromaDB is saved |
| `--collection-name` | `nasa_space_missions_text` | Collection name |
| `--embedding-model` | `text-embedding-3-small` | OpenAI embedding model |
| `--batch-size` | `50` | Chunks embedded per OpenAI request |
| `--update-mode` | `skip` | `skip` existing chunks, `update` them, or `replace` all chunks of each file |
| `--stats-only` | | Print collection size and breakdowns, then exit |
| `--test-query` | | Run a sample search after processing |

Check what is stored:

```bash
python embedding_pipeline.py --stats-only
```

### 2. Start the chat app

```bash
streamlit run chat.py
```

In the sidebar you can choose the collection, model, number of documents to retrieve, and a **mission filter** (All missions, Apollo 11, Apollo 13, Challenger). Each answer shows its sources, and the sidebar shows quality scores for the latest answer.

### 3. Run the batch evaluation

```bash
python ragas_evaluator.py --dataset evaluation_dataset.txt
```

This runs every question in [`evaluation_dataset.txt`](evaluation_dataset.txt) through retrieval, generation, and scoring. It prints scores for each question, then the mean, min, and max for each metric, and saves everything to `evaluation_results.json`. Options: `--n-results`, `--model`, `--chroma-dir`, `--collection-name`, `--output`.

## Design Choices

**Chunking.** Text is split into chunks of at most `chunk_size` characters. The splitter prefers to end a chunk at a paragraph or sentence break (if that still leaves at least half a chunk), and every chunk starts exactly `chunk_overlap` characters before the previous one ended. 1500/300 gave clearly better answers than the 500/100 default (see `REPORT.md`).

**Metadata.** Each chunk stores `source`, `file_path`, `mission` (`apollo_11`, `apollo_13`, `challenger`), `data_type`, `document_category`, chunk position (`chunk_index`, `start_char`, `end_char`), and the chunking settings used. Chunk IDs follow `mission_source_fingerprint_chunk_0001`; the short fingerprint of the file path keeps IDs unique when two folders contain files with the same name.

**Retrieval.** The question is embedded with the same OpenAI model as the documents (the model name is stored in the collection metadata) and the closest `k` chunks are returned, optionally filtered by mission through ChromaDB metadata filtering. The context sent to the LLM labels each chunk with `[Source N] Mission | Category | File`, separates chunks clearly, removes duplicate snippets, and keeps Chroma's best-first order.

**Generation.** The system prompt makes the model a NASA mission expert that answers only from the retrieved documents, cites sources, and says clearly when the context is not enough. Only the last 6 conversation turns are sent, and the retrieved context is attached to the current question only (it is never stored in history).

**Evaluation.** Every chat answer is scored with **Faithfulness**, **Response Relevancy**, and **Context Precision** (LLM-based, no reference needed). Batch evaluation also computes **BLEU** and **ROUGE** against the expected answers. Empty or malformed inputs return a clear error message instead of crashing, and a metric that fails is reported without stopping the others.

## Evaluation Dataset

[`evaluation_dataset.txt`](evaluation_dataset.txt) contains 7 questions across all six categories: overview, emergency, disaster analysis, crew, technical, and timeline. Each entry has a `CATEGORY`, `MISSION` (used as the retrieval filter), `QUESTION`, and `EXPECTED` answer, in blocks separated by blank lines.

## Results (batch evaluation, 1500/300 chunks, k = 3, gpt-3.5-turbo)

| Metric | Mean | Min | Max |
|---|---|---|---|
| Context precision | 0.869 | 0.500 | 1.000 |
| Response relevancy | 0.870 | 0.553 | 1.000 |
| Faithfulness | 0.714 | 0.000 | 1.000 |
| ROUGE | 0.335 | 0.113 | 0.612 |
| BLEU | 0.155 | 0.019 | 0.595 |

See `REPORT.md` for discussion.