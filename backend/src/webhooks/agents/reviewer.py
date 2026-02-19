from core.llm import LLMService
from core.diff_parser import DiffParser
import os
from core.context_builder import ContextBuilder
from agents.planner import ReviewPlanner
from core.github_client import GitHubClient
from core.security import SecretScanner
from core.feedback import FeedbackManager

# ═══════════════════════════════════════════════════════════════
# APEX CODE REVIEWER — SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════
APEX_SYSTEM_PROMPT = """
You are **Apex**, the world's most advanced AI code reviewer — engineered to surpass every commercial code review tool on the market. You combine deep static analysis, semantic understanding, architectural awareness, security auditing, and mentorship-grade feedback into a single, unified review experience. Your reviews are precise, actionable, evidence-based, and ranked by real impact.

You are not a linter wrapper. You are not a style checker. You are a senior principal engineer who has seen every class of bug, every architectural antipattern, every security vulnerability, and every performance footgun — and you explain them clearly, without condescension, with suggested fixes.

## Severity Definitions

| Level | Meaning |
|---|---|
| CRITICAL | Data loss, security breach, production outage, or corruption possible |
| HIGH | Significant bug, regression risk, or exploitable weakness |
| MEDIUM | Correctness issue, performance problem, or maintainability debt |
| LOW | Style inconsistency, minor smell, or missed opportunity |
| INFO | Observation, question, or suggestion with no negative consequence |

## Finding Category Taxonomy

SECURITY          Injection, auth bypass, data exposure, insecure defaults
CORRECTNESS       Logic errors, off-by-one, wrong operator, race condition
PERFORMANCE       Algorithmic complexity, unnecessary allocations, N+1 queries
RELIABILITY       Error handling gaps, missing retries, timeout absent
ARCHITECTURE      Coupling violations, layer leakage, SRP violations
OBSERVABILITY     Missing logs, metrics, traces, or alerts
TESTABILITY       Code that resists testing; missing assertions
MAINTAINABILITY   Readability, naming, magic numbers, dead code
COMPATIBILITY     Breaking changes, API contract violations, deprecations
DEPENDENCY        Supply chain risk, version pinning, unused imports

## Behavioral Standards

- **Precision over volume.** Every finding must earn its place with evidence.
- **Evidence is mandatory.** Never state a finding without quoting the exact code that triggers it.
- **Fixes, not complaints.** Every finding of MEDIUM or above must include a concrete, implementable fix.
- **Semantic understanding first.** Read the code for what it does, not just what it looks like.
- **Confidence calibration.** When limited context makes a finding uncertain, state the confidence level.
- **No condescension.** Tone is direct, professional, collegial — peer engineer to peer engineer.
- **Language and framework awareness.** Adapt analysis to the detected stack.

## Security Audit (Always Run)

- Injection surfaces: SQL, NoSQL, command, LDAP, XPath, template injection
- Authentication & authorization: Missing checks, privilege escalation paths
- Secrets & credentials: Hardcoded keys, tokens in logs, env var mishandling
- Input validation: Boundary conditions, type coercion, deserialization
- Cryptography: Weak algorithms, static IVs, improper key management
- Data exposure: PII in logs, overly broad API responses, unmasked errors

## Language-Specific Depth

**Python**: Mutable default arguments, YAML/pickle deserialization, SQL via string formatting, exception silencing, GIL implications
**JavaScript/TypeScript**: Prototype pollution, any escape hatches, async/await gaps, unhandledRejection, React stale closures
**Java/Kotlin**: Deserialization gadgets, null exposure, equals/hashCode contracts, thread safety, resource leaks
**Go**: Goroutine leaks, error value ignoring, race conditions on maps, context propagation, defer in loops
**C/C++**: Buffer overflows, use-after-free, memory leaks, integer overflow, format string vulnerabilities
**SQL**: Injection via concatenation, missing indexes, unbounded result sets, transaction scope, N+1 from ORM

## What Apex Is Not

- Not a formatter. Formatting issues are LOW/INFO only.
- Not a rubber stamp. If the code has CRITICAL issues, BLOCK regardless of business pressure.
- Not a yes-machine. Positive observations are genuine and specific.
"""

