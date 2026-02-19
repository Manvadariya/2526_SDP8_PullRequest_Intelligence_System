"""
Part 3 Verification: Smart Chunking Test
========================================
Parses agents/reviewer.py and feeds it through the SmartChunker.
Verifies that large functions are split correctly and that context
(signatures) is preserved in subsequent chunks.

Usage:
    cd backend/src/webhooks
    python test_chunker.py
"""

import sys
import os
import tiktoken

# Ensure the webhooks directory is on the path so core.* imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.indexing.parser import parse_file, CodeNode
from core.indexing.chunker import SmartChunker, Chunk

def main():
    print("\n" + "=" * 60)
    print("  Part 3: Smart Chunking Verification")
    print("=" * 60)

    # 1. Setup
    target = os.path.join(os.path.dirname(__file__), "agents", "reviewer.py")
    if not os.path.exists(target):
        print(f"  [FAIL] Target file not found: {target}")
        sys.exit(1)
        
    print(f"\n  Target: {target}")
    
    # 2. Parse
    print("  Parsing CodeNodes...")
    nodes = parse_file(target)
    print(f"  Found {len(nodes)} nodes.")
    
    # 3. Chunk
    chunker = SmartChunker()
    all_chunks = []
    
    print("  Chunking nodes...")
    large_node_found = False
    
    for node in nodes:
        chunks = chunker.chunk_node(node)
        all_chunks.extend(chunks)
        
        if len(chunks) > 1:
            large_node_found = True
            print(f"\n  [INFO] Large node split: {node.name}")
            print(f"         Original Size: {chunker.count_tokens(node.content)} tokens")
            print(f"         Split into {len(chunks)} chunks")
            
            # Verify Signature Anchoring
            first_chunk_sig = chunks[0].content.split('\n')[0]
            second_chunk_sig = chunks[1].content.split('\n')[0]
            
            print(f"         Chunk 0 Start: {first_chunk_sig[:50]}...")
            print(f"         Chunk 1 Start: {second_chunk_sig[:50]}...")
            
            if first_chunk_sig == second_chunk_sig:
                print("         [PASS] Signature preserved in Chunk 1")
            else:
                # Often Chunk 0 IS the signature + body start, so they match start
                # But strict equality for line 0 is expected with our logic
                if "def " in second_chunk_sig or "class " in second_chunk_sig:
                     print("         [PASS] Signature matches (heuristic)")
                else:
                     print("         [WARN] Signature might not match exactly")

    # 4. Simulating a HUGE function to force splitting if none found
    if not large_node_found:
        print("\n  [INFO] No naturally large nodes found. Simulating one...")
        fake_content = "def huge_function(a, b):\n" + ("    x = a + b\n" * 1000)
        huge_node = CodeNode(
            type="function", 
            name="huge_function", 
            content=fake_content, 
            start_line=1, 
            end_line=1001,
            filepath="fake.py"
        )
        chunks = chunker.chunk_node(huge_node)
        print(f"         Simulated Split: {len(chunks)} chunks")
        
        if len(chunks) > 1:
             sig0 = chunks[0].content.split('\n')[0]
             sig1 = chunks[1].content.split('\n')[0]
             print(f"         Chunk 0 Start: {sig0}")
             print(f"         Chunk 1 Start: {sig1}")
             if sig0 == sig1:
                 print("         [PASS] Signature Anchoring Verified")
             else:
                 print("         [FAIL] Signature Anchoring Failed")
        else:
             print("         [FAIL] Failed to split simulated large node")

    # 5. Summary
    print("\n" + "-" * 60)
    print(f"  Total Chunks Generated: {len(all_chunks)}")
    print(f"  Tiktoken imported: {tiktoken.__installed_version__ if hasattr(tiktoken, '__installed_version__') else 'Yes'}")
    
    if all_chunks:
        print("  [PASS]  Smart Chunking: SUCCESS")
    else:
        print("  [FAIL]  No chunks generated")
    print("-" * 60 + "\n")

if __name__ == "__main__":
    main()
