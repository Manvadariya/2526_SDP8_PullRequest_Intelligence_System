"""
API Router — Backend endpoints for frontend integration.
=========================================================
Adds REST endpoints for:
  1. Job management (list, detail) — consumed by ScanDetail.jsx
  2. MCP chat (send a message to the AI agent)
  3. Config info (current provider, mode, model)
  4. Manual PR review trigger

All endpoints are prefixed with /api/.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_
from sqlmodel import select
from database import get_session
from models import Job, AgentResult, User, ActivatedRepo
from auth import get_current_user
from core.security import verify_github_signature
from core.logger import get_logger, set_log_context, clear_log_context
from config import config as app_config
import json
import httpx

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["API"])


# ═══════════════════════════════════════════
# 1. JOB ENDPOINTS (used by frontend)
# ═══════════════════════════════════════════

@router.get("/jobs")
async def list_jobs(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """List review jobs for the authenticated user (most recent first)."""
    # Get the repos this user has activated
    repos_result = await session.execute(
        select(ActivatedRepo.repo_full_name).where(ActivatedRepo.user_id == current_user.id)
    )
    user_repo_names = [r for r in repos_result.scalars().all()]

    result = await session.execute(
        select(Job)
        .where(
            or_(
                Job.user_id == current_user.id,
                # Also include old jobs (user_id IS NULL) for repos this user owns
                (Job.user_id == None) & (Job.repo_full_name.in_(user_repo_names)),
            )
        )
        .order_by(Job.created_at.desc())
        .limit(50)
    )
    jobs = result.scalars().all()
    return [
        {
            "id": j.id,
            "repo_full_name": j.repo_full_name,
            "pr_number": j.pr_number,
            "commit_sha": j.commit_sha,
            "status": j.status,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_job(job_id: int, session: AsyncSession = Depends(get_session)):
    """Get a specific job with its agent results."""
    job = await session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Fetch agent results for this job
    result = await session.execute(
        select(AgentResult).where(AgentResult.job_id == job_id)
    )
    results = result.scalars().all()
    
    return {
        "job": {
            "id": job.id,
            "repo_full_name": job.repo_full_name,
            "pr_number": job.pr_number,
            "commit_sha": job.commit_sha,
            "status": job.status,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        },
        "results": [
            {
                "id": r.id,
                "agent_name": r.agent_name,
                "output_json": r.output_json,
            }
            for r in results
        ],
    }


# ═══════════════════════════════════════════
# 2. CONFIG ENDPOINT
# ═══════════════════════════════════════════

@router.get("/config")
async def get_config():
    """Get current system configuration (safe fields only)."""
    return {
        "llm_provider": app_config.LLM_PROVIDER,
        "review_mode": app_config.REVIEW_MODE,
        "model": app_config.OLLAMA_MODEL if app_config.LLM_PROVIDER == "ollama" else app_config.MODEL,
        "ollama_base_url": app_config.OLLAMA_BASE_URL if app_config.LLM_PROVIDER == "ollama" else None,
        "docker_checks_enabled": app_config.ENABLE_DOCKER_CHECKS,
    }


# ═══════════════════════════════════════════
# 3. MANUAL REVIEW TRIGGER
# ═══════════════════════════════════════════

class ManualReviewRequest(BaseModel):
    repo: str                    # e.g. "owner/repo"
    pr_number: int
    commit_sha: Optional[str] = None  # Optional — will fetch from GitHub if not provided

@router.post("/review")
async def trigger_manual_review(
    request: Request,
    req: ManualReviewRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Manually trigger a PR review (without GitHub webhook).
    Useful for testing or re-reviewing a PR.
    """
    from core.orchestrator import Orchestrator
    from core.types import PRMetadata
    from models import JobStatus

    # If no commit_sha, try to fetch it from GitHub
    commit_sha = req.commit_sha
    title = f"PR #{req.pr_number}"
    description = ""
    branch = "unknown"

    if not commit_sha:
        from core.github_client import GitHubClient
        import httpx
        gh = GitHubClient()
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/repos/{req.repo}/pulls/{req.pr_number}"
                resp = await client.get(url, headers=gh.headers)
                resp.raise_for_status()
                pr_data = resp.json()
                commit_sha = pr_data["head"]["sha"]
                title = pr_data.get("title", title)
                description = pr_data.get("body", "") or ""
                branch = pr_data["head"]["ref"]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch PR info: {e}")

    # --- Deduplicate: only skip if an ACTIVE job already exists for this commit ---
    from sqlmodel import select as sql_select

    ACTIVE_STATUSES = [
        JobStatus.QUEUED, JobStatus.PROCESSING,
        JobStatus.FETCHING, JobStatus.ANALYZING, JobStatus.REVIEWING
    ]

    existing = await session.execute(
        sql_select(Job).where(
            Job.repo_full_name == req.repo,
            Job.pr_number == req.pr_number,
            Job.commit_sha == commit_sha,
        )
    )
    existing_job = existing.scalars().first()

    if existing_job:
        if existing_job.status in ACTIVE_STATUSES:
            # Already actively processing — return the existing job
            return {
                "status": "already_in_progress",
                "job_id": existing_job.id,
                "msg": "Review already in progress for this commit",
            }
        # Job completed or failed — reset and re-trigger it
        existing_job.status = JobStatus.QUEUED
        existing_job.error_detail = None
        existing_job.finished_at = None
        existing_job.started_at = None
        existing_job.retry_count = 0
        existing_job.user_id = current_user.id
        session.add(existing_job)
        await session.commit()
        await session.refresh(existing_job)
        new_job = existing_job
    else:
        # --- Supersede: cancel older queued/processing jobs for this PR ---
        older_result = await session.execute(
            sql_select(Job).where(
                Job.repo_full_name == req.repo,
                Job.pr_number == req.pr_number,
                Job.status.in_(ACTIVE_STATUSES)
            )
        )
        for old_job in older_result.scalars().all():
            old_job.status = JobStatus.SUPERSEDED
            session.add(old_job)

        # Create new job
        new_job = Job(
            repo_full_name=req.repo,
            pr_number=req.pr_number,
            commit_sha=commit_sha,
            status=JobStatus.QUEUED,
            user_id=current_user.id,
        )
        session.add(new_job)
        await session.commit()
        await session.refresh(new_job)


    # --- Enqueue to durable queue (with BackgroundTasks fallback) ---
    try:
        queue = request.app.state.queue
        await queue.enqueue("review:fetch", {
            "job_id": new_job.id,
            "repo_full_name": req.repo,
            "pr_number": req.pr_number,
            "commit_sha": commit_sha,
            "title": title,
            "description": description,
            "branch_name": branch,
        })
    except Exception:
        # Fallback: run in-process
        orchestrator = Orchestrator()
        background_tasks.add_task(orchestrator.process_pr, metadata, new_job.id)

    return {
        "status": "Review queued",
        "job_id": new_job.id,
        "review_mode": getattr(app_config, 'REVIEW_MODE', 'full'),
        "llm_provider": getattr(app_config, 'LLM_PROVIDER', 'groq'),
    }