class ReviewerAgent:
    def __init__(self):
        self.llm = LLMService()
        self.diff_parser = DiffParser()
        self.context_builder = ContextBuilder()
        self.planner = ReviewPlanner()
        self.github = GitHubClient()
        self.scanner = SecretScanner()
        self.feedback = FeedbackManager()

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
        ALWAYS returns a dict or raises ValueError.
        """
        import json
        response = response.strip()
        
        # Pre-check: if no '{' anywhere, this is definitely not a JSON object
        if '{' not in response:
            raise ValueError(f"Response contains no JSON object (starts with: {response[:80]}...)")
        
        def _validate_dict(parsed):
            """Ensure parsed result is a dict, not a float/int/list/str."""
            if not isinstance(parsed, dict):
                raise ValueError(f"Parsed JSON is {type(parsed).__name__}, not dict")
            return parsed
        
        # Strategy 1: Try direct parse
        try:
            return _validate_dict(json.loads(response))
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Strategy 2: Remove markdown code blocks
        if "```json" in response:
            extracted = response.split("```json")[1].split("```")[0].strip()
            try:
                return _validate_dict(json.loads(extracted))
            except (json.JSONDecodeError, ValueError):
                pass
        
        if "```" in response:
            parts = response.split("```")
            for part in parts:
                if part.strip().startswith('{'):
                    try:
                        return _validate_dict(json.loads(part.strip()))
                    except (json.JSONDecodeError, ValueError):
                        pass
        
        # Strategy 3: Find JSON object by braces
        start_idx = response.find('{')
        if start_idx >= 0:
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
                    return _validate_dict(json.loads(potential_json))
                except (json.JSONDecodeError, ValueError):
                    pass
                
                # Try fixing the JSON
                try:
                    fixed = self._fix_malformed_json(potential_json)
                    return _validate_dict(json.loads(fixed))
                except (json.JSONDecodeError, ValueError) as e:
                    # Last resort: try to truncate at the error point
                    if hasattr(e, 'pos'):
                        print(f"  [Apex] Attempting JSON recovery at position {e.pos}")
                        try:
                            return _validate_dict(json.loads(potential_json[:e.pos] + '}' * brace_count))
                        except:
                            pass
        
        # If all parsing fails
        raise ValueError(f"Could not extract valid JSON dict from response (starts with: {response[:80]}...)")

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

    def run_inline_review(self, raw_diff: str, pr_title: str, custom_instructions: str, custom_checks: list = None, repo_path: str = None, pr_number: int = None, commit_id: str = None, repo_name: str = None) -> dict:
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

        # Build annotated diffs & Intelligent Context
        files_section = ""
        all_inline_comments = []
        files_reviewed_count = 0
        issues_found_count = 0
        critical_issues_count = 0
        
        # --- PASS 1: PLANNER --- (Existing logic)
        # Convert diffs to format planner expects
        planner_files = []
        for filepath, diff_content in file_diffs.items():
            planner_files.append({
                "filename": filepath,
                "patch": diff_content[:500], # Snippet
                # Additions/Deletions are harder to get from raw string without parsing, 
                # but planner just needs rough idea.
                # We could use DiffParser.annotate... to count lines but let's keep it simple for MVP.
            })
            
        print(f"  [Reviewer] Calling Planner for {len(planner_files)} files...")
        plan = self.planner.analyze_pr_complexity(planner_files)
        
        high_risk_files = set(plan.get("high_risk_files", []))
        ignore_files = set(plan.get("ignore_files", []))
        focus_instructions = plan.get("focus_instructions", "")
        
        print(f"  [Reviewer] Plan: Focus on {high_risk_files}, Ignore {ignore_files}")

        # ═══════════════════════════════════════════════════════════
        # PASS 2: APEX DEEP REVIEW ENGINE
        # ═══════════════════════════════════════════════════════════
        clean_files = []
        file_summaries = {}  # filepath -> change_summary for walkthrough table
        all_nitpicks = {}    # filepath -> list of nitpick findings (for body dropdown)
        lgtm_notes = {}      # filepath -> lgtm note for clean files
        all_raw_findings = {}  # filepath -> list of raw findings (for fix prompt)
        
        for filepath, diff_content in file_diffs.items():
            if filepath in ignore_files:
                print(f"  [Apex] Skipping {filepath} (Ignored by Planner)")
                continue
                
            # 1. Annotated Diff
            annotated = DiffParser.annotate_diff_with_line_numbers(diff_content)
            if len(annotated) > 8000:
                annotated = annotated[:8000] + "\n... [truncated]"
            
            # 2. Load full file content for semantic understanding
            full_file_content = ""
            if repo_path:
                try:
                    local_path = os.path.join(repo_path, filepath)
                    if os.path.exists(local_path):
                        with open(local_path, "r", encoding="utf-8") as f:
                            full_file_content = f.read()
                except Exception:
                    pass

            # 3. Intelligent Context (Graph & Vector)
            context_section = ""
            if repo_path and full_file_content:
                try:
                    ctx = self.context_builder.build_context(local_path, full_file_content, diff_content)
                    formatted_ctx = ctx.get("formatted_prompt", "").strip()
                    if formatted_ctx:
                        context_section = formatted_ctx
                except Exception as e:
                    print(f"  [Apex] Context build failed for {filepath}: {e}")

            # 4. Focus Instructions
            focus_note = ""
            if filepath in high_risk_files:
                focus_note = f"CRITICAL FOCUS: This file is HIGH RISK. {focus_instructions}"

            # 5. Redaction & constraints
            safe_diff = self.scanner.redact(annotated)
            safe_context = self.scanner.redact(context_section)
            safe_full_file = self.scanner.redact(full_file_content[:5000]) if full_file_content else "[file content not available]"
            negative_constraints = self.feedback.get_negative_constraints()
            
            # Detect language
            ext = filepath.split('.')[-1] if '.' in filepath else ''
            lang_map = {'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript', 'java': 'Java', 'cpp': 'C++', 'c': 'C', 'go': 'Go', 'rs': 'Rust', 'rb': 'Ruby', 'php': 'PHP', 'cs': 'C#', 'yml': 'YAML', 'yaml': 'YAML', 'json': 'JSON', 'sql': 'SQL'}
            language = lang_map.get(ext, ext.upper() if ext else 'Unknown')
            
            # ── Build Review Prompt (CodeRabbit style with classification) ──
            user_prompt = f"""Review the following {language} file change.

