from core.openai_service import OpenAIService
from mcp_client import MCPClient
from core.tools import ToolManager

class Chat:
    def __init__(self, claude_service: OpenAIService, clients: dict[str, MCPClient]):
        # Keeping variable name 'claude_service' to minimize refactor, 
        # but type is OpenAIService
        self.claude_service: OpenAIService = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[dict] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    # ... inside core/chat.py ...

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            try:
                # 1. Get tools
                tools = await ToolManager.get_all_tools(self.clients)

                # 2. Call the AI Service (Wrapped in try/except)
                message = self.claude_service.chat(
                    messages=self.messages,
                    tools=tools if tools else None,
                )
            except Exception as e:
                # Catch API errors (like 400 Bad Request) and return them as text
                return f"Error calling AI model: {str(e)}"

            # 3. Add assistant message to history
            assistant_msg_dict = {
                "role": "assistant",
                "content": message.content,
            }
            if message.tool_calls:
                assistant_msg_dict["tool_calls"] = message.tool_calls
            
            self.messages.append(assistant_msg_dict)

            # 4. Handle Tool Calls
            # 4. Handle Tool Calls
            if message.tool_calls:
                print(f"Tool calls: {[t.function.name for t in message.tool_calls]}")
                
                tool_results = await ToolManager.execute_tool_requests(
                    self.clients, message.tool_calls
                )

                # --- NEW TRIMMING LOGIC ---
                for result in tool_results:
                    # If content is huge (e.g., > 20,000 chars), truncate it
                    content_str = str(result.get("content", ""))
                    if len(content_str) > 20000:
                        print("⚠️ Trimming massive tool output to prevent rate limits...")
                        result["content"] = content_str[:20000] + "\n...[Output Truncated]..."
                # --------------------------

                self.messages.extend(tool_results)
            else:
                final_text_response = message.content or ""
                break

        return final_text_response