# ═══════════════════════════════════════════
# 4. GITHUB WEBHOOK ENDPOINT
# ═══════════════════════════════════════════

@router.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives GitHub webhook events.
    Validates the signature, extracts PR metadata, creates/updates a job,
    and enqueues it for processing.
    """
    from core.orchestrator import Orchestrator
    from core.types import PRMetadata
    from models import JobStatus
    from database import engine

    # 1. Validate Signature
    try:
        webhook_secret = app_config.GITHUB_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("GITHUB_WEBHOOK_SECRET is not set. Cannot validate webhook signature.")
            raise HTTPException(status_code=500, detail="Webhook secret not configured.")

        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256")
        if not signature:
            raise HTTPException(status_code=401, detail="X-Hub-Signature-256 header missing")

        await verify_github_signature(request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = json.loads(body)
    event = request.headers.get("X-GitHub-Event")

    # 2. Extract Event Metadata
    try:
        if event == "pull_request":
            action = payload.get("action")
            if action not in ["opened", "synchronize", "reopened"]:
                logger.info(f"Ignoring pull_request action: {action}")
                return {"status": "ignored", "reason": f"unhandled action: {action}"}
            
            pr_data = payload.get("pull_request", {})
            repo_data = payload.get("repository", {})
            
            metadata = PRMetadata(
                repo_full_name=repo_data.get("full_name"),
                pr_number=pr_data.get("number"),
                commit_sha=pr_data.get("head", {}).get("sha"),
                title=pr_data.get("title", ""),
                description=pr_data.get("body", ""),
                branch_name=pr_data.get("head", {}).get("ref")
            )
        else:
            logger.info(f"Ignoring GitHub event: {event}")
            return {"status": "ignored", "reason": f"unhandled event: {event}"}
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload structure")
    
    # --- Context Injection ---
    set_log_context(repo=metadata.repo_full_name, pr=metadata.pr_number)
    logger.info(f"Received webhook for {metadata.repo_full_name}#{metadata.pr_number} (sha: {metadata.commit_sha})")
    
    # 3. Create or Update DB Job
    try:
        async with AsyncSession(engine) as session:
            # Check for existing job
            stmt = select(Job).where(
                Job.repo_full_name == metadata.repo_full_name,
                Job.pr_number == metadata.pr_number,
                Job.commit_sha == metadata.commit_sha
            )
            result = await session.execute(stmt)
            existing_job = result.scalars().first()
            
            if existing_job:
                # Deduplication: If this exact commit is already enqueued or processing
                if existing_job.status in [JobStatus.QUEUED, JobStatus.PROCESSING, JobStatus.FETCHING, JobStatus.ANALYZING]:
                    logger.info(f"Job {existing_job.id} already active. Deduplicating.")
                    clear_log_context()
                    return {"status": "ignored", "reason": "Already tracking this commit."}
                
                # If it's done or failed, we can re-run it
                job = existing_job
                job.status = JobStatus.QUEUED
                job.current_stage = "fetch"
            else:
                # 3b. Cancel previous jobs for this PR (Supersede)
                cancel_stmt = select(Job).where(
                    Job.repo_full_name == metadata.repo_full_name,
                    Job.pr_number == metadata.pr_number,
                    Job.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING, JobStatus.FETCHING, JobStatus.ANALYZING])
                )
                cancel_res = await session.execute(cancel_stmt)
                stale_jobs = cancel_res.scalars().all()
                for sj in stale_jobs:
                    logger.warning(f"Superseding stale job {sj.id} with new commit {metadata.commit_sha}")
                    sj.status = JobStatus.SUPERSEDED
            
                # 3c. Create new job
                job = Job(
                    repo_full_name=metadata.repo_full_name,
                    pr_number=metadata.pr_number,
                    commit_sha=metadata.commit_sha,
                    status=JobStatus.QUEUED,
                    current_stage="fetch"
                )
                session.add(job)
            
            await session.commit()
            await session.refresh(job)
            job_id = job.id
            set_log_context(job_id=job_id)
            logger.info("Database job created successfully.")
    except Exception as e:
        logger.error(f"Failed to create/update job in DB: {e}")
        clear_log_context()
        raise HTTPException(status_code=500, detail="Database error during job creation")

    # 4. Enqueue to durable queue (with BackgroundTasks fallback)
    try:
        queue = request.app.state.queue
        await queue.enqueue("review:fetch", {
            "job_id": job_id,
            "repo_full_name": metadata.repo_full_name,
            "pr_number": metadata.pr_number,
            "commit_sha": metadata.commit_sha,
            "title": metadata.title,
            "description": metadata.description,
            "branch_name": metadata.branch_name,
        })
        logger.info("Successfully enqueued durable worker task")
        clear_log_context()
        
        return {"status": "accepted", "job_id": job_id, "message": "Enqueued to Redis streams"}
    except Exception as e:
        logger.error(f"Failed during DB/Queue operations: {e}")
        clear_log_context()
        raise HTTPException(status_code=500, detail="Internal processing error")


# ═══════════════════════════════════════════
# 5. MCP CHAT ENDPOINT
# ═══════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None  # Optional context (e.g., file content, diff)

@router.post("/chat")
async def mcp_chat(req: ChatRequest):
    """
    Send a message to the AI agent (powered by Ollama/OpenRouter).
    Simple stateless chat — each request is independent.
    
    Used by frontend for AI assistant features.
    """
    import sys, os
    MCP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "MCP"))
    sys.path.insert(0, MCP_PATH)
    
    from core.openai_service import OpenAIService
    
    llm = OpenAIService()
    
    messages = []
    if req.context:
        messages.append({
            "role": "system",
            "content": f"You are Apex, an AI code review assistant. Here is some context:\n\n{req.context}"
        })
    else:
        messages.append({
            "role": "system",
            "content": "You are Apex, an AI code review assistant. Help the user with code analysis, review questions, and development guidance."
        })
    
    messages.append({"role": "user", "content": req.message})
    
    try:
        response = llm.chat(messages=messages)
        return {
            "response": response.content,
            "model": llm.model,
            "provider": llm._provider,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


# ═══════════════════════════════════════════
# 6. OLLAMA STATUS ENDPOINT
# ═══════════════════════════════════════════

@router.get("/ollama/status")
async def ollama_status():
    """Check if Ollama is running and what models are available."""
    import httpx
    
    base_url = app_config.OLLAMA_BASE_URL.replace("/v1", "")
    
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Check Ollama API
            resp = await client.get(f"{base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
            
            models = [
                {
                    "name": m.get("name"),
                    "size": m.get("size"),
                    "modified_at": m.get("modified_at"),
                }
                for m in data.get("models", [])
            ]
            
            return {
                "status": "running",
                "base_url": base_url,
                "models": models,
                "active_model": app_config.OLLAMA_MODEL,
            }
    except Exception as e:
        return {
            "status": "offline",
            "error": str(e),
            "base_url": base_url,
        }


# ═══════════════════════════════════════════
# 7. REPO REVIEW STATS (aggregated from jobs)
# ═══════════════════════════════════════════

@router.get("/repos/{owner}/{repo}/stats")
async def get_repo_stats(
    owner: str,
    repo: str,
    session: AsyncSession = Depends(get_session),
):
    """Aggregate review stats for a specific repo from all jobs + agent results."""
    repo_full_name = f"{owner}/{repo}"

    # Fetch all jobs for this repo
    result = await session.execute(
        select(Job)
        .where(Job.repo_full_name == repo_full_name)
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()

    total_reviews = len(jobs)
    succeeded = sum(1 for j in jobs if j.status == "success")
    failed = sum(1 for j in jobs if j.status == "failure")
    latest_job = jobs[0] if jobs else None

    # Collect all issues from agent results
    all_issues = []
    issue_categories = {
        "bug_risk": 0, "anti_pattern": 0, "security": 0,
        "performance": 0, "style": 0, "documentation": 0, "coverage": 0,
    }
    languages_seen = set()

    for job in jobs:
        res = await session.execute(
            select(AgentResult).where(AgentResult.job_id == job.id)
        )
        results = res.scalars().all()
        for r in results:
            try:
                data = json.loads(r.output_json) if isinstance(r.output_json, str) else r.output_json
            except (json.JSONDecodeError, TypeError):
                continue

            # Extract inline comments as issues
            comments = []
            if isinstance(data, dict):
                ic = data.get("inline_comments", [])
                cm = data.get("comments", [])
                comments = ic if isinstance(ic, list) else (cm if isinstance(cm, list) else [])
                # If the agent stored a summary with issues
                issues = data.get("issues")
                if isinstance(issues, list):
                    comments.extend(issues)
                # Track languages from file extensions
                for c in comments:
                    if not isinstance(c, dict):
                        continue
                    path = c.get("path", "") or c.get("file", "")
                    if path:
                        ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
                        lang_map = {
                            "js": "JavaScript", "jsx": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript",
                            "py": "Python", "java": "Java", "c": "C", "cpp": "C++", "h": "C",
                            "go": "Go", "rs": "Rust", "rb": "Ruby", "php": "PHP", "sh": "Shell",
                        }
                        if ext in lang_map:
                            languages_seen.add(lang_map[ext])

            for c in comments:
                if not isinstance(c, dict):
                    continue
                severity = (c.get("severity", "") or "").lower()
                body = (c.get("body", "") or c.get("message", "") or "").lower()

                # Categorize issues
                if "security" in body or "vulnerab" in body or "secret" in body or "xss" in body or "inject" in body:
                    issue_categories["security"] += 1
                    cat = "Security"
                elif "performance" in body or "slow" in body or "optimize" in body or "memory" in body:
                    issue_categories["performance"] += 1
                    cat = "Performance"
                elif "style" in body or "format" in body or "naming" in body or "indent" in body:
                    issue_categories["style"] += 1
                    cat = "Style"
                elif "doc" in body or "comment" in body or "readme" in body:
                    issue_categories["documentation"] += 1
                    cat = "Documentation"
                elif "bug" in body or "error" in body or "undefined" in body or "null" in body or "exception" in body:
                    issue_categories["bug_risk"] += 1
                    cat = "Bug risk"
                else:
                    issue_categories["anti_pattern"] += 1
                    cat = "Anti-pattern"

                all_issues.append({
                    "id": f"PR-{job.pr_number}-{len(all_issues)+1}",
                    "title": (c.get("body", "") or c.get("message", ""))[:120],
                    "category": cat,
                    "severity": "Major" if severity in ("high", "critical", "major") else "Minor",
                    "file": c.get("path", "") or c.get("file", ""),
                    "line": c.get("line", c.get("start_line", 0)),
                    "pr_number": job.pr_number,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                })

    active_issues = len(all_issues)

    return {
        "repo_full_name": repo_full_name,
        "total_reviews": total_reviews,
        "succeeded": succeeded,
        "failed": failed,
        "active_issues": active_issues,
        "issues_prevented": succeeded,
        "categories": issue_categories,
        "languages": sorted(languages_seen),
        "issues": all_issues[:50],  # Return latest 50 for the issues page
        "latest_job": {
            "id": latest_job.id,
            "pr_number": latest_job.pr_number,
            "commit_sha": latest_job.commit_sha,
            "status": latest_job.status,
            "created_at": latest_job.created_at.isoformat() if latest_job.created_at else None,
        } if latest_job else None,
    }


# ═══════════════════════════════════════════
# 7. ACTIVATED REPOS (user-selected for review)
# ═══════════════════════════════════════════

class ActivateRepoRequest(BaseModel):
    repo_full_name: str   # e.g. "owner/repo"
    repo_name: str
    language: str = ""
    description: str = ""
    private: bool = False


@router.get("/activated-repos")
async def list_activated_repos(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List repositories the user has activated for review."""
    result = await session.execute(
        select(ActivatedRepo)
        .where(ActivatedRepo.user_id == user.id)
        .order_by(ActivatedRepo.activated_at.desc())
    )
    repos = result.scalars().all()
    return [
        {
            "id": r.id,
            "repo_full_name": r.repo_full_name,
            "repo_name": r.repo_name,
            "language": r.language,
            "description": r.description,
            "private": r.private,
            "activated_at": r.activated_at.isoformat() if r.activated_at else None,
        }
        for r in repos
    ]


