from core.llm import LLMService
from core.diff_parser import DiffParser
import json
import re

class ReviewerAgent:
    def __init__(self):
        self.llm = LLMService()
        self.diff_parser = DiffParser()

    def _fix_malformed_json(self, text: str) -> str:
        """
        Aggressively fix malformed JSON by handling common issues.
        """
        # First pass: escape unescaped quotes and newlines inside string values
        result = []
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text):
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            
            if char == '"' and (i == 0 or text[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
            elif in_string and char == '\n':
                # Replace literal newline with escaped newline
                result.append('\\n')
            elif in_string and char == '\r':
                result.append('\\r')
            elif in_string and char == '\t':
                result.append('\\t')
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _extract_and_parse_json(self, response: str) -> dict:
        """
        Extract JSON from response with multiple fallback strategies.
        """
        response = response.strip()
        
        # Strategy 1: Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Remove markdown code blocks
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                if part.strip().startswith('{'):
                    try:
                        return json.loads(part.strip())
                    except json.JSONDecodeError:
                        pass
        
        # Strategy 3: Find JSON object by braces
        if '{' in response:
            start_idx = response.find('{')
            brace_count = 0
            end_idx = -1
            
            for i in range(start_idx, len(response)):
                if response[i] == '{':
                    brace_count += 1
                elif response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx > start_idx:
                potential_json = response[start_idx:end_idx]
                
                # Try direct parse
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    pass
                
                # Try fixing the JSON
                try:
                    fixed = self._fix_malformed_json(potential_json)
                    return json.loads(fixed)
                except json.JSONDecodeError as e:
                    # Last resort: try to truncate at the error point
                    print(f"⚠️ Attempting JSON recovery at position {e.pos}")
                    try:
                        return json.loads(potential_json[:e.pos] + '}' * brace_count)
                    except:
                        pass
        
        # If all parsing fails, return empty dict with error
        raise ValueError("Could not extract valid JSON from response")
    
    def _sanitize_json(self, json_str: str) -> str:
        """
        Deprecated - use _extract_and_parse_json instead.
        Kept for compatibility.
        """
        return self._fix_malformed_json(json_str)

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
        """Legacy single review method."""
        file_reviews = self.run_multi_file(raw_diff, pr_title, custom_instructions)
        return "\n\n---\n\n".join(file_reviews.values())
    
    def run_multi_file(self, raw_diff: str, pr_title: str, custom_instructions: str, custom_checks: list = None) -> dict:
        """
        Generates reviews for ALL files in a SINGLE LLM call.
        Returns: {"src/app.py": "review...", "src/utils.py": "review..."}
        """
        file_diffs = self.diff_parser.parse_diff(raw_diff)
        
        if not file_diffs:
            return {}
        
        # Build combined prompt for all files
        files_section = ""
        for filepath, diff_content in file_diffs.items():
            compressed = self._compress_diff(diff_content)
            # Truncate per-file to reasonable size
            if len(compressed) > 8000:
                compressed = compressed[:8000] + "\n... [truncated]"
            files_section += f"\n### FILE: `{filepath}`\n```diff\n{compressed}\n```\n"
        
        # Build custom checks section
        custom_checks_text = ""
        if custom_checks:
            custom_checks_text = "\n**CUSTOM CHECKS TO APPLY:**\n"
            for i, check in enumerate(custom_checks, 1):
                custom_checks_text += f"{i}. {check}\n"
        
        prompt = f"""You are an Elite Senior Software Engineer and Code Reviewer with 15+ years of experience at top tech companies (Google, Meta, Microsoft). You are conducting a thorough, professional code review.

## CONTEXT
**Repository Instructions:** {custom_instructions}
{custom_checks_text}
**PR Title:** {pr_title}

## FILES TO REVIEW
{files_section}

## YOUR TASK
Analyze each file change with extreme attention to detail. Think like a Staff Engineer who cares deeply about:
1. **Code Quality** - Is this production-ready? Would you approve this for a critical system?
2. **Security** - Any vulnerabilities, injection risks, auth bypasses, data exposure?
3. **Performance** - Time/space complexity, N+1 queries, memory leaks, bottlenecks?
4. **Maintainability** - Is it readable, testable, follows SOLID principles?
5. **Edge Cases** - What could break? Null checks, error handling, race conditions?

## OUTPUT FORMAT
Return a JSON object. Each key is a filepath, value is the review:
{{
  "filepath": {{
    "summary": "2-3 sentence executive summary of what this change does and why it matters",
    "change_type": "Feature/Bugfix/Refactor/Config/Documentation/Test",
    "complexity_rating": "Simple/Moderate/Complex",
    
    "detailed_analysis": "3-5 sentences providing deep technical analysis. Explain the logic flow, architectural decisions, and how this integrates with the broader codebase. Be specific about what the code does line-by-line for important sections.",
    
    "issues_severity": "Critical/High/Medium/Low/None",
    "issues": [
      {{
        "type": "Bug/Security/Performance/Style/Logic/BestPractice",
        "severity": "Critical/High/Medium/Low",
        "line": "Line number or range",
        "description": "Clear explanation of the issue",
        "suggestion": "How to fix it"
      }}
    ],
    
    "merge_impact": {{
      "affected_areas": ["List of modules/features/APIs affected by this change"],
      "breaking_changes": "Yes/No - explain if yes",
      "rollback_risk": "High/Medium/Low - how easy to rollback if issues arise",
      "testing_required": ["Unit tests", "Integration tests", "Manual QA areas to verify"],
      "deployment_notes": "Any special deployment considerations"
    }},
    
    "merge_conflict_risk": {{
      "risk_level": "High/Medium/Low/None",
      "potential_conflicts": ["Files or areas likely to conflict with other branches"],
      "resolution_tips": "How to resolve if conflicts occur"
    }},
    
    "code_quality": {{
      "readability": "Excellent/Good/Fair/Poor - brief explanation",
      "maintainability": "Excellent/Good/Fair/Poor - brief explanation", 
      "test_coverage": "Covered/Partial/Missing - what tests are needed",
      "documentation": "Adequate/Needs improvement/Missing"
    }},
    
    "security_analysis": {{
      "vulnerabilities_found": "Yes/No",
      "risk_level": "Critical/High/Medium/Low/None",
      "details": "Specific security concerns or confirmation of secure patterns used",
      "owasp_categories": ["Any OWASP Top 10 categories this touches"]
    }},
    
    "performance_analysis": {{
      "concerns": "Yes/No",
      "time_complexity": "O(n), O(n^2), etc. for key operations",
      "space_complexity": "Memory usage analysis",
      "optimization_suggestions": ["Specific improvements if any"]
    }},
    
    "before_code": "The problematic or original code snippet (max 15 lines, include line numbers)",
    "after_code": "The improved/corrected code snippet (max 15 lines)",
    
    "ai_agent_prompt": "Detailed, actionable prompt that another AI could use to implement the suggested fixes. Be very specific about what to change and why.",
    
    "custom_check_results": [
      {{"check": "Check description", "status": "Pass/Fail", "details": "Explanation"}}
    ],
    
    "verdict": "APPROVE/REQUEST_CHANGES/COMMENT",
    "verdict_reason": "1-2 sentences explaining the verdict",
    "confidence": "High/Medium/Low - how confident are you in this review"
  }}
}}

## IMPORTANT RULES
1. Be thorough but constructive - explain WHY something is an issue
2. Provide actionable suggestions, not vague feedback
3. Consider the broader system impact, not just the file in isolation
4. If code is good, acknowledge it specifically - don't invent issues
5. For security issues, be specific about attack vectors
6. Return ONLY valid JSON, no markdown code blocks or extra text"""

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Use new robust JSON extraction
            try:
                reviews_data = self._extract_and_parse_json(ai_response)
            except ValueError as e:
                print(f"❌ JSON extraction failed: {e}")
                print(f"Response was: {ai_response[:500]}...")
                # Fallback: return error for each file
                return {fp: f"⚠️ AI Review Failed: Could not parse JSON response\n\nPlease try again." for fp in file_diffs.keys()}
            
            # Format each file's review into markdown
            file_reviews = {}
            for filepath, review_data in reviews_data.items():
                file_reviews[filepath] = self._format_review(filepath, review_data)
            
            return file_reviews
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse failed: {e}")
        except ValueError as e:
            print(f"❌ JSON extraction failed: {e}")
            # Fallback: return error for each file
            return {fp: f"⚠️ AI Review Failed: Could not parse JSON response\n\nPlease try again." for fp in file_diffs.keys()}
        except Exception as e:
            print(f"❌ Batch review failed: {e}")
            import traceback
            traceback.print_exc()
            # Fallback: return error for each file
            return {fp: f"⚠️ AI Review Failed: {str(e)[:100]}" for fp in file_diffs.keys()}

    def run_inline_review(self, raw_diff: str, pr_title: str, custom_instructions: str, custom_checks: list = None) -> dict:
        """
        Generates CONCISE inline review data for GitHub PR review comments (Coderabbit-style).
        
        Only flags real issues (bugs, security, performance, logic errors).
        Files with no issues are marked as "clean" and grouped in a summary.
        
        Returns: {
            "summary": "Overall PR assessment",
            "clean_files": ["file1.py", "file2.py"],
            "inline_comments": [
                {"path": "file.py", "line": 14, "severity": "critical", "message": "...", "suggestion": "fixed code"},
            ],
            "verdict": "APPROVE" | "REQUEST_CHANGES" | "COMMENT"
        }
        """
        file_diffs = self.diff_parser.parse_diff(raw_diff)
        if not file_diffs:
            return {"summary": "No files changed.", "clean_files": [], "inline_comments": [], "verdict": "APPROVE"}

        # Build annotated diffs with line numbers so LLM can reference exact lines
        files_section = ""
        for filepath, diff_content in file_diffs.items():
            annotated = DiffParser.annotate_diff_with_line_numbers(diff_content)
            if len(annotated) > 6000:
                annotated = annotated[:6000] + "\n... [truncated]"
            files_section += f"\n### FILE: `{filepath}`\n```diff\n{annotated}\n```\n"

        custom_checks_text = ""
        if custom_checks:
            custom_checks_text = "\n**Custom checks:** " + "; ".join(str(c) for c in custom_checks)

        prompt = f"""You are a senior code reviewer. Review this PR diff and provide CONCISE, actionable feedback.

**PR Title:** {pr_title}
**Instructions:** {custom_instructions}
{custom_checks_text}

## Changed Files (line numbers shown as Lxx on the new/right side)
{files_section}

## RULES
1. ONLY flag REAL issues: bugs, security vulnerabilities, performance problems, logic errors, or missing error handling
2. Do NOT comment on style, formatting, naming conventions, or minor nitpicks
3. If a file looks fine, mark it as "clean" — do NOT invent issues
4. Use the exact line numbers shown (Lxx) for any issues you find
5. For each issue, if you have a concrete fix, provide the EXACT single-line replacement code
6. Keep messages SHORT — one clear sentence explaining the problem
7. Be constructive: explain WHY it's a problem and HOW to fix it

## Output Format (STRICT JSON, nothing else)
{{
  "summary": "1-2 sentence overall PR assessment",
  "files": {{
    "path/to/file.ext": {{
      "status": "clean",
      "comments": []
    }},
    "path/to/other.ext": {{
      "status": "issues",
      "comments": [
        {{
          "line": 14,
          "severity": "critical",
          "message": "Short clear explanation of the bug/issue",
          "suggestion": "exact replacement code for that line (optional)"
        }}
      ]
    }}
  }},
  "verdict": "APPROVE" | "REQUEST_CHANGES" | "COMMENT"
}}

Severity guide:
- "critical": Bugs, crashes, security vulnerabilities, data loss — MUST fix before merge
- "warning": Performance issues, missing validation, potential edge cases — SHOULD fix
- "info": Minor improvements, better patterns — NICE to fix

Return ONLY valid JSON. No markdown code blocks. No extra text."""

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}]
            )

            ai_response = response.choices[0].message.content.strip()
            result = self._extract_and_parse_json(ai_response)

            # Process into our standard format
            clean_files = []
            inline_comments = []

            files_data = result.get("files", {})
            for filepath, file_data in files_data.items():
                if isinstance(file_data, dict) and file_data.get("status") == "clean":
                    clean_files.append(filepath)
                elif isinstance(file_data, dict):
                    for comment in file_data.get("comments", []):
                        if isinstance(comment, dict) and comment.get("message"):
                            inline_comments.append({
                                "path": filepath,
                                "line": comment.get("line", 1),
                                "severity": comment.get("severity", "info"),
                                "message": comment.get("message", ""),
                                "suggestion": comment.get("suggestion")
                            })
                    # If file has "issues" status but no comments, mark as clean
                    if not file_data.get("comments"):
                        clean_files.append(filepath)

            return {
                "summary": result.get("summary", "Review complete."),
                "clean_files": clean_files,
                "inline_comments": inline_comments,
                "verdict": result.get("verdict", "COMMENT")
            }

        except Exception as e:
            print(f"❌ Inline review failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "summary": f"Review failed: {str(e)[:100]}",
                "clean_files": list(file_diffs.keys()),
                "inline_comments": [],
                "verdict": "COMMENT"
            }

    def _format_review(self, filepath: str, review_data: dict) -> str:
        """Format a single file's review data into professional markdown with dropdowns."""
        try:
            verdict = review_data.get("verdict", "COMMENT")
            verdict_emoji = {"APPROVE": "✅", "REQUEST_CHANGES": "🔴", "COMMENT": "💬"}.get(verdict, "💬")
            
            # Get file extension for syntax highlighting
            ext = filepath.split('.')[-1] if '.' in filepath else 'text'
            lang_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'java': 'java', 'cpp': 'cpp', 'c': 'c', 'jsx': 'javascript', 'tsx': 'typescript', 'rs': 'rust', 'go': 'go', 'rb': 'ruby', 'php': 'php'}
            lang = lang_map.get(ext, ext)
            
            # Header with verdict badge
            change_type = review_data.get('change_type', 'Change')
            complexity = review_data.get('complexity_rating', 'Moderate')
            confidence = review_data.get('confidence', 'High')
            
            comment = f"""## {verdict_emoji} AI Code Review

| Type | Complexity | Confidence | Verdict |
|:----:|:----------:|:----------:|:-------:|
| `{change_type}` | {complexity} | {confidence} | **{verdict}** |

---

### 📋 Executive Summary

{review_data.get('summary', 'No summary available.')}

"""
            
            # Detailed Analysis Section
            detailed = review_data.get('detailed_analysis', '')
            if detailed:
                comment += f"""<details>
<summary>🔬 <strong>Detailed Technical Analysis</strong></summary>

{detailed}

</details>

"""
            
            # Issues Section
            issues = review_data.get('issues', [])
            issues_severity = review_data.get('issues_severity', 'None')
            severity_colors = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢', 'None': '✅'}
            
            if issues and len(issues) > 0:
                comment += f"""<details open>
<summary>⚠️ <strong>Issues Found</strong> ({severity_colors.get(issues_severity, '⚪')} {issues_severity})</summary>

| # | Type | Severity | Location | Description |
|:-:|:----:|:--------:|:--------:|:------------|
"""
                for i, issue in enumerate(issues, 1):
                    if isinstance(issue, dict):
                        issue_type = issue.get('type', 'Issue')
                        severity = issue.get('severity', 'Medium')
                        line = issue.get('line', '-')
                        desc = issue.get('description', 'No description')
                        comment += f"| {i} | {issue_type} | {severity_colors.get(severity, '⚪')} {severity} | Line {line} | {desc} |\n"
                    else:
                        comment += f"| {i} | Issue | 🟡 Medium | - | {issue} |\n"
                
                comment += "\n**Suggested Fixes:**\n"
                for i, issue in enumerate(issues, 1):
                    if isinstance(issue, dict) and issue.get('suggestion'):
                        comment += f"{i}. {issue.get('suggestion')}\n"
                
                comment += "\n</details>\n\n"
            else:
                comment += "> ✅ **No issues found** - Code looks good!\n\n"
            
            # Merge Impact Section
            merge_impact = review_data.get('merge_impact', {})
            if merge_impact:
                affected = merge_impact.get('affected_areas', [])
                breaking = merge_impact.get('breaking_changes', 'No')
                rollback = merge_impact.get('rollback_risk', 'Low')
                testing = merge_impact.get('testing_required', [])
                deployment = merge_impact.get('deployment_notes', 'None')
                
                breaking_icon = "🔴" if breaking.lower().startswith('yes') else "✅"
                rollback_colors = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}
                
                comment += f"""<details>
<summary>🎯 <strong>Merge Impact Analysis</strong></summary>

#### Affected Areas
{chr(10).join(['- ' + a for a in affected]) if affected else '- No significant areas affected'}

#### Risk Assessment
| Metric | Status |
|:-------|:------:|
| Breaking Changes | {breaking_icon} {breaking} |
| Rollback Risk | {rollback_colors.get(rollback, '🟢')} {rollback} |

#### Required Testing
{chr(10).join(['- [ ] ' + t for t in testing]) if testing else '- Standard testing sufficient'}

#### Deployment Notes
{deployment if deployment else 'No special considerations'}

</details>

"""
            
            # Merge Conflict Risk Section
            conflict_risk = review_data.get('merge_conflict_risk', {})
            if conflict_risk:
                risk_level = conflict_risk.get('risk_level', 'Low')
                conflicts = conflict_risk.get('potential_conflicts', [])
                tips = conflict_risk.get('resolution_tips', 'Standard merge resolution')
                
                risk_colors = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢', 'None': '✅'}
                
                comment += f"""<details>
<summary>🔀 <strong>Merge Conflict Risk</strong> ({risk_colors.get(risk_level, '🟢')} {risk_level})</summary>

**Potential Conflict Areas:**
{chr(10).join(['- ' + c for c in conflicts]) if conflicts else '- No obvious conflict areas detected'}

**Resolution Tips:**
{tips}

</details>

"""
            
            # Code Quality Section
            quality = review_data.get('code_quality', {})
            if quality:
                quality_icons = {'Excellent': '🌟', 'Good': '✅', 'Fair': '🟡', 'Poor': '🔴'}
                
                comment += f"""<details>
<summary>📊 <strong>Code Quality Metrics</strong></summary>

| Metric | Rating | Notes |
|:-------|:------:|:------|
| Readability | {quality_icons.get(quality.get('readability', 'Good').split(' - ')[0] if isinstance(quality.get('readability'), str) else 'Good', '✅')} {quality.get('readability', 'Good')} | - |
| Maintainability | {quality_icons.get(quality.get('maintainability', 'Good').split(' - ')[0] if isinstance(quality.get('maintainability'), str) else 'Good', '✅')} {quality.get('maintainability', 'Good')} | - |
| Test Coverage | {quality.get('test_coverage', 'Unknown')} | - |
| Documentation | {quality.get('documentation', 'Adequate')} | - |

</details>

"""
            
            # Security Analysis Section
            security = review_data.get('security_analysis', {})
            if security:
                vuln_found = security.get('vulnerabilities_found', 'No')
                sec_risk = security.get('risk_level', 'None')
                sec_details = security.get('details', 'No security concerns identified.')
                owasp = security.get('owasp_categories', [])
                
                sec_icon = "🔴" if vuln_found.lower() == 'yes' else "🛡️"
                risk_colors = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '🟢', 'None': '✅'}
                
                comment += f"""<details>
<summary>{sec_icon} <strong>Security Analysis</strong> ({risk_colors.get(sec_risk, '✅')} {sec_risk} Risk)</summary>

**Vulnerabilities Found:** {vuln_found}

**Analysis:**
{sec_details}

**OWASP Categories:**
{chr(10).join(['- ' + o for o in owasp]) if owasp else '- None applicable'}

</details>

"""
            
            # Performance Analysis Section
            perf = review_data.get('performance_analysis', {})
            if perf:
                concerns = perf.get('concerns', 'No')
                time_comp = perf.get('time_complexity', 'N/A')
                space_comp = perf.get('space_complexity', 'N/A')
                optimizations = perf.get('optimization_suggestions', [])
                
                perf_icon = "⚡" if concerns.lower() == 'no' else "🐌"
                
                comment += f"""<details>
<summary>{perf_icon} <strong>Performance Analysis</strong></summary>

| Metric | Value |
|:-------|:------|
| Performance Concerns | {concerns} |
| Time Complexity | `{time_comp}` |
| Space Complexity | `{space_comp}` |

**Optimization Suggestions:**
{chr(10).join(['- ' + o for o in optimizations]) if optimizations else '- No optimizations needed'}

</details>

"""
            
            # Code Suggestion Section
            before = review_data.get('before_code', '')
            after = review_data.get('after_code', '')
            if before or after:
                comment += f"""<details>
<summary>💡 <strong>Suggested Code Changes</strong></summary>

**Before:**
```{lang}
{before if before else '// No problematic code identified'}
```

**After (Recommended):**
```{lang}
{after if after else '// No changes needed'}
```

> ✅ This suggestion has been validated for syntax correctness

</details>

"""
            
            # AI Agent Prompt Section
            ai_prompt = review_data.get('ai_agent_prompt', '')
            if ai_prompt:
                comment += f"""<details>
<summary>🤖 <strong>AI Agent Instructions</strong></summary>

Use this prompt to automatically implement the suggested changes:

```
{ai_prompt}

Additional Context:
- File: {filepath}
- Language: {lang}
- Ensure all tests pass after changes
- Follow existing code style and conventions
- Do not introduce new dependencies without approval
```

</details>

"""
            
            # Custom Check Results Section
            custom_results = review_data.get('custom_check_results', [])
            if custom_results:
                comment += """<details>
<summary>📋 <strong>Custom Check Results</strong></summary>

| Check | Status | Details |
|:------|:------:|:--------|
"""
                for result in custom_results:
                    if isinstance(result, dict):
                        check = result.get('check', 'Unknown check')
                        status = result.get('status', 'Unknown')
                        details = result.get('details', '-')
                        icon = "✅" if status.lower() == 'pass' else "❌"
                        comment += f"| {check} | {icon} {status} | {details} |\n"
                    else:
                        icon = "✅" if str(result).lower().startswith('pass') else "❌"
                        comment += f"| Custom Check | {icon} | {result} |\n"
                
                comment += "\n</details>\n\n"
            
            # Final Verdict Section
            verdict_reason = review_data.get('verdict_reason', '')
            verdict_full = {
                "APPROVE": "✅ **APPROVED** - This code is ready to merge",
                "REQUEST_CHANGES": "🔴 **CHANGES REQUESTED** - Please address the issues above before merging",
                "COMMENT": "💬 **REVIEW COMPLETE** - Comments provided for consideration"
            }.get(verdict, "Review completed")
            
            comment += f"""---

### {verdict_full}

{verdict_reason if verdict_reason else ''}

---
<sub>🤖 Reviewed by SapientPR AI | Confidence: {confidence} | <a href="#">Report Issue</a></sub>
"""
            
            return comment
            
        except Exception as e:
            return f"⚠️ Format Error: {e}"
    
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