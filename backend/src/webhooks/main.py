from fastapi import FastAPI, BackgroundTasks, HTTPException, Body, Depends, Request
from contextlib import asynccontextmanager
from core.types import PRMetadata
from core.orchestrator import Orchestrator
from core.security import verify_github_signature
from database import init_db, get_session
from models import Job
from sqlalchemy.ext.asyncio import AsyncSession

# 1. Lifecycle Event to Init DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(title="PR Review Bot", lifespan=lifespan)
orchestrator = Orchestrator()

@app.post("/webhook/pr", dependencies=[Depends(verify_github_signature)])
async def receive_webhook(
    request: Request, # Needed for signature verification
    background_tasks: BackgroundTasks,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    action = payload.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return {"msg": "Action ignored"}
        
    pr_data = payload.get("pull_request")
    if not pr_data:
        raise HTTPException(status_code=400, detail="Not a PR event")

    metadata = PRMetadata(
        repo_full_name=payload["repository"]["full_name"],
        pr_number=pr_data["number"],
        commit_sha=pr_data["head"]["sha"],
        title=pr_data["title"],
        description=pr_data.get("body", "") or "",
        branch_name=pr_data["head"]["ref"]
    )

    # 2. Persist Job to DB (Req 4.1)
    new_job = Job(
        repo_full_name=metadata.repo_full_name,
        pr_number=metadata.pr_number,
        commit_sha=metadata.commit_sha,
        status="queued"
    )
    session.add(new_job)
    await session.commit()
    await session.refresh(new_job)

    # 3. Enqueue with Job ID
    background_tasks.add_task(orchestrator.process_pr, metadata, new_job.id)
    
    return {"status": "job accepted", "job_id": new_job.id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)