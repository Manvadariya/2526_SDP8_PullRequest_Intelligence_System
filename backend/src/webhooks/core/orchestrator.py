from sqlmodel import select
from core.github_client import GitHubClient
from core.types import PRMetadata
from agents.reviewer import ReviewerAgent
from models import Job, AgentResult
from database import engine
from sqlalchemy.ext.asyncio import AsyncSession

class Orchestrator:
    def __init__(self):
        self.gh = GitHubClient()
        self.reviewer = ReviewerAgent()

    async def process_pr(self, metadata: PRMetadata, job_id: int):
        print(f"🚀 Job {job_id}: Processing PR #{metadata.pr_number}")
        
        # FIX 1: expire_on_commit=False prevents the "greenlet" error
        # by keeping the 'job' object valid after the first commit.
        async with AsyncSession(engine, expire_on_commit=False) as session:
            try:
                # 1. Update status to 'processing'
                job = await session.get(Job, job_id)
                if not job:
                    print(f"❌ Job {job_id} not found in DB")
                    return

                job.status = "processing"
                session.add(job)
                await session.commit()

                # 2. Get Diff & Run Agent
                raw_diff = await self.gh.get_pr_diff(metadata.repo_full_name, metadata.pr_number)
                review_comment = self.reviewer.run(raw_diff, metadata.title)
                
                # 3. Post to GitHub
                await self.gh.post_comment(metadata.repo_full_name, metadata.pr_number, review_comment)
                await self.gh.add_label(metadata.repo_full_name, metadata.pr_number, "SepientPR")

                # 4. Save Result & Update Status
                job.status = "success"
                
                result = AgentResult(
                    job_id=job.id, 
                    agent_name="reviewer", 
                    output_json=review_comment
                )
                session.add(result)
                session.add(job)
                await session.commit()
                
                print(f"✅ Job {job_id}: Success")

            except Exception as e:
                print(f"❌ Job {job_id}: Failed - {e}")
                
                # FIX 2: Explicit rollback to reset the broken transaction
                await session.rollback()
                
                if job:
                    job.status = "failure"
                    session.add(job)
                    try:
                        await session.commit()
                    except Exception as commit_error:
                        print(f"Critical error saving failure status: {commit_error}")