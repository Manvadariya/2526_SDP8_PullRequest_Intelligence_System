
import json
import traceback
from typing import List, Dict, Any
from core.llm import LLMService

class ReviewPlanner:
    """
    Pass 1 Agent: The "Tech Lead"
    Scans the PR files and decides WHAT to review and WHERE to focus.
    """
    def __init__(self):
        self.llm = LLMService()

    def analyze_pr_complexity(self, pr_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes the list of changed files to determine review strategy.
        
        Args:
            pr_files: List of dicts with keys like 'filename', 'patch', 'additions', 'deletions'
            
        Returns:
            JSON plan with keys:
            - review_strategy (str)
            - high_risk_files (List[str])
            - ignore_files (List[str])
            - focus_instructions (str)
        """
        # Prepare a lightweight summary for the LLM
        files_summary = []
        for f in pr_files:
            summary = f"- {f.get('filename')}: +{f.get('additions', 0)}/-{f.get('deletions', 0)} lines"
            # Add a snippet of the patch if small, or just first few lines
            patch = f.get('patch', '')
            if patch:
                summary += f"\n  Snippet: {patch[:200].replace(chr(10), ' ')}..."
            files_summary.append(summary)
            
        files_text = "\n".join(files_summary)
        
        prompt = f"""
        You are a Tech Lead triaging files for a Pull Request code review.
        
        ## Changed Files
        {files_text}
        
        ## Task
        Classify files for review priority:
        
        **high_risk_files**: Files with logic, security, APIs, database, or auth code. These get extra scrutiny.
        **ignore_files**: ONLY files that cannot contain bugs: README.md, CHANGELOG, LICENSE, .gitignore, package-lock.json, yarn.lock, *.yml config files.
        
        IMPORTANT: NEVER ignore source code files (.py, .java, .js, .ts, .cpp, .c, .go, .rs, .rb, .php). ALL source code MUST be reviewed.
        
        ## Output JSON
        {{
          "review_strategy": "focus_on_critical" | "broad_review",
          "high_risk_files": ["files needing extra attention"],
          "ignore_files": ["ONLY non-code files like docs/configs"],
          "focus_instructions": "Specific advice for the reviewer"
        }}
        
        Return ONLY valid JSON.
        """
        
        try:
            result = None
            max_retries = 3
            
            for attempt in range(1, max_retries + 1):
                try:
                    messages = [{"role": "user", "content": prompt}]
                    
                    # On retry, add explicit correction
                    if attempt > 1:
                        messages.append({"role": "assistant", "content": "0e400"})
                        messages.append({"role": "user", "content": "That is NOT valid JSON. You returned a number. Return a JSON object with keys: review_strategy, high_risk_files, ignore_files, focus_instructions. Start with { immediately."})
                    
                    response = self.llm.client.chat.completions.create(
                        model=self.llm.model,
                        messages=messages,
                        response_format={"type": "json_object"},
                        temperature=0.1
                    )
                    content = response.choices[0].message.content
                    print(f"  [Planner] Response (attempt {attempt}): {content[:100]}...")
                    
                    # Pre-check: must contain { to be a JSON object
                    if '{' not in content:
                        print(f"  [Planner] ⚠️ No JSON object in response (attempt {attempt})")
                        continue
                    
                    # Strip markdown code fences if present
                    clean = content.strip()
                    if clean.startswith("```"):
                        # Remove opening fence (```json or ```)
                        first_newline = clean.find('\n')
                        if first_newline > 0:
                            clean = clean[first_newline + 1:]
                        # Remove closing fence
                        if clean.rstrip().endswith("```"):
                            clean = clean.rstrip()[:-3].rstrip()
                    
                    plan = json.loads(clean)
                    
                    if not isinstance(plan, dict):
                        print(f"  [Planner] ⚠️ Got {type(plan).__name__} instead of dict (attempt {attempt})")
                        continue
                    
                    # Sanity checks
                    if "high_risk_files" not in plan: plan["high_risk_files"] = []
                    if "ignore_files" not in plan: plan["ignore_files"] = []
                    
                    print(f"  [Planner] ✅ Plan ready: {len(plan.get('high_risk_files', []))} high-risk, {len(plan.get('ignore_files', []))} ignored")
                    return plan
                    
                except (json.JSONDecodeError, ValueError) as parse_err:
                    print(f"  [Planner] ⚠️ Parse failed (attempt {attempt}): {parse_err}")
                    continue
            
            # All retries failed
            print(f"  [Planner] ❌ All {max_retries} attempts failed. Falling back to full review.")
            return {
                "review_strategy": "fallback_full_review",
                "high_risk_files": [f.get('filename') for f in pr_files],
                "ignore_files": [],
                "focus_instructions": "Review all files — planner could not generate plan after 3 attempts."
            }
            
        except Exception as e:
            print(f"⚠️ Planner Failed: {e}")
            traceback.print_exc()
            # Fallback: Review everything
            return {
                "review_strategy": "fallback_full_review",
                "high_risk_files": [f.get('filename') for f in pr_files],
                "ignore_files": [],
                "focus_instructions": "Review all files due to planner failure."
            }
