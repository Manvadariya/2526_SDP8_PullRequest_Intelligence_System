"""
Part 9: Index Manager (Incremental Updates)
===========================================
Orchestrates the indexing process with local state management.
Ensures we only re-index changed files to save time and API credits.
"""

import os
import json
import hashlib
from typing import List, Optional

from .vector_store import CodeVectorStore
from .graph import SymbolGraph
from .parser import UniversalParser

class IndexManager:
    """
    Manages the lifecycle of code indexing.
    - Tracks file hashes in a local JSON file to detect changes.
    - Handles "Surgical Removal" of old data before re-indexing.
    """

    def __init__(self, vector_store=None, graph=None):
        # 1. Local State Store (JSON file)
        self._state_file = os.path.join(os.path.dirname(__file__), "..", "..", "index_state.json")
        self._state = self._load_state()
        print(f"  [IndexManager] Using local state ({len(self._state)} entries tracked)")

        # 2. Components
        self.vector_store = vector_store if vector_store else CodeVectorStore()
        self.graph = graph if graph else SymbolGraph()
        self.parser = UniversalParser()

    def _load_state(self) -> dict:
        """Load state from JSON file."""
        try:
            if os.path.exists(self._state_file):
                with open(self._state_file, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_state(self):
        """Persist state to JSON file."""
        try:
            with open(self._state_file, "w") as f:
                json.dump(self._state, f, indent=2)
        except Exception as e:
            print(f"  [IndexManager] Warning: Could not save state: {e}")

    def _compute_hash(self, content: str) -> str:
        """Returns MD5 hash of the content."""
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    def _get_stored_hash(self, file_path: str) -> Optional[str]:
        """Retrieve old hash."""
        return self._state.get(f"hash:{file_path}")

    def _set_stored_hash(self, file_path: str, new_hash: str):
        """Save new hash."""
        self._state[f"hash:{file_path}"] = new_hash

    def index_file(self, file_path: str, content: str, force: bool = False) -> bool:
        """
        Indexes a file ONLY if it has changed.
        Returns True if processed, False if skipped.
        """
        new_hash = self._compute_hash(content)
        old_hash = self._get_stored_hash(file_path)

        if not force and new_hash == old_hash:
            return False

        print(f"  [IndexManager] Updating {os.path.basename(file_path)}...")

        # Surgical Removal
        self.vector_store.delete_file(file_path)
        self.graph.remove_file_nodes(file_path)

        # Re-Index
        self.vector_store.index_file(file_path, code_content=content)

        nodes = self.parser.parse_code(content, file_path)
        self.graph.build_from_nodes(nodes)

        # Update State
        self._set_stored_hash(file_path, new_hash)
        return True

    def process_diff(self, file_paths: List[str], repo_root: str):
        """Batch process changed files from a PR."""
        processed_count = 0
        skipped_count = 0

        for rel_path in file_paths:
            full_path = os.path.join(repo_root, rel_path)

            if not os.path.exists(full_path):
                print(f"  [IndexManager] File deleted: {rel_path}")
                self.vector_store.delete_file(full_path)
                self.graph.remove_file_nodes(full_path)
                self._state.pop(f"hash:{full_path}", None)
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                if self.index_file(full_path, content):
                    processed_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"  [FAIL] Failed to process {rel_path}: {e}")

        self._save_state()
        print(f"  [IndexManager] Processed {processed_count}, Skipped {skipped_count}.")
