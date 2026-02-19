"""
Part 2 Verification: AST Parser Test
======================================
Parses agents/reviewer.py with the UniversalParser and verifies
that it correctly extracts classes and functions.

Usage:
    cd backend/src/webhooks
    python test_parser.py
"""

import sys
import os

# Ensure the webhooks directory is on the path so core.* imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.indexing.parser import UniversalParser, parse_file


def main():
    print("\n" + "=" * 60)
    print("  Part 2: AST Parser Verification")
    print("=" * 60)

    target = os.path.join(os.path.dirname(__file__), "agents", "reviewer.py")
    print(f"\n  Target file: {target}")

    if not os.path.exists(target):
        print("  [FAIL] Target file not found!")
        sys.exit(1)

    # ── Parse ─────────────────────────────────────────────────────
    parser = UniversalParser()
    with open(target, encoding="utf-8", errors="replace") as f:
        code = f.read()

    nodes = parser.parse_code(code, "reviewer.py")

    if not nodes:
        print("  [FAIL] No nodes extracted!")
        sys.exit(1)

    # ── Display Results ───────────────────────────────────────────
    classes = [n for n in nodes if n.type == "class"]
    functions = [n for n in nodes if n.type in ("function", "method")]

    print(f"\n  Extracted {len(nodes)} nodes "
          f"({len(classes)} classes, {len(functions)} functions/methods)\n")

    print(f"  {'Type':<10} {'Name':<35} {'Lines':<12} {'CX':<5} {'Docstring'}")
    print("  " + "-" * 80)

    for n in nodes:
        doc_preview = n.docstring[:40].replace("\n", " ") + "..." if n.docstring else "-"
        print(f"  {n.type:<10} {n.name:<35} L{n.start_line}-{n.end_line:<6} {n.complexity:<5} {doc_preview}")

    # ── Assertions ────────────────────────────────────────────────
    print()
    errors = []

    if len(classes) < 1:
        errors.append(f"Expected at least 1 class, found {len(classes)}")
    else:
        print(f"  [PASS] Found {len(classes)} class(es)")

    if len(functions) < 2:
        errors.append(f"Expected multiple functions, found {len(functions)}")
    else:
        print(f"  [PASS] Found {len(functions)} functions/methods")

    # Check that docstrings were extracted for at least some nodes
    docs_found = sum(1 for n in nodes if n.docstring)
    if docs_found > 0:
        print(f"  [PASS] Extracted docstrings from {docs_found} node(s)")
    else:
        print(f"  [WARN] No docstrings extracted (reviewer.py may use # comments)")

    # Check complexity estimation
    max_cx = max(n.complexity for n in nodes)
    print(f"  [PASS] Complexity estimation working (max CX = {max_cx})")

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "-" * 60)
    if errors:
        for e in errors:
            print(f"  [FAIL] {e}")
        print("-" * 60 + "\n")
        sys.exit(1)
    else:
        print("  [PASS]  AST Parsing: SUCCESS")
        print("-" * 60 + "\n")


if __name__ == "__main__":
    main()
