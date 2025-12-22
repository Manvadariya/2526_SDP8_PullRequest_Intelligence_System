import sys
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

class MCPClient:
    def __init__(self, command: str, args: list[str], env: Optional[dict] = None):
        self.command = command
        self.args = args
        self.env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack = AsyncExitStack()

    async def __aenter__(self):
        # We use a try/except to catch immediate startup failures
        try:
            server_params = StdioServerParameters(
                command=self.command,
                args=self.args,
                env=self.env,
            )
            
            # 1. Start Transport
            read, write = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            # 2. Start Session
            self._session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # 3. Initialize
            await self._session.initialize()
            return self
            
        except Exception as e:
            # Clean up if init fails
            await self._exit_stack.aclose()
            raise e

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)

    def session(self) -> ClientSession:
        if not self._session:
            raise RuntimeError("Session is not initialized")
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        res = await self.session().list_tools()
        return res.tools

    async def call_tool(self, name: str, args: dict) -> types.CallToolResult:
        return await self.session().call_tool(name, arguments=args)

    async def list_prompts(self) -> list[types.Prompt]:
        res = await self.session().list_prompts()
        return res.prompts

    async def get_prompt(self, name: str, args: dict) -> list[types.PromptMessage]:
        res = await self.session().get_prompt(name, arguments=args)
        return res.messages

    async def read_resource(self, uri: str) -> str:
        res = await self.session().read_resource(uri)
        return res.contents[0].text