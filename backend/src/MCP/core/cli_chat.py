from typing import List, Tuple
from mcp.types import Prompt, PromptMessage

from core.chat import Chat
from core.openai_service import OpenAIService
from mcp_client import MCPClient

class CliChat(Chat):
    def __init__(
        self,
        doc_client: MCPClient,
        clients: dict[str, MCPClient],
        claude_service: OpenAIService,
    ):
        super().__init__(clients=clients, claude_service=claude_service)
        self.doc_client: MCPClient = doc_client

    # ... [Keep existing methods: list_prompts, list_docs_ids, get_doc_content, get_prompt, _extract_resources] ...
    
    # We must replicate the existing methods because we are overwriting the file content.
    # To save space, I assume you keep the logic for list_prompts, list_docs_ids etc. 
    # Only _process_command and convert functions need check for message format.

    async def list_prompts(self) -> list[Prompt]:
        return await self.doc_client.list_prompts()

    async def list_docs_ids(self) -> list[str]:
        return await self.doc_client.read_resource("docs://documents")

    async def get_doc_content(self, doc_id: str) -> str:
        return await self.doc_client.read_resource(f"docs://documents/{doc_id}")

    async def get_prompt(self, command: str, doc_id: str) -> list[PromptMessage]:
        return await self.doc_client.get_prompt(command, {"doc_id": doc_id})

    async def _extract_resources(self, query: str) -> str:
        mentions = [word[1:] for word in query.split() if word.startswith("@")]
        doc_ids = await self.list_docs_ids()
        mentioned_docs: list[Tuple[str, str]] = []

        for doc_id in doc_ids:
            if doc_id in mentions:
                content = await self.get_doc_content(doc_id)
                mentioned_docs.append((doc_id, content))

        return "".join(
            f'\n<document id="{doc_id}">\n{content}\n</document>\n'
            for doc_id, content in mentioned_docs
        )

    async def _process_command(self, query: str) -> bool:
        if not query.startswith("/"):
            return False

        words = query.split()
        command = words[0].replace("/", "")
        
        # Helper to avoid index out of bounds if user types just /command
        arg = words[1] if len(words) > 1 else ""

        messages = await self.doc_client.get_prompt(
            command, {"doc_id": arg}
        )

        self.messages += convert_prompt_messages_to_dict(messages)
        return True

    async def _process_query(self, query: str):
        if await self._process_command(query):
            return

        added_resources = await self._extract_resources(query)

        prompt = f"""
        The user has a question:
        <query>
        {query}
        </query>

        The following context may be useful in answering their question:
        <context>
        {added_resources}
        </context>

        Answer directly and concisely.
        """

        self.messages.append({"role": "user", "content": prompt})


def convert_prompt_messages_to_dict(
    prompt_messages: List[PromptMessage],
) -> List[dict]:
    # Simplified converter for OpenAI which uses simple "role", "content" dicts
    result = []
    for msg in prompt_messages:
        role = "user" if msg.role == "user" else "assistant"
        content_text = ""
        
        if hasattr(msg.content, "text"):
            content_text = msg.content.text
        elif isinstance(msg.content, list):
             # Extract text from list of blocks
             content_text = "\n".join(
                 [item.text for item in msg.content if hasattr(item, "text")]
             )
        elif isinstance(msg.content, str):
            content_text = msg.content
            
        result.append({"role": role, "content": content_text})
    return result