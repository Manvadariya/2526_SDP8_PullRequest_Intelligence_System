import time
import traceback
from openai import OpenAI
from config import config


class LLMService:
    """
    Multi-provider LLM Service with automatic fallback chain:
      1. Groq (fastest, free)
      2. Gemini (reliable, Google)
      3. OpenRouter (broad model selection)
    
    If a provider fails or returns empty, automatically tries the next one.
    """
    
    def __init__(self):
        self.provider = config.LLM_PROVIDER.lower()  # kept for backward compat
        self._failed_providers = set()  # Track providers that failed this session
        
        # --- Initialize ALL available providers ---
        
        # 1. Groq (Primary)
        self.groq_client = None
        self.groq_model = config.GROQ_MODEL
        if config.GROQ_API_KEY:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=config.GROQ_API_KEY)
                print(f"  [LLM] ✓ Groq ready (model: {self.groq_model})")
            except Exception as e:
                print(f"  [LLM] ✗ Groq init failed: {e}")
        else:
            print("  [LLM] ✗ Groq not configured (no GROQ_API_KEY)")
        
        # 2. Gemini
        self.gemini_client = None
        self.gemini_model = config.GEMINI_MODEL
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                print(f"  [LLM] ✓ Gemini ready (model: {self.gemini_model})")
            except Exception as e:
                print(f"  [LLM] ✗ Gemini init failed: {e}")
        else:
            print("  [LLM] ✗ Gemini not configured (no GEMINI_API_KEY)")
        
        # 3. OpenRouter
        self.openrouter_client = None
        self.openrouter_model = config.MODEL
        if config.OPENROUTER_API_KEY:
            try:
                self.openrouter_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=config.OPENROUTER_API_KEY
                )
                print(f"  [LLM] ✓ OpenRouter ready (model: {self.openrouter_model})")
            except Exception as e:
                print(f"  [LLM] ✗ OpenRouter init failed: {e}")
        else:
            print("  [LLM] ✗ OpenRouter not configured (no OPENROUTER_API_KEY)")
        
        # Legacy alias for backward compat
        self.client = self.openrouter_client
        self.model = self.openrouter_model

    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = None, response_format: dict = None) -> str:
        """
        Unified chat with automatic fallback: Groq → Gemini → OpenRouter.
        
        If a provider fails, it's skipped for subsequent calls in this session.
        """
        # Build provider chain in priority order
        providers = []
        if self.groq_client and "groq" not in self._failed_providers:
            providers.append(("groq", self._chat_groq))
        if self.gemini_client and "gemini" not in self._failed_providers:
            providers.append(("gemini", self._chat_gemini))
        if self.openrouter_client and "openrouter" not in self._failed_providers:
            providers.append(("openrouter", self._chat_openrouter))
        
        # Also add failed providers at the end as last resort
        if self.groq_client and "groq" in self._failed_providers:
            providers.append(("groq", self._chat_groq))
        if self.gemini_client and "gemini" in self._failed_providers:
            providers.append(("gemini", self._chat_gemini))
        if self.openrouter_client and "openrouter" in self._failed_providers:
            providers.append(("openrouter", self._chat_openrouter))
        
        if not providers:
            print("  [LLM] ❌ No LLM providers available!")
            return ""
        
        for provider_name, chat_fn in providers:
            try:
                result = chat_fn(messages, temperature, max_tokens, response_format)
                if result:
                    # Success — un-fail this provider if it was marked
                    if provider_name in self._failed_providers:
                        print(f"  [LLM] ✓ {provider_name} recovered!")
                        self._failed_providers.discard(provider_name)
                    return result
                else:
                    print(f"  [LLM] ⚠ {provider_name} returned empty response, trying next provider...")
            except Exception as e:
                print(f"  [LLM] ❌ {provider_name} failed: {e}")
                self._failed_providers.add(provider_name)
                continue
        
        print(f"  [LLM] ❌ All providers failed!")
        return ""

    # ─── GROQ ──────────────────────────────────────────────────
    def _chat_groq(self, messages: list, temperature: float, max_tokens: int, response_format: dict) -> str:
        """Send chat to Groq API."""
        kwargs = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format
        
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = self.groq_client.chat.completions.create(**kwargs)
                
                if not response.choices or not response.choices[0].message.content:
                    self._log_empty_response("Groq", self.groq_model, response, attempt, max_retries)
                    if attempt < max_retries:
                        time.sleep(2 * attempt)
                        continue
                    return ""
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"  [LLM] ❌ Groq error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                else:
                    raise  # Let the fallback chain catch it

        return ""

    # ─── GEMINI ────────────────────────────────────────────────
    def _chat_gemini(self, messages: list, temperature: float, max_tokens: int, response_format: dict) -> str:
        """Send chat to Google Gemini."""
        from google.genai import types
        
        system_instruction = None
        contents = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=content)]
                ))
            else:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content)]
                ))
        
        config_kwargs = {"temperature": temperature}
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens
        if response_format and response_format.get("type") == "json_object":
            config_kwargs["response_mime_type"] = "application/json"
        
        gen_config = types.GenerateContentConfig(
            **config_kwargs,
            system_instruction=system_instruction,
        )
        
        response = self.gemini_client.models.generate_content(
            model=self.gemini_model,
            contents=contents,
            config=gen_config,
        )
        
        if not response.text:
            return ""
        return response.text.strip()

    # ─── OPENROUTER ────────────────────────────────────────────
    def _chat_openrouter(self, messages: list, temperature: float, max_tokens: int, response_format: dict) -> str:
        """Send chat to OpenRouter via OpenAI SDK with diagnostic logging."""
        kwargs = {
            "model": self.openrouter_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens
        if response_format:
            kwargs["response_format"] = response_format
        
        max_retries = 2
        for attempt in range(1, max_retries + 1):
            try:
                response = self.openrouter_client.chat.completions.create(**kwargs)
                
                if not response.choices or not response.choices[0].message.content:
                    self._log_empty_response("OpenRouter", self.openrouter_model, response, attempt, max_retries)
                    if attempt < max_retries:
                        time.sleep(2 * attempt)
                        continue
                    return ""
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"  [LLM] ❌ OpenRouter error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    time.sleep(2 * attempt)
                else:
                    raise  # Let the fallback chain catch it
        
        return ""

    # ─── HELPERS ───────────────────────────────────────────────
    def _log_empty_response(self, provider: str, model: str, response, attempt: int, max_retries: int):
        """Log diagnostic info when a response is empty."""
        print(f"  [LLM] ⚠ Empty response from {provider}/{model} (attempt {attempt}/{max_retries}):")
        print(f"    Choices count: {len(response.choices) if response.choices else 0}")
        if response.choices:
            choice = response.choices[0]
            print(f"    Finish reason: {getattr(choice, 'finish_reason', 'unknown')}")
            print(f"    Content: {repr(choice.message.content) if choice.message else 'no message'}")
        print(f"    Usage: {getattr(response, 'usage', 'unknown')}")

    def generate_summary(self, diff_text: str, title: str) -> dict:
        """Generates a summary using the LLM."""
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