@router.post("/activated-repos")
async def activate_repo(
    req: ActivateRepoRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Activate a repository for review."""
    # Check if already activated
    result = await session.execute(
        select(ActivatedRepo).where(
            ActivatedRepo.user_id == user.id,
            ActivatedRepo.repo_full_name == req.repo_full_name,
        )
    )
    existing = result.scalars().first()
    if existing:
        return {"status": "already_activated", "id": existing.id}

    repo = ActivatedRepo(
        user_id=user.id,
        repo_full_name=req.repo_full_name,
        repo_name=req.repo_name,
        language=req.language,
        description=req.description,
        private=req.private,
    )
    session.add(repo)
    await session.commit()
    await session.refresh(repo)
    return {"status": "activated", "id": repo.id}


@router.delete("/activated-repos/{repo_full_name:path}")
async def deactivate_repo(
    repo_full_name: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Deactivate (remove) a repository from review tracking."""
    result = await session.execute(
        select(ActivatedRepo).where(
            ActivatedRepo.user_id == user.id,
            ActivatedRepo.repo_full_name == repo_full_name,
        )
    )
    repo = result.scalars().first()
    if not repo:
        raise HTTPException(status_code=404, detail="Activated repo not found")
    await session.delete(repo)
    await session.commit()
    return {"status": "deactivated"}


# ═══════════════════════════════════════════
# 7. GITHUB PROXY (user-authenticated)
# ═══════════════════════════════════════════

GITHUB_API = "https://api.github.com"
BITBUCKET_API = "https://api.bitbucket.org/2.0"

def _gh_headers(user: User) -> dict:
    """Build GitHub API headers using the user's stored access token."""
    return {
        "Authorization": f"Bearer {user.access_token}",
        "Accept": "application/vnd.github.v3+json",
    }

def _bb_headers(user: User) -> dict:
    """Build Bitbucket API headers using the user's stored access token."""
    return {
        "Authorization": f"Bearer {user.access_token}",
        "Accept": "application/json",
    }

def _handle_github_network_error(exc: Exception) -> None:
    """Convert httpx network errors into a clean 503 HTTPException."""
    raise HTTPException(
        status_code=503,
        detail=f"Could not reach GitHub API: {type(exc).__name__} – {exc}",
    ) from exc

def _handle_bitbucket_network_error(exc: Exception) -> None:
    """Convert httpx network errors into a clean 503 for Bitbucket."""
    raise HTTPException(
        status_code=503,
        detail=f"Could not reach Bitbucket API: {type(exc).__name__} – {exc}",
    ) from exc

def _user_provider(user: User) -> str:
    return getattr(user, "provider", "github") or "github"


@router.get("/user/repos")
async def list_user_repos(user: User = Depends(get_current_user)):
    """Fetch the authenticated user's repositories (GitHub or Bitbucket)."""
    provider = _user_provider(user)
    
    if provider == "bitbucket":
        return await _list_bitbucket_repos(user)
    
    # Default: GitHub
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API}/user/repos",
                headers=_gh_headers(user),
                params={"sort": "updated", "per_page": 50, "type": "all"},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="GitHub API error")
            repos = resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        _handle_github_network_error(exc)
    
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "full_name": r["full_name"],
            "owner": r["owner"]["login"],
            "description": r.get("description") or "",
            "language": r.get("language") or "Unknown",
            "stars": r.get("stargazers_count", 0),
            "open_issues": r.get("open_issues_count", 0),
            "private": r.get("private", False),
            "updated_at": r.get("updated_at"),
            "html_url": r.get("html_url"),
            "provider": "github",
        }
        for r in repos
    ]