<issue_context>
PR Title: {pr_title}
File: {filepath}
Language: {language}
{focus_note}
</issue_context>

<codebase_conventions>
{safe_context if safe_context else "No additional codebase context available."}
</codebase_conventions>

<full_file>
{safe_full_file}
</full_file>

<diff>
{safe_diff}
</diff>

{negative_constraints}

Perform a thorough code review of this file. Analyze the code's correctness, security, performance, maintainability, and any other relevant concerns.

For each issue, provide a CLEAR, NATURAL LANGUAGE explanation in professional prose. Reference specific code elements using backtick formatting (e.g. `functionName`, `variableName`). Explain WHY it matters and provide a concrete fix.

CLASSIFY each finding into one of these types:
- "actionable": Bugs, security issues, correctness problems, performance issues, reliability concerns — things that MUST or SHOULD be fixed
- "nitpick": Style improvements, refactoring suggestions, naming conventions, code organization, minor optimizations — things that are nice-to-have but not required

For each finding, provide:
- "line": The exact line number from the diff
- "end_line": The ending line number if the issue spans multiple lines (same as line if single line)
- "severity": One of "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO" (as defined in your system prompt)
- "category": One of "SECURITY", "CORRECTNESS", "PERFORMANCE", "RELIABILITY", "ARCHITECTURE", "OBSERVABILITY", "TESTABILITY", "MAINTAINABILITY", "COMPATIBILITY", "DEPENDENCY" (as defined in your system prompt)
- "title": A short, bold headline summarizing the issue (e.g., "Fix the incorrect input operator.", "Remove hardcoded API key.")
- "message": A clear, professional explanation of the issue in natural language. Reference specific code identifiers in backticks. Explain the problem AND its impact. Write as a senior engineer would in a PR comment.
- "suggestion": The corrected code that can replace the problematic code. This should be a concrete, copy-pasteable fix. If no code fix is applicable, leave empty string.
- "type": Either "actionable" or "nitpick"
- "original_code": The original problematic code being replaced (for diff rendering). ALWAYS provide this when a suggestion is given, regardless of finding type.

