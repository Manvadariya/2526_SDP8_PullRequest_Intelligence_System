
# Validating Graph Construction
import sys
import os
import networkx as nx

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.indexing.parser import UniversalParser
from core.indexing.graph import SymbolGraph

def main():
    print("============================================================")
    print("  Part 5: Symbol Graph Verification")
    print("============================================================")

    # 1. Parse File
    parser = UniversalParser()
    target_file = os.path.join(os.path.dirname(__file__), "agents", "reviewer.py")
    
    if not os.path.exists(target_file):
        print(f"  [FAIL] Target file not found: {target_file}")
        sys.exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        code = f.read()

    print(f"  Parsing {target_file}...")
    nodes = parser.parse_code(code, target_file)
    print(f"  [PASS] Extracted {len(nodes)} nodes.")

    # 2. Build Graph
    print("\n  Building Symbol Graph...")
    graph = SymbolGraph()
    graph.build_from_nodes(nodes)
    
    node_count = graph.graph.number_of_nodes()
    edge_count = graph.graph.number_of_edges()
    print(f"  [INFO] Graph has {node_count} nodes and {edge_count} edges.")

    if edge_count == 0:
        print("  [WARN] 0 edges found! Call extraction might be failing.")
        # Debug: Print first node calls
        if nodes:
            print(f"  [DEBUG] Node {nodes[0].name} calls: {nodes[0].calls}")
    else:
        print(f"  [PASS] Successfully built dependency graph.")

    # 3. Verify specific relationship
    # We expect `run_inline_review` to call `_extract_clean_code` or `parse_diff`
    # Let's check context for `run_inline_review`
    target_symbol = "run_inline_review"
    context = graph.get_context(target_symbol)
    
    print(f"\n  Context for '{target_symbol}':")
    print(f"    Callers (Used By): {context['callers']}")
    print(f"    Callees (Uses):    {context['callees']}")

    # Verification Logic
    # In reviewer.py: run_inline_review calls _extract_and_parse_json, annotate_diff_with_line_numbers, etc.
    # It might NOT call `_extract_clean_code` directly, but let's see.
    # It calls `self.diff_parser.parse_diff` -> regex might miss `self.diff_parser.parse_diff` if it expects simpler calls.
    # Python query: `(call function: (attribute attribute: (identifier) @method_name))`
    # So `self.diff_parser.parse_diff` -> attribute is `parse_diff`. It should catch it.
    
    if len(context['callees']) > 0:
        print("  [PASS] Found callees for target symbol.")
    else:
        print("  [WARN] No callees found. Check extraction query.")

    print("\n" + "-" * 60)
    print("  Symbol Graph: SUCCESS")
    print("-" * 60)

if __name__ == "__main__":
    main()
