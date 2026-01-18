from core.llm import LLMService
from core.diff_parser import DiffParser
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ReviewerAgent:
    def __init__(self):
        self.llm = LLMService()
        self.diff_parser = DiffParser()
        self.executor = ThreadPoolExecutor(max_workers=5)

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
    
    async def run_multi_file(self, raw_diff: str, pr_title: str, custom_instructions: str) -> dict:
        """
        Generates separate reviews for each file in the diff (in parallel).
        Returns: {"src/app.py": "review...", "src/utils.py": "review..."}
        """
        # Parse diff into per-file sections
        file_diffs = self.diff_parser.parse_diff(raw_diff)
        
        # Process all files in parallel
        loop = asyncio.get_event_loop()
        tasks = []
        
        for filepath, diff_content in file_diffs.items():
            formatted_diff = self.diff_parser.format_diff_block(diff_content)
            # Run each file review in parallel using thread pool
            task = loop.run_in_executor(
                self.executor,
                self._review_single_file,
                filepath,
                formatted_diff,
                pr_title,
                custom_instructions
            )
            tasks.append((filepath, task))
        
        # Wait for all reviews to complete
        file_reviews = {}
        for filepath, task in tasks:
            review = await task
            file_reviews[filepath] = review
        
        return file_reviews
    
    def _review_single_file(self, filepath: str, formatted_diff: str, pr_title: str, custom_instructions: str) -> str:
        """Review a single file."""
        
        # Truncate if too long
        if len(formatted_diff) > 20000:
            formatted_diff = formatted_diff[:20000]
        
        # Get AI analysis with simplified prompt
        prompt = f"""
Review this code change. Reply ONLY with JSON (no markdown):

File: {filepath}
Diff:
{formatted_diff[:3000]}

JSON Format:
{{
  "what_changed": "brief description",
  "issues_severity": "Critical/Warning/None",
  "issues_list": ["issue with line #"],
  "impact": "Positive/Negative/Neutral",
  "proposed_fixes": ["action"],
  "before_code": "bad code",
  "after_code": "fixed code",
  "ai_agent_prompt": "fix instruction",
  "security_risk": "Yes/No",
  "stability_risk": "Yes/No",
  "risk_level": "High/Low/None",
  "verdict": "APPROVE/REQUEST_CHANGES/COMMENT"
}}

Instructions: {custom_instructions[:200]}
"""
        
        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}],
            )
            ai_response = response.choices[0].message.content
            
            # Parse JSON response
            try:
                import json
                import re
                
                # Extract JSON from markdown code blocks if present
                if "```json" in ai_response:
                    ai_response = ai_response.split("```json")[1].split("```")[0].strip()
                elif "```" in ai_response:
                    ai_response = ai_response.split("```")[1].split("```")[0].strip()
                
                review_data = json.loads(ai_response)
            except:
                # Fallback data
                review_data = {
                    "what_changed": "Code modifications detected",
                    "issues_severity": "Info",
                    "issues_list": [],
                    "impact": "Neutral - Review manually",
                    "proposed_fixes": [],
                    "before_code": "",
                    "after_code": "",
                    "ai_agent_prompt": "Review and validate the changes",
                    "security_risk": "No",
                    "stability_risk": "No",
                    "risk_level": "Low",
                    "verdict": "COMMENT"
                }
            
            # Extract clean code blocks from diff (remove diff markers)
            clean_code_blocks = self._extract_clean_code(formatted_diff)
            
            # Build comment
            verdict_emoji = "✅" if review_data["verdict"] == "APPROVE" else "⚠️" if review_data["verdict"] == "REQUEST_CHANGES" else "💬"
            
            final_comment = f"""## {verdict_emoji} AI Code Review

### 📋 Summary

- **What Changed:** {review_data['what_changed']}
- **Issues Found:** {review_data['issues_severity']}
- **Impact:** {review_data['impact']}

"""
            
            # Proposed Fix section
            if review_data['proposed_fixes']:
                fixes_list = "\n".join([f"- {fix}" for fix in review_data['proposed_fixes']])
                final_comment += f"""<details>
<summary>🔎 <strong>Proposed Fix</strong></summary>

#### Action

{fixes_list}

#### Example

{clean_code_blocks if clean_code_blocks else "See diff above"}

</details>

"""
            
            # Committable Suggestion section
            if review_data['before_code'] or review_data['after_code']:
                before = review_data['before_code'] or "// No before code"
                after = review_data['after_code'] or "// No after code"
                
                final_comment += f"""<details>
<summary>📝 <strong>Committable Suggestion</strong></summary>

```javascript
// ❌ Before
{before}
```

```javascript
// ✅ After
{after}
```

✔ Safe to commit

</details>

"""
            
            # Prompt for AI Agents
            final_comment += f"""<details>
<summary>🤖 <strong>Prompt for AI Agents</strong></summary>

```
{review_data['ai_agent_prompt']}
Ensure the code builds and runs.
Follow existing project conventions.
Return updated code only.
```

</details>

"""
            
            # Risk Check
            security_status = "❌" if review_data['security_risk'] == "Yes" else "✅"
            stability_status = "❌" if review_data['stability_risk'] == "Yes" else "✅"
            
            final_comment += f"""<details>
<summary>⚠️ <strong>Risk Check</strong></summary>

- **Security:** {security_status} {review_data['security_risk']}
- **Stability:** {stability_status} {review_data['stability_risk']}
- **Risk Level:** {review_data['risk_level']}

</details>

"""
            
            # Verdict
            verdict_text = {
                "APPROVE": "✅ Approved - Safe to merge",
                "REQUEST_CHANGES": "⚠️ Changes required before merge",
                "COMMENT": "💬 Review comments provided"
            }.get(review_data['verdict'], "Review completed")
            
            final_comment += f"### {verdict_text}\n"
            
            return final_comment
            
        except Exception as e:
            return f"⚠️ AI Review Failed: {e}"
    
    def _extract_clean_code(self, diff: str, max_lines: int = 50) -> str:
        """Extract clean code from diff, removing diff markers and applying ellipsis if too long."""
        lines = diff.split('\n')
        clean_lines = []
        
        for line in lines:
            # Skip diff headers
            if line.startswith('diff --git') or line.startswith('index ') or \
               line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                continue
            
            # Remove +/- markers but keep the code
            if line.startswith('+') and not line.startswith('+++'):
                clean_lines.append(line[1:])  # Remove the + marker
            elif line.startswith('-') and not line.startswith('---'):
                continue  # Skip deleted lines in clean view
            elif not line.startswith('-') and not line.startswith('+'):
                clean_lines.append(line)  # Context lines
        
        # Apply ellipsis if too long
        if len(clean_lines) > max_lines:
            top = clean_lines[:15]
            bottom = clean_lines[-15:]
            middle_count = len(clean_lines) - 30
            clean_lines = top + [f"\n  // ... ({middle_count} lines omitted) ...\n"] + bottom
        
        return '\n'.join(clean_lines)