async def _list_bitbucket_repos(user: User):
    """Fetch all Bitbucket repositories the user has access to."""
    all_repos = []
    # Bitbucket paginated: first get user's workspaces, then repos per workspace
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Get workspaces the user belongs to
            ws_resp = await client.get(
                f"{BITBUCKET_API}/workspaces",
                headers=_bb_headers(user),
                params={"pagelen": 25},
            )
            if ws_resp.status_code != 200:
                raise HTTPException(status_code=ws_resp.status_code,
                                    detail=f"Bitbucket workspaces API error: {ws_resp.text}")
            workspaces = ws_resp.json().get("values", [])
            
            for ws in workspaces:
                slug = ws.get("slug", "")
                if not slug:
                    continue
                
                repos_resp = await client.get(
                    f"{BITBUCKET_API}/repositories/{slug}",
                    headers=_bb_headers(user),
                    params={"pagelen": 50, "sort": "-updated_on", "role": "member"},
                )
                if repos_resp.status_code != 200:
                    continue
                
                for r in repos_resp.json().get("values", []):
                    full_name = r.get("full_name", "")  # "workspace/repo-slug"
                    owner = full_name.split("/")[0] if "/" in full_name else slug
                    lang = r.get("language") or "Unknown"
                    all_repos.append({
                        "id": r.get("uuid", ""),
                        "name": r.get("name", ""),
                        "full_name": full_name,
                        "owner": owner,
                        "description": r.get("description") or "",
                        "language": lang if lang else "Unknown",
                        "stars": 0,  # Bitbucket doesn't have stars
                        "open_issues": 0,
                        "private": r.get("is_private", False),
                        "updated_at": r.get("updated_on"),
                        "html_url": r.get("links", {}).get("html", {}).get("href", ""),
                        "provider": "bitbucket",
                    })
    except HTTPException:
        raise
    except Exception as exc:
        _handle_bitbucket_network_error(exc)
    
    return all_repos


