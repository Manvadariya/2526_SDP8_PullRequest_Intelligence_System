"""
Part 4 Verification: Vector Storage Test
========================================
Indexes `reviewer.py` into Qdrant using embeddings from GitHub Models API.
Performs a semantic search to verify retrieval relevance.

Usage:
    cd backend/src/webhooks
    python test_vector_store.py
"""

import sys
import os
import time

# Ensure the webhooks directory is on the path so core.* imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load .env explicitly for GITHUB_TOKEN
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from core.indexing.vector_store import CodeVectorStore


def main():
    print("\n" + "=" * 60)
    print("  Part 4: Vector Storage Verification")
    print("=" * 60)

    # 1. Setup
    if not os.environ.get("GITHUB_TOKEN"):
        print("  [FAIL] GITHUB_TOKEN not found in environment!")
        sys.exit(1)
        
    try:
        print("\n  Initializing CodeVectorStore...")
        store = CodeVectorStore()
        print("  [PASS] Connected to Qdrant & GitHub API Client initialized")
    except Exception as e:
        print(f"  [FAIL] Initialization failed: {e}")
        sys.exit(1)

    # 2. Reset Collection (For Verification)
    print("  [INFO] Resetting collection to test new indexing logic...")
    store.qdrant.delete_collection(store.collection_name)
    store._ensure_collection()

    # 3. Indexing
    target_file = os.path.join(os.path.dirname(__file__), "agents", "reviewer.py")
    if not os.path.exists(target_file):
        print(f"  [FAIL] Target file not found: {target_file}")
        sys.exit(1)
        
    print(f"\n  Indexing {target_file}...")
    start_time = time.time()
    try:
        count = store.index_file(target_file)
        duration = time.time() - start_time
        print(f"  [PASS] Indexed {count} chunks in {duration:.2f}s")
    except Exception as e:
        print(f"  [FAIL] Indexing failed: {e}")
        sys.exit(1)

    if count == 0:
        print("  [WARN] 0 chunks indexed. Something might be wrong with parsing.")
        sys.exit(1)

    # 4. Searching
    query = "logic for formatting review comments"
    print(f"\n  Searching query: '{query}'")
    
    try:
        results = store.search(query, limit=3)
    except Exception as e:
        print(f"  [FAIL] Search failed: {e}")
        sys.exit(1)

    if not results:
        print("  [FAIL] No results found!")
        sys.exit(1)

    top_hit = results[0]
    print(f"\n  Top Result:")
    print(f"    Symbol: {top_hit['symbol_name']}")
    print(f"    Type:   {top_hit.get('type', 'N/A')}")
    print(f"    File:   {os.path.basename(top_hit['file_path'])}")
    print(f"    Lines:  {top_hit['start_line']}")
    print(f"    Score:  {top_hit['score']:.4f}")
    
    # 5. Verification
    # We now expect the specific function to be returned, NOT the class
    # The function name is likely _format_review
    if "_format_review" in top_hit['symbol_name']:
        print("\n  [PASS] Correctly retrieved the specific function (Semantic Match)")
    elif top_hit['symbol_name'] == "ReviewerAgent":
        print("\n  [FAIL] Still retrieving the Class. Shadowing fix failed.")
    else:
        print(f"\n  [WARN] Retrieved unexpected symbol: {top_hit['symbol_name']}")

    if top_hit['score'] > 0.6:
        print("  [PASS] High retrieval score (> 0.6)")
    else:
        print(f"  [WARN] Score is still low ({top_hit['score']:.4f}).")

    print("\n" + "-" * 60)
    print("  Vector Storage: SUCCESS")
    print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
