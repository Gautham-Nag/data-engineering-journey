import os
import re
import chromadb
from chromadb.config import Settings
from typing import Dict, List, Optional
from pathlib import Path
from openai import OpenAI

# Must match the model used by embedding_pipeline.py. The pipeline also stores
# the model name in the collection metadata, which takes priority if present.
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# Longest document text (in characters) included in the LLM context.
MAX_DOC_CHARS = 1500

# Accepted spellings of each mission, mapped to the value stored in metadata.
MISSION_ALIASES = {
    "apollo11": "apollo_11",
    "apollo13": "apollo_13",
    "challenger": "challenger",
}


def _get_openai_client() -> OpenAI:
    """Create an OpenAI client from environment variables.

    chat.py stores the key in CHROMA_OPENAI_API_KEY; OPENAI_API_KEY is used as
    a fallback (e.g. when testing from the terminal). Udacity/Vocareum keys
    (starting with "voc-") are routed to Vocareum's server.
    """
    api_key = os.getenv("CHROMA_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No OpenAI API key found. Set OPENAI_API_KEY first.")
    base_url = os.getenv("OPENAI_BASE_URL")
    if not base_url and api_key.startswith("voc-"):
        base_url = "https://openai.vocareum.com/v1"
    return OpenAI(api_key=api_key, base_url=base_url)


def _normalize_mission(mission: str) -> str:
    """Turn 'Apollo 11', 'apollo11' or 'apollo_11' into the stored value 'apollo_11'."""
    key = re.sub(r"[^a-z0-9]", "", mission.lower())
    return MISSION_ALIASES.get(key, mission)


def discover_chroma_backends() -> Dict[str, Dict[str, str]]:
    """Discover available ChromaDB backends in the project directory"""
    backends = {}
    current_dir = Path(".")

    # Look for ChromaDB directories
    # Create list of directories that match specific criteria (directory type and name pattern)
    chroma_dirs = [
        d for d in current_dir.iterdir()
        if d.is_dir() and "chroma" in d.name.lower()
    ]

    # Loop through each discovered directory
    for chroma_dir in chroma_dirs:
        # Wrap connection attempt in try-except block for error handling
        try:
            # Initialize database client with directory path and configuration settings
            client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False),
            )

            # Retrieve list of available collections from the database
            collections = client.list_collections()

            # Loop through each collection found
            for col in collections:
                # Newer Chroma versions return names, older ones return objects
                collection_name = col if isinstance(col, str) else col.name

                # Create unique identifier key combining directory and collection names
                key = f"{chroma_dir.name}::{collection_name}"

                # Get document count with fallback for unsupported operations
                try:
                    count = client.get_collection(collection_name).count()
                except Exception:
                    count = "unknown"

                # Build information dictionary
                backends[key] = {
                    "directory": str(chroma_dir),               # directory path as string
                    "collection_name": collection_name,         # collection name
                    "display_name": f"{collection_name} ({chroma_dir.name}) - {count} chunks",
                    "count": str(count),
                }

        # Handle connection or access errors gracefully
        except Exception as e:
            # Create fallback entry for inaccessible directories
            error_text = str(e)
            if len(error_text) > 50:
                error_text = error_text[:50] + "..."
            backends[f"{chroma_dir.name}::error"] = {
                "directory": str(chroma_dir),
                "collection_name": "",
                "display_name": f"{chroma_dir.name} (error: {error_text})",
                "count": "0",
            }

    # Return complete backends dictionary with all discovered collections
    return backends


def initialize_rag_system(chroma_dir: str, collection_name: str):
    """Initialize the RAG system with specified backend (cached for performance)

    Returns a tuple (collection, success, error_message), as chat.py expects.
    """
    try:
        # Create a chromadb PersistentClient
        client = chromadb.PersistentClient(
            path=chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        # Return the collection with the collection_name
        collection = client.get_collection(collection_name)
        return collection, True, None
    except Exception as e:
        return None, False, str(e)


def retrieve_documents(collection, query: str, n_results: int = 3,
                       mission_filter: Optional[str] = None) -> Optional[Dict]:
    """Retrieve relevant documents from ChromaDB with optional filtering"""
    if collection is None or not query or not query.strip():
        return None

    # Initialize filter variable to None (represents no filtering)
    where_filter = None

    # Check if filter parameter exists and is not set to "all" or equivalent
    if mission_filter and mission_filter.strip().lower() not in ("all", "all missions", "none", ""):
        # Create filter dictionary with appropriate field-value pairs
        where_filter = {"mission": _normalize_mission(mission_filter)}

    # Embed the user question with the same OpenAI model used for the documents
    embedding_model = (collection.metadata or {}).get("embedding_model", DEFAULT_EMBEDDING_MODEL)
    client = _get_openai_client()
    query_embedding = client.embeddings.create(
        model=embedding_model,
        input=[query],
    ).data[0].embedding

    # Execute database query (results come back sorted by similarity, best first)
    results = collection.query(
        query_embeddings=[query_embedding],   # search query as an embedding
        n_results=n_results,                  # maximum number of results
        where=where_filter,                   # None = no filtering
        include=["documents", "metadatas", "distances"],
    )

    # Return query results to caller
    return results


def format_context(documents: List[str], metadatas: List[Dict]) -> str:
    """Format retrieved documents into context"""
    if not documents:
        return ""

    # Initialize list with header text for context section
    context_parts = ["The following excerpts were retrieved from NASA mission archives:", ""]

    seen_texts = set()
    source_number = 0

    # Loop through paired documents and their metadata using enumeration
    for i, (doc, meta) in enumerate(zip(documents, metadatas or [{}] * len(documents))):
        if not doc or not doc.strip():
            continue

        # Skip repeated snippets (overlapping chunks can produce duplicates)
        normalized = " ".join(doc.split()).lower()
        if normalized in seen_texts:
            continue
        seen_texts.add(normalized)
        source_number += 1

        meta = meta or {}
        # Extract mission information from metadata with fallback value
        mission = meta.get("mission", "unknown_mission")
        # Clean up mission name formatting (replace underscores, capitalize)
        mission = mission.replace("_", " ").title()
        # Extract source information from metadata with fallback value
        source = meta.get("source") or meta.get("file_path") or "unknown source"
        # Extract category information from metadata with fallback value
        category = meta.get("document_category") or meta.get("category") or "general"
        # Clean up category name formatting (replace underscores, capitalize)
        category = category.replace("_", " ").title()

        # Create formatted source header with index number and extracted information
        header = f"[Source {source_number}] Mission: {mission} | Category: {category} | File: {source}"
        # Add source header to context parts list
        context_parts.append(header)

        # Check document length and truncate if necessary
        text = doc.strip()
        if len(text) > MAX_DOC_CHARS:
            text = text[:MAX_DOC_CHARS] + "... [truncated]"
        # Add truncated or full document content to context parts list
        context_parts.append(text)
        context_parts.append("-" * 60)

    # Join all context parts with newlines and return formatted string
    return "\n".join(context_parts)