@router.get("/user/repos/{owner}/{repo}/pulls")
async def list_repo_pulls(
    owner: str,
    repo: str,
    state: str = "open",
    user: User = Depends(get_current_user),
):
    """Fetch pull requests for a specific repo (GitHub or Bitbucket)."""
    provider = _user_provider(user)
    
    if provider == "bitbucket":
        return await _list_bitbucket_pulls(user, owner, repo, state)
    
    # Default: GitHub
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls",
                headers=_gh_headers(user),
                params={"state": state, "per_page": 30, "sort": "updated"},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="GitHub API error")
            pulls = resp.json()
    except HTTPException:
        raise
    except Exception as exc:
        _handle_github_network_error(exc)
    
    return [
        {
            "number": p["number"],
            "title": p["title"],
            "state": p["state"],
            "author": p["user"]["login"],
            "author_avatar": p["user"]["avatar_url"],
            "created_at": p["created_at"],
            "updated_at": p["updated_at"],
            "head_sha": p["head"]["sha"],
            "head_branch": p["head"]["ref"],
            "base_branch": p["base"]["ref"],
            "additions": p.get("additions", 0),
            "deletions": p.get("deletions", 0),
            "html_url": p["html_url"],
            "provider": "github",
        }
        for p in pulls
    ]


