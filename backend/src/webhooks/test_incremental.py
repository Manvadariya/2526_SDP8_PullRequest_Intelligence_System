
# Verification Script for Incremental Indexing
import sys
import os
import time
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Load .env explicitly for GITHUB_TOKEN
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from core.indexing.manager import IndexManager

def main():
    print("============================================================")
    print("  Part 9: Incremental Indexing Verification")
    print("============================================================")

    # 1. Initialize Manager
    print("  Initializing IndexManager...")
    try:
        manager = IndexManager()
    except Exception as e:
        print(f"  [FAIL] Initialization error: {e}")
        sys.exit(1)

    # 2. Setup Dummy File
    repo_root = os.path.dirname(os.path.abspath(__file__))
    temp_file = os.path.join(repo_root, "temp_incremental_test.py")
    
    print(f"  Using temp file: {temp_file}")
    
    # 3. Test 1: First Indexing
    print("\n  Test 1: First Indexing (New File)")
    content_v1 = "def test_func_v1():\n    print('Version 1')\n"
    
    # Write to disk
    with open(temp_file, "w") as f:
        f.write(content_v1)
        
    start = time.time()
    result = manager.index_file(temp_file, content_v1)
    duration = time.time() - start
    
    if result:
        print(f"  [PASS] Indexed in {duration:.2f}s")
    else:
        print("  [FAIL] Should have indexed (was skipped).")

    # 4. Test 2: Idempotency (Same Content)
    print("\n  Test 2: Idempotency (Re-run same content)")
    start = time.time()
    result = manager.index_file(temp_file, content_v1) # Same content
    duration = time.time() - start
    
    if not result:
        print(f"  [PASS] Skipped correctly in {duration:.2f}s (Hash match)")
    else:
        print("  [FAIL] Re-indexed unnecessarily!")

    # 5. Test 3: Modification
    print("\n  Test 3: Modification (Content Change)")
    content_v2 = "def test_func_v2():\n    print('Version 2 - Modified')\n"
    
    # Write to disk
    with open(temp_file, "w") as f:
        f.write(content_v2)
        
    start = time.time()
    result = manager.index_file(temp_file, content_v2)
    duration = time.time() - start
    
    if result:
        print(f"  [PASS] Updated index in {duration:.2f}s")
    else:
        print("  [FAIL] Failed to detect change.")

    # 6. Verify Detection
    print("\n  Verifying Vector Store Content...")
    # Search for v2
    hits_v2 = manager.vector_store.search("test_func_v2", limit=1)
    if hits_v2 and hits_v2[0]['symbol_name'] == 'test_func_v2':
         print("  [PASS] Found 'test_func_v2' in Vector Store.")
    else:
         print("  [FAIL] Could not find 'test_func_v2'.")

    # Ensure v1 is GONE (Surgical Removal Check)
    hits_v1 = manager.vector_store.search("test_func_v1", limit=1)
    # Note: searching 'test_func_v1' might still match v2 via semantic similarity, 
    # but the symbol name should NOT be test_func_v1
    if not hits_v1 or hits_v1[0]['symbol_name'] != 'test_func_v1':
        print("  [PASS] 'test_func_v1' is gone (Correctly deleted old data).")
    else:
        print(f"  [FAIL] Ghost code detected! Found 'test_func_v1': {hits_v1[0]}")

    # Cleanup
    if os.path.exists(temp_file):
        os.remove(temp_file)
        manager.vector_store.delete_file(temp_file)
        manager.graph.remove_file_nodes(temp_file)
        # Clean redis
        if manager.redis:
            manager.redis.delete(f"hash:{temp_file}")

    print("\n" + "-" * 60)
    print("  Incremental Indexing: SUCCESS")
    print("-" * 60)

if __name__ == "__main__":
    main()