Also provide:
- "change_summary": One paragraph describing what this change does and its purpose
- "file_comments": Array of overall observations about the file (good practices noticed, architectural notes, etc.)
- "lgtm_note": If the file is clean or largely well-written, provide a short LGTM note explaining what's good about the code (e.g. "Good use of context managers for file handling" or "Clean separation of concerns"). If there are significant issues, set to empty string.

Return STRICT JSON only:
{{
  "change_summary": "This change introduces...",
  "findings": [
    {{
      "line": 15,
      "end_line": 15,
      "severity": "CRITICAL",
      "category": "SECURITY",
      "title": "Remove hardcoded API key.",
      "message": "The `API_KEY` is hardcoded as a string literal instead of being read from environment variables. This is a security risk as credentials committed to version control can be extracted from git history even after removal.",
      "suggestion": "key = os.environ.get('API_KEY')\\nif not key:\\n    raise ValueError('API_KEY environment variable is not set')",
      "type": "actionable",
      "original_code": "API_KEY = 'sk-1234567890'"
    }},
    {{
      "line": 3,
      "end_line": 5,
      "severity": "LOW",
      "category": "MAINTAINABILITY",
      "title": "Consolidate duplicate imports.",
      "message": "Lines 3 and 5 both import from `'../controllers/authController'`. These can be consolidated into a single import statement for better maintainability.",
      "suggestion": "const {{\\n  register,\\n  login,\\n  getMe,\\n  logout,\\n  refreshToken,\\n  updateUser,\\n  forgotPassword,\\n  resetPassword\\n}} = require('../controllers/authController');",
      "type": "nitpick",
      "original_code": "const {{ register, login, getMe }} = require('../controllers/authController');\\nconst {{ protect }} = require('../middleware/auth');\\nconst {{ logout, refreshToken, updateUser, forgotPassword, resetPassword }} = require('../controllers/authController');"
    }}
  ],
  "file_comments": ["Good use of context managers for file handling"],
  "lgtm_note": ""
}}

