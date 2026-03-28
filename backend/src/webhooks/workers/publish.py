"""
Publish Worker — Stage 4: Post review results to GitHub/Bitbucket.

Responsibilities:
  - Build the review summary (CodeRabbit-style markdown)
  - Post inline review comments
  - Post summary comment  
  - Set commit status
  - Track published comments for idempotency
  - Clean up workspace after publish
"""

import os
import shutil
import logging
from typing import Dict, Any, Optional

from workers.base import BaseWorker

logger = logging.getLogger("agenticpr.worker.publish")


class PublishWorker(BaseWorker):
    QUEUE_NAME = "review:publish"
    GROUP_NAME = "cg_publish"
    STAGE_NAME = "publishing"
    MAX_RETRIES = 5  # Publish is idempotent, safe to retry aggressively
    TIMEOUT_SECONDS = 60
    BACKOFF_SECONDS = [5, 10, 20, 40, 60]
    NEXT_QUEUE = None  # Terminal stage
    
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Publish review results to GitHub."""
        job_id = data["job_id"]
        repo_full_name = data["repo_full_name"]
        pr_number = data["pr_number"]
        commit_sha = data["commit_sha"]
        review_result = data.get("review_result")
        findings_count = data.get("findings_count", 0)
        workspace_dir = data.get("workspace_dir", "")
        
        logger.info(f"[publish] Job {job_id}: Publishing to {repo_full_name}#{pr_number}")
        
        from core.github_client import GitHubClient
        github = GitHubClient()
        
        try:
            # --- 1. Set commit status to pending ---
            await github.set_commit_status(
                repo_full_name, commit_sha, "pending",
                "AgenticPR review publishing...",
            )
            
            # --- 2. Publish review results ---
            if review_result:
                await self._publish_review(
                    github, repo_full_name, pr_number, commit_sha, review_result, data
                )
            else:
                # No review result — post a quick summary
                await github.post_or_update_comment(
                    repo_full_name, pr_number,
                    "## ✅ AgenticPR Review\n\n"
                    "No issues found. All checks passed!\n\n"
                    f"*Reviewed commit: `{commit_sha[:7]}`*"
                )
            
            # --- 3. Set final commit status ---
            if findings_count > 0:
                status_desc = f"AgenticPR: {findings_count} issue(s) found"
                await github.set_commit_status(
                    repo_full_name, commit_sha, "success", status_desc
                )
            else:
                await github.set_commit_status(
                    repo_full_name, commit_sha, "success",
                    "AgenticPR: All checks passed"
                )
            
            # --- 4. Add labels ---
            try:
                if findings_count > 5:
                    await github.add_label(repo_full_name, pr_number, "needs-review")
                else:
                    await github.add_label(repo_full_name, pr_number, "pr-reviewed")
            except Exception as e:
                logger.debug(f"[publish] Label failed (non-critical): {e}")
            
            logger.info(f"[publish] Job {job_id}: Published successfully")
            
        except Exception as e:
            logger.error(f"[publish] Job {job_id}: Publish failed: {e}")
            # Set error status on commit
            try:
                await github.set_commit_status(
                    repo_full_name, commit_sha, "error",
                    "AgenticPR review publish failed"
                )
            except Exception:
                pass
            raise
        
        finally:
            # --- 5. Clean up workspace ---
            self._cleanup_workspace(workspace_dir, job_id)
        
        return None  # Terminal stage
    
    async def _publish_review(
        self, github, repo_full_name: str, pr_number: int,
        commit_sha: str, review_result: Any, data: Dict
    ):
        """Publish the review using the full rich CodeRabbit-style body."""
        try:
            if isinstance(review_result, dict):
                inline_comments = review_result.get("inline_comments", [])
                
                # Build the full rich body (Walkthrough + Pre-merge checks + Review body)
                full_body = self._build_rich_body(review_result, data, commit_sha)
                
                event = "REQUEST_CHANGES" if review_result.get("verdict") in ("REQUEST_CHANGES", "BLOCK") else "COMMENT"
                if review_result.get("verdict") == "APPROVE" and not inline_comments:
                    event = "APPROVE"
                
                if inline_comments:
                    await github.post_inline_review(
                        repo_full_name, pr_number, commit_sha,
                        inline_comments, full_body, event
                    )
                else:
                    await github.post_or_update_comment(
                        repo_full_name, pr_number, full_body
                    )
            
            elif isinstance(review_result, str) and review_result.strip():
                await github.post_or_update_comment(
                    repo_full_name, pr_number, review_result
                )
                
        except Exception as e:
            logger.error(f"[publish] Review formatting error: {e}")
            # Fallback: post raw result as a comment
            try:
                fallback_body = f"## 🤖 AgenticPR Review\n\n{str(review_result)[:4000]}"
                await github.post_or_update_comment(
                    repo_full_name, pr_number, fallback_body
                )
            except Exception as e2:
                logger.error(f"[publish] Fallback publish also failed: {e2}")
                raise

    def _build_rich_body(self, review_result: Dict, data: Dict, commit_sha: str) -> str:
        """Build the full CodeRabbit-style rich markdown body from a review_result dict."""
        file_summaries = review_result.get("file_summaries", {})
        nitpicks = review_result.get("nitpicks", {})
        lgtm_notes = review_result.get("lgtm_notes", {})
        all_raw_findings = review_result.get("all_raw_findings", {})
        inline_comments = review_result.get("inline_comments", [])
        clean_files = review_result.get("clean_files", [])
        verdict = review_result.get("verdict", "COMMENT")
        stats = review_result.get("stats", {})

        # File diffs keys — try to reconstruct from inline_comments + clean_files + file_summaries
        all_files = list(file_summaries.keys()) or list(all_raw_findings.keys())
        for c in inline_comments:
            fp = c.get("path", "")
            if fp and fp not in all_files:
                all_files.append(fp)
        for fp in clean_files:
            if fp not in all_files:
                all_files.append(fp)

        # ── BLOCK 0: DeepSource-style PR Report Card ──
        from core.summary_builder import build_report_card_block
        repo_full_name = data.get("repo_full_name", "")
        pr_number = data.get("pr_number", 0)
        report_card = build_report_card_block(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            commit_sha=commit_sha,
            inline_comments=inline_comments,
            nitpicks=nitpicks,
            clean_files=clean_files,
            all_files=all_files,
            all_raw_findings=all_raw_findings,
            verdict=verdict,
        )

        # ── BLOCK 1: Walkthrough ──
        walkthrough_parts = [cs.strip() for cs in file_summaries.values() if cs and cs.strip()]
        walkthrough = " ".join(walkthrough_parts) if walkthrough_parts else review_result.get("summary", "Review complete.")

        summary = report_card
        summary += "<details>\n"
        summary += "<summary> Walkthrough</summary>\n\n"
        summary += f"## Walkthrough\n\n{walkthrough}\n\n"
        summary += "## Changes\n\n"
        summary += "| Cohort / File(s) | Summary |\n"
        summary += "|---|---|\n"
        lang_names = {
            'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript', 'java': 'Java',
            'cpp': 'C++', 'c': 'C', 'go': 'Go', 'rs': 'Rust', 'rb': 'Ruby',
            'php': 'PHP', 'cs': 'C#', 'yml': 'YAML', 'yaml': 'YAML', 'json': 'JSON',
            'sql': 'SQL', 'html': 'HTML', 'css': 'CSS', 'jsx': 'React JSX',
            'tsx': 'React TSX', 'md': 'Documentation'
        }
        for fp in all_files:
            ext = fp.rsplit('.', 1)[-1] if '.' in fp else ''
            cohort = lang_names.get(ext, ext.upper() if ext else 'File')
            change_desc = file_summaries.get(fp, "Modified in this PR")
            summary += f"| **{cohort}**<br>`{fp}` | {change_desc} |\n"
        summary += "\n</details>\n\n"

        # ── Pre-merge checks ──
        # We don't have lint/sec results here, so build minimal checks from what we have
        checks = []
        n_issues = len(inline_comments)
        if verdict in ("REQUEST_CHANGES", "BLOCK"):
            checks.append({"name": "Code Review", "status": "Failed", "emoji": "", "group": "failed",
                "explanation": f"Found {n_issues} issue(s) that require changes before merging.",
                "resolution": "Address the issues flagged in the inline review comments."})
        elif n_issues > 0:
            checks.append({"name": "Code Review", "status": "Warning", "emoji": "", "group": "failed",
                "explanation": f"Found {n_issues} issue(s) that should be reviewed.",
                "resolution": "Review the inline comments and address the suggestions."})
        else:
            checks.append({"name": "Code Review", "status": "Passed", "emoji": "", "group": "passed",
                "explanation": "All reviewed files passed with no issues.", "resolution": ""})

        pr_desc = data.get("description", "")
        if not pr_desc or len(str(pr_desc).strip()) < 20:
            checks.append({"name": "PR Description", "status": "Inconclusive", "emoji": "❓", "group": "failed",
                "explanation": "The PR description is missing or too brief to assess intent.",
                "resolution": "Add a descriptive PR body summarizing the changes and their purpose."})
        else:
            checks.append({"name": "PR Description", "status": "Passed", "emoji": "", "group": "passed",
                "explanation": "PR has a meaningful description.", "resolution": ""})

        failed_checks = [c for c in checks if c["group"] == "failed"]
        passed_checks = [c for c in checks if c["group"] == "passed"]

        n_warnings = sum(1 for c in failed_checks if c["status"] == "Warning")
        n_failures = sum(1 for c in failed_checks if c["status"] == "Failed")
        n_inconclusive = sum(1 for c in failed_checks if c["status"] == "Inconclusive")
        failed_parts = []
        if n_failures: failed_parts.append(f"{n_failures} failed")
        if n_warnings: failed_parts.append(f"{n_warnings} warning")
        if n_inconclusive: failed_parts.append(f"{n_inconclusive} inconclusive")

        summary += "## Pre-merge checks and finishing touches\n\n"

        if failed_checks:
            failed_label = ", ".join(failed_parts)
            summary += "<details>\n"
            summary += f"<summary> Failed checks ({failed_label})</summary>\n\n"
            summary += "| Check name | Status | Explanation | Resolution |\n"
            summary += "|---|---|---|---|\n"
            for c in failed_checks:
                summary += f"| {c['name']} | {c['emoji']} {c['status']} | {c['explanation']} | {c['resolution']} |\n"
            summary += "\n</details>\n\n"

        if passed_checks:
            summary += "<details>\n"
            summary += f"<summary> Passed checks ({len(passed_checks)} passed)</summary>\n\n"
            summary += "| Check name | Status | Explanation |\n"
            summary += "|---|---|---|\n"
            for c in passed_checks:
                summary += f"| {c['name']} |  Passed | {c['explanation']} |\n"
            summary += "\n</details>\n\n"

        # Finishing touches
        finishing = []
        has_python = any(f.endswith('.py') for f in all_files)
        if has_python:
            finishing.append("📄 Add or update docstrings for changed functions")
        has_tests = any('test' in f.lower() for f in all_files)
        if not has_tests and len(all_files) > 1:
            finishing.append("🧪 Add unit tests for the new or modified code")
        has_changelog = any('changelog' in f.lower() or 'changes' in f.lower() for f in all_files)
        if not has_changelog and len(all_files) > 2:
            finishing.append("📋 Update CHANGELOG or release notes")

        if finishing:
            summary += "<details>\n"
            summary += "<summary>✨ Finishing touches</summary>\n\n"
            for ft in finishing:
                summary += f"- [ ] {ft}\n"
            summary += "\n</details>\n\n"

        summary += "---\n"
        summary += "Comment `@agenticpr help` to get the list of available commands and usage tips.\n"

        # ── BLOCK 2: Review body (Actionable comments + Nitpicks + Review details) ──
        total_actionable = len(inline_comments)
        total_nitpicks = sum(len(v) for v in nitpicks.values())
        total_comments = total_actionable + total_nitpicks

        review_body = ""
        if total_comments > 0:
            review_body += f"**Actionable comments posted: {total_actionable}**\n\n"
        else:
            review_body += "**No actionable comments posted.**\n\n"

        # Fix all issues dropdown
        if all_raw_findings:
            try:
                from agents.fix_prompt_agent import FixPromptAgent
                fix_agent = FixPromptAgent()
                fix_prompt = fix_agent.generate_fix_prompt(all_raw_findings, pr_title=data.get("title", ""))
            except Exception as e:
                logger.warning(f"[publish] Fix prompt generation failed: {e}")
                fix_prompt = "Fix prompt generation failed. Please refer to inline comments."
            review_body += "<details>\n"
            review_body += "<summary>Fix all issues with AI Agents 🤖</summary>\n\n"
            review_body += fix_prompt + "\n\n"
            review_body += "</details>\n\n"

        # Nitpick comments dropdown
        if nitpicks:
            review_body += "<details>\n"
            review_body += f"<summary> Nitpick comments ({total_nitpicks})</summary>\n\n"
            for nit_file, nit_list in nitpicks.items():
                review_body += "<details>\n"
                review_body += f"<summary>{nit_file} ({len(nit_list)})</summary>\n\n"
                for nit in nit_list:
                    line = nit.get('line', '?')
                    end_line = nit.get('end_line', line)
                    message = nit.get('message', 'Style suggestion')
                    suggestion = nit.get('suggestion', '')
                    original_code = nit.get('original_code', '')
                    line_badge = f"`{line}-{end_line}`" if end_line and end_line != line else f"`{line}`"
                    review_body += f"{line_badge} : {message}\n\n"
                    if suggestion and original_code:
                        ext = nit_file.rsplit('.', 1)[-1] if '.' in nit_file else ''
                        lang_map = {'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'java': 'java'}
                        lang = lang_map.get(ext, ext)
                        review_body += "<details>\n"
                        review_body += "<summary>🔧 Proposed refactor</summary>\n\n"
                        review_body += "```diff\n"
                        for ol in original_code.split('\n'):
                            review_body += f"-{ol}\n"
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

        # Review details dropdown
        review_body += "<details>\n"
        review_body += "<summary>📜 Review details</summary>\n\n"
        review_body += "**Configuration used:** AgenticPR defaults\n\n"
        review_body += "**Review profile:** ASSERTIVE\n\n"
        review_body += "<details>\n"
        review_body += "<summary>📥 Commits</summary>\n\n"
        review_body += f"Reviewing files that changed from the base of the PR and at commit `{commit_sha[:7]}`.\n\n"
        review_body += "</details>\n\n"
        review_body += "<details>\n"
        review_body += f"<summary>📒 Files selected for processing ({len(all_files)})</summary>\n\n"
        for af in all_files:
            review_body += f"- `{af}`\n"
        review_body += "\n</details>\n\n"

        if lgtm_notes:
            review_body += "<details>\n"
            review_body += f"<summary>🔇 Additional comments ({len(lgtm_notes)})</summary>\n\n"
            for lgtm_file, lgtm_text in lgtm_notes.items():
                review_body += "<details>\n"
                review_body += f"<summary>{lgtm_file} (1)</summary>\n\n"
                review_body += f"LGTM!\n\n{lgtm_text}\n\n"
                review_body += "</details>\n\n"
            review_body += "</details>\n\n"

        review_body += "</details>\n"

        return summary + "\n\n" + review_body
    
    def _cleanup_workspace(self, workspace_dir: str, job_id: int):
        """Clean up the workspace directory after publishing."""
        if workspace_dir and os.path.exists(workspace_dir):
            try:
                shutil.rmtree(workspace_dir, ignore_errors=True)
                logger.debug(f"[publish] Cleaned up workspace for job {job_id}")
            except Exception as e:
                logger.debug(f"[publish] Workspace cleanup failed: {e}")
