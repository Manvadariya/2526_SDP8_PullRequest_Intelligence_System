"""Quick test: Verify PR Review MCP Server starts and tools are listed."""
import sys
import os
import asyncio

sys.stdout.reconfigure(encoding='utf-8')

# Add paths
MCP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "MCP"))
WEBHOOKS_PATH = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, MCP_PATH)
sys.path.insert(0, WEBHOOKS_PATH)

from dotenv import load_dotenv
load_dotenv(override=True)

from mcp_client import MCPClient
from contextlib import AsyncExitStack

async def test():
    print("=" * 60)
    print("  Testing PR Review MCP Server")
    print("=" * 60)
    
    async with AsyncExitStack() as stack:
        print("\n[1] Starting pr_review_server.py via MCP...")
        try:
            client = await stack.enter_async_context(
                MCPClient(
                    command=sys.executable,
                    args=[os.path.join(MCP_PATH, "pr_review_server.py")],
                    env=os.environ.copy(),
                )
            )
            print("    OK - Server started and connected")
        except Exception as e:
            print(f"    FAIL - {e}")
            return
        
        print("\n[2] Listing available tools...")
        try:
            tools = await client.list_tools()
            print(f"    OK - Found {len(tools)} tools:")
            for t in tools:
                print(f"      - {t.name}: {t.description[:60]}...")
        except Exception as e:
            print(f"    FAIL - {e}")
            return
        
        print("\n[3] Testing list_changed_files tool with sample diff...")
        try:
            sample_diff = """diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,3 +1,5 @@
+import logging
 from flask import Flask
 app = Flask(__name__)
+logging.basicConfig(level=logging.DEBUG)
"""
            result = await client.call_tool("list_changed_files", {"diff_text": sample_diff})
            print(f"    OK - Result: {result.content[0].text}")
        except Exception as e:
            print(f"    FAIL - {e}")
    
    print("\n" + "=" * 60)
    print("  All tests passed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
