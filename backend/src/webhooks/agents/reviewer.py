from core.llm import LLMService

class ReviewerAgent:
    def __init__(self):
        self.llm = LLMService()

    def _compress_diff(self, raw_diff: str) -> str:
        """
        Compresses deleted blocks but ALWAYS preserves added lines (+).
        """
        lines = raw_diff.split('\n')
        compressed_lines = []
        deletion_count = 0
        
        for line in lines:
            # Case 1: Deleted line
            if line.startswith('-') and not line.startswith('---'):
                deletion_count += 1
                if deletion_count <= 5: # Keep first 5 deleted lines for context
                    compressed_lines.append(line)
                elif deletion_count == 6:
                    compressed_lines.append(f"... [ {deletion_count} lines deleted ] ...")
                # Skip the rest
            
            # Case 2: Added line or Context or Header
            else:
                # If we were deleting, update the marker (visual fix)
                if deletion_count > 5:
                    compressed_lines[-1] = f"... [ {deletion_count} lines deleted ] ..."
                
                deletion_count = 0
                compressed_lines.append(line)
        
        # Join back together
        return "\n".join(compressed_lines)

    def run(self, raw_diff: str, pr_title: str, custom_instructions: str) -> str:
        
        # 1. Compress
        clean_diff = self._compress_diff(raw_diff)
        
        # 2. Safety Truncate (Keep first 30k chars, but usually 'clean_diff' is small now)
        final_diff = clean_diff[:30000]

        prompt = f"""
        You are a Senior Code Reviewer.
        
        INSTRUCTIONS FROM REPO OWNER:
        {custom_instructions}

        PR TITLE: {pr_title}

        CODE DIFF:
        ```diff
        {final_diff}
        ```

        OUTPUT RULES:
        1. **Length**: Keep it MEDIUM sized. Be direct.
        2. **Structure**:
           - **🔍 Critics & Issues**: List specific problems.
           - **💡 Recommendations**: Brief suggestions.
           - **📝 Executive Summary**: Final verdict.
        3. **Tone**: Follow the instructions style.

        Review the code now.
        """

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"AI Review Failed: {e}"