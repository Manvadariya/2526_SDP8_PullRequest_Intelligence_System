"""
Review Worker — Stage 3: LLM-powered code review.

Responsibilities:
  - Build review prompt from diff + context
  - Call LLM with provider fallback chain
  - Parse structured findings from LLM response
  - Save findings to database
  - Handle large PRs via chunked review
"""

import json
import hashlib
import logging
from typing import Dict, Any, Optional, List

from workers.base import BaseWorker

logger = logging.getLogger("agenticpr.worker.review")


class ReviewWorker(BaseWorker):
    QUEUE_NAME = "review:llm"
    GROUP_NAME = "cg_review"
    STAGE_NAME = "reviewing"
    MAX_RETRIES = 2
    TIMEOUT_SECONDS = 600  # 10 min — LLM calls can be slow
    BACKOFF_SECONDS = [30, 90]
    NEXT_QUEUE = "review:publish"
    NEXT_STAGE_STATUS = "publishing"
    
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute LLM-powered code review."""
        job_id = data["job_id"]
        repo_full_name = data["repo_full_name"]
        pr_number = data["pr_number"]
        diff_text = data.get("diff_text", "")
        title = data.get("title", "")
        description = data.get("description", "")
        context_pack = data.get("context_pack", "")
        static_findings = data.get("static_findings", [])
        
        # ═══ PROMINENT LOGGING: Review started ═══
        logger.info("")
        logger.info("══════════════════════════════════════════════════")
        logger.info(f"🔍 REVIEWING STARTED for PR #{pr_number}")
        logger.info(f"   Repo:   {repo_full_name}")
        logger.info(f"   Job ID: {job_id}")
        logger.info(f"   Title:  {title}")
        logger.info(f"   Diff:   {len(diff_text)} chars")
        logger.info("══════════════════════════════════════════════════")
        logger.info("")
        
        if not diff_text:
            logger.info(f"[review] Job {job_id}: No diff to review")
            return {"review_result": None, "findings": []}
        
        logger.info(f"[review] Job {job_id}: Starting LLM review for {repo_full_name}#{pr_number}")
        
        # --- 0. Rate Limiting (Token Bucket) ---
        from core.rate_limiter import TokenBucketRateLimiter
        rate_limiter = TokenBucketRateLimiter(self.queue)
        
        # We need 1 tokens for this request. Wait up to 5 minutes to acquire it.
        acquired = await rate_limiter.acquire(tokens=1, timeout=300)
        if not acquired:
            logger.warning(f"[review] Job {job_id}: Token Bucket limit reached, timed out waiting for capacity.")
            raise TimeoutError("LLM Token Bucket capacity exhausted. Rate limit backoff failed.")
        
        # --- 1. Use the existing reviewer agent ---
        try:
            from agents.reviewer import ReviewerAgent
            from core.llm import LLMService
            from core.security import SecretScanner
            
            llm = LLMService()
            scanner = SecretScanner()
            
            # Sanitize diff before sending to LLM
            safe_diff = scanner.redact(diff_text)
            safe_context = scanner.redact(context_pack) if context_pack else ""
            
            # Use the existing reviewer agent for the actual review
            reviewer = ReviewerAgent(llm_service=llm)
            
            review_result = reviewer.review(
                diff=safe_diff,
                title=title,
                description=description,
                context=safe_context,
                repo=repo_full_name,
                pr_number=pr_number,
            )
            
            # --- 2. Parse findings from review result ---
            findings = self._extract_findings(review_result, job_id)
            
            # Merge static analysis findings
            for sf in static_findings:
                findings.append({
                    "fingerprint": self._fingerprint(sf.get("file", ""), sf.get("line", 0), sf.get("message", "")),
                    "category": sf.get("category", "lint"),
                    "severity": sf.get("severity", "minor"),
                    "file_path": sf.get("file", ""),
                    "line_start": sf.get("line", 0),
                    "title": sf.get("rule", "Lint issue"),
                    "body": sf.get("message", ""),
                    "source": "lint",
                })
            
            # --- 3. Save findings to database ---
            await self._save_findings(job_id, findings)
            
            logger.info(f"[review] Job {job_id}: Review complete — {len(findings)} findings")
            
            return {
                "review_result": review_result,
                "findings_count": len(findings),
            }
            
        except Exception as e:
            logger.error(f"[review] Job {job_id}: Review failed: {e}")
            raise
    
    def _extract_findings(self, review_result: Any, job_id: int) -> List[Dict]:
        """Extract structured findings from reviewer agent output."""
        findings = []
        
        if not review_result:
            return findings
        
        # Handle different result formats from the existing reviewer
        if isinstance(review_result, dict):
            # If the reviewer returns structured data
            inline_comments = review_result.get("inline_comments", [])
            for comment in inline_comments:
                findings.append({
                    "fingerprint": self._fingerprint(
                        comment.get("path", ""), 
                        comment.get("line", 0),
                        comment.get("body", "")
                    ),
                    "category": comment.get("category", "review"),
                    "severity": comment.get("severity", "minor"),
                    "file_path": comment.get("path", ""),
                    "line_start": comment.get("line", 0),
                    "title": comment.get("title", ""),
                    "body": comment.get("body", ""),
                    "suggestion": comment.get("suggestion", ""),
                    "source": "llm",
                })
        
        return findings
    
    def _fingerprint(self, file_path: str, line: int, body: str) -> str:
        """Create a dedup fingerprint for a finding."""
        raw = f"{file_path}:{line}:{body[:100]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]
    
    async def _save_findings(self, job_id: int, findings: List[Dict]):
        """Save findings to the database."""
        if not findings:
            return
        
        try:
            async with self.db_session_factory() as session:
                from models import Finding
                
                for f in findings:
                    finding = Finding(
                        review_attempt_id=job_id,  # Using job_id for now
                        fingerprint=f["fingerprint"],
                        category=f.get("category"),
                        severity=f.get("severity"),
                        file_path=f.get("file_path"),
                        line_start=f.get("line_start"),
                        title=f.get("title"),
                        body=f.get("body"),
                        suggestion=f.get("suggestion"),
                        source=f.get("source", "llm"),
                    )
                    session.add(finding)
                
                await session.commit()
                logger.info(f"[review] Saved {len(findings)} findings for job {job_id}")
                
        except Exception as e:
            logger.error(f"[review] Failed to save findings: {e}")
