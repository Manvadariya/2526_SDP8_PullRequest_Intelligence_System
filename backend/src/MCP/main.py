import sys
import os
import shutil
from dotenv import load_dotenv
from contextlib import AsyncExitStack

from mcp_client import MCPClient
from core.openai_service import OpenAIService
from core.cli_chat import CliChat
from core.cli import CliApp

# Import anyio for the event loop
import anyio

load_dotenv()


or_key = os.getenv("OPENROUTER_API_KEY", "")
assert or_key, "Error: OPENROUTER_API_KEY cannot be empty. Update .env"


# Check Environment

assert hf_token, "Error: HF_TOKEN cannot be empty. Update .env"

assert github_token, "Error: GITHUB_TOKEN cannot be empty. Update .env"

async def main():
    openai_service = OpenAIService()
    
    # Define the servers we want to use
    servers_config = [
        # 1. Your Local Document Server (Python)
        {
            "name": "local_docs",
            "command": "python",
            "args": ["mcp_server.py"]
        },
        # 2. Official GitHub Server (Node.js via npx)
        {
            "name": "official_github",
            "command": "npx", 
            "args": ["-y", "@modelcontextprotocol/server-github"]
        }
    ]

    # Windows Compatibility Fix: Use npx.cmd if on Windows
    if sys.platform == "win32":
        npx_path = shutil.which("npx")
        for server in servers_config:
            if server["command"] == "npx":
                if npx_path:
                    server["command"] = npx_path
                else:
                    server["command"] = "npx.cmd"

    clients = {}
    doc_client = None

    async with AsyncExitStack() as stack:
        print("\n🔌 Connecting to servers...")
        
        for config in servers_config:
            try:
                print(f"   - {config['name']}...", end=" ", flush=True)
                
                client = await stack.enter_async_context(
                    MCPClient(
                        command=config["command"], 
                        args=config["args"],
                        # Pass environment to subprocess so GitHub server sees the token
                        env=os.environ.copy() 
                    )
                )
                clients[config['name']] = client
                print("✅ Connected")
                
                # Assign first server as doc_client (needed by your CliChat class)
                if doc_client is None:
                    doc_client = client
                    
            except Exception as e:
                print(f"❌ Failed: {e}")
                print(f"     (Make sure Node.js is installed if using npx)")

        if not clients:
            print("Error: No servers connected. Exiting.")
            return

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            claude_service=openai_service,
        )

        cli = CliApp(chat)
        await cli.initialize()
        await cli.run()

if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        pass