#!/usr/bin/env python3
"""
ChromaDB Embedding Pipeline for NASA Space Mission Data - Text Files Only

This script reads parsed text data from various NASA space mission folders and creates
a permanent ChromaDB collection with OpenAI embeddings for RAG applications.
Optimized to process only text files to avoid duplication with JSON versions.

Supported data sources:
- Apollo 11 extracted data (text files only)
- Apollo 13 extracted data (text files only)
- Apollo 11 Textract extracted data (text files only)
- Challenger transcribed audio data (text files only)

Example usage:
    python embedding_pipeline.py --data-path ./data_text
    python embedding_pipeline.py --chunk-size 800 --chunk-overlap 150 --update-mode replace
    python embedding_pipeline.py --stats-only
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
import openai
from openai import OpenAI
import hashlib
import time
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chroma_embedding_text_only.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ChromaEmbeddingPipelineTextOnly:
    """Pipeline for creating ChromaDB collections with OpenAI embeddings - Text files only"""

    def __init__(self,
                 openai_api_key: str,
                 chroma_persist_directory: str = "./chroma_db",
                 collection_name: str = "nasa_space_missions_text",
                 embedding_model: str = "text-embedding-3-small",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the embedding pipeline

        Args:
            openai_api_key: OpenAI API key
            chroma_persist_directory: Directory to persist ChromaDB
            collection_name: Name of the ChromaDB collection
            embedding_model: OpenAI embedding model to use
            chunk_size: Maximum size of text chunks (in characters)
            chunk_overlap: Overlap between consecutive chunks (in characters)
        """
        # Validate chunking parameters so every chunk is well-defined
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0 or chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be 0 or more and smaller than chunk_size")

        # Initialize OpenAI client
        # Udacity/Vocareum keys (starting with "voc-") must use Vocareum's server.
        self.openai_client = None
        if openai_api_key:
            base_url = os.getenv("OPENAI_BASE_URL")
            if not base_url and openai_api_key.startswith("voc-"):
                base_url = "https://openai.vocareum.com/v1"
            self.openai_client = OpenAI(api_key=openai_api_key, base_url=base_url)

        # Store configuration parameters
        self.chroma_persist_directory = chroma_persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize ChromaDB client (data is saved to disk in chroma_persist_directory)
        self.chroma_client = chromadb.PersistentClient(
            path=chroma_persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Create or get collection. The embedding model name is stored in the
        # collection metadata so rag_client.py embeds questions the same way.
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={
                "embedding_model": embedding_model,
                "description": "NASA mission text chunks (Apollo 11, Apollo 13, Challenger)",
            },
        )
        stored_model = (self.collection.metadata or {}).get("embedding_model")
        if stored_model and stored_model != embedding_model:
            logger.warning(
                f"Collection '{collection_name}' was built with '{stored_model}', "
                f"but '{embedding_model}' was requested. Mixing models gives poor search results."
            )
        logger.info(
            f"Using collection '{collection_name}' in '{chroma_persist_directory}' "
            f"({self.collection.count()} chunks currently stored)"
        )

    @staticmethod
    def _file_hash(file_path: Path) -> str:
        """Short, stable fingerprint of a file's full path (keeps IDs unique when
        two folders contain files with the same name)."""
        return hashlib.md5(str(file_path.resolve()).encode("utf-8")).hexdigest()[:8]

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Split text into chunks with metadata

        Every chunk is at most chunk_size characters long, and each chunk starts
        exactly chunk_overlap characters before the previous chunk ended.

        Args:
            text: Text to chunk
            metadata: Base metadata for the text

        Returns:
            List of (chunk_text, chunk_metadata) tuples
        """
        if not text or not text.strip():
            return []

        # Handle short texts that don't need chunking
        if len(text) <= self.chunk_size:
            chunk_metadata = dict(metadata)
            chunk_metadata.update({
                'chunk_index': 0,
                'total_chunks': 1,
                'start_char': 0,
                'end_char': len(text),
                'chunk_length': len(text),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
            })
            return [(text, chunk_metadata)]

        # Implement chunking logic with overlap
        text_length = len(text)
        # A sentence break is only used if the chunk is still reasonably long.
        # It must also be longer than the overlap, so the loop always moves forward.
        min_chunk_length = max(self.chunk_overlap + 1, self.chunk_size // 2)
        boundaries = ("\n\n", ". ", "? ", "! ", "\n")

        spans = []
        start = 0
        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # Try to break at sentence boundaries
            if end < text_length:
                window = text[start:end]
                best_cut = -1
                for boundary in boundaries:
                    pos = window.rfind(boundary)
                    if pos != -1:
                        cut = pos + len(boundary)
                        if cut >= min_chunk_length and cut > best_cut:
                            best_cut = cut
                if best_cut != -1:
                    end = start + best_cut

            spans.append((start, end))
            if end >= text_length:
                break
            # Next chunk starts chunk_overlap characters before this one ended
            start = end - self.chunk_overlap

        # Create metadata for each chunk
        chunks = []
        for start, end in spans:
            chunk = text[start:end]
            if not chunk.strip():
                continue
            chunks.append((chunk, start, end))

        results = []
        for index, (chunk, start, end) in enumerate(chunks):
            chunk_metadata = dict(metadata)
            chunk_metadata.update({
                'chunk_index': index,
                'total_chunks': len(chunks),
                'start_char': start,
                'end_char': end,
                'chunk_length': len(chunk),
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap,
            })
            results.append((chunk, chunk_metadata))
        return results

    def check_document_exists(self, doc_id: str) -> bool:
        """
        Check if a document with the given ID already exists in the collection

        Args:
            doc_id: Document ID to check

        Returns:
            True if document exists, False otherwise
        """
        try:
            # Query collection for document ID
            result = self.collection.get(ids=[doc_id])
            # Return True if exists, False otherwise
            return len(result.get('ids', [])) > 0
        except Exception as e:
            logger.error(f"Error checking document {doc_id}: {e}")
            return False

    def update_document(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> bool:
        """
        Update an existing document in the collection

        Args:
            doc_id: Document ID to update
            text: New text content
            metadata: New metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get new embedding
            embedding = self.get_embedding(text)

            # Update the document
            self.collection.update(
                ids=[doc_id],
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding]
            )
            logger.debug(f"Updated document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            return False

    def delete_documents_by_source(self, source_pattern: str) -> int:
        """
        Delete all documents from a specific source (useful for re-processing files)

        Args:
            source_pattern: Pattern to match source names

        Returns:
            Number of documents deleted
        """
        try:
            # Get all documents
            all_docs = self.collection.get()

            # Find documents matching the source pattern
            ids_to_delete = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if source_pattern in metadata.get('source', ''):
                    ids_to_delete.append(all_docs['ids'][i])

            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} documents matching source pattern: {source_pattern}")
                return len(ids_to_delete)
            else:
                logger.info(f"No documents found matching source pattern: {source_pattern}")
                return 0

        except Exception as e:
            logger.error(f"Error deleting documents by source: {e}")
            return 0

    def get_file_documents(self, file_path: Path) -> List[str]:
        """
        Get all document IDs for a specific file

        Args:
            file_path: Path to the file

        Returns:
            List of document IDs for the file
        """
        try:
            result = self.collection.get(where={'file_hash': self._file_hash(file_path)})
            return list(result.get('ids', []))
        except Exception as e:
            logger.error(f"Error getting file documents: {e}")
            return []

    def get_embeddings(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """
        Get OpenAI embeddings for several texts in one API call (much faster than
        one call per chunk). Retries with a growing wait on temporary errors.
        """
        if self.openai_client is None:
            raise RuntimeError("OpenAI client not initialized. Provide --openai-key or set OPENAI_API_KEY.")

        for attempt in range(1, max_retries + 1):
            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=texts,
                )
                # Keep results in the same order as the input texts
                ordered = sorted(response.data, key=lambda item: item.index)
                return [item.embedding for item in ordered]
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Embedding request failed after {max_retries} attempts: {e}")
                    raise
                wait_seconds = 2 ** attempt
                logger.warning(f"Embedding request failed (attempt {attempt}/{max_retries}): {e}. "
                               f"Retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
        return []

    def get_embedding(self, text: str) -> List[float]:
        """
        Get OpenAI embedding for text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Call OpenAI embeddings API, return embedding vector
        # (error handling and retries are in get_embeddings)
        return self.get_embeddings([text])[0]

    def generate_document_id(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """
        Generate stable document ID based on file path and chunk position
        This allows for document updates without changing IDs
        """
        # Create consistent ID format using mission, source, and chunk_index.
        # A short file fingerprint is included so files with the same name in
        # different folders never share IDs.
        # Format: mission_source_fingerprint_chunk_0001
        mission = metadata.get('mission', 'unknown')
        source = metadata.get('source', file_path.stem)
        file_hash = metadata.get('file_hash') or self._file_hash(file_path)
        chunk_index = int(metadata.get('chunk_index', 0))
        return f"{mission}_{source}_{file_hash}_chunk_{chunk_index:04d}"

    def process_text_file(self, file_path: Path) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Process plain text files with enhanced metadata extraction

        Args:
            file_path: Path to text file

        Returns:
            List of (text, metadata) tuples
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            if not content.strip():
                return []

            # Enhanced metadata extraction
            metadata = {
                'source': file_path.stem,
                'file_path': str(file_path),
                'file_hash': self._file_hash(file_path),
                'file_type': 'text',
                'content_type': 'full_text',
                'mission': self.extract_mission_from_path(file_path),
                'data_type': self.extract_data_type_from_path(file_path),
                'document_category': self.extract_document_category_from_filename(file_path.name),
                'file_size': len(content),
                'processed_timestamp': datetime.now().isoformat()
            }

            return self.chunk_text(content, metadata)

        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            return []

    def extract_mission_from_path(self, file_path: Path) -> str:
        """Extract mission name from file path"""
        path_str = str(file_path).lower()
        if 'apollo11' in path_str or 'apollo_11' in path_str:
            return 'apollo_11'
        elif 'apollo13' in path_str or 'apollo_13' in path_str:
            return 'apollo_13'
        elif 'challenger' in path_str:
            return 'challenger'
        else:
            return 'unknown'

    def extract_data_type_from_path(self, file_path: Path) -> str:
        """Extract data type from file path"""
        path_str = str(file_path).lower()
        if 'transcript' in path_str:
            return 'transcript'
        elif 'textract' in path_str:
            return 'textract_extracted'
        elif 'audio' in path_str:
            return 'audio_transcript'
        elif 'flight_plan' in path_str:
            return 'flight_plan'
        else:
            return 'document'

    def extract_document_category_from_filename(self, filename: str) -> str:
        """Extract document category from filename for better organization"""
        filename_lower = filename.lower()

        # Apollo transcript types
        if 'pao' in filename_lower:
            return 'public_affairs_officer'
        elif 'cm' in filename_lower:
            return 'command_module'
        elif 'tec' in filename_lower:
            return 'technical'
        elif 'flight_plan' in filename_lower:
            return 'flight_plan'

        # Challenger audio segments
        elif 'mission_audio' in filename_lower:
            return 'mission_audio'

        # NASA archive documents
        elif 'ntrs' in filename_lower:
            return 'nasa_archive'
        elif '19900066485' in filename_lower:
            return 'technical_report'
        elif '19710015566' in filename_lower:
            return 'mission_report'

        # General categories
        elif 'full_text' in filename_lower:
            return 'complete_document'
        else:
            return 'general_document'

    def scan_text_files_only(self, base_path: str) -> List[Path]:
        """
        Scan data directories for text files only (avoiding JSON duplicates)

        Args:
            base_path: Base directory path

        Returns:
            List of text file paths to process
        """
        base_path = Path(base_path)
        files_to_process = []

        # Define directories to scan
        data_dirs = [
            'apollo11',
            'apollo13',
            'challenger'
        ]

        for data_dir in data_dirs:
            dir_path = base_path / data_dir
            if dir_path.exists():
                logger.info(f"Scanning directory: {dir_path}")

                # Find only text files
                text_files = list(dir_path.glob('**/*.txt'))
                files_to_process.extend(text_files)
                logger.info(f"Found {len(text_files)} text files in {data_dir}")

        # Filter out unwanted files
        filtered_files = []
        for file_path in files_to_process:
            # Skip system files and summaries
            if (file_path.name.startswith('.') or
                    'summary' in file_path.name.lower() or
                    file_path.suffix.lower() != '.txt'):
                continue
            filtered_files.append(file_path)

        # Sort so files are always processed in the same order
        filtered_files.sort()
        logger.info(f"Total text files to process: {len(filtered_files)}")

        # Log file breakdown by mission
        mission_counts = {}
        for file_path in filtered_files:
            mission = self.extract_mission_from_path(file_path)
            mission_counts[mission] = mission_counts.get(mission, 0) + 1

        logger.info("Files by mission:")
        for mission, count in mission_counts.items():
            logger.info(f"  {mission}: {count} files")

        return filtered_files

    def add_documents_to_collection(self, documents: List[Tuple[str, Dict[str, Any]]],
                                    file_path: Path, batch_size: int = 50,
                                    update_mode: str = 'skip') -> Dict[str, int]:
        """
        Add documents to ChromaDB collection in batches with update handling

        Args:
            documents: List of (text, metadata) tuples
            file_path: Path to the source file
            batch_size: Number of documents to process in each batch
            update_mode: How to handle existing documents:
                        'skip' - skip existing documents
                        'update' - update existing documents
                        'replace' - delete all existing documents from file and re-add

        Returns:
            Dictionary with counts of added, updated, and skipped documents
        """
        if not documents:
            return {'added': 0, 'updated': 0, 'skipped': 0}

        if update_mode not in ('skip', 'update', 'replace'):
            raise ValueError(f"Unknown update_mode '{update_mode}'. Use skip, update, or replace.")

        stats = {'added': 0, 'updated': 0, 'skipped': 0}
        file_hash = documents[0][1].get('file_hash') or self._file_hash(file_path)

        # Handle 'replace' mode: remove every existing chunk from this file first
        if update_mode == 'replace':
            existing = self.collection.get(where={'file_hash': file_hash})
            if existing['ids']:
                self.collection.delete(ids=existing['ids'])
                logger.info(f"Replace mode: removed {len(existing['ids'])} old chunks from {file_path.name}")

        new_ids = set()

        # Process documents in batches
        for batch_start in range(0, len(documents), batch_size):
            batch = documents[batch_start:batch_start + batch_size]

            # Generate document IDs
            ids = [self.generate_document_id(file_path, metadata) for _, metadata in batch]
            new_ids.update(ids)

            # Check which ones already exist (one lookup for the whole batch)
            existing_ids = set()
            if update_mode != 'replace':
                existing_ids = set(self.collection.get(ids=ids)['ids'])

            to_add, to_update = [], []
            for doc_id, (text, metadata) in zip(ids, batch):
                if doc_id in existing_ids:
                    if update_mode == 'skip':
                        stats['skipped'] += 1
                        continue
                    to_update.append((doc_id, text, metadata))
                else:
                    to_add.append((doc_id, text, metadata))

            pending = to_add + to_update
            if not pending:
                continue

            # Get embeddings for every chunk that needs one (one API call)
            embeddings = self.get_embeddings([text for _, text, _ in pending])
            add_count = len(to_add)

            # Add new chunks
            if to_add:
                self.collection.add(
                    ids=[doc_id for doc_id, _, _ in to_add],
                    documents=[text for _, text, _ in to_add],
                    metadatas=[metadata for _, _, metadata in to_add],
                    embeddings=embeddings[:add_count],
                )
                stats['added'] += add_count

            # Update existing chunks
            if to_update:
                self.collection.update(
                    ids=[doc_id for doc_id, _, _ in to_update],
                    documents=[text for _, text, _ in to_update],
                    metadatas=[metadata for _, _, metadata in to_update],
                    embeddings=embeddings[add_count:],
                )
                stats['updated'] += len(to_update)

        # In 'update' mode, remove leftover chunks if the file now has fewer chunks
        if update_mode == 'update':
            existing = self.collection.get(where={'file_hash': file_hash})
            stale_ids = [doc_id for doc_id in existing['ids'] if doc_id not in new_ids]
            if stale_ids:
                self.collection.delete(ids=stale_ids)
                logger.info(f"Update mode: removed {len(stale_ids)} outdated chunks from {file_path.name}")

        # Return statistics
        return stats

    def process_all_text_data(self, base_path: str, update_mode: str = 'skip',
                              batch_size: int = 50) -> Dict[str, int]:
        """
        Process all text files and add to ChromaDB

        Args:
            base_path: Base directory containing data folders
            update_mode: How to handle existing documents:
                        'skip' - skip existing documents (default)
                        'update' - update existing documents
                        'replace' - delete all existing documents from file and re-add
            batch_size: Number of chunks embedded per OpenAI request

        Returns:
            Statistics about processed files
        """
        stats = {
            'files_processed': 0,
            'documents_added': 0,
            'documents_updated': 0,
            'documents_skipped': 0,
            'errors': 0,
            'total_chunks': 0,
            'missions': {}
        }

        # Get files to process
        files = self.scan_text_files_only(base_path)
        if not files:
            logger.warning(f"No text files found under '{base_path}'. "
                           f"Check --data-path (the NASA files are usually in ./data_text).")
            return stats

        # Loop through each file
        for i, file_path in enumerate(files, start=1):
            mission = self.extract_mission_from_path(file_path)
            mission_stats = stats['missions'].setdefault(
                mission, {'files': 0, 'chunks': 0, 'added': 0, 'updated': 0, 'skipped': 0}
            )

            # Handle errors gracefully: one bad file does not stop the whole run
            try:
                # Process file and add to collection
                documents = self.process_text_file(file_path)
                if not documents:
                    logger.info(f"[{i}/{len(files)}] {file_path.name}: empty or unreadable, skipped")
                    continue

                result = self.add_documents_to_collection(
                    documents, file_path, batch_size=batch_size, update_mode=update_mode
                )

                # Update statistics
                stats['files_processed'] += 1
                stats['total_chunks'] += len(documents)
                stats['documents_added'] += result['added']
                stats['documents_updated'] += result['updated']
                stats['documents_skipped'] += result['skipped']
                mission_stats['files'] += 1
                mission_stats['chunks'] += len(documents)
                mission_stats['added'] += result['added']
                mission_stats['updated'] += result['updated']
                mission_stats['skipped'] += result['skipped']

                logger.info(f"[{i}/{len(files)}] {file_path.name}: {len(documents)} chunks "
                            f"(added {result['added']}, updated {result['updated']}, "
                            f"skipped {result['skipped']})")

            except Exception as e:
                stats['errors'] += 1
                logger.error(f"[{i}/{len(files)}] Error processing {file_path}: {e}")

        return stats

    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the ChromaDB collection"""
        # Return collection name, document count, metadata
        try:
            return {
                'collection_name': self.collection.name,
                'document_count': self.collection.count(),
                'metadata': self.collection.metadata,
                'chroma_dir': self.chroma_persist_directory,
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {'error': str(e)}

    def query_collection(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Query the collection for testing

        Args:
            query_text: Query text
            n_results: Number of results to return

        Returns:
            Query results
        """
        # Perform test query and return results
        try:
            query_embedding = self.get_embedding(query_text)
            return self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances'],
            )
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            return {}

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get detailed statistics about the collection"""
        try:
            # Get all documents to analyze
            all_docs = self.collection.get()

            if not all_docs['metadatas']:
                return {'error': 'No documents in collection'}

            stats = {
                'total_documents': len(all_docs['metadatas']),
                'missions': {},
                'data_types': {},
                'document_categories': {},
                'file_types': {}
            }

            # Analyze metadata
            for metadata in all_docs['metadatas']:
                mission = metadata.get('mission', 'unknown')
                data_type = metadata.get('data_type', 'unknown')
                doc_category = metadata.get('document_category', 'unknown')
                file_type = metadata.get('file_type', 'unknown')

                # Count by mission
                stats['missions'][mission] = stats['missions'].get(mission, 0) + 1

                # Count by data type
                stats['data_types'][data_type] = stats['data_types'].get(data_type, 0) + 1

                # Count by document category
                stats['document_categories'][doc_category] = stats['document_categories'].get(doc_category, 0) + 1

                # Count by file type
                stats['file_types'][file_type] = stats['file_types'].get(file_type, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {'error': str(e)}


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='ChromaDB Embedding Pipeline for NASA Data')
    parser.add_argument('--data-path', default='./data_text', help='Path to data directories')
    parser.add_argument('--openai-key', default=os.getenv('OPENAI_API_KEY'),
                        help='OpenAI API key (defaults to the OPENAI_API_KEY environment variable)')
    parser.add_argument('--chroma-dir', default='./chroma_db_openai', help='ChromaDB persist directory')
    parser.add_argument('--collection-name', default='nasa_space_missions_text', help='Collection name')
    parser.add_argument('--embedding-model', default='text-embedding-3-small', help='OpenAI embedding model')
    parser.add_argument('--chunk-size', type=int, default=500, help='Maximum chunk size in characters')
    parser.add_argument('--chunk-overlap', type=int, default=100, help='Chunk overlap in characters')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size for processing')
    parser.add_argument('--update-mode', choices=['skip', 'update', 'replace'], default='skip',
                        help='How to handle existing documents: skip, update, or replace')
    parser.add_argument('--test-query', help='Test query after processing')
    parser.add_argument('--stats-only', action='store_true', help='Only show collection statistics')
    parser.add_argument('--delete-source', help='Delete all documents from a specific source pattern')

    args = parser.parse_args()

    # An API key is only needed when creating embeddings
    needs_key = not (args.stats_only or args.delete_source)
    if needs_key and not args.openai_key:
        parser.error("No OpenAI API key found. Set OPENAI_API_KEY or pass --openai-key.")
    if args.batch_size <= 0:
        parser.error("--batch-size must be greater than 0")

    # Initialize pipeline
    logger.info("Initializing ChromaDB Embedding Pipeline...")
    logger.info(f"Chunk size: {args.chunk_size} characters, overlap: {args.chunk_overlap} characters")
    try:
        pipeline = ChromaEmbeddingPipelineTextOnly(
            openai_api_key=args.openai_key,
            chroma_persist_directory=args.chroma_dir,
            collection_name=args.collection_name,
            embedding_model=args.embedding_model,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
    except ValueError as e:
        parser.error(str(e))

    # Handle delete source operation
    if args.delete_source:
        deleted_count = pipeline.delete_documents_by_source(args.delete_source)
        logger.info(f"Deleted {deleted_count} documents matching source pattern: {args.delete_source}")
        return

    # If stats only, show collection statistics and exit
    if args.stats_only:
        info = pipeline.get_collection_info()
        logger.info("Collection Statistics:")
        logger.info(f"collection_name: {info.get('collection_name', 'N/A')}")
        logger.info(f"chroma_dir: {info.get('chroma_dir', 'N/A')}")
        logger.info(f"collection_size (chunks): {info.get('document_count', 'N/A')}")
        stats = pipeline.get_collection_stats()
        for key, value in stats.items():
            logger.info(f"{key}: {value}")
        return

    # Process all data
    logger.info(f"Starting text data processing with update mode: {args.update_mode}")
    start_time = time.time()

    stats = pipeline.process_all_text_data(args.data_path, update_mode=args.update_mode,
                                           batch_size=args.batch_size)

    end_time = time.time()
    processing_time = end_time - start_time

    # Print results
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Files processed: {stats['files_processed']}")
    logger.info(f"Total chunks created: {stats['total_chunks']}")
    logger.info(f"Documents added to collection: {stats['documents_added']}")
    logger.info(f"Documents updated in collection: {stats['documents_updated']}")
    logger.info(f"Documents skipped (already exist): {stats['documents_skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Processing time: {processing_time:.2f} seconds")

    # Mission breakdown
    logger.info("\nMission breakdown:")
    for mission, mission_stats in stats['missions'].items():
        logger.info(f"  {mission}: {mission_stats['files']} files, {mission_stats['chunks']} chunks")
        logger.info(f"    Added: {mission_stats['added']}, Updated: {mission_stats['updated']}, Skipped: {mission_stats['skipped']}")

    # Collection info
    collection_info = pipeline.get_collection_info()
    logger.info(f"\nCollection: {collection_info.get('collection_name', 'N/A')}")
    logger.info(f"Total documents in collection: {collection_info.get('document_count', 'N/A')}")

    # Test query if provided
    if args.test_query:
        logger.info(f"\nTesting query: '{args.test_query}'")
        results = pipeline.query_collection(args.test_query)
        if results and results.get('documents'):
            logger.info(f"Found {len(results['documents'][0])} results:")
            for i, doc in enumerate(results['documents'][0][:3]):  # Show top 3
                logger.info(f"Result {i+1}: {doc[:200]}...")

    logger.info("Pipeline completed successfully!")


if __name__ == "__main__":
    main()