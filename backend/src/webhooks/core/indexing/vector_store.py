"""
Part 4: Vector Storage Pipeline
===============================
Manages embedding generation and storage in Qdrant.
Supports multiple embedding backends with automatic fallback:
  1. Gemini (text-embedding-004) — generous free-tier
  2. GitHub Models (text-embedding-3-large) — fallback
"""

from __future__ import annotations

import os
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, models

from .parser import UniversalParser, parse_file
from .chunker import SmartChunker, Chunk


class CodeVectorStore:
    """
    Vector storage engine using Qdrant + Gemini/GitHub Models Inference API.
    Uses singleton pattern to prevent multiple Qdrant local clients.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, collection_name: str = "repo_codebase"):
        if self._initialized:
            return
        self._initialized = True
        
        self.collection_name = collection_name
        
        # 1. Initialize Qdrant (Local Storage — no Docker needed)
        local_path = os.path.join(os.path.dirname(__file__), "..", "..", "qdrant_data")
        os.makedirs(local_path, exist_ok=True)
        self.qdrant = QdrantClient(path=local_path)
        print(f"  [VectorStore] Using local Qdrant storage: {local_path}")
        
        # 2. Initialize Embedding Backend
        # Priority: Gemini → GitHub Models
        self.embedding_backend = None  # "gemini" or "github"
        self.gemini_client = None
        self.ai_client = None
        
        # Try Gemini first (generous free-tier: 1,500 RPM)
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if gemini_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=gemini_key)
                self.embedding_backend = "gemini"
                self.model_name = "gemini-embedding-001"
                self.vector_size = 3072  # gemini-embedding-001 dimension
                print(f"  [VectorStore] ✓ Using Gemini embeddings ({self.model_name}, dim={self.vector_size})")
            except Exception as e:
                print(f"  [VectorStore] ✗ Gemini embedding init failed: {e}")
        
        # Fallback to GitHub Models
        if not self.embedding_backend:
            from openai import OpenAI
            api_key = os.environ.get("GITHUB_TOKEN")
            if not api_key:
                raise ValueError("No embedding API available: GEMINI_API_KEY and GITHUB_TOKEN not set")
            self.ai_client = OpenAI(
                base_url="https://models.github.ai/inference",
                api_key=api_key,
            )
            self.embedding_backend = "github"
            self.model_name = "text-embedding-3-large"
            self.vector_size = 3072  # GitHub text-embedding-3-large dimension
            print(f"  [VectorStore] Using GitHub Models embeddings ({self.model_name}, dim={self.vector_size})")
        
        # 3. Ensure collection exists
        self._ensure_collection()
        
        # 4. Helpers
        self.parser = UniversalParser()
        self.chunker = SmartChunker(model_name=self.model_name)

    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        if self.qdrant.collection_exists(self.collection_name):
            # Check if existing collection has matching vector size
            info = self.qdrant.get_collection(self.collection_name)
            existing_size = info.config.params.vectors.size
            if existing_size != self.vector_size:
                print(f"  [VectorStore] ⚠ Collection vector size mismatch ({existing_size} → {self.vector_size}). Recreating...")
                self.qdrant.delete_collection(self.collection_name)
                self.qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
        else:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE
                )
            )

    def _generate_id(self, file_path: str, chunk_index: int) -> str:
        """
        Deterministic UUID based on file path and chunk index.
        Ensures strict deduplication: re-indexing the same file overwrites old chunks.
        """
        unique_str = f"{file_path}::{chunk_index}"
        hash_val = hashlib.md5(unique_str.encode("utf-8")).hexdigest()
        return str(uuid.UUID(hash_val))

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using the configured backend."""
        if self.embedding_backend == "gemini":
            return self._get_embeddings_gemini(texts)
        else:
            return self._get_embeddings_github(texts)

    def _get_embeddings_gemini(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Google Gemini API."""
        all_embeddings = []
        max_retries = 3
        
        # Process one at a time for reliability
        for i, text in enumerate(texts):
            for attempt in range(max_retries):
                try:
                    result = self.gemini_client.models.embed_content(
                        model=self.model_name,
                        contents=text,
                    )
                    all_embeddings.append(result.embeddings[0].values)
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    is_rate_limit = "429" in error_str or "rate" in error_str or "quota" in error_str
                    
                    if attempt == max_retries - 1:
                        raise e
                    
                    if is_rate_limit:
                        wait_time = min(60, 5 * (2 ** attempt))
                        print(f"  [VectorStore] Gemini rate limited on text {i+1}/{len(texts)} (attempt {attempt+1}/{max_retries}). Waiting {wait_time}s...")
                    else:
                        wait_time = min(15, 2 * (2 ** attempt))
                        print(f"  [VectorStore] Gemini embedding error (attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            # Small delay between texts
            if i + 1 < len(texts):
                time.sleep(0.3)
        
        return all_embeddings

    def _get_embeddings_github(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using GitHub Models API in batches (fallback)."""
        max_retries = 6
        all_embeddings = []
        batch_size = 1
        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            for attempt in range(max_retries):
                try:
                    response = self.ai_client.embeddings.create(
                        input=batch,
                        model=self.model_name
                    )
                    all_embeddings.extend([data.embedding for data in response.data])
                    break
                except Exception as e:
                    error_str = str(e).lower()
                    is_rate_limit = "too many requests" in error_str or "rate limit" in error_str or "429" in error_str
                    if attempt == max_retries - 1:
                        raise e
                    if is_rate_limit:
                        wait_time = min(120, 10 * (2 ** attempt))
                        print(f"  [VectorStore] Rate limited on batch {batch_num}/{total_batches} (attempt {attempt+1}/{max_retries}). Waiting {wait_time}s...")
                    else:
                        wait_time = min(30, 2 * (2 ** attempt))
                        print(f"  [VectorStore] Embedding error on batch {batch_num}/{total_batches} (attempt {attempt+1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            # Delay between batches
            if i + batch_size < len(texts):
                time.sleep(2)
        return all_embeddings

    def index_file(self, file_path: str, code_content: Optional[str] = None) -> int:
        """
        Parse, chunk, embed, and index a source file.
        Returns number of chunks indexed.
        """
        # 1. Read & Parse
        if code_content is None:
            nodes = parse_file(file_path)
        else:
            nodes = self.parser.parse_code(code_content, file_path)
            
        if not nodes:
            return 0

        # 2. Chunk
        chunks: List[Chunk] = []
        for node in nodes:
            chunks.extend(self.chunker.chunk_node(node))

        if not chunks:
            return 0

        # 3. Embed
        # ENRICHED SEMANTIC INDEXING: bridge the gap between NL and Code.
        texts = []
        for chunk in chunks:
            # "Semantic Packet"
            semantic_text = f"File: {file_path}\n"
            semantic_text += f"Symbol: {chunk.metadata['name']}\n"
            semantic_text += f"Type: {chunk.metadata.get('type', 'code')}\n"
            
            # Intent is King
            if chunk.metadata.get("docstring"):
                semantic_text += f"Intent: {chunk.metadata['docstring']}\n"
            
            semantic_text += f"Code:\n{chunk.content}"
            texts.append(semantic_text)
            
        embeddings = self.get_embeddings(texts)

        # 4. Prepare Points
        points = []
        for i, chunk in enumerate(chunks):
            # Deterministic ID for idempotency
            point_id = self._generate_id(file_path, chunk.metadata["chunk_index"])
            
            payload = {
                "file_path": file_path,
                "symbol_name": chunk.metadata["name"],
                "type": chunk.metadata["type"],
                "docstring": chunk.metadata.get("docstring", ""),
                "chunk_index": chunk.metadata["chunk_index"],
                "total_chunks": chunk.metadata["total_chunks"],
                "start_line": chunk.metadata["start_line"],
                "end_line": chunk.metadata["end_line"],
                "content": chunk.content,
                "language": chunk.metadata["language"]
            }
            
            
            points.append(models.PointStruct(
                id=point_id,
                vector=embeddings[i],
                payload=payload
            ))

        # 5. Upsert to Qdrant
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        return len(points)

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search for code snippets.
        """
        # 1. Embed query
        query_vector = self.get_embeddings([query])[0]
        
        # 2. Search Qdrant
        # New API uses query_points
        results = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            with_payload=True
        ).points
        
        # 3. Format results
        output = []
        for hit in results:
            output.append({
                "score": hit.score,
                "file_path": hit.payload["file_path"],
                "symbol_name": hit.payload["symbol_name"],
                "type": hit.payload.get("type", "unknown"),
                "content": hit.payload["content"],
                "start_line": hit.payload["start_line"]
            })
            
            
        return output

    def delete_file(self, file_path: str) -> bool:
        """
        Deletes all vectors associated with a specific file.
        """
        try:
            # Create a filter for the file_path in payload
            self.qdrant.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="file_path",
                                match=models.MatchValue(value=file_path)
                            )
                        ]
                    )
                )
            )
            return True
        except Exception as e:
            print(f" Failed to delete file {file_path} from Qdrant: {e}")
            return False
