from openai import OpenAI
from config import config

class LLMService:
    def __init__(self):
        # self.client = OpenAI(
        #     base_url=config.LLM_BASE_URL,
        #     api_key=config.A4F_API_KEY
        # )
        # self.model = config.LLM_MODEL
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
            # FIX: Pass headers here inside the constructor
            default_headers={
                "HTTP-Referer": "https://github.com/Manvadariya/ai-review-test",
                "X-Title": "PR Review Bot"
            }
        )
        
        # OpenRouter requires the provider prefix (e.g., "openai/")
        self.model = config.MODEL

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            import json
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"LLM Error: {e}")
            return {"short_summary": "Analysis failed", "bullet_points": [], "risk_flags": []}