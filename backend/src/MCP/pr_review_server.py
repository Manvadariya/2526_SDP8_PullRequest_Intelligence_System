"""
PR Review MCP Server
====================
Exposes the project's PR review capabilities as MCP tools.
The AI agent calls these tools to autonomously review Pull Requests.

Tools:
  - get_pr_diff        : Fetch PR diff from GitHub
  - get_pr_metadata    : Get PR title, description, author
  - read_file          : Read a file from the cloned repo
  - list_changed_files : List files changed in the diff
  - run_linter         : Run language-specific linters
  - scan_security      : Run Bandit security scan
  - get_custom_rules   : Load team's custom review rules
  - post_review        : Post review comments to GitHub PR
  - set_commit_status  : Set commit status on GitHub

Usage:
  python pr_review_server.py
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add webhooks to path so we can import existing agents
WEBHOOKS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webhooks"))
sys.path.insert(0, WEBHOOKS_PATH)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ─── Lazy imports from webhooks (loaded on first use) ───
_github_client = None
_linter_agent = None
_security_agent = None

def _get_github_client():
    global _github_client
    if _github_client is None:
        from core.github_client import GitHubClient
        _github_client = GitHubClient()
    return _github_client

def _get_linter_agent():
    global _linter_agent
    if _linter_agent is None:
        from agents.linter import LinterAgent
        _linter_agent = LinterAgent()
    return _linter_agent

def _get_security_agent():
    global _security_agent
    if _security_agent is None:
        from agents.security import SecurityAgent
        _security_agent = SecurityAgent()
    return _security_agent


# ─── Shared state (set per-review) ───
_review_context = {
    "repo_path": os.environ.get("REVIEW_REPO_PATH"),       # Local clone path
    "repo_name": os.environ.get("REVIEW_REPO"),       # e.g. "owner/repo"
    "pr_number": int(os.environ.get("REVIEW_PR_NUMBER")) if os.environ.get("REVIEW_PR_NUMBER") else None,
    "commit_sha": os.environ.get("REVIEW_COMMIT_SHA"),
}

def set_review_context(repo_path: str, repo_name: str, pr_number: int, commit_sha: str):
    """Called by the orchestrator before starting an agentic review. This is kept for backward compatibility if running in-process."""
    _review_context.update({
        "repo_path": repo_path,
        "repo_name": repo_name,
        "pr_number": pr_number,
        "commit_sha": commit_sha,
    })


# ═══════════════════════════════════════════
# MCP Server Definition
# ═══════════════════════════════════════════

server = Server("pr-review-tools")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_pr_diff",
            description="Fetch the unified diff for a Pull Request from GitHub. Returns the raw diff text showing all file changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository full name (e.g. 'owner/repo')"},
                    "pr_number": {"type": "integer", "description": "Pull Request number"},
                },
                "required": ["repo", "pr_number"],
            },
        ),
        types.Tool(
            name="get_pr_metadata",
            description="Get metadata for a Pull Request: title, description, author, branch, and number of changed files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repository full name (e.g. 'owner/repo')"},
                    "pr_number": {"type": "integer", "description": "Pull Request number"},
                },
                "required": ["repo", "pr_number"],
            },
        ),
        types.Tool(
            name="read_file",
            description="Read the contents of a specific file from the cloned repository. Use this to examine code in detail.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Relative path to the file within the repo (e.g. 'src/main.py')"},
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="list_changed_files",
            description="Parse the PR diff and return a list of all changed file paths with their change stats (additions, deletions).",
            inputSchema={
                "type": "object",
                "properties": {
                    "diff_text": {"type": "string", "description": "The raw diff text (from get_pr_diff)"},
                },
                "required": ["diff_text"],
            },
        ),
        types.Tool(
            name="run_linter",
            description="Run language-specific linters (flake8, eslint, checkstyle, cppcheck) on the cloned repository. Returns structured lint issues.",
            inputSchema={
                "type": "object",
                "properties": {
                    "changed_files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changed file paths to focus linting on",
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="scan_security",
            description="Run Bandit security scanner on the repository. Returns Medium/High severity security issues with file locations and remediation advice.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_custom_rules",
            description="Load team-specific coding rules from the repository (.pr-reviewer.yml, best_practices.md). Returns a list of custom checks the PR should be validated against.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="post_review",
            description="Post a code review to the GitHub Pull Request. Can include inline comments on specific lines and a summary body.",
            inputSchema={
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Review summary body (markdown)"},
                    "verdict": {
                        "type": "string",
                        "enum": ["APPROVE", "COMMENT", "REQUEST_CHANGES"],
                        "description": "Review verdict",
                    },
                    "inline_comments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "File path"},
                                "line": {"type": "integer", "description": "Line number"},
                                "body": {"type": "string", "description": "Comment text"},
                            },
                            "required": ["path", "line", "body"],
                        },
                        "description": "Inline comments on specific lines (optional)",
                    },
                },
                "required": ["summary", "verdict"],
            },
        ),
        types.Tool(
            name="set_commit_status",
            description="Set the commit status on GitHub (pending, success, failure, error). Shows up as a check on the PR.",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["pending", "success", "failure", "error"],
                        "description": "Status state",
                    },
                    "description": {"type": "string", "description": "Short status description (max 140 chars)"},
                },
                "required": ["state", "description"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    ctx = _review_context

    try:
        if name == "get_pr_diff":
            repo = arguments.get("repo", ctx.get("repo_name"))
            pr_number = arguments.get("pr_number", ctx.get("pr_number"))
            gh = _get_github_client()
            diff = await gh.get_pr_diff(repo, pr_number)
            # Truncate if very large to avoid overwhelming the model
            if len(diff) > 50000:
                diff = diff[:50000] + "\n\n...[Diff truncated at 50,000 chars]..."
            return [types.TextContent(type="text", text=diff)]

        elif name == "get_pr_metadata":
            repo = arguments.get("repo", ctx.get("repo_name"))
            pr_number = arguments.get("pr_number", ctx.get("pr_number"))
            gh = _get_github_client()
            import httpx
            url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=gh.headers)
                resp.raise_for_status()
                data = resp.json()
            metadata = {
                "title": data.get("title"),
                "description": data.get("body", ""),
                "author": data.get("user", {}).get("login"),
                "branch": data.get("head", {}).get("ref"),
                "base_branch": data.get("base", {}).get("ref"),
                "changed_files": data.get("changed_files"),
                "additions": data.get("additions"),
                "deletions": data.get("deletions"),
                "state": data.get("state"),
            }
            return [types.TextContent(type="text", text=json.dumps(metadata, indent=2))]

        elif name == "read_file":
            repo_path = ctx.get("repo_path")
            if not repo_path:
                return [types.TextContent(type="text", text="Error: No repository cloned. repo_path not set.")]
            file_path = arguments["file_path"]
            full_path = os.path.join(repo_path, file_path)
            if not os.path.exists(full_path):
                return [types.TextContent(type="text", text=f"Error: File not found: {file_path}")]
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            # Add line numbers
            lines = content.split("\n")
            numbered = "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines))
            if len(numbered) > 30000:
                numbered = numbered[:30000] + "\n...[File truncated]..."
            return [types.TextContent(type="text", text=numbered)]

        elif name == "list_changed_files":
            from core.diff_parser import DiffParser
            diff_text = arguments["diff_text"]
            file_diffs = DiffParser.parse_diff(diff_text)
            result = []
            for filepath, diff in file_diffs.items():
                additions = diff.count("\n+") - diff.count("\n+++")
                deletions = diff.count("\n-") - diff.count("\n---")
                result.append({
                    "path": filepath,
                    "additions": max(0, additions),
                    "deletions": max(0, deletions),
                })
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "run_linter":
            repo_path = ctx.get("repo_path")
            if not repo_path:
                return [types.TextContent(type="text", text="Error: No repository cloned.")]
            linter = _get_linter_agent()
            changed_files = arguments.get("changed_files", [])
            results = linter.run(repo_path, changed_files=changed_files if changed_files else None)
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "scan_security":
            repo_path = ctx.get("repo_path")
            if not repo_path:
                return [types.TextContent(type="text", text="Error: No repository cloned.")]
            scanner = _get_security_agent()
            results = scanner.run(repo_path)
            return [types.TextContent(type="text", text=json.dumps(results, indent=2))]

        elif name == "get_custom_rules":
            repo_name = ctx.get("repo_name")
            commit_sha = ctx.get("commit_sha")
            if not repo_name:
                return [types.TextContent(type="text", text="Error: repo_name not set.")]
            from core.custom_checks import CustomCheckLoader
            gh = _get_github_client()
            config = await CustomCheckLoader.load_from_repo(gh, repo_name, commit_sha)
            return [types.TextContent(type="text", text=json.dumps(config, indent=2))]

        elif name == "post_review":
            repo_name = ctx.get("repo_name")
            pr_number = ctx.get("pr_number")
            commit_sha = ctx.get("commit_sha")
            if not all([repo_name, pr_number, commit_sha]):
                return [types.TextContent(type="text", text="Error: Missing review context (repo_name, pr_number, commit_sha).")]
            
            gh = _get_github_client()
            summary = arguments.get("summary", "")
            verdict = arguments.get("verdict", "COMMENT")
            inline_comments = arguments.get("inline_comments", [])
            
            # Add RIGHT side to inline comments if not present
            for c in inline_comments:
                if "side" not in c:
                    c["side"] = "RIGHT"

            # Fetch the raw diff to validate line numbers
            print(f"Fetching raw diff for validation...")
            try:
                raw_diff = await gh.get_pr_diff(repo_name, pr_number)
            except Exception as e:
                print(f"Warning: Could not fetch diff for validation: {e}")
                raw_diff = ""

            if inline_comments:
                success = await gh.post_inline_review(
                    repo_name, pr_number, commit_sha,
                    inline_comments, summary, verdict, raw_diff=raw_diff
                )
            else:
                await gh.post_or_update_comment(repo_name, pr_number, summary)
                success = True
            
            status = "Review posted successfully" if success else "Review posting had issues (fallback used)"
            
            # --- DEBUG LOGGING ---
            try:
                with open("mcp_post_debug_log.txt", "a") as df:
                    df.write(f"\n--- POST REVIEW CALL ---\n")
                    df.write(f"Repo: {repo_name} | PR: {pr_number} | SHA: {commit_sha[:7]}\n")
                    df.write(f"Verdict: {verdict} | Inline Comments: {len(inline_comments)}\n")
                    df.write(f"Success Flag: {success}\n")
            except Exception as e:
                pass
            
            return [types.TextContent(type="text", text=status)]

        elif name == "set_commit_status":
            repo_name = ctx.get("repo_name")
            commit_sha = ctx.get("commit_sha")
            if not all([repo_name, commit_sha]):
                return [types.TextContent(type="text", text="Error: Missing context.")]
            gh = _get_github_client()
            await gh.set_commit_status(
                repo_name, commit_sha,
                arguments["state"],
                arguments["description"]
            )
            return [types.TextContent(type="text", text=f"Status set: {arguments['state']}")]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        import traceback
        return [types.TextContent(type="text", text=f"Error in {name}: {str(e)}\n{traceback.format_exc()}")]


# ─── Standalone server entry point ───
async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(run_server())
