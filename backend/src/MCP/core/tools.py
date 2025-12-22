import json
from typing import Optional, List
from mcp.types import CallToolResult, Tool, TextContent
from mcp_client import MCPClient
from openai.types.chat import ChatCompletionMessageToolCall

class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        """Gets all tools and formats them for OpenAI."""
        tools = []
        for client in clients.values():
            tool_models = await client.list_tools()
            for t in tool_models:
                # OpenAI expects 'parameters' instead of 'input_schema'
                # and the whole thing wrapped in type: function
                tools.append({
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.inputSchema  # MCP schema is compatible with OpenAI parameters
                    }
                })
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        for client in clients:
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return client
        return None

    @classmethod
    async def execute_tool_requests(
        cls, clients: dict[str, MCPClient], tool_calls: List[ChatCompletionMessageToolCall]
    ) -> List[dict]:
        """Executes OpenAI tool calls and returns the results as tool messages."""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            tool_call_id = tool_call.id

            client = await cls._find_client_with_tool(
                list(clients.values()), tool_name
            )

            content = ""
            is_error = False

            if not client:
                content = "Error: Could not find that tool"
                is_error = True
            else:
                try:
                    tool_output: CallToolResult | None = await client.call_tool(
                        tool_name, tool_args
                    )
                    items = tool_output.content if tool_output else []
                    text_parts = [
                        item.text for item in items if isinstance(item, TextContent)
                    ]
                    content = "\n".join(text_parts)
                    if tool_output and tool_output.isError:
                        is_error = True
                except Exception as e:
                    content = f"Error executing tool '{tool_name}': {str(e)}"
                    is_error = True

            # OpenAI expects the result in a specific message format
            results.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": content
            })
            
        return results