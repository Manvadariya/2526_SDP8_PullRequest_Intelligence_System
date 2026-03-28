from fastapi import FastAPI, BackgroundTasks, HTTPException, Body, Depends, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from core.types import PRMetadata
from core.orchestrator import Orchestrator
from core.security import verify_github_signature
from database import init_db, get_session
from models import Job, ReviewRequest, ReviewAttempt, JobStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from fastapi.middleware.cors import CORSMiddleware
import auth
import api_router
import os
import logging

logger = logging.getLogger("agenticpr")

# 1. Lifecycle Event to Init DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Initialize Redis queue connection
    from workers.queue import QueueManager
    app.state.queue = QueueManager()
    await app.state.queue.connect()
    logger.info("Database and queue initialized")
    yield
    await app.state.queue.disconnect()

app = FastAPI(title="AgenticPR - PR Review Bot", lifespan=lifespan)

# --- CORS MUST BE FIRST ---
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "*"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS] if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()

# Register routers
app.include_router(auth.router)
app.include_router(api_router.router)

# NOTE: DebugMiddleware REMOVED — it logged all request headers including auth tokens.
# Use structured logging (logger.debug) for request tracing instead.

# --- Health check endpoint (GET) ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Server is running!"}

@app.get("/webhook/pr")
async def webhook_health():
    return {"status": "ok", "message": "Webhook endpoint is reachable! Use POST for actual webhooks."}

@app.post("/webhook/pr", dependencies=[Depends(verify_github_signature)])
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    # --- 1. Parse and validate ---
    action = payload.get("action")
    delivery_id = request.headers.get("X-GitHub-Delivery", "")
    logger.info(f"Webhook received: action={action} delivery={delivery_id}")
    
    if action not in ["opened", "synchronize", "reopened"]:
        return {"msg": "Action ignored"}
        
    pr_data = payload.get("pull_request")
    if not pr_data:
        raise HTTPException(status_code=400, detail="Not a PR event")

    repo_full_name = payload["repository"]["full_name"]
    pr_number = pr_data["number"]
    commit_sha = pr_data["head"]["sha"]
    
    metadata = PRMetadata(
        repo_full_name=repo_full_name,
        pr_number=pr_number,
        commit_sha=commit_sha,
        title=pr_data["title"],
        description=pr_data.get("body", "") or "",
        branch_name=pr_data["head"]["ref"]
    )

    # --- 2. Deduplicate: Skip only if an ACTIVE job exists for this exact commit ---
    dedupe_key = f"github:{repo_full_name}:{pr_number}:{commit_sha}"
    existing = await session.execute(
        select(Job).where(
            Job.repo_full_name == repo_full_name,
            Job.pr_number == pr_number,
            Job.commit_sha == commit_sha
        )
    )
    existing_job = existing.scalars().first()
    if existing_job:
        # Only deduplicate if the job is still actively processing
        active_statuses = [
            JobStatus.QUEUED, JobStatus.PROCESSING,
            JobStatus.FETCHING, JobStatus.ANALYZING, JobStatus.REVIEWING
        ]
        if existing_job.status in active_statuses:
            logger.info(f"Duplicate webhook ignored (job still active): {dedupe_key}")
            return {"status": "duplicate", "msg": "Review already in progress for this commit"}
        
        # Job failed/completed/superseded — allow re-trigger by resetting it
        logger.info(f"Re-triggering job {existing_job.id} (was {existing_job.status}) for {dedupe_key}")
        existing_job.status = JobStatus.QUEUED
        existing_job.error_detail = None
        existing_job.finished_at = None
        existing_job.started_at = None
        existing_job.retry_count = 0
        session.add(existing_job)
        await session.commit()
        await session.refresh(existing_job)
        new_job = existing_job  # Reuse the existing job record
    else:
        # --- 3. Supersede: Cancel older queued/processing jobs for the same PR ---
        older_jobs_result = await session.execute(
            select(Job).where(
                Job.repo_full_name == repo_full_name,
                Job.pr_number == pr_number,
                Job.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING])
            )
        )
        for old_job in older_jobs_result.scalars().all():
            old_job.status = JobStatus.SUPERSEDED
            session.add(old_job)
            logger.info(f"Superseded job {old_job.id} (sha={old_job.commit_sha[:7]}) for PR #{pr_number}")

        # --- 4. Persist new job ---
        new_job = Job(
            repo_full_name=repo_full_name,
            pr_number=pr_number,
            commit_sha=commit_sha,
            status=JobStatus.QUEUED
        )
        session.add(new_job)
        await session.commit()
        await session.refresh(new_job)

    # --- 5. Set GitHub commit status to pending ---
    try:
        from core.github_client import GitHubClient
        gh_client = GitHubClient()
        await gh_client.set_commit_status(
            repo_full_name, commit_sha, "pending",
            "AgenticPR review queued — processing will begin shortly."
        )
        logger.info(f"✅ GitHub status set to 'pending' for {repo_full_name}#{pr_number} (sha: {commit_sha[:7]})")
    except Exception as e:
        logger.warning(f"Failed to set initial GitHub status: {e}")

    # --- 6. Enqueue to durable queue (with BackgroundTasks fallback) ---
    try:
        queue: 'QueueManager' = request.app.state.queue
        await queue.enqueue("review:fetch", {
            "job_id": new_job.id,
            "repo_full_name": repo_full_name,
            "pr_number": pr_number,
            "commit_sha": commit_sha,
            "title": metadata.title,
            "description": metadata.description,
            "branch_name": metadata.branch_name,
        })
        logger.info(f"")
        logger.info(f"══════════════════════════════════════════════════")
        logger.info(f"📥 WEBHOOK: Job {new_job.id} enqueued for review")
        logger.info(f"   PR:    {repo_full_name}#{pr_number}")
        logger.info(f"   SHA:   {commit_sha[:7]}")
        logger.info(f"   Title: {metadata.title}")
        logger.info(f"══════════════════════════════════════════════════")
        logger.info(f"")
    except Exception as e:
        # Fallback: run in-process if Redis is not available
        logger.warning(f"Redis enqueue failed ({e}), falling back to BackgroundTasks")
        background_tasks.add_task(orchestrator.process_pr, metadata, new_job.id)
    
    return {"status": "job accepted", "job_id": new_job.id, "dedupe_key": dedupe_key}

if __name__ == "__main__":
    import asyncio
    import sys
    import subprocess
    import os

    PORT = 8000

    def kill_port(port):
        """Kill any process currently using the given port (Windows only)."""
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            pids_killed = set()
            my_pid = os.getpid()
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.strip().split()
                    pid = int(parts[-1])
                    if pid != my_pid and pid not in pids_killed:
                        try:
                            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                           capture_output=True, check=True)
                            print(f"🔪 Killed zombie process {pid} on port {port}")
                            pids_killed.add(pid)
                        except subprocess.CalledProcessError:
                            pass
            if not pids_killed:
                print(f" Port {port} is free")
        except Exception as e:
            print(f" Could not check port: {e}")

    # Auto-clear the port before starting
    if sys.platform.startswith("win"):
        kill_port(PORT)
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn
    print(f"\n Starting PR Review Bot on http://0.0.0.0:{PORT}")
    print(f"   Health check: http://localhost:{PORT}/health")
    print(f"   Webhook: POST http://localhost:{PORT}/webhook/pr\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)