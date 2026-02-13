from sqlmodel import select
from core.github_client import GitHubClient
from core.custom_checks import CustomCheckLoader
from core.repo_manager import RepoManager
from core.project_context import ProjectContextBuilder
from core.types import PRMetadata
from core.diff_parser import DiffParser
from agents.reviewer import ReviewerAgent
from agents.linter import LinterAgent
from agents.security import SecurityAgent
from models import Job, AgentResult
from database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from config import config as app_config
import json

class Orchestrator:
    def __init__(self):
        self.gh = GitHubClient()
        self.reviewer = ReviewerAgent()
        self.linter = LinterAgent()
        self.security = SecurityAgent()

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
                    
                    # 5. Run Linters (Multi-language, only changed files)
                    lint_results = self.linter.run(repo_path, changed_files)
                    
                    # 6. Run Security Scan
                    sec_results = self.security.run(repo_path)
                    
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
                        custom_checks=custom_checks
                    )
                    
                    # 10. Build Inline GitHub Comments
                    inline_comments = []
                    for comment in review_result.get("inline_comments", []):
                        file_diff = file_diffs.get(comment["path"], "")
                        valid_lines = DiffParser.get_valid_right_lines(file_diff)
                        
                        line = comment["line"]
                        if valid_lines and line not in valid_lines:
                            # Snap to nearest valid diff line
                            line = min(valid_lines, key=lambda x: abs(x - comment["line"]))
                        
                        severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "💡"}.get(
                            comment.get("severity", "info"), "💡"
                        )
                        body = f"{severity_emoji} **{comment.get('severity', 'info').upper()}**: {comment['message']}"
                        
                        if comment.get("suggestion"):
                            body += f"\n\n```suggestion\n{comment['suggestion']}\n```"
                        
                        inline_comments.append({
                            "path": comment["path"],
                            "line": line,
                            "side": "RIGHT",
                            "body": body
                        })
                    
                    # 11. Build Summary (clean files grouped together)
                    clean_files = review_result.get("clean_files", [])
                    verdict = review_result.get("verdict", "COMMENT")
                    summary = f"## 🤖 SapientPR Review\n\n{review_result.get('summary', 'Review complete.')}\n\n"
                    
                    if clean_files:
                        summary += "### ✅ Files Reviewed — No Issues\n"
                        for f in clean_files:
                            summary += f"- `{f}`\n"
                        summary += "\nThese files look good — no conflicts or issues detected.\n\n"
                    
                    if not inline_comments:
                        summary += "> All files passed review. No inline comments needed.\n"
                    
                    # 12. Post Review to GitHub
                    event = "REQUEST_CHANGES" if verdict == "REQUEST_CHANGES" else "COMMENT"
                    if verdict == "APPROVE" and not inline_comments:
                        event = "APPROVE"
                    
                    if inline_comments:
                        await self.gh.post_inline_review(
                            metadata.repo_full_name, metadata.pr_number, metadata.commit_sha,
                            inline_comments, summary, event
                        )
                    else:
                        await self.gh.post_or_update_comment(
                            metadata.repo_full_name, metadata.pr_number, summary
                        )
                    
                    await self.gh.add_label(metadata.repo_full_name, metadata.pr_number, "ReviewedBySapientPR")
                    
                    # 13. Determine Status
                    status_state = "success"
                    status_desc = "Checks Passed"
                    
                    if sec_results.get("error"):
                        status_state = "failure"
                        status_desc = "Security Scan Failed"
                    elif sec_results.get("details"):
                        status_state = "failure"
                        status_desc = f"Found {len(sec_results['details'])} Security Issues"
                    elif verdict == "REQUEST_CHANGES":
                        status_state = "failure"
                        status_desc = f"Changes requested ({len(inline_comments)} issue(s) found)"
                    elif lint_results.get("details") and len(lint_results["details"]) > 10:
                        status_state = "warning"
                        status_desc = f"Found {len(lint_results['details'])} Lint Issues"

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