"""
Phase 1 Infrastructure Verification Script
============================================
Verifies that all new dependencies are importable and that the
Qdrant vector database and Redis cache are reachable.

Usage:
    1. Start Qdrant:  docker-compose up -d  (from project root)
    2. Install deps:  pip install -r backend/requirements.txt
    3. Run this:      python backend/src/webhooks/test_infra.py
"""

import sys
from importlib.metadata import version as pkg_version

PASS = "[PASS]"
FAIL = "[FAIL]"
results: list = []


def check(name: str, fn):
    """Run a check and record the result."""
    try:
        detail = fn()
        results.append((name, True, detail))
        print(f"  {PASS} {name}: {detail}")
    except Exception as e:
        results.append((name, False, str(e)))
        print(f"  {FAIL} {name}: {e}")


# ── 1. Import checks ─────────────────────────────────────────────
def check_import_qdrant():
    import qdrant_client  # noqa: F811
    v = pkg_version("qdrant-client")
    return f"qdrant_client {v} imported"


def check_import_tree_sitter():
    import tree_sitter  # noqa: F811
    v = pkg_version("tree-sitter")
    return f"tree_sitter {v} imported"


def check_import_tree_sitter_languages():
    import tree_sitter_languages  # noqa: F811
    return "tree_sitter_languages imported"


def check_import_networkx():
    import networkx as nx  # noqa: F811
    v = pkg_version("networkx")
    return f"networkx {v} imported"


def check_import_openai():
    import openai  # noqa: F811
    v = pkg_version("openai")
    return f"openai {v} imported (for embeddings)"


def check_import_redis():
    import redis as r  # noqa: F811
    v = pkg_version("redis")
    return f"redis {v} imported"


# ── 2. Qdrant connectivity ───────────────────────────────────────
def check_qdrant_connection():
    from qdrant_client import QdrantClient

    client = QdrantClient(url="http://localhost:6333", timeout=5)
    collections = client.get_collections().collections
    names = [c.name for c in collections]
    return f"Connected! Collections: {names if names else '(none yet)'}"


# ── 3. NetworkX graph sanity ─────────────────────────────────────
def check_networkx_graph():
    import networkx as nx

    G = nx.DiGraph()
    G.add_edge("function_a", "function_b")
    G.add_edge("function_b", "function_c")
    return f"DiGraph created with {G.number_of_nodes()} nodes, {G.number_of_edges()} edges"


# ── 4. Redis connectivity ────────────────────────────────────────
def check_redis_connection():
    import redis

    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    r.set("test_key", "hello_from_infra_check")
    val = r.get("test_key")
    r.delete("test_key")
    return f"Connected! set/get round-trip OK (got '{val}')"


# ── Main ──────────────────────────────────────────────────────────
def main():
    print("\n" + "=" * 55)
    print("  Phase 1 Infrastructure Verification")
    print("=" * 55 + "\n")

    print("[Imports]")
    check("qdrant-client", check_import_qdrant)
    check("tree-sitter", check_import_tree_sitter)
    check("tree-sitter-languages", check_import_tree_sitter_languages)
    check("networkx", check_import_networkx)
    check("openai", check_import_openai)
    check("redis", check_import_redis)

    print("\n[Qdrant Connection]")
    check("Qdrant @ localhost:6333", check_qdrant_connection)

    print("\n[NetworkX Graph]")
    check("DiGraph creation", check_networkx_graph)

    print("\n[Redis Connection]")
    check("Redis @ localhost:6379", check_redis_connection)

    # ── Summary ───────────────────────────────────────────────────
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print("\n" + "-" * 55)
    if passed == total:
        print(f"  {PASS}  ALL {total} CHECKS PASSED — infrastructure is ready!")
    else:
        print(f"  {FAIL}  {passed}/{total} checks passed. Review errors above.")
    print("-" * 55 + "\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
