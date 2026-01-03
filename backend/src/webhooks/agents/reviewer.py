import os
from core.llm import LLMService

class ReviewerAgent:
    def __init__(self):
        self.llm = LLMService()

    def _read_best_practices(self) -> str:
        try:
            with open("best_practices.md", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "No specific best practices provided."

    def run(self, raw_diff: str, pr_title: str) -> str:
        # 1. Load Local Knowledge
        best_practices = self._read_best_practices()

        # 2. Construct the Prompt (Matching n8n logic)
        prompt = f"""
        You are a Senior Code Reviewer.
        
        CONTEXT:
        We have a set of team guidelines that MUST be followed:
        {best_practices}

        YOUR MISSION:
        - Review the code changes below file by file.
        - Generate inline comments/feedback based on the Best Practices above.
        - Ignore files without significant changes.
        - Do not summarize what the code does, point out improvements or bugs.
        - If the code violates a Best Practice, reference it explicitly.

        PR TITLE: {pr_title}

        CODE DIFF:
        ```diff
        {raw_diff[:25000]}  # Truncate to prevent token overflow
        ```

        OUTPUT FORMAT:
        Provide a friendly but professional Markdown review.
        """

        # 3. Call AI
        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Review Failed: {e}"