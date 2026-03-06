from openai import OpenAI
from config import config

class LLMService:
    def __init__(self):
        self.provider = config.LLM_PROVIDER.lower()
        
        if self.provider == "gemini":
            from google import genai
            self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
            self.model = config.GEMINI_MODEL
            self.client = None  # No OpenAI client for Gemini
            print(f"  [LLM] Using Gemini provider with model: {self.model}")
        else:
            # Default: OpenRouter via OpenAI-compatible SDK
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=config.OPENROUTER_API_KEY
            )
            self.model = config.MODEL
            self.gemini_client = None
            print(f"  [LLM] Using OpenRouter provider with model: {self.model}")

    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = None, response_format: dict = None) -> str:
        """
        Unified chat method that works with both OpenRouter and Gemini.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Roles: 'system', 'user', 'assistant'
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Max tokens in response (optional)
            response_format: OpenAI-style response format, e.g. {"type": "json_object"}
            
        Returns:
            The text content of the LLM response.
        """
        if self.provider == "gemini":
            return self._chat_gemini(messages, temperature, max_tokens, response_format)
        else:
            return self._chat_openrouter(messages, temperature, max_tokens, response_format)

    def _chat_openrouter(self, messages: list, temperature: float, max_tokens: int, response_format: dict) -> str:
        """Send chat to OpenRouter via OpenAI SDK."""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        
        if not response.choices or not response.choices[0].message.content:
            return ""
        return response.choices[0].message.content.strip()

    def _chat_gemini(self, messages: list, temperature: float, max_tokens: int, response_format: dict) -> str:
        """Send chat to Google Gemini."""
        from google.genai import types
        
        # Separate system prompt from conversation messages
        system_instruction = None
        contents = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                # Gemini uses system_instruction instead of a system message
                system_instruction = content
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=content)]
                ))
            else:
                # user messages
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content)]
                ))
        
        # Build generation config
        config_kwargs = {
            "temperature": temperature,
        }
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
        
        # Map response_format to Gemini's response_mime_type
        if response_format and response_format.get("type") == "json_object":
            config_kwargs["response_mime_type"] = "application/json"
        
        gen_config = types.GenerateContentConfig(
            **config_kwargs,
            system_instruction=system_instruction,
        )
        
        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=contents,
            config=gen_config,
        )
        
        if not response.text:
            return ""
        return response.text.strip()

    def generate_summary(self, diff_text: str, title: str) -> dict:
        """
        Generates a summary using the LLM.
        """
        prompt = f"""
        Analyze this Git Diff for PR: "{title}"
        
        Diff:
        {diff_text[:15000]} # Truncate to avoid limit
        
        Output valid JSON with keys: 
        - short_summary (1 sentence)
        - bullet_points (list of 3-5 strings)
        - risk_flags (list of strings, e.g. "Database Migration")
        """
        
        try:
            content = self.chat(
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            import json
            return json.loads(content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"short_summary": "Analysis failed", "bullet_points": [], "risk_flags": []}