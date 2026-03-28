from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from enum import Enum


# ─── Canonical Status Enum ──────────────────────────────────────
class JobStatus(str, Enum):
    """Canonical job/review status values. Never use raw strings."""
    QUEUED = "queued"
    PROCESSING = "processing"
    FETCHING = "fetching"
    ANALYZING = "analyzing"
    REVIEWING = "reviewing"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    CANCELED = "canceled"


# ─── Core Models ────────────────────────────────────────────────
class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_full_name: str = Field(index=True)
    pr_number: int = Field(index=True)
    commit_sha: str
    status: str = Field(default=JobStatus.QUEUED)
    current_stage: Optional[str] = Field(default=None)
    error_detail: Optional[str] = Field(default=None)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    retry_count: int = Field(default=0)
    worker_id: Optional[str] = Field(default=None)
    
    # Relationship to agent results
    results: List["AgentResult"] = Relationship(back_populates="job")


class AgentResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    agent_name: str  # e.g., "reviewer", "linter", "static"
    output_json: str # Store full JSON response here
    
    job: Optional[Job] = Relationship(back_populates="results")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    github_id: Optional[int] = Field(default=None, index=True)
    username: str
    avatar_url: Optional[str] = Field(default="")
    access_token: str  # TODO: Encrypt at rest (Phase 2)
    refresh_token: Optional[str] = Field(default="")
    provider: str = Field(default="github")       # "github" | "bitbucket"
    provider_id: Optional[str] = Field(default="", index=True)
    provider_url: Optional[str] = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ActivatedRepo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    repo_full_name: str = Field(index=True)
    repo_name: Optional[str] = Field(default="")
    language: Optional[str] = Field(default="")
    description: Optional[str] = Field(default="")
    private: bool = Field(default=False)
    activated_at: datetime = Field(default_factory=datetime.utcnow)


# ─── New Models for Production Architecture ─────────────────────
class ReviewRequest(SQLModel, table=True):
    """Represents the intent to review a specific PR at a specific commit.
    Persisted before any work begins — the source of truth for 'what was requested'."""
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(default="github")  # 'github' | 'bitbucket'
    repo_full_name: str = Field(index=True)
    pr_number: int = Field(index=True)
    head_sha: str
    base_sha: Optional[str] = Field(default=None)
    delivery_id: Optional[str] = Field(default=None, index=True)
    trigger_source: str = Field(default="webhook")  # 'webhook' | 'manual' | 'rerun'
    triggered_by: Optional[int] = Field(default=None, foreign_key="user.id")
    dedupe_key: str = Field(index=True)  # provider:repo:pr:sha
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to attempts
    attempts: List["ReviewAttempt"] = Relationship(back_populates="review_request")


class ReviewAttempt(SQLModel, table=True):
    """Each execution of a review. A ReviewRequest can have multiple attempts (retries)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    review_request_id: int = Field(foreign_key="reviewrequest.id", index=True)
    attempt_number: int = Field(default=1)
    status: str = Field(default=JobStatus.QUEUED)
    current_stage: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    error_code: Optional[str] = Field(default=None)
    error_detail: Optional[str] = Field(default=None)
    worker_id: Optional[str] = Field(default=None)
    
    review_request: Optional[ReviewRequest] = Relationship(back_populates="attempts")
    stage_runs: List["StageRun"] = Relationship(back_populates="attempt")
    findings: List["Finding"] = Relationship(back_populates="attempt")


class StageRun(SQLModel, table=True):
    """Per-stage execution tracking for a review attempt."""
    id: Optional[int] = Field(default=None, primary_key=True)
    review_attempt_id: int = Field(foreign_key="reviewattempt.id", index=True)
    stage_name: str  # 'fetch' | 'analyze' | 'review' | 'publish'
    status: str = Field(default=JobStatus.QUEUED)
    worker_id: Optional[str] = Field(default=None)
    queue_wait_ms: Optional[int] = Field(default=None)
    run_duration_ms: Optional[int] = Field(default=None)
    retry_count: int = Field(default=0)
    output_ref: Optional[str] = Field(default=None)  # JSON blob or storage key
    error_detail: Optional[str] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    
    attempt: Optional[ReviewAttempt] = Relationship(back_populates="stage_runs")


class Finding(SQLModel, table=True):
    """Individual review finding (issue, suggestion, nitpick)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    review_attempt_id: int = Field(foreign_key="reviewattempt.id", index=True)
    fingerprint: str = Field(index=True)  # hash of (file, line, body) for dedup
    category: Optional[str] = Field(default=None)  # 'bug_risk' | 'security' | 'performance' | etc.
    severity: Optional[str] = Field(default=None)  # 'critical' | 'major' | 'minor' | 'nitpick'
    file_path: Optional[str] = Field(default=None)
    line_start: Optional[int] = Field(default=None)
    line_end: Optional[int] = Field(default=None)
    title: Optional[str] = Field(default=None)
    body: Optional[str] = Field(default=None)
    suggestion: Optional[str] = Field(default=None)
    source: str = Field(default="llm")  # 'llm' | 'lint' | 'security' | 'policy'
    
    attempt: Optional[ReviewAttempt] = Relationship(back_populates="findings")


class ReviewEvent(SQLModel, table=True):
    """Append-only audit log for review lifecycle events."""
    id: Optional[int] = Field(default=None, primary_key=True)
    review_attempt_id: Optional[int] = Field(default=None, foreign_key="reviewattempt.id", index=True)
    job_id: Optional[int] = Field(default=None, foreign_key="job.id", index=True)
    event_type: str  # 'queued' | 'stage_started' | 'stage_completed' | 'failed' | etc.
    event_data: Optional[str] = Field(default=None)  # JSON
    created_at: datetime = Field(default_factory=datetime.utcnow)