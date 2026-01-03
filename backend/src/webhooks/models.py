from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_full_name: str
    pr_number: int
    commit_sha: str
    status: str = Field(default="queued")  # queued, processing, success, failure
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to agent results
    results: List["AgentResult"] = Relationship(back_populates="job")

class AgentResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    agent_name: str  # e.g., "reviewer", "linter", "static"
    output_json: str # Store full JSON response here
    
    job: Optional[Job] = Relationship(back_populates="results")