async def _list_bitbucket_pulls(user: User, workspace: str, repo_slug: str, state: str):
    """Fetch pull requests from Bitbucket."""
    # Map state: GitHub uses "open"/"closed"/"all", Bitbucket uses "OPEN"/"MERGED"/"DECLINED"/"SUPERSEDED"
    bb_state_map = {
        "open": "OPEN",
        "closed": "MERGED",  # Closest equivalent
        "all": "",
    }
    bb_state = bb_state_map.get(state, "OPEN")
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            params = {"pagelen": 30}
            if bb_state:
                params["state"] = bb_state
            
            resp = await client.get(
                f"{BITBUCKET_API}/repositories/{workspace}/{repo_slug}/pullrequests",
                headers=_bb_headers(user),
                params=params,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code,
                                    detail=f"Bitbucket PRs API error: {resp.text}")
            data = resp.json()
            pulls = data.get("values", [])
    except HTTPException:
        raise
    except Exception as exc:
        _handle_bitbucket_network_error(exc)
    
    result = []
    for p in pulls:
        author = p.get("author", {})
        source = p.get("source", {})
        dest = p.get("destination", {})
        source_commit = source.get("commit", {}) or {}
        
        result.append({
            "number": p.get("id"),
            "title": p.get("title", ""),
            "state": p.get("state", "").lower(),
            "author": author.get("nickname", "") or author.get("display_name", ""),
            "author_avatar": author.get("links", {}).get("avatar", {}).get("href", ""),
            "created_at": p.get("created_on", ""),
            "updated_at": p.get("updated_on", ""),
            "head_sha": source_commit.get("hash", ""),
            "head_branch": source.get("branch", {}).get("name", ""),
            "base_branch": dest.get("branch", {}).get("name", ""),
            "additions": 0,
            "deletions": 0,
            "html_url": p.get("links", {}).get("html", {}).get("href", ""),
            "provider": "bitbucket",
        })
    
    return result


@router.get("/user/repos/{owner}/{repo}/pulls/{number}")
async def get_pull_detail(
    owner: str,
    repo: str,
    number: int,
    user: User = Depends(get_current_user),
):
    """Fetch detailed info for a specific pull request (GitHub or Bitbucket)."""
    provider = _user_provider(user)
    
    if provider == "bitbucket":
        return await _get_bitbucket_pull_detail(user, owner, repo, number)
    
    # Default: GitHub
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # PR detail
            resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}",
                headers=_gh_headers(user),
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code, detail="GitHub API error")

            pr = resp.json()

            # Also fetch files changed
            files_resp = await client.get(
                f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}/files",
                headers=_gh_headers(user),
                params={"per_page": 100},
            )
            files = files_resp.json() if files_resp.status_code == 200 else []
    except HTTPException:
        raise
    except Exception as exc:
        _handle_github_network_error(exc)
    
    return {
        "number": pr["number"],
        "title": pr["title"],
        "body": pr.get("body") or "",
        "state": pr["state"],
        "author": pr["user"]["login"],
        "author_avatar": pr["user"]["avatar_url"],
        "created_at": pr["created_at"],
        "updated_at": pr["updated_at"],
        "merged": pr.get("merged", False),
        "head_sha": pr["head"]["sha"],
        "head_branch": pr["head"]["ref"],
        "base_branch": pr["base"]["ref"],
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "changed_files": pr.get("changed_files", 0),
        "html_url": pr["html_url"],
        "provider": "github",
        "files": [
            {
                "filename": f["filename"],
                "status": f["status"],
                "additions": f["additions"],
                "deletions": f["deletions"],
                "patch": f.get("patch", ""),
            }
            for f in files
        ],
    }


