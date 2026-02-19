from sqlmodel import select
from core.github_client import GitHubClient
from core.custom_checks import CustomCheckLoader
from core.repo_manager import RepoManager
from core.project_context import ProjectContextBuilder
from core.types import PRMetadata
from core.diff_parser import DiffParser
from core.docker_runner import DockerRunner
from agents.reviewer import ReviewerAgent
from agents.fix_prompt_agent import FixPromptAgent
from models import Job, AgentResult
from database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from config import config as app_config
import json
from core.indexing.manager import IndexManager

class Orchestrator:
    def __init__(self):
        self.gh = GitHubClient()
        self.reviewer = ReviewerAgent()
        self.fix_prompt_agent = FixPromptAgent()
        self.docker_runner = DockerRunner()
        self.indexer = IndexManager()

    async def process_pr(self, metadata: PRMetadata, job_id: int):
        print(f"🚀 Job {job_id}: Processing PR #{metadata.pr_number}")
        
        async with AsyncSession(engine, expire_on_commit=False) as session:
            try:
                # 1. DB Update
                job = await session.get(Job, job_id)
                if job:
                    job.status = "processing"
                    session.add(job)
                    await session.commit()

                await self.gh.set_commit_status(metadata.repo_full_name, metadata.commit_sha, "pending", "Running analysis...")
                
                # 2. Load Config with Custom Checks
                repo_config = await CustomCheckLoader.load_from_repo(
                    self.gh, 
                    metadata.repo_full_name, 
                    metadata.commit_sha
                )
                
                # 3. Clone Repo
                repo_url = f"https://github.com/{metadata.repo_full_name}.git"
                manager = RepoManager(repo_url, metadata.commit_sha, app_config.GITHUB_TOKEN)
                repo_path = manager.clone_and_checkout()

                try:
                    # 4. Get changed files for targeted linting
                    raw_diff = await self.gh.get_pr_diff(metadata.repo_full_name, metadata.pr_number)
                    
                    # Extract changed file paths from diff
                    file_diffs = DiffParser.parse_diff(raw_diff)
                    changed_files = list(file_diffs.keys())
                    
                    # 5. Run Linters + Security in Docker container
                    docker_results = {"lint": {}, "security": {}}
                    if app_config.ENABLE_DOCKER_CHECKS:
                        try:
                            docker_results = await DockerRunner.run_checks_in_container(repo_path, changed_files)
                        except Exception as e:
                            print(f"⚠️ Docker checks failed (continuing with LLM review): {e}")
                            docker_results = {
                                "lint": {"summary": "Skipped due to Docker error", "details": [], "error": str(e)},
                                "security": {"summary": "Skipped due to Docker error", "details": [], "error": str(e)}
                            }
                    else:
                         print("⚠️ Docker checks disabled in config. Skipping.")
                         docker_results = {
                             "lint": {"summary": "Disabled by config", "details": []},
                             "security": {"summary": "Disabled by config", "details": []}
                         }

                    lint_results = docker_results["lint"]
                    sec_results = docker_results["security"]
                    
                    # 6. Update Vector Index (Incremental)
                    print(f"  [Orchestrator] Updating index for {len(changed_files)} changed files...")
                    try:
                        self.indexer.process_diff(changed_files, repo_path)
                    except Exception as e:
                        print(f"⚠️ Index update failed (continuing): {e}")

                    # 7. Combine Reports for Context
                    project_context = await ProjectContextBuilder.build(
                        repo_path=repo_path,
                        repo_full_name=metadata.repo_full_name,
                        pr_title=metadata.title,
                        changed_files=changed_files,
                    )

                    combined_report = f"""
{project_context}

## Automated Analysis Results

### 🔍 Linting ({lint_results.get('summary', 'N/A')})
{self._format_lint_results(lint_results)}

### 🛡️ Security ({sec_results.get('summary', 'N/A')})
{self._format_security_results(sec_results)}
"""
                    
                    # 8. Build full instructions with custom checks
                    full_instructions = repo_config.get("custom_instructions", "")
                    full_instructions += "\n\n" + combined_report
                    
                    custom_checks = repo_config.get("custom_checks", [])
                    
                    # 9. Generate Inline Review (concise, line-specific)
                    review_result = self.reviewer.run_inline_review(
                        raw_diff, 
                        metadata.title, 
                        full_instructions,
                        custom_checks=custom_checks,
                        repo_path=repo_path
                    )
                    
                    # 10. Build Inline GitHub Comments
                    inline_comments = []      # Only path/line/side/body for GitHub API
                    comments_failed_validation = []
                    
                    for comment in review_result.get("inline_comments", []):
                        file_diff = file_diffs.get(comment.get("path", ""), "")
                        valid_lines = DiffParser.get_valid_right_lines(file_diff)
                        
                        line = comment.get("line")
                        if line is None:
                            continue
                        try:
                            line = int(line)
                        except (ValueError, TypeError):
                            continue
                        original_line = line
                        
                        # Validate line is part of the PR diff
                        if not valid_lines:
                             comments_failed_validation.append(f"- **{comment.get('path', 'unknown')}**: {comment.get('body', 'No message')[:80]} (File not in diff)")
                             continue
                             
                        if line not in valid_lines:
                            # Snap to nearest valid diff line (generous: 20 lines)
                            if valid_lines:
                                nearest = min(valid_lines, key=lambda x: abs(x - line))
                                if abs(nearest - line) <= 20:
                                    line = nearest
                                else:
                                    comments_failed_validation.append(f"- **{comment.get('path', 'unknown')}**: Line {original_line} not in diff")
                                    continue
                            else:
                                comments_failed_validation.append(f"- **{comment.get('path', 'unknown')}**: No valid lines in diff")
                                continue
                        
                        # GitHub API: ONLY path, line, side, body (no extra fields!)
                        inline_comments.append({
                            "path": comment.get("path", "unknown"),
                            "line": line,
                            "side": "RIGHT",
                            "body": comment.get("body", "Issue found")
                        })
                    
                    # ═══════════════════════════════════════════════════════
                    # 11. BUILD CODERABBIT-STYLE SUMMARY (Dynamic Dropdowns)
                    # ═══════════════════════════════════════════════════════
                    clean_files = review_result.get("clean_files", [])
                    verdict = review_result.get("verdict", "COMMENT")
                    file_summaries = review_result.get("file_summaries", {})
                    stats = review_result.get("stats", {})
                    
                    # ── DROPDOWN 1: 📝 Walkthrough ──
                    walkthrough_parts = []
                    for fp, cs in file_summaries.items():
                        if cs and cs.strip():
                            walkthrough_parts.append(cs.strip())
                    walkthrough = " ".join(walkthrough_parts) if walkthrough_parts else review_result.get("summary", "Review complete.")
                    
                    summary = "<details>\n"
                    summary += "<summary>📝 Walkthrough</summary>\n\n"
                    summary += f"## Walkthrough\n\n{walkthrough}\n\n"
                    summary += "## Changes\n\n"
                    summary += "| Cohort / File(s) | Summary |\n"
                    summary += "|---|---|\n"
                    lang_names = {'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript', 'java': 'Java', 'cpp': 'C++', 'c': 'C', 'go': 'Go', 'rs': 'Rust', 'rb': 'Ruby', 'php': 'PHP', 'cs': 'C#', 'yml': 'YAML', 'yaml': 'YAML', 'json': 'JSON', 'sql': 'SQL', 'html': 'HTML', 'css': 'CSS', 'jsx': 'React JSX', 'tsx': 'React TSX', 'md': 'Documentation'}
                    for fp in file_diffs.keys():
                        ext = fp.rsplit('.', 1)[-1] if '.' in fp else ''
                        cohort = lang_names.get(ext, ext.upper() if ext else 'File')
                        change_desc = file_summaries.get(fp, "Modified in this PR")
                        summary += f"| **{cohort}**<br>`{fp}` | {change_desc} |\n"
                    summary += "\n</details>\n\n"
                    
                    # ── BUILD CHECKS DATA ──
                    checks = []
                    
                    # Check: Security Scan
                    if sec_results.get("error"):
                        checks.append({"name": "Security Scan", "status": "Failed", "emoji": "❌", "group": "failed",
                            "explanation": f"Security scan encountered an error: {sec_results['error'][:100]}",
                            "resolution": "Fix the security scanner configuration or dependencies."})
                    elif sec_results.get("details"):
                        n_sec = len(sec_results["details"])
                        checks.append({"name": "Security Scan", "status": "Warning", "emoji": "⚠️", "group": "failed",
                            "explanation": f"Found {n_sec} potential security issue(s) in the codebase.",
                            "resolution": "Review the security findings and address any confirmed vulnerabilities."})
                    else:
                        checks.append({"name": "Security Scan", "status": "Passed", "emoji": "✅", "group": "passed",
                            "explanation": "No security issues detected.", "resolution": ""})
                    
                    # Check: Lint Analysis
                    lint_details = lint_results.get("details", [])
                    if lint_details and len(lint_details) > 10:
                        checks.append({"name": "Lint Analysis", "status": "Warning", "emoji": "⚠️", "group": "failed",
                            "explanation": f"Found {len(lint_details)} linting issues across the changed files.",
                            "resolution": "Run the project linter and fix the reported issues before merging."})
                    elif lint_details:
                        checks.append({"name": "Lint Analysis", "status": "Passed", "emoji": "✅", "group": "passed",
                            "explanation": f"Minor lint issues ({len(lint_details)}), within acceptable threshold.", "resolution": ""})
                    else:
                        checks.append({"name": "Lint Analysis", "status": "Passed", "emoji": "✅", "group": "passed",
                            "explanation": "No linting issues detected.", "resolution": ""})
                    
                    # Check: Code Review
                    n_issues = len(inline_comments)
                    if verdict in ("REQUEST_CHANGES", "BLOCK"):
                        checks.append({"name": "Code Review", "status": "Failed", "emoji": "❌", "group": "failed",
                            "explanation": f"Found {n_issues} issue(s) that require changes before merging.",
                            "resolution": "Address the issues flagged in the inline review comments."})
                    elif n_issues > 0:
                        checks.append({"name": "Code Review", "status": "Warning", "emoji": "⚠️", "group": "failed",
                            "explanation": f"Found {n_issues} issue(s) that should be reviewed.",
                            "resolution": "Review the inline comments and address the suggestions."})
                    else:
                        checks.append({"name": "Code Review", "status": "Passed", "emoji": "✅", "group": "passed",
                            "explanation": "All reviewed files passed with no issues.", "resolution": ""})
                    
                    # Check: PR Description
                    pr_desc = metadata.description if hasattr(metadata, 'description') and metadata.description else ""
                    if not pr_desc or len(pr_desc.strip()) < 20:
                        checks.append({"name": "PR Description", "status": "Inconclusive", "emoji": "❓", "group": "failed",
                            "explanation": "The PR description is missing or too brief to assess intent.",
                            "resolution": "Add a descriptive PR body summarizing the changes and their purpose."})
                    else:
                        checks.append({"name": "PR Description", "status": "Passed", "emoji": "✅", "group": "passed",
                            "explanation": "PR has a meaningful description.", "resolution": ""})
                    
                    # ── Separate into groups ──
                    failed_checks = [c for c in checks if c["group"] == "failed"]
                    passed_checks = [c for c in checks if c["group"] == "passed"]
                    
                    # Count sub-types for failed label
                    n_warnings = sum(1 for c in failed_checks if c["status"] == "Warning")
                    n_failures = sum(1 for c in failed_checks if c["status"] == "Failed")
                    n_inconclusive = sum(1 for c in failed_checks if c["status"] == "Inconclusive")
                    failed_parts = []
                    if n_failures: failed_parts.append(f"{n_failures} failed")
                    if n_warnings: failed_parts.append(f"{n_warnings} warning")
                    if n_inconclusive: failed_parts.append(f"{n_inconclusive} inconclusive")
                    
                    summary += "## Pre-merge checks and finishing touches\n\n"
                    
                    # ── DROPDOWN 2: ❌ Failed checks (dynamic) ──
                    if failed_checks:
                        failed_label = ", ".join(failed_parts)
                        summary += "<details>\n"
                        summary += f"<summary>❌ Failed checks ({failed_label})</summary>\n\n"
                        summary += "| Check name | Status | Explanation | Resolution |\n"
                        summary += "|---|---|---|---|\n"
                        for c in failed_checks:
                            summary += f"| {c['name']} | {c['emoji']} {c['status']} | {c['explanation']} | {c['resolution']} |\n"
                        summary += "\n</details>\n\n"
                    
                    # ── DROPDOWN 3: ✅ Passed checks (dynamic) ──
                    if passed_checks:
                        summary += "<details>\n"
                        summary += f"<summary>✅ Passed checks ({len(passed_checks)} passed)</summary>\n\n"
                        summary += "| Check name | Status | Explanation |\n"
                        summary += "|---|---|---|\n"
                        for c in passed_checks:
                            summary += f"| {c['name']} | ✅ Passed | {c['explanation']} |\n"
                        summary += "\n</details>\n\n"
                    
                    # ── DROPDOWN 4: ✨ Finishing touches (dynamic) ──
                    finishing = []
                    has_python = any(f.endswith('.py') for f in file_diffs.keys())
                    if has_python:
                        finishing.append("📄 Add or update docstrings for changed functions")
                    has_tests = any('test' in f.lower() for f in file_diffs.keys())
                    if not has_tests and len(file_diffs) > 1:
                        finishing.append("🧪 Add unit tests for the new or modified code")
                    has_changelog = any('changelog' in f.lower() or 'changes' in f.lower() for f in file_diffs.keys())
                    if not has_changelog and len(file_diffs) > 2:
                        finishing.append("📋 Update CHANGELOG or release notes")
                    
                    if finishing:
                        summary += "<details>\n"
                        summary += "<summary>✨ Finishing touches</summary>\n\n"
                        for ft in finishing:
                            summary += f"- [ ] {ft}\n"
                        summary += "\n</details>\n\n"
                    
                    summary += "---\n"
                    summary += "Comment `@agenticpr help` to get the list of available commands and usage tips.\n"
                    
                    # ═══════════════════════════════════════════════════════
                    # 12. BUILD BLOCK 2: REVIEW BODY (Fix prompt, Nitpicks, Review details)
                    # ═══════════════════════════════════════════════════════
                    nitpicks = review_result.get("nitpicks", {})
                    lgtm_notes = review_result.get("lgtm_notes", {})
                    all_raw_findings = review_result.get("all_raw_findings", {})
                    total_actionable = len(inline_comments)
                    total_nitpicks = sum(len(v) for v in nitpicks.values())
                    total_comments = total_actionable + total_nitpicks
                    
                    review_body = ""
                    
                    if total_comments > 0:
                        review_body += f"**Actionable comments posted: {total_actionable}**\n\n"
                    else:
                        review_body += "**No actionable comments posted.**\n\n"
                    
                    # ── BLOCK 2 DROPDOWN 1: Fix all issues with AI Agents 🤖 ──
                    if all_raw_findings:
                        try:
                            fix_prompt = self.fix_prompt_agent.generate_fix_prompt(
                                all_raw_findings, pr_title=metadata.title
                            )
                        except Exception as e:
                            print(f"  [FixBot] ⚠️ Fix prompt generation failed: {e}")
                            fix_prompt = "Fix prompt generation failed. Please refer to inline comments."
                        
                        review_body += "<details>\n"
                        review_body += "<summary>Fix all issues with AI Agents 🤖</summary>\n\n"
                        review_body += fix_prompt + "\n\n"
                        review_body += "</details>\n\n"
                    
                    # ── BLOCK 2 DROPDOWN 2: 🧹 Nitpick comments (N) ──
                    if nitpicks:
                        review_body += "<details>\n"
                        review_body += f"<summary>🧹 Nitpick comments ({total_nitpicks})</summary>\n\n"
                        
                        for nit_file, nit_list in nitpicks.items():
                            # Sub-dropdown per file
                            review_body += "<details>\n"
                            review_body += f"<summary>{nit_file} ({len(nit_list)})</summary>\n\n"
                            
                            for nit in nit_list:
                                line = nit.get('line', '?')
                                end_line = nit.get('end_line', line)
                                message = nit.get('message', 'Style suggestion')
                                suggestion = nit.get('suggestion', '')
                                original_code = nit.get('original_code', '')
                                
                                # Line range badge
                                if end_line and end_line != line:
                                    line_badge = f"`{line}-{end_line}`"
                                else:
                                    line_badge = f"`{line}`"
                                
                                review_body += f"{line_badge} : {message}\n\n"
                                
                                # Proposed refactor sub-dropdown (if suggestion exists)
                                if suggestion and original_code:
                                    # Detect language for syntax highlighting
                                    ext = nit_file.rsplit('.', 1)[-1] if '.' in nit_file else ''
                                    lang_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'java': 'java', 'cpp': 'cpp', 'c': 'c', 'go': 'go', 'rs': 'rust', 'rb': 'ruby', 'php': 'php', 'cs': 'csharp', 'jsx': 'javascript', 'tsx': 'typescript'}
                                    lang = lang_map.get(ext, ext)
                                    
                                    review_body += "<details>\n"
                                    review_body += "<summary>🔧 Proposed refactor</summary>\n\n"
                                    review_body += f"```diff\n"
                                    # Show original code as removed lines
                                    for ol in original_code.split('\n'):
                                        review_body += f"-{ol}\n"
                                    # Show suggestion as added lines
                                    for sl in suggestion.split('\n'):
                                        review_body += f"+{sl}\n"
                                    review_body += "```\n\n"
                                    review_body += "</details>\n\n"
                                elif suggestion:
                                    review_body += "<details>\n"
                                    review_body += "<summary>🔧 Proposed refactor</summary>\n\n"
                                    review_body += f"```suggestion\n{suggestion}\n```\n\n"
                                    review_body += "</details>\n\n"
                            
                            review_body += "</details>\n\n"
                        
                        review_body += "</details>\n\n"
                    
                    # ── BLOCK 2 DROPDOWN 3: 📜 Review details ──
                    review_body += "<details>\n"
                    review_body += "<summary>📜 Review details</summary>\n\n"
                    review_body += "**Configuration used:** AgenticPR defaults\n\n"
                    review_body += "**Review profile:** ASSERTIVE\n\n"
                    
                    # Sub-dropdown: 📥 Commits
                    review_body += "<details>\n"
                    review_body += "<summary>📥 Commits</summary>\n\n"
                    review_body += f"Reviewing files that changed from the base of the PR and at commit `{metadata.commit_sha[:7]}`.\n\n"
                    review_body += "</details>\n\n"
                    
                    # Sub-dropdown: 📒 Files selected for processing (N)
                    all_files = list(file_diffs.keys())
                    review_body += "<details>\n"
                    review_body += f"<summary>📒 Files selected for processing ({len(all_files)})</summary>\n\n"
                    for af in all_files:
                        review_body += f"- `{af}`\n"
                    review_body += "\n</details>\n\n"
                    
                    # Sub-dropdown: 🧰 Additional context used
                    has_lint_ctx = lint_results.get("details") and len(lint_results["details"]) > 0
                    has_sec_ctx = sec_results.get("details") and len(sec_results["details"]) > 0
                    
                    if has_lint_ctx or has_sec_ctx:
                        review_body += "<details>\n"
                        review_body += "<summary>🧰 Additional context used</summary>\n\n"
                        
                        if has_lint_ctx:
                            review_body += "<details>\n"
                            review_body += "<summary>🪛 Lint Analysis</summary>\n\n"
                            for issue in lint_results["details"][:15]:
                                lint_file = issue.get('file', '')
                                lint_line = issue.get('line', '')
                                lint_code = issue.get('code', '')
                                lint_msg = issue.get('message', '')
                                review_body += f"`{lint_file}`\n"
                                review_body += f"[error] {lint_line}-{lint_line}: {lint_msg}\n\n"
                                if lint_code:
                                    review_body += f"({lint_code})\n\n"
                            review_body += "</details>\n\n"
                        
                        if has_sec_ctx:
                            review_body += "<details>\n"
                            review_body += "<summary>🔒 Security Scan</summary>\n\n"
                            for issue in sec_results["details"][:10]:
                                sec_file = issue.get('file', '')
                                sec_line = issue.get('line', '')
                                sec_sev = issue.get('severity', 'Unknown')
                                sec_msg = issue.get('message', '')
                                review_body += f"`{sec_file}`\n"
                                review_body += f"[{sec_sev.lower()}] {sec_line}-{sec_line}: {sec_msg}\n\n"
                            review_body += "</details>\n\n"
                        
                        review_body += "</details>\n\n"
                    
                    # Sub-dropdown: 🔇 Additional comments (LGTM files)
                    if lgtm_notes:
                        total_lgtm = len(lgtm_notes)
                        review_body += "<details>\n"
                        review_body += f"<summary>🔇 Additional comments ({total_lgtm})</summary>\n\n"
                        
                        for lgtm_file, lgtm_text in lgtm_notes.items():
                            review_body += "<details>\n"
                            review_body += f"<summary>{lgtm_file} (1)</summary>\n\n"
                            review_body += f"LGTM!\n\n{lgtm_text}\n\n"
                            review_body += "</details>\n\n"
                        
                        review_body += "</details>\n\n"
                    
                    review_body += "</details>\n"
                    
                    # 13. Post to GitHub (Block 1 + Block 2 combined at same level)
                    full_body = summary + "\n\n" + review_body
                    
                    event = "REQUEST_CHANGES" if verdict in ("REQUEST_CHANGES", "BLOCK") else "COMMENT"
                    if verdict in ("APPROVE", "APPROVE_WITH_SUGGESTIONS") and not inline_comments:
                        event = "APPROVE"
                    
                    if inline_comments:
                        # Post combined body as review body + inline comments
                        await self.gh.post_inline_review(
                            metadata.repo_full_name, metadata.pr_number, metadata.commit_sha,
                            inline_comments, full_body, event
                        )
                    else:
                        # Post combined body as a regular comment
                        await self.gh.post_or_update_comment(
                            metadata.repo_full_name, metadata.pr_number, full_body
                        )
                    
                    await self.gh.add_label(metadata.repo_full_name, metadata.pr_number, "ReviewedByApex")
                    
                    # 13. Determine Status
                    # ✅ = review completed (even if issues found)
                    # ❌ = only if an actual error/crash occurred during the process
                    status_state = "success"
                    
                    if verdict == "REQUEST_CHANGES":
                        status_desc = f"Review complete — Changes requested ({len(inline_comments)} issue(s) found)"
                    elif len(inline_comments) > 0:
                        status_desc = f"Review complete — {len(inline_comments)} issue(s) found"
                    else:
                        status_desc = "Review complete — All checks passed"

                    await self.gh.set_commit_status(metadata.repo_full_name, metadata.commit_sha, status_state, status_desc)
                    
                    # 14. Save Results
                    job.status = status_state
                    result = AgentResult(
                        job_id=job.id, 
                        agent_name="reviewer", 
                        output_json=json.dumps({
                            "file_count": len(file_diffs),
                            "files": list(file_diffs.keys()),
                            "clean_files": len(clean_files),
                            "inline_comments": len(inline_comments),
                            "verdict": verdict,
                            "lint_issues": len(lint_results.get("details", [])),
                            "security_issues": len(sec_results.get("details", []))
                        })
                    )
                    session.add(result)
                    session.add(job)
                    await session.commit()
                    
                    print(f"✅ Job {job_id}: {status_state.upper()} - {len(file_diffs)} files, {len(inline_comments)} inline comments, {len(clean_files)} clean")

                finally:
                    manager.cleanup()

            except Exception as e:
                print(f"❌ Job {job_id}: Failed - {e}")
                import traceback
                traceback.print_exc()
                
                try:
                    job = await session.get(Job, job_id)
                    if job:
                        job.status = "failed"
                        session.add(job)
                        await session.commit()
                except:
                    pass
                
                await session.rollback()
                await self.gh.set_commit_status(metadata.repo_full_name, metadata.commit_sha, "failure", f"Error: {str(e)[:50]}")

    def _format_lint_results(self, results: dict) -> str:
        """Format lint results for the LLM context."""
        if not results.get("details"):
            return "No issues found."
        
        output = ""
        for issue in results["details"][:10]:
            output += f"- `{issue.get('file', '')}:{issue.get('line', '')}` [{issue.get('code', '')}] {issue.get('message', '')}\n"
        
        if len(results["details"]) > 10:
            output += f"\n... and {len(results['details']) - 10} more issues"
        
        return output

    def _format_security_results(self, results: dict) -> str:
        """Format security results for the LLM context."""
        if results.get("error"):
            return f"Scan error: {results['error']}"
        
        if not results.get("details"):
            return "No security issues found."
        
        output = ""
        for issue in results["details"][:5]:
            output += f"- **{issue.get('severity', 'Unknown')}** in `{issue.get('file', '')}:{issue.get('line', '')}`: {issue.get('message', '')}\n"
        
        if len(results["details"]) > 5:
            output += f"\n... and {len(results['details']) - 5} more issues"
        
        return output