"""
Part 4: Vector Storage Pipeline
===============================
Manages embedding generation via GitHub Models API and storage in Qdrant.
Ensures deterministic IDs for deduplication and handles the full indexing flow.
"""

from __future__ import annotations

import os
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, models
from openai import OpenAI

from .parser import UniversalParser, parse_file
from .chunker import SmartChunker, Chunk


class CodeVectorStore:
    """
    Vector storage engine using Qdrant + GitHub Models Inference API.
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
        self.vector_size = 3072  # text-embedding-3-large dimension
        self.model_name = "text-embedding-3-large"
        
        # 1. Initialize Qdrant (Local Storage — no Docker needed)
        local_path = os.path.join(os.path.dirname(__file__), "..", "..", "qdrant_data")
        os.makedirs(local_path, exist_ok=True)
        self.qdrant = QdrantClient(path=local_path)
        print(f"  [VectorStore] Using local Qdrant storage: {local_path}")
        
        # 2. Initialize OpenAI for GitHub Models
        api_key = os.environ.get("GITHUB_TOKEN")
        if not api_key:
            raise ValueError("GITHUB_TOKEN environment variable not set")
            
        self.ai_client = OpenAI(
            base_url="https://models.github.ai/inference",
            api_key=api_key,
        )
        
        # 3. Ensure collection exists
        self._ensure_collection()
        
        # 4. Helpers
        self.parser = UniversalParser()
        self.chunker = SmartChunker(model_name=self.model_name)

    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist."""
        if not self.qdrant.collection_exists(self.collection_name):
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
        """Generate embeddings using GitHub Models API."""
        # GitHub API has rate limits, so simple retry logic is good practice
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.ai_client.embeddings.create(
                    input=texts,
                    model=self.model_name
                )
                return [data.embedding for data in response.data]
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 * (attempt + 1))
        return []

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
            print(f"⚠️ Failed to delete file {file_path} from Qdrant: {e}")
            return False
