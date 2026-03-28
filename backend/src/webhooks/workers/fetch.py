"""
Fetch Worker — Stage 1: Clone/fetch repo and extract diff.

Responsibilities:
  - Clone the repository (or fetch latest if mirror exists)
  - Extract the PR diff
  - Build file manifest (which files changed)
  - Store workspace reference for subsequent stages
"""

import os
import shutil
import asyncio
import logging
import tempfile
from typing import Dict, Any, Optional

from workers.base import BaseWorker

logger = logging.getLogger("agenticpr.worker.fetch")


class FetchWorker(BaseWorker):
    QUEUE_NAME = "review:fetch"
    GROUP_NAME = "cg_fetch"
    STAGE_NAME = "fetching"
    MAX_RETRIES = 3
    TIMEOUT_SECONDS = 120
    BACKOFF_SECONDS = [5, 15, 45]
    NEXT_QUEUE = "review:analyze"
    NEXT_STAGE_STATUS = "analyzing"
    
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Clone repo, extract diff, prepare workspace."""
        repo_full_name = data["repo_full_name"]
        pr_number = data["pr_number"]
        commit_sha = data["commit_sha"]
        job_id = data["job_id"]
        
        logger.info("")
        logger.info("══════════════════════════════════════════════════")
        logger.info(f"📦 FETCHING STARTED for PR #{pr_number}")
        logger.info(f"   Repo:   {repo_full_name}")
        logger.info(f"   Job ID: {job_id}")
        logger.info(f"   SHA:    {commit_sha[:7]}")
        logger.info("══════════════════════════════════════════════════")
        logger.info("")
        
        logger.info(f"[fetch] Job {job_id}: Fetching {repo_full_name}#{pr_number} @ {commit_sha[:7]}")
        
        # --- 1. Get PR diff from GitHub ---
        from core.github_client import GitHubClient
        github = GitHubClient()
        diff_text = await github.get_pr_diff(repo_full_name, pr_number)
        
        if not diff_text:
            logger.warning(f"[fetch] Job {job_id}: Empty diff for PR #{pr_number}")
            return {"diff_text": "", "changed_files": []}
        
        # --- 2. Parse changed files from diff ---
        changed_files = self._parse_changed_files(diff_text)
        
        logger.info(
            f"[fetch] Job {job_id}: Got diff ({len(diff_text)} chars, "
            f"{len(changed_files)} files changed)"
        )
        
        # --- 3. Clone/fetch repo for local analysis ---
        workspace_dir = os.path.join(
            os.getcwd(), "workspaces", "runs", str(job_id)
        )
        os.makedirs(workspace_dir, exist_ok=True)
        
        clone_success = await self._clone_repo(repo_full_name, commit_sha, workspace_dir)
        
        return {
            "diff_text": diff_text,
            "changed_files": changed_files,
            "workspace_dir": workspace_dir,
            "clone_success": clone_success,
        }
    
    def _parse_changed_files(self, diff_text: str) -> list:
        """Extract list of changed file paths from diff output."""
        files = []
        for line in diff_text.split("\n"):
            if line.startswith("diff --git"):
                parts = line.split(" b/")
                if len(parts) >= 2:
                    files.append(parts[-1].strip())
        return files
    
    async def _clone_repo(self, repo_full_name: str, sha: str, workspace_dir: str) -> bool:
        """Clone or fetch the repository. Returns True on success."""
        from config import config
        
        token = config.GITHUB_TOKEN
        if not token:
            logger.warning("[fetch] No GITHUB_TOKEN — skipping clone")
            return False
        
        clone_url = f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
        
        # Check if we have a mirror cache
        mirror_dir = os.path.join(
            os.getcwd(), "workspaces", "mirrors",
            repo_full_name.replace("/", os.sep) + ".git"
        )
        
        try:
            if os.path.exists(mirror_dir):
                # Fetch latest
                proc = await asyncio.create_subprocess_exec(
                    "git", "fetch", "--all",
                    cwd=mirror_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.wait(), timeout=60)
            else:
                # Create mirror
                os.makedirs(os.path.dirname(mirror_dir), exist_ok=True)
                proc = await asyncio.create_subprocess_exec(
                    "git", "clone", "--mirror", clone_url, mirror_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await asyncio.wait_for(proc.wait(), timeout=90)
            
            # Create worktree for this specific run
            proc = await asyncio.create_subprocess_exec(
                "git", "clone", "--reference", mirror_dir,
                "--single-branch", clone_url, workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.wait(), timeout=60)
            
            # Checkout specific SHA
            proc = await asyncio.create_subprocess_exec(
                "git", "checkout", sha,
                cwd=workspace_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.wait(), timeout=30)
            
            return True
            
        except Exception as e:
            logger.warning(f"[fetch] Clone failed for {repo_full_name}: {e}")
            return False
