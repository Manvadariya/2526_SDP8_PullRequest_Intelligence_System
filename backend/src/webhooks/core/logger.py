"""
Structured Contextual Logger for AgenticPR.
Automatically injects job_id, repo, and pr_number into log lines when available in the context vars.
"""
import logging
import sys
from contextvars import ContextVar

# Context variables for request/worker tracing
current_job_id = ContextVar("job_id", default=None)
current_repo = ContextVar("repo", default=None)
current_pr = ContextVar("pr", default=None)

class ContextFilter(logging.Filter):
    """Filter that injects context variables into the log record."""
    def filter(self, record):
        job_id = current_job_id.get()
        repo = current_repo.get()
        pr = current_pr.get()
        
        ctx = []
        if job_id: ctx.append(f"job={job_id}")
        if repo: ctx.append(f"repo={repo}")
        if pr: ctx.append(f"pr={pr}")
        
        record.trace_ctx = f"[{' '.join(ctx)}]" if ctx else ""
        return True

def get_logger(name: str) -> logging.Logger:
    """Returns a structured logger with context injection."""
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not getattr(logger, "_context_configured", False):
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler(sys.stdout)
        
        # Format: TIME [LEVEL] [LOGGER_NAME] [job=123 repo=org/repo] Message
        formatter = logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] [%(name)s] %(trace_ctx)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        handler.setFormatter(formatter)
        handler.addFilter(ContextFilter())
        
        # Remove existing handlers to prevent duplicates
        if logger.hasHandlers():
            logger.handlers.clear()
            
        logger.addHandler(handler)
        logger.propagate = False
        logger._context_configured = True
        
    return logger

def set_log_context(job_id=None, repo=None, pr=None):
    """Sets the current context variables for logging."""
    if job_id is not None: current_job_id.set(job_id)
    if repo is not None: current_repo.set(repo)
    if pr is not None: current_pr.set(pr)

def clear_log_context():
    """Clears the context variables."""
    current_job_id.set(None)
    current_repo.set(None)
    current_pr.set(None)
