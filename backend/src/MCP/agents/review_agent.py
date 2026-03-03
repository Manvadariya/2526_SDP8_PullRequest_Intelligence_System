"""
MCP Review Agent
================
Agentic PR reviewer powered by MCP tools + Ollama/OpenRouter.

The agent receives PR metadata, then autonomously decides which
MCP tools to call (fetch diff, lint, scan security, read files)
and posts a comprehensive review.

Two modes:
  - AUTONOMOUS: The LLM freely decides tool order (best for large models)
  - GUIDED:     The agent follows a fixed tool sequence (best for small models like 3B)

Usage:
  agent = MCPReviewAgent()
  await agent.review_pr(repo="owner/repo", pr_number=42, commit_sha="abc123", repo_path="/tmp/clone")
"""

import os
import sys
import json
import traceback
from typing import Optional
from contextlib import AsyncExitStack

# ─── Path setup ───
MCP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, MCP_ROOT)

from mcp_client import MCPClient
from core.openai_service import OpenAIService
from core.tools import ToolManager

# ═══════════════════════════════════════════
# System Prompt — The Agent's Identity
# ═══════════════════════════════════════════

SYSTEM_PROMPT = """You are **Apex**, an elite AI code reviewer with deep expertise in software engineering.

You have access to MCP tools that let you analyze Pull Requests. Use them autonomously.

## Available Tools

1. **get_pr_diff** — Fetch the PR diff (all file changes)
2. **get_pr_metadata** — Get PR title, description, author, branch
3. **read_file** — Read a specific file from the repo for deeper inspection
4. **list_changed_files** — Parse the diff to get a list of changed files with stats
5. **run_linter** — Run language-specific linters (flake8, eslint, etc.)
6. **scan_security** — Run Bandit security scanner for vulnerabilities
7. **get_custom_rules** — Load team-specific coding standards
8. **post_review** — Post your review to the GitHub PR with inline comments
9. **set_commit_status** — Set the commit status (pending/success/failure)

## Your Workflow

1. First, set the commit status to "pending" with description "Reviewing PR..."
2. Fetch the PR diff and metadata to understand the changes
3. List the changed files and identify high-risk ones (auth, API, database, security)
4. Run the linter on the repository
5. If the PR touches Python code, run the security scanner
6. Read specific files if you need more context beyond the diff
7. Load custom rules if available
8. Analyze all the information and form your review
9. Post your review using the post_review tool with:
   - A markdown summary with findings
   - Inline comments on specific lines where you found issues
   - A verdict: APPROVE (no issues), COMMENT (minor), or REQUEST_CHANGES (serious issues)
10. Set the commit status to "success" with a brief result summary

## Review Quality Standards

- **Precision over volume**: Only flag real issues with evidence
- **Categorize**: Bug, Security, Performance, Style, Logic Error
- **Be specific**: Reference exact line numbers and code
- **Provide fixes**: Include code suggestions when possible
- **No false positives**: If the code looks fine, say so

## Output Format for post_review

Your review summary should use markdown. Include:
- Executive summary (2-3 sentences)
- Issues found (if any) with severity
- Overall assessment

IMPORTANT: You MUST call the post_review tool to submit your review. DO NOT just describe what you would do — actually do it by calling the tools."""


