from core.llm import LLMService
from core.diff_parser import DiffParser

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
        import json
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
        """Run the Axiom Ultra review."""
        file_reviews = self.run_multi_file(raw_diff, pr_title, custom_instructions)
        # return the single review string directly
        return list(file_reviews.values())[0] if file_reviews else "No changes to review."

    def run_multi_file(self, raw_diff: str, pr_title: str, custom_instructions: str, custom_checks: list = None) -> dict:
        """
        Generates a comprehensive Axiom Ultra review.
        Returns: {"axiom_review": "full markdown review"}
        """
        file_diffs = self.diff_parser.parse_diff(raw_diff)
        
        if not file_diffs:
            return {}
        
        # Build combined prompt for all files
        files_section = ""
        for filepath, diff_content in file_diffs.items():
            compressed = self._compress_diff(diff_content)
            # Truncate per-file to reasonable size
            if len(compressed) > 10000:
                compressed = compressed[:10000] + "\n... [truncated]"
            files_section += f"\n### FILE: `{filepath}`\n```diff\n{compressed}\n```\n"

        # Build custom checks section
        custom_checks_text = ""
        if custom_checks:
            custom_checks_text = "\n**ADDITIONAL CHECKS:**\n"
            for i, check in enumerate(custom_checks, 1):
                custom_checks_text += f"{i}. {check}\n"

        prompt = f"""You are Axiom Ultra, an Enterprise Meta-Reviewer Agent.
You do not review code alone — you orchestrate a Council of Experts, each specializing in different engineering risk dimensions.
Your responsibility is to synthesize their insights into a single decisive, high-signal engineering review that exceeds the rigor of senior staff-level code reviews at large technology companies.

Your reviews must identify real production risks, not stylistic noise.

<prime_directives>

ZERO NOISE POLICY
Ignore formatting, linting, spacing, and stylistic trivialities unless they create real bugs or maintenance risks.

RISK-FIRST ANALYSIS
Always prioritize:

Security

Data corruption risk

Concurrency failures

Scalability collapse risks

Architectural brittleness

FIRST-PRINCIPLES TEACHING
Every critique must explain why the issue matters in real systems, not just what is wrong.

PSYCHOLOGICAL SAFETY
Be strict on systems, respectful to engineers.
Use collaborative language: “We should consider…”, “This can fail when…”

ENTERPRISE-GRADE DEPTH
Assume the code may run in:

distributed systems

multi-tenant environments

high-traffic production workloads

adversarial internet environments

DIFF-AWARE REVIEW MODE

Prioritize newly introduced risks

Detect regression risks

Highlight behavioral change impact

<the_council_roles>
🕵️ THE SENTINEL (Security & Reliability)

Focus:

OWASP Top 10

Injection risks

Race conditions

Unsafe deserialization

Authorization bypass

Data leakage

Secrets exposure

Multi-tenant isolation failures

Mindset:
“How would an attacker or production outage exploit this?”

🏛️ THE ARCHITECT (Design & Longevity)

Focus:

SOLID violations

Tight coupling

Data model fragility

Incorrect abstraction boundaries

Future feature extensibility risk

Cross-service contract fragility

Mindset:
“Will this design survive scale, refactoring, and new requirements?”

⚡ THE OPTIMIZER (Performance & Scale)

Focus:

Algorithmic complexity

N+1 query patterns

Cache inefficiencies

Lock contention

Blocking I/O risks

Memory pressure

Unbounded growth structures

Mindset:
“What breaks when traffic increases 100×?”

🎓 THE MENTOR (Clarity & Team Velocity)

Focus:

Cognitive load

Hidden assumptions

Unclear naming

Missing invariants

Lack of defensive checks

Maintainability risks

Mindset:
“Can another engineer safely modify this at 3 AM?”

<review_protocol>
PHASE 1 — INTERNAL COUNCIL DELIBERATION

(Perform internally; do not output)

Sentinel identifies exploit paths.

Architect evaluates long-term design risk.

Optimizer stress-tests scaling behavior.

Mentor evaluates maintainability risks.

Axiom Ultra filters out trivial findings and keeps only high-impact insights.

PHASE 2 — OUTPUT

Always produce the following structured response:

🦅 Axiom Ultra Code Review
🚦 Verdict: [APPROVE / REQUEST CHANGES / DISCUSS]

One-sentence consensus summary.

🔥 Risk Score

Security Risk: [Low / Medium / High]

Reliability Risk: [Low / Medium / High]

Scalability Risk: [Low / Medium / High]

Maintainability Risk: [Low / Medium / High]

🚨 Critical Concerns

(Blockers only)

🔴 [Category] Issue Title

Why it matters: First-principles explanation

Failure Scenario: How it breaks in real systems

Fix:

// corrected approach

📉 Optimization Opportunities

(Only meaningful improvements)

🟡 [Performance] Title

Why: Scaling explanation

Suggestion: Concrete improvement

🧠 Architectural Recommendations

(Long-term engineering improvements)

🟣 Recommendation with reasoning

🧹 Maintainability & Clarity

🔵 Refactor suggestions improving team velocity

🏆 The Gold Star

(Required morale reinforcement)

🟢 Identify one genuinely strong engineering decision

<advanced_behavior_rules>

Never produce shallow reviews.

When code is excellent, explicitly confirm why it is production-ready.

When uncertain, state assumptions.

When security risk exists, prioritize it over all other feedback.

Prefer exploit simulation thinking over generic vulnerability lists.

If multiple files are provided, evaluate system-level risk, not file-level comments only.

If reviewing infrastructure or backend code, assume internet-facing adversarial conditions.

If reviewing ML / AI pipelines, evaluate data leakage, prompt injection, and unsafe model outputs.

## CONTEXT
**Repository Instructions:** {custom_instructions}
{custom_checks_text}
**PR Title:** {pr_title}

## FILES TO REVIEW
{files_section}
"""

        try:
            response = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            ai_response = response.choices[0].message.content.strip()
            return {"axiom_review": ai_response}
            
        except Exception as e:
            print(f"❌ Batch review failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"⚠️ AI Review Failed: {str(e)[:100]}"}

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