async def _get_bitbucket_pull_detail(user: User, workspace: str, repo_slug: str, pr_id: int):
    """Fetch detailed Bitbucket PR info including diff."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # PR detail
            resp = await client.get(
                f"{BITBUCKET_API}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}",
                headers=_bb_headers(user),
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=resp.status_code,
                                    detail=f"Bitbucket PR detail error: {resp.text}")
            pr = resp.json()
            
            # Fetch diffstat (files changed)
            diff_resp = await client.get(
                f"{BITBUCKET_API}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/diffstat",
                headers=_bb_headers(user),
                params={"pagelen": 100},
            )
            diff_files = diff_resp.json().get("values", []) if diff_resp.status_code == 200 else []
    except HTTPException:
        raise
    except Exception as exc:
        _handle_bitbucket_network_error(exc)
    
    author = pr.get("author", {})
    source = pr.get("source", {})
    dest = pr.get("destination", {})
    source_commit = source.get("commit", {}) or {}
    
    total_add = sum(f.get("lines_added", 0) for f in diff_files)
    total_del = sum(f.get("lines_removed", 0) for f in diff_files)
    
    merged = pr.get("state", "").upper() == "MERGED"
    
    files = []
    for f in diff_files:
        new_path = f.get("new", {})
        old_path = f.get("old", {})
        filename = ""
        if isinstance(new_path, dict):
            filename = new_path.get("path", "")
        if not filename and isinstance(old_path, dict):
            filename = old_path.get("path", "")
        
        status = f.get("status", "modified")
        files.append({
            "filename": filename,
            "status": status,
            "additions": f.get("lines_added", 0),
            "deletions": f.get("lines_removed", 0),
            "patch": "",  # Bitbucket diffstat doesn't include patches inline
        })
    
    return {
        "number": pr.get("id"),
        "title": pr.get("title", ""),
        "body": pr.get("description") or "",
        "state": pr.get("state", "").lower(),
        "author": author.get("nickname", "") or author.get("display_name", ""),
        "author_avatar": author.get("links", {}).get("avatar", {}).get("href", ""),
        "created_at": pr.get("created_on", ""),
        "updated_at": pr.get("updated_on", ""),
        "merged": merged,
        "head_sha": source_commit.get("hash", ""),
        "head_branch": source.get("branch", {}).get("name", ""),
        "base_branch": dest.get("branch", {}).get("name", ""),
        "additions": total_add,
        "deletions": total_del,
        "changed_files": len(diff_files),
        "html_url": pr.get("links", {}).get("html", {}).get("href", ""),
        "provider": "bitbucket",
        "files": files,
    }


# ═══════════════════════════════════════════
# 8. PR COMMENTS (GitHub issue + review comments)
# ═══════════════════════════════════════════

@router.get("/user/repos/{owner}/{repo}/pulls/{number}/comments")
async def get_pr_comments(
    owner: str,
    repo: str,
    number: int,
    user: User = Depends(get_current_user),
):
    """Fetch all comments for a PR (GitHub or Bitbucket)."""
    provider = _user_provider(user)
    
    if provider == "bitbucket":
        return await _get_bitbucket_pr_comments(user, owner, repo, number)
    
    # Default: GitHub
    async with httpx.AsyncClient(timeout=15) as client:
        # Issue comments (general PR conversation)
        issue_resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/issues/{number}/comments",
            headers=_gh_headers(user),
            params={"per_page": 50},
        )
        issue_comments = issue_resp.json() if issue_resp.status_code == 200 else []

        # Review comments (inline code comments)
        review_resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{number}/comments",
            headers=_gh_headers(user),
            params={"per_page": 50},
        )
        review_comments = review_resp.json() if review_resp.status_code == 200 else []

    formatted = []

    for c in (issue_comments if isinstance(issue_comments, list) else []):
        formatted.append({
            "id": c["id"],
            "type": "comment",
            "body": c.get("body", ""),
            "author": c["user"]["login"],
            "author_avatar": c["user"]["avatar_url"],
            "created_at": c["created_at"],
            "html_url": c.get("html_url", ""),
        })

    for c in (review_comments if isinstance(review_comments, list) else []):
        formatted.append({
            "id": c["id"],
            "type": "review",
            "body": c.get("body", ""),
            "author": c["user"]["login"],
            "author_avatar": c["user"]["avatar_url"],
            "created_at": c["created_at"],
            "path": c.get("path", ""),
            "line": c.get("line") or c.get("original_line"),
            "diff_hunk": c.get("diff_hunk", ""),
            "html_url": c.get("html_url", ""),
        })

    formatted.sort(key=lambda x: x["created_at"])
    return formatted


async def _get_bitbucket_pr_comments(user: User, workspace: str, repo_slug: str, pr_id: int):
    """Fetch comments for a Bitbucket pull request."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # General PR comments (activity includes comments, approvals, etc.)
            resp = await client.get(
                f"{BITBUCKET_API}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/comments",
                headers=_bb_headers(user),
                params={"pagelen": 50},
            )
            comments = resp.json().get("values", []) if resp.status_code == 200 else []
    except Exception:
        comments = []
    
    formatted = []
    for c in comments:
        content = c.get("content", {})
        body = content.get("raw", "") or content.get("markup", "")
        author = c.get("user", {})
        inline = c.get("inline", {})
        
        comment_type = "review" if inline else "comment"
        
        formatted.append({
            "id": c.get("id"),
            "type": comment_type,
            "body": body,
            "author": author.get("nickname", "") or author.get("display_name", ""),
            "author_avatar": author.get("links", {}).get("avatar", {}).get("href", ""),
            "created_at": c.get("created_on", ""),
            "path": inline.get("path", "") if inline else "",
            "line": inline.get("to") if inline else None,
            "diff_hunk": "",
            "html_url": c.get("links", {}).get("html", {}).get("href", ""),
        })
    
    formatted.sort(key=lambda x: x.get("created_at", ""))
    return formatted


# ═══════════════════════════════════════════
# 9. PR REVIEW DATA (from our Jobs + AgentResults)
# ═══════════════════════════════════════════

@router.get("/repos/{owner}/{repo}/pr/{number}/review-data")
async def get_pr_review_data(
    owner: str,
    repo: str,
    number: int,
    session: AsyncSession = Depends(get_session),
):
    """Get review analysis data for a specific PR from Jobs + AgentResults."""
    repo_full_name = f"{owner}/{repo}"

    # Find jobs for this repo + PR number
    result = await session.execute(
        select(Job)
        .where(Job.repo_full_name == repo_full_name, Job.pr_number == number)
        .order_by(Job.created_at.desc())
    )
    jobs = result.scalars().all()

    if not jobs:
        return {
            "has_review": False,
            "report_card": {},
            "secrets_count": 0,
            "feedback": [],
            "dimensions": {},
            "overall_grade": "-",
            "focus_area": "None",
            "summary": None,
            "total_reviews": 0,
        }

    latest_job = jobs[0]

    # Get agent results from the latest job
    res = await session.execute(
        select(AgentResult).where(AgentResult.job_id == latest_job.id)
    )
    agent_results = res.scalars().all()

    # Parse all comments/issues from agent results
    all_comments = []
    lang_issues = {}
    category_counts = {
        "security": 0, "bug_risk": 0, "anti_pattern": 0,
        "performance": 0, "style": 0, "documentation": 0,
    }
    secrets_count = 0

    for r in agent_results:
        try:
            data = json.loads(r.output_json) if isinstance(r.output_json, str) else r.output_json
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(data, dict):
            continue
            
        review_summaries = {
            "file_summaries": data.get("file_summaries", {}),
            "lgtm_notes": data.get("lgtm_notes", {}),
            "markdown_summary": data.get("markdown_summary", "")
        }

        # The new schema stores comments as a dict of lists keyed by filepath
        inline_comments_dict = data.get("inline_comments", {})
        nitpicks_dict = data.get("nitpicks", {})
        
        # Helper to process a flat list or newly-structured dict-of-lists
        def _extract_comments(source_data):
            if isinstance(source_data, list):
                return source_data
            elif isinstance(source_data, dict):
                flat_list = []
                for _, file_items in source_data.items():
                    if isinstance(file_items, list):
                        flat_list.extend(file_items)
                return flat_list
            return []

        all_source_comments = _extract_comments(inline_comments_dict) + _extract_comments(nitpicks_dict)
        
        # Backwards compatibility check
        if not all_source_comments:
            legacy_comments = data.get("comments", []) or data.get("issues", [])
            if isinstance(legacy_comments, list):
                all_source_comments = legacy_comments

        # Defensive check to ensure we definitively have a list before iterating
        if not isinstance(all_source_comments, list):
            all_source_comments = []

        for c in all_source_comments:
            body = (c.get("body", "") or c.get("message", "") or "").strip()
            path = c.get("path", "") or c.get("file", "")
            severity = (c.get("severity", "") or "").lower()
            finding_type = (c.get("type", "") or "").lower()

            # Determine language from file extension
            ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
            lang_map = {
                "js": "JavaScript", "jsx": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript",
                "py": "Python", "java": "Java", "c": "C & C++", "cpp": "C & C++", "h": "C & C++",
                "go": "Go", "rs": "Rust", "rb": "Ruby", "php": "PHP", "sh": "Shell",
                "yml": "YAML", "yaml": "YAML",
            }
            lang = lang_map.get(ext, "Other")
            if "dockerfile" in path.lower():
                lang = "Docker"

            lang_issues[lang] = lang_issues.get(lang, 0) + 1

            # Categorize
            body_lower = body.lower()
            if finding_type == "nitpick":
                category_counts["style"] += 1
                cat = "Nitpick / Style"
            elif any(kw in body_lower for kw in ("secret", "api key", "password", "credential", "vulnerab", "xss")):
                secrets_count += 1 if "secret" in body_lower or "api key" in body_lower else 0
                category_counts["security"] += 1
                cat = "Security"
            elif any(kw in body_lower for kw in ("performance", "slow", "optimize", "memory")):
                category_counts["performance"] += 1
                cat = "Performance"
            elif any(kw in body_lower for kw in ("style", "format", "naming", "indent")):
                category_counts["style"] += 1
                cat = "Style"
            elif any(kw in body_lower for kw in ("doc", "comment", "readme")):
                category_counts["documentation"] += 1
                cat = "Documentation"
            elif any(kw in body_lower for kw in ("bug", "error", "undefined", "null", "exception")):
                category_counts["bug_risk"] += 1
                cat = "Bug risk"
            else:
                category_counts["anti_pattern"] += 1
                cat = "Code issue"

            all_comments.append({
                "title": body[:120] if body else "Code issue",
                "description": body,
                "category": cat,
                "severity": severity,
                "file": path,
                "line": c.get("line", c.get("start_line", 0)),
                "language": lang,
                "original_code": c.get("original_code", ""),
                "suggestion": c.get("suggestion", "")
            })

    # Compute dimension grades
    def grade(count):
        if count == 0:
            return "A"
        elif count <= 2:
            return "B"
        elif count <= 5:
            return "C"
        return "D"

    dimensions = {
        "security": {"grade": grade(category_counts["security"]), "count": category_counts["security"]},
        "reliability": {"grade": grade(category_counts["bug_risk"]), "count": category_counts["bug_risk"]},
        "complexity": {"grade": grade(category_counts["anti_pattern"]), "count": category_counts["anti_pattern"]},
        "hygiene": {"grade": grade(category_counts["style"] + category_counts["documentation"]),
                     "count": category_counts["style"] + category_counts["documentation"]},
        "coverage": {"grade": "-", "count": 0},
    }

    # Overall grade: average of scored dimensions
    grade_values = {"A": 4, "B": 3, "C": 2, "D": 1}
    scored = [grade_values[d["grade"]] for d in dimensions.values() if d["grade"] != "-"]
    avg = sum(scored) / len(scored) if scored else 0
    if avg >= 3.5:
        overall = "A"
    elif avg >= 2.5:
        overall = "B"
    elif avg >= 1.5:
        overall = "C"
    else:
        overall = "D"

    # Focus area: the worst-scoring dimension
    non_na = [(k, v) for k, v in dimensions.items() if v["grade"] != "-"]
    worst = min(non_na, key=lambda x: grade_values.get(x[1]["grade"], 0), default=("", {"grade": "-"}))
    focus_area = worst[0].capitalize() if worst[0] else "None"

    created_at = latest_job.created_at.isoformat() if latest_job.created_at else None

    return {
        "has_review": True,
        "report_card": lang_issues,
        "secrets_count": secrets_count,
        "feedback": all_comments,  # Return all findings, not just first 10
        "review_summaries": review_summaries if 'review_summaries' in locals() else {},
        "dimensions": dimensions,
        "overall_grade": overall,
        "focus_area": focus_area,
        "summary": {
            "created_at": created_at,
            "commit_sha": latest_job.commit_sha,
            "status": latest_job.status,
            "job_id": latest_job.id,
            "total_issues": len(all_comments),
        },
        "total_reviews": len(jobs),
    }