class MCPReviewAgent:
    """
    Agentic PR reviewer that uses MCP tools to analyze and review PRs.
    """

    def __init__(self, mode: str = "auto"):
        """
        Args:
            mode: "auto" (autonomous) or "guided" (fixed tool order)
        """
        self.mode = mode
        self.llm = OpenAIService()
        self._provider = self.llm._provider

    async def review_pr(
        self,
        repo: str,
        pr_number: int,
        commit_sha: str,
        repo_path: str,
    ) -> dict:
        """
        Run a full agentic PR review.

        Args:
            repo: Repository full name (e.g. "owner/repo")
            pr_number: Pull Request number
            commit_sha: Commit SHA for the PR
            repo_path: Local path to the cloned repository

        Returns:
            dict with keys: success, summary, verdict, tool_calls_made
        """
        print(f"\n{'='*60}")
        print(f"  MCP Review Agent ({self.mode} mode, {self._provider})")
        print(f"  PR: {repo}#{pr_number}")
        print(f"{'='*60}\n")

        # Context is passed via environment variables to the subprocess
        
        if self.mode == "guided":
            return await self._run_guided(repo, pr_number, commit_sha, repo_path)
        else:
            return await self._run_autonomous(repo, pr_number, commit_sha, repo_path)

    # ═══════════════════════════════════════════
    # AUTONOMOUS MODE — LLM decides tool order
    # ═══════════════════════════════════════════

    async def _run_autonomous(self, repo, pr_number, commit_sha, repo_path) -> dict:
        """Let the LLM freely decide which tools to call and in what order."""

        async with AsyncExitStack() as stack:
            # Connect to the PR Review MCP Server
            env = os.environ.copy()
            env["REVIEW_REPO"] = repo
            env["REVIEW_PR_NUMBER"] = str(pr_number)
            env["REVIEW_COMMIT_SHA"] = commit_sha
            env["REVIEW_REPO_PATH"] = repo_path

            pr_client = await stack.enter_async_context(
                MCPClient(
                    command=sys.executable,
                    args=[os.path.join(MCP_ROOT, "pr_review_server.py")],
                    env=env,
                )
            )
            clients = {"pr_review": pr_client}

            # Get available tools
            tools = await ToolManager.get_all_tools(clients)
            print(f"  [Agent] Discovered {len(tools)} tools")

            # Prepare messages
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Review this Pull Request:\n"
                    f"- Repository: {repo}\n"
                    f"- PR Number: {pr_number}\n"
                    f"- Commit SHA: {commit_sha}\n\n"
                    f"Use the available tools to analyze the PR and post your review. "
                    f"Start by setting the commit status to pending, then fetch the diff."
                )},
            ]

            tool_calls_made = 0
            max_iterations = 15  # Safety limit

            for iteration in range(max_iterations):
                try:
                    message = self.llm.chat(
                        messages=messages,
                        tools=tools if tools else None,
                    )
                except Exception as e:
                    print(f"  [Agent] LLM Error: {e}")
                    return {"success": False, "summary": f"LLM Error: {e}", "verdict": "ERROR", "tool_calls_made": tool_calls_made}

                # Add assistant message to history
                assistant_msg = {"role": "assistant", "content": message.content}
                if message.tool_calls:
                    assistant_msg["tool_calls"] = message.tool_calls
                messages.append(assistant_msg)

                # Handle tool calls
                if message.tool_calls:
                    tool_names = [t.function.name for t in message.tool_calls]
                    print(f"  [Agent] Iteration {iteration+1}: Calling tools: {tool_names}")
                    tool_calls_made += len(message.tool_calls)

                    tool_results = await ToolManager.execute_tool_requests(clients, message.tool_calls)

                    # Truncate massive outputs
                    for result in tool_results:
                        content = str(result.get("content", ""))
                        if len(content) > 20000:
                            print(f"  [Agent] Trimming large tool output ({len(content)} chars)")
                            result["content"] = content[:20000] + "\n...[Output Truncated]..."

                    messages.extend(tool_results)
                else:
                    # No tool calls — agent is done
                    final_response = message.content or ""
                    print(f"  [Agent] Review complete after {iteration+1} iterations, {tool_calls_made} tool calls")
                    return {
                        "success": True,
                        "summary": final_response,
                        "verdict": "COMPLETED",
                        "tool_calls_made": tool_calls_made,
                    }

            print(f"  [Agent] Hit max iterations ({max_iterations})")
            return {
                "success": True,
                "summary": "Review completed (max iterations reached)",
                "verdict": "COMPLETED",
                "tool_calls_made": tool_calls_made,
            }

    # ═══════════════════════════════════════════
    # GUIDED MODE — Fixed tool sequence
    # ═══════════════════════════════════════════

    async def _run_guided(self, repo, pr_number, commit_sha, repo_path) -> dict:
        """
        Follow a predetermined tool sequence.
        Best for small models (3B) that struggle with autonomous tool selection.
        """

        async with AsyncExitStack() as stack:
            env = os.environ.copy()
            env["REVIEW_REPO"] = repo
            env["REVIEW_PR_NUMBER"] = str(pr_number)
            env["REVIEW_COMMIT_SHA"] = commit_sha
            env["REVIEW_REPO_PATH"] = repo_path

            pr_client = await stack.enter_async_context(
                MCPClient(
                    command=sys.executable,
                    args=[os.path.join(MCP_ROOT, "pr_review_server.py")],
                    env=env,
                )
            )
            clients = {"pr_review": pr_client}
            tool_calls_made = 0

            try:
                # Step 1: Set status pending
                print("  [Guided] Step 1/7: Setting commit status to pending...")
                await pr_client.call_tool("set_commit_status", {
                    "state": "pending", "description": "Reviewing PR..."
                })
                tool_calls_made += 1

                # Step 2: Get PR diff
                print("  [Guided] Step 2/7: Fetching PR diff...")
                diff_result = await pr_client.call_tool("get_pr_diff", {
                    "repo": repo, "pr_number": pr_number
                })
                diff_text = diff_result.content[0].text if diff_result.content else ""
                tool_calls_made += 1

                # Step 3: Get PR metadata
                print("  [Guided] Step 3/7: Fetching PR metadata...")
                meta_result = await pr_client.call_tool("get_pr_metadata", {
                    "repo": repo, "pr_number": pr_number
                })
                metadata = meta_result.content[0].text if meta_result.content else "{}"
                tool_calls_made += 1

                # Step 4: List changed files
                print("  [Guided] Step 4/7: Parsing changed files...")
                files_result = await pr_client.call_tool("list_changed_files", {
                    "diff_text": diff_text
                })
                changed_files_json = files_result.content[0].text if files_result.content else "[]"
                changed_files = json.loads(changed_files_json)
                file_paths = [f["path"] for f in changed_files]
                tool_calls_made += 1

                # Step 5: Run linter
                print("  [Guided] Step 5/7: Running linter...")
                lint_result = await pr_client.call_tool("run_linter", {
                    "changed_files": file_paths
                })
                lint_text = lint_result.content[0].text if lint_result.content else "{}"
                tool_calls_made += 1

                # Step 6: Run security scan
                print("  [Guided] Step 6/7: Running security scan...")
                sec_result = await pr_client.call_tool("scan_security", {})
                sec_text = sec_result.content[0].text if sec_result.content else "{}"
                tool_calls_made += 1

                # Step 7: Ask LLM to synthesize everything and generate review
                print("  [Guided] Step 7/7: Generating review with LLM...")
                
                # Truncate diff based on model capability
                max_diff_len = 30000 if self._provider == "openrouter" else 12000
                diff_for_llm = diff_text[:max_diff_len] if len(diff_text) > max_diff_len else diff_text

                synthesis_prompt = f"""You are **Apex**, an elite AI code reviewer engineered to surpass every commercial code review tool.
You combine deep static analysis, semantic understanding, architectural awareness, security auditing, and mentorship-grade feedback.

Your reviews MUST be:
- **Precise**: Every finding must reference the exact file, line, and code snippet.
- **Actionable**: Every issue MEDIUM or above must include a concrete fix.
- **Evidence-based**: Quote the code that triggers the issue.
- **Categorized**: Use categories — Security, Correctness, Performance, Reliability, Architecture, Maintainability.
- **Severity-rated**: CRITICAL / HIGH / MEDIUM / LOW / INFO.

## Security Audit (ALWAYS run this):
- Injection surfaces (SQL, command, template)
- Auth/authz gaps, privilege escalation paths
- Hardcoded secrets, tokens in logs, env var mishandling
- Input validation, boundary conditions
- Data exposure (PII in logs, overly broad API responses)

## PR Metadata
{metadata}

## Diff (Changed Code)
```diff
{diff_for_llm}
```

## Changed Files
{changed_files_json}

## Linter Results
{lint_text}

## Security Scan Results
{sec_text}

## Your Task
Carefully analyze EVERY changed line in the diff. Do NOT give a generic response.

For each file, check for:
1. Bugs, logic errors, off-by-one errors
2. Security vulnerabilities (injection, auth bypass, data exposure)
3. Performance issues (N+1 queries, unbounded loops, memory leaks)
4. Error handling gaps (missing try/catch, swallowed exceptions)
5. Race conditions or concurrency issues
6. Hardcoded values that should be configurable
7. Missing input validation

Generate a code review in this EXACT JSON format:
{{
    "summary": "A detailed markdown review summary with: executive summary (2-3 sentences), list of issues found with severity and category, overall assessment, and what was done well",
    "verdict": "APPROVE or COMMENT or REQUEST_CHANGES",
    "inline_comments": [
        {{"path": "exact/file/path.py", "line": 42, "body": "**[SEVERITY/CATEGORY]** Issue description with code reference and suggested fix"}}
    ]
}}

CRITICAL RULES:
- The summary MUST be detailed markdown (at least 100 words) — never a single generic sentence
- Each inline_comment body MUST start with severity+category like **[HIGH/Security]** or **[MEDIUM/Correctness]**
- The "line" MUST be a line number from the RIGHT side of the diff (added lines starting with +)
- The "path" MUST exactly match a file path from the changed files list
- If the code is genuinely clean, explain WHY in detail (what patterns are good, what was checked)
- If issues are found, provide code suggestions using markdown code blocks
- Return ONLY the JSON, nothing else"""

                response = self.llm.chat(
                    messages=[{"role": "user", "content": synthesis_prompt}]
                )
                raw_response = response.content or ""

                # Parse the LLM response
                review_data = self._extract_review_json(raw_response)

                # Step 8: Post the review
                print("  [Guided] Posting review to GitHub...")
                await pr_client.call_tool("post_review", review_data)
                tool_calls_made += 1

                # Step 9: Set final status
                verdict = review_data.get("verdict", "COMMENT")
                n_issues = len(review_data.get("inline_comments", []))
                status_desc = f"Review complete - {verdict} ({n_issues} issue(s))"
                await pr_client.call_tool("set_commit_status", {
                    "state": "success", "description": status_desc
                })
                tool_calls_made += 1

                print(f"  [Guided] Done! {tool_calls_made} tool calls, verdict: {verdict}")
                return {
                    "success": True,
                    "summary": review_data.get("summary", ""),
                    "verdict": verdict,
                    "tool_calls_made": tool_calls_made,
                }

            except Exception as e:
                print(f"  [Guided] Error: {e}")
                traceback.print_exc()
                # Try to set failure status
                try:
                    await pr_client.call_tool("set_commit_status", {
                        "state": "failure", "description": f"Review error: {str(e)[:100]}"
                    })
                except:
                    pass
                return {
                    "success": False,
                    "summary": f"Review failed: {e}",
                    "verdict": "ERROR",
                    "tool_calls_made": tool_calls_made,
                }

    def _extract_review_json(self, text: str) -> dict:
        """Extract review JSON from LLM response (handles markdown wrapping)."""
        import re

        # Try direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Try code block extraction
        code_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if code_block:
            try:
                return json.loads(code_block.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding first { ... }
        brace_match = re.search(r'\{.*\}', text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        # Fallback: create a basic review from the text
        print("  [Agent] Warning: Could not parse LLM response as JSON. Using text as summary.")
        return {
            "summary": text[:2000] if text else "Review generation failed",
            "verdict": "COMMENT",
            "inline_comments": [],
        }
