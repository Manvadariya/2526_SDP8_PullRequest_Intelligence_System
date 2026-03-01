"""
Part 3: Smart Chunking Strategy
===============================
Handles splitting of large CodeNodes into vector-ready Chunks.
Includes robust handling for large functions by "anchoring" the function
signature to every chunk so the LLM never loses context.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any

import tiktoken

from .parser import CodeNode


# ─── Data Model ───────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    """A piece of code ready for embedding."""
    chunk_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─── Smart Chunker ────────────────────────────────────────────────────────────

class SmartChunker:
    """
    Splits CodeNodes into chunks that fit within embedding model context limits.
    
    Key Features:
    - Token-aware splitting (using tiktoken)
    - Signature Anchoring: Large functions have their signature prepended to EVERY chunk
    - Sliding windows for body content
    """

    def __init__(self, model_name: str = "text-embedding-3-large"):
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base if model name is unknown
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Configuration
        self.signature_token_limit = 100   # Max tokens for a signature
        self.chunk_token_limit = 1500      # Soft limit for chunks
        self.window_size = 1000            # Size of sliding window
        self.window_overlap = 200          # Overlap between windows

    def count_tokens(self, text: str) -> int:
        """Accurate token count using tiktoken."""
        return len(self.tokenizer.encode(text))

    def chunk_node(self, node: CodeNode, base_metadata: Dict[str, Any] = None) -> List[Chunk]:
        """
        Convert a CodeNode into one or more Chunks.
        """
        if base_metadata is None:
            base_metadata = {}
        
        # Base metadata for retrieval
        meta = {
            "type": node.type,
            "name": node.name,
            "filepath": node.filepath,
            "language": node.language,
            "start_line": node.start_line,
            "end_line": node.end_line,
            "docstring": node.docstring,  # Persist docstring for semantic headers
            "type": node.type,            # Persist type (function/class/method)
            **base_metadata
        }

        # 1. Check if the whole node fits in one chunk
        total_tokens = self.count_tokens(node.content)
        
        if total_tokens <= self.chunk_token_limit or node.type == "class":
            # Skeleton classes should always be one chunk
            meta["is_skeleton"] = (node.type == "class")
            return [self._create_chunk(node.content, meta, 0, 1)]

        meta["is_skeleton"] = False

        # 2. Large Node Strategy: Signature Anchoring
        return self._chunk_large_node(node, meta)

    def _chunk_large_node(self, node: CodeNode, meta: Dict[str, Any]) -> List[Chunk]:
        """
        Split a large node while preserving its signature (context) in every chunk.
        """
        lines = node.content.split('\n')
        
        # Extract Signature (First few lines until we hit the body)
        # Heuristic: Take up to first 5 lines or until we have a block start
        # Ideally, we'd use the AST for this, but a heuristic works well for 
        # prepending context.
        signature_lines = []
        token_count = 0
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            if token_count + line_tokens > self.signature_token_limit:
                break
            signature_lines.append(line)
            token_count += line_tokens
            # If we hit a colon at the end of a def/class line, that's a good break point
            if line.strip().endswith(':'):
                break
                
        signature_text = '\n'.join(signature_lines)
        remaining_lines = lines[len(signature_lines):]
        remaining_text = '\n'.join(remaining_lines)
        
        # If remaining text is empty, just return the signature (edge case)
        if not remaining_text.strip():
            return [self._create_chunk(node.content, meta, 0, 1)]

        # Sliding Window over the remaining body
        chunks = []
        window_tokens = self.window_size - self.count_tokens(signature_text)
        
        # We need to window by *lines* to avoid splitting mid-line, but measure in tokens
        current_window_lines = []
        current_tokens = 0
        all_windows = []

        # Simple greedy line accumulation
        # (A more advanced version would use overlap, but for this implementation
        # we will do a simpler segmented approach with signature pre-pended,
        # or a proper sliding window if we track index)
        
        # Let's do a proper token-based sliding window over the text
        body_tokens = self.tokenizer.encode(remaining_text)
        
        step = self.window_size - self.window_overlap
        
        # If the body is small enough to fit in one window after signature extraction
        if len(body_tokens) <= window_tokens:
             full_content = signature_text + "\n" + remaining_text
             return [self._create_chunk(full_content, meta, 0, 1)]

        # Slice tokens
        num_windows = (len(body_tokens) // step) + 1
        
        for i in range(0, len(body_tokens), step):
            window_slice = body_tokens[i : i + window_tokens]
            decoded_window = self.tokenizer.decode(window_slice)
            
            # Combine Signature + Window
            full_content = f"{signature_text}\n... [lines {node.start_line}-{node.end_line} context] ...\n{decoded_window}"
            
            chunk_index = len(chunks)
            chunk_meta = meta.copy()
            chunk_meta.update({
                "chunk_index": chunk_index,
                "is_continuation": True,
                "signature_anchored": True
            })
            
            chunks.append(self._create_chunk(full_content, chunk_meta, chunk_index, -1))
            
            # Stop if we've reached the end
            if i + window_tokens >= len(body_tokens):
                break
        
        # Update total_chunks count
        for chunk in chunks:
            chunk.metadata["total_chunks"] = len(chunks)
            
        return chunks

    def _create_chunk(self, content: str, meta: Dict[str, Any], index: int, total: int) -> Chunk:
        """Helper to create a Chunk object with a unique ID."""
        # Deterministic ID based on content to avoid duplicates on re-indexing
        chunk_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        chunk_id = f"{meta['name']}-{index}-{chunk_hash[:8]}"
        
        final_meta = meta.copy()
        final_meta["chunk_index"] = index
        final_meta["total_chunks"] = total
        
        return Chunk(
            chunk_id=chunk_id,
            content=content,
            metadata=final_meta
        )