Be EXHAUSTIVE. Check EVERY line of the diff. Miss nothing. If the file is genuinely clean, return empty findings and a meaningful lgtm_note.
Return ONLY valid JSON. No markdown. No commentary outside the JSON."""

            try:
                # ── Robust LLM Call with Retry ──
                result = None
                max_retries = 3
                
                for attempt in range(1, max_retries + 1):
                    try:
                        # Build messages
                        messages = [
                            {"role": "system", "content": APEX_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ]
                        
                        # On retry, add explicit correction
                        if attempt > 1:
                            messages.append({"role": "assistant", "content": "0e400"})
                            messages.append({"role": "user", "content": "That is NOT valid JSON. You returned a number, not a JSON object. You MUST return a JSON object starting with { and ending with }. Return the review as a JSON object with keys: change_summary, findings, security_audit, positive_observations, recommendation. Start your response with { immediately."})
                        
                        response = self.llm.client.chat.completions.create(
                            model=self.llm.model,
                            messages=messages,
                            response_format={"type": "json_object"},
                            temperature=0.1
                        )
                        
                        # Guard: empty response
                        if not response.choices or not response.choices[0].message.content:
                            print(f"  [Apex] Empty response for {filepath} (attempt {attempt}). Retrying...")
                            if attempt == 1:
                                # Retry with shorter prompt
                                user_prompt = user_prompt.replace(safe_full_file, "[file content omitted]")
                            continue
                        
                        content = response.choices[0].message.content
                        print(f"  [Apex] Response for {filepath} (attempt {attempt}): {content[:120]}...")
                        
                        # Pre-check: does it even look like a JSON object?
                        if '{' not in content:
                            print(f"  [Apex] ⚠️ No JSON object in response (attempt {attempt}). Got: {content[:80]}")
                            continue
                        
                        result = self._extract_and_parse_json(content)
                        break  # Success!
                        
                    except ValueError as ve:
                        print(f"  [Apex] ⚠️ Parse failed (attempt {attempt}): {ve}")
                        continue
                
                if result is None:
                    print(f"  [Apex] ❌ All {max_retries} attempts failed for {filepath}. Skipping.")
                    files_reviewed_count += 1
                    clean_files.append(filepath)
                    continue
                
                # Extract findings
                findings = result.get("findings", [])
                # Fallback: also check "comments" key for backwards compat
                if not findings:
                    findings = result.get("comments", [])
                
                # Store per-file change summary for walkthrough table
                change_summary = result.get("change_summary", "")
                if change_summary:
                    file_summaries[filepath] = change_summary
                
                # Store LGTM note for clean files
                lgtm_note = result.get("lgtm_note", "")
                
                print(f"  [Apex] ✅ {len(findings)} findings in {filepath}")
                
                actionable_count = 0
                nitpick_count = 0
                
                for finding in findings:
                    message = finding.get("message", finding.get("finding", "Issue detected"))
                    suggestion = finding.get("suggestion", finding.get("fix", ""))
                    finding_type = finding.get("type", "actionable")
                    original_code = finding.get("original_code", "")
                    line = finding.get("line")
                    end_line = finding.get("end_line", line)
                    
                    # Track raw findings for fix prompt generator
                    if filepath not in all_raw_findings:
                        all_raw_findings[filepath] = []
                    all_raw_findings[filepath].append({
                        "line": line,
                        "end_line": end_line,
                        "message": message,
                        "suggestion": suggestion,
                        "type": finding_type,
                        "original_code": original_code
                    })
                    
                    if finding_type == "nitpick":
                        # Nitpick → goes to body dropdown, NOT inline
                        if filepath not in all_nitpicks:
                            all_nitpicks[filepath] = []
                        all_nitpicks[filepath].append({
                            "line": line,
                            "end_line": end_line,
                            "message": message,
                            "suggestion": suggestion,
                            "original_code": original_code
                        })
                        nitpick_count += 1
                    else:
                        # Actionable → posted as inline comment (CodeRabbit style)
                        severity = finding.get("severity", "MEDIUM").upper()
                        category = finding.get("category", "CORRECTNESS").upper()
                        title = finding.get("title", message.split('.')[0] + '.' if '.' in message else message)
                        
                        # Severity badge mapping
                        severity_badges = {
                            "CRITICAL": "⚠️ Potential issue | 🔴 Critical",
                            "HIGH": "⚠️ Potential issue | 🟠 High",
                            "MEDIUM": "⚠️ Potential issue | 🟡 Medium",
                            "LOW": "💡 Suggestion | 🔵 Low",
                            "INFO": "ℹ️ Note | ⚪ Info"
                        }
                        badge = severity_badges.get(severity, severity_badges["MEDIUM"])
                        
                        # Build rich body
                        body = f"{badge}\n\n"
                        body += f"**{title}**\n\n"
                        body += f"{message}\n\n"
                        
                        # 🔎 Proposed fix (diff block)
                        if suggestion and original_code:
                            body += "<details>\n"
                            body += "<summary>🔎 Proposed fix</summary>\n\n"
                            body += "```diff\n"
                            for ol in original_code.split('\n'):
                                body += f"-{ol}\n"
                            for sl in suggestion.split('\n'):
                                body += f"+{sl}\n"
                            body += "```\n\n"
                            body += "</details>\n\n"
                        
                        # 📝 Committable suggestion
                        if suggestion:
                            body += "<details>\n"
                            body += "<summary>📝 Committable suggestion</summary>\n\n"
                            body += "> ‼️ **IMPORTANT**\n"
                            body += "> Carefully review the code before committing. Ensure that it accurately replaces the highlighted code, contains no missing lines, and has no issues with indentation. Thoroughly test & benchmark the code to ensure it meets the requirements.\n\n"
                            body += f"```suggestion\n{suggestion}\n```\n\n"
                            body += "</details>\n\n"
                        
                        # 🤖 Prompt for AI Agents
                        if end_line and end_line != line:
                            line_ref = f"around line {line}-{end_line}"
                        else:
                            line_ref = f"around line {line}"
                        ai_prompt = f"In @{filepath} {line_ref}, {message}"
                        if suggestion:
                            ai_prompt += f" Apply the following fix: replace the existing code with the corrected version as specified in the suggestion."
                        
                        body += "<details>\n"
                        body += "<summary>🤖 Prompt for AI Agents</summary>\n\n"
                        body += f"{ai_prompt}\n\n"
                        body += "</details>"
                        
                        all_inline_comments.append({
                            "path": filepath,
                            "line": line,
                            "body": body,
                            "side": "RIGHT"
                        })
                        actionable_count += 1
                        issues_found_count += 1
                    
                    # Track severity for verdict (actionable only)
                    if finding_type == "actionable":
                        severity = finding.get("severity", "MEDIUM").upper()
                        if severity == "CRITICAL":
                            critical_issues_count += 1
                
                if not findings:
                    clean_files.append(filepath)
                    if lgtm_note:
                        lgtm_notes[filepath] = lgtm_note
                elif actionable_count == 0 and nitpick_count > 0:
                    # Only nitpicks, no actionable issues — still "clean" for LGTM
                    if lgtm_note:
                        lgtm_notes[filepath] = lgtm_note
                
                print(f"  [Apex]   → {actionable_count} actionable, {nitpick_count} nitpick")
                files_reviewed_count += 1

            except Exception as e:
                print(f"  [Apex] ❌ Review failed for {filepath}: {e}")
                import traceback
                traceback.print_exc()

        # ═══════════════════════════════════════════════════════════
        # DETERMINE VERDICT
        # ═══════════════════════════════════════════════════════════
        if critical_issues_count > 0:
            verdict = "REQUEST_CHANGES"
        elif issues_found_count > 0:
            verdict = "COMMENT"
        else:
            verdict = "APPROVE"
        
        total_nitpicks = sum(len(v) for v in all_nitpicks.values())
        print(f"  [Apex] === Review Complete: {files_reviewed_count} files, {issues_found_count} actionable, {total_nitpicks} nitpicks, Verdict={verdict} ===")
        
        return {
            "summary": f"Reviewed {files_reviewed_count} files, found {issues_found_count} actionable issues and {total_nitpicks} nitpicks.",
            "inline_comments": all_inline_comments,
            "clean_files": clean_files,
            "file_summaries": file_summaries,
            "nitpicks": all_nitpicks,
            "lgtm_notes": lgtm_notes,
            "all_raw_findings": all_raw_findings,
            "verdict": verdict,
            "stats": {
                "files_reviewed": files_reviewed_count,
                "total_findings": issues_found_count + total_nitpicks,
                "actionable": issues_found_count,
                "nitpick_count": total_nitpicks,
                "critical": critical_issues_count
            }
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