from typing import List, Optional, Dict, Literal
from pydantic import BaseModel

class PRMetadata(BaseModel):
    repo_full_name: str
    pr_number: int
    commit_sha: str
    title: str
    description: str
    branch_name: str

class FileChange(BaseModel):
    path: str
    change_type: Literal["added", "modified", "deleted", "renamed"]
    patch: Optional[str] = None

class LintIssue(BaseModel):
    file: str
    line: int
    rule: str
    message: str
    severity: Literal["error", "warning", "info"]

class StaticIssue(BaseModel):
    file: str
    line: int
    issue: str
    suggestion: str
    severity: Literal["critical", "high", "medium", "low"]

class AgentResult(BaseModel):
    summary: Optional[Dict] = None
    lint: Optional[Dict] = None
    static: Optional[Dict] = None
    status: Literal["PASS", "WARN", "FAIL"]