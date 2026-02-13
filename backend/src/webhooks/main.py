from fastapi import FastAPI, BackgroundTasks, HTTPException, Body, Depends, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
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

# --- DEBUG: Log ALL incoming requests ---
class DebugMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"\n{'='*60}")
        print(f"📨 INCOMING REQUEST: {request.method} {request.url.path}")
        print(f"   Headers: {dict(request.headers)}")
        print(f"{'='*60}")
        response = await call_next(request)
        print(f"📤 RESPONSE: {response.status_code}")
        return response

app.add_middleware(DebugMiddleware)

# --- Health check endpoint (GET) ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Server is running!"}

@app.get("/webhook/pr")
async def webhook_health():
    return {"status": "ok", "message": "Webhook endpoint is reachable! Use POST for actual webhooks."}

@app.post("/webhook/pr", dependencies=[Depends(verify_github_signature)])
async def receive_webhook(
    request: Request, # Needed for signature verification
    background_tasks: BackgroundTasks,
    payload: dict = Body(...),
    session: AsyncSession = Depends(get_session)
):
    print(f"✅ Webhook received! Action: {payload.get('action')}")
    
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
                print(f"✅ Port {port} is free")
        except Exception as e:
            print(f"⚠️ Could not check port: {e}")

    # Auto-clear the port before starting
    if sys.platform.startswith("win"):
        kill_port(PORT)
        # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import uvicorn
    print(f"\n🚀 Starting PR Review Bot on http://0.0.0.0:{PORT}")
    print(f"   Health check: http://localhost:{PORT}/health")
    print(f"   Webhook: POST http://localhost:{PORT}/webhook/pr\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT)