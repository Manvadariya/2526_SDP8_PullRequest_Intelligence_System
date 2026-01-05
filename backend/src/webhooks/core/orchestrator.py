from sqlmodel import select
from core.github_client import GitHubClient
from core.config_loader import load_repo_config
from core.repo_manager import RepoManager
from core.types import PRMetadata
from agents.reviewer import ReviewerAgent
from agents.linter import LinterAgent
from agents.security import SecurityAgent # NEW
from models import Job, AgentResult
from database import engine
from sqlalchemy.ext.asyncio import AsyncSession
from config import config as app_config

class Orchestrator:
    def __init__(self):
        self.gh = GitHubClient()
        self.reviewer = ReviewerAgent()
        self.linter = LinterAgent()
        self.security = SecurityAgent() # NEW

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
                
                # 2. Config & Clone
                repo_config = await load_repo_config(self.gh, metadata.repo_full_name, metadata.commit_sha)
                repo_url = f"https://github.com/{metadata.repo_full_name}.git"
                manager = RepoManager(repo_url, metadata.commit_sha, app_config.GITHUB_TOKEN)
                repo_path = manager.clone_and_checkout()

                try:
                    # 3. Run All Agents
                    lint_results = self.linter.run(repo_path)
                    sec_results = self.security.run(repo_path) # NEW
                    
                    raw_diff = await self.gh.get_pr_diff(metadata.repo_full_name, metadata.pr_number)
                    
                    # Combine Reports for LLM
                    combined_report = f"""
                    1. LINTING RESULTS (Style):
                    {lint_results}

                    2. SECURITY RESULTS (Bandit):
                    {sec_results}
                    """
                    
                    full_instructions = repo_config.get("custom_instructions", "") + "\n\n" + combined_report

                    review_comment = self.reviewer.run(raw_diff, metadata.title, full_instructions)
                    
                    # 4. Post/Update Comment
                    await self.gh.post_or_update_comment(metadata.repo_full_name, metadata.pr_number, review_comment)
                    await self.gh.add_label(metadata.repo_full_name, metadata.pr_number, "ReviewedBySapientPR")
                    
                    # 5. Determine Success/Failure based on critical issues
                    status_state = "success"
                    status_desc = "Checks Passed"
                    
                    # Fail status check if security issues found (handle both error and details cases)
                    if sec_results.get("error"):
                        status_state = "failure"
                        status_desc = "Security Scan Failed"
                    elif sec_results.get("details"):
                        status_state = "failure"
                        status_desc = "Security Issues Found"

                    await self.gh.set_commit_status(metadata.repo_full_name, metadata.commit_sha, status_state, status_desc)
                    
                    job.status = status_state
                    # Save results (you can save sec_results too if you expand the DB model)
                    result = AgentResult(job_id=job.id, agent_name="reviewer", output_json=review_comment)
                    session.add(result)
                    session.add(job)
                    await session.commit()
                    
                    print(f"✅ Job {job_id}: {status_state.upper()}")

                finally:
                    manager.cleanup()

            except Exception as e:
                print(f"❌ Job {job_id}: Failed - {e}")
                import traceback
                traceback.print_exc()  # Print full traceback for debugging
                
                try:
                    job = await session.get(Job, job_id)
                    if job:
                        job.status = "failed"
                        session.add(job)
                        await session.commit()
                except:
                    pass
                
                await session.rollback()
                await self.gh.set_commit_status(metadata.repo_full_name, metadata.commit_sha, "failure", "Error")