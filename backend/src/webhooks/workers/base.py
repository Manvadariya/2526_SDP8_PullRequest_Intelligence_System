"""
Base Worker — shared logic for all stage workers.

Every worker:
  1. Listens on a specific Redis queue
  2. Processes messages with retry + backoff
  3. Updates job status in the database
  4. Emits events for SSE
  5. Handles supersede checks at stage boundaries
"""

import time
import asyncio
import logging
import socket
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("agenticpr.worker")


class BaseWorker(ABC):
    """Abstract base class for all stage workers."""
    
    # Subclasses MUST set these
    QUEUE_NAME: str = ""          # e.g. "review:fetch"
    GROUP_NAME: str = ""          # e.g. "cg_fetch"
    STAGE_NAME: str = ""          # e.g. "fetch"
    MAX_RETRIES: int = 3
    TIMEOUT_SECONDS: int = 120
    BACKOFF_SECONDS: list = [5, 15, 45]
    
    # Next queue to enqueue to after success (None if terminal)
    NEXT_QUEUE: Optional[str] = None
    NEXT_STAGE_STATUS: Optional[str] = None
    
    def __init__(self, queue_manager, db_session_factory):
        self.queue = queue_manager
        self.db_session_factory = db_session_factory
        self.worker_id = f"{self.STAGE_NAME}@{socket.gethostname()}:{id(self)}"
        self._running = False
    
    async def start(self, concurrency: int = 1):
        """Start consuming messages from the queue."""
        self._running = True
        await self.queue.ensure_consumer_group(self.QUEUE_NAME, self.GROUP_NAME)
        
        logger.info(
            f"Worker started: {self.worker_id} | "
            f"queue={self.QUEUE_NAME} concurrency={concurrency}"
        )
        
        tasks = []
        for i in range(concurrency):
            consumer_name = f"{self.worker_id}:{i}"
            tasks.append(asyncio.create_task(self._consume_loop(consumer_name)))
        
        # Also start a reclaim loop for crashed worker recovery
        tasks.append(asyncio.create_task(self._reclaim_loop()))
        
        await asyncio.gather(*tasks)
    
    def stop(self):
        """Signal the worker to stop."""
        self._running = False
        logger.info(f"Worker stopping: {self.worker_id}")
    
    async def _consume_loop(self, consumer_name: str):
        """Main consume loop — dequeue and process messages."""
        while self._running:
            try:
                messages = await self.queue.dequeue(
                    self.QUEUE_NAME,
                    self.GROUP_NAME,
                    consumer_name,
                    count=1,
                    block_ms=5000,
                )
                
                for msg_id, data in messages:
                    try:
                        await self._process_with_tracking(msg_id, data)
                    except Exception as e:
                        logger.error(
                            f"Unhandled error in {self.STAGE_NAME}: {e}\n"
                            f"{traceback.format_exc()}"
                        )
                    finally:
                        await self.queue.ack(self.QUEUE_NAME, self.GROUP_NAME, msg_id)
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Consume loop error: {e}")
                await asyncio.sleep(2)
    
    async def _reclaim_loop(self):
        """Periodically reclaim messages from dead consumers."""
        while self._running:
            await asyncio.sleep(30)  # Check every 30 seconds
            try:
                reclaimed = await self.queue.reclaim_stale(
                    self.QUEUE_NAME,
                    self.GROUP_NAME,
                    f"{self.worker_id}:reclaim",
                    min_idle_ms=60000,
                )
                for msg_id, data in reclaimed:
                    logger.info(f"Reclaimed stale message {msg_id} from {self.QUEUE_NAME}")
                    await self._process_with_tracking(msg_id, data)
                    await self.queue.ack(self.QUEUE_NAME, self.GROUP_NAME, msg_id)
            except Exception as e:
                logger.debug(f"Reclaim cycle error: {e}")
    
    async def _process_with_tracking(self, msg_id: str, data: Dict[str, Any]):
        """Process a message with DB tracking, retry logic, and event emission."""
        job_id = data.get("job_id")
        if not job_id:
            logger.error(f"Message missing job_id: {data}")
            return
        
        start_time = time.time()
        retry_count = data.get("retry_count", 0)
        
        async with self.db_session_factory() as session:
            # --- Update job status to current stage ---
            from models import Job, JobStatus
            
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalars().first()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # --- Supersede check: if job is superseded, skip ---
            if job.status == JobStatus.SUPERSEDED:
                logger.info(f"Job {job_id} is superseded — skipping {self.STAGE_NAME}")
                return
            
            if job.status == JobStatus.CANCELED:
                logger.info(f"Job {job_id} is canceled — skipping {self.STAGE_NAME}")
                return
            
            # Update status to current stage
            stage_status = getattr(JobStatus, self.STAGE_NAME.upper(), JobStatus.PROCESSING)
            job.status = stage_status
            job.current_stage = self.STAGE_NAME
            job.worker_id = self.worker_id
            if not job.started_at:
                job.started_at = datetime.utcnow()
            session.add(job)
            await session.commit()
            
            # --- Emit stage_started event ---
            await self._emit_event(job_id, "stage_started", {
                "stage": self.STAGE_NAME,
                "worker_id": self.worker_id,
            })
            
            # --- Sync Status to GitHub ---
            from core.github_client import GitHubClient
            gh_client = GitHubClient()
            desc = f"Running phase: {self.STAGE_NAME.capitalize()}"
            await gh_client.set_commit_status(job.repo_full_name, job.commit_sha, "pending", desc)
        
        # --- Execute the actual work ---
        try:
            result_data = await asyncio.wait_for(
                self.process(data),
                timeout=self.TIMEOUT_SECONDS,
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result_data is None:
                result_data = {}
            
            async with self.db_session_factory() as session:
                result = await session.execute(select(Job).where(Job.id == job_id))
                job = result.scalars().first()
                
                # Re-check supersede after work completes
                if job and job.status == JobStatus.SUPERSEDED:
                    logger.info(f"Job {job_id} superseded during {self.STAGE_NAME}")
                    return
                
                if job:
                    # --- Emit stage_completed ---
                    await self._emit_event(job_id, "stage_completed", {
                        "stage": self.STAGE_NAME,
                        "duration_ms": duration_ms,
                    })
                    
                    # --- Enqueue next stage or mark complete ---
                    if self.NEXT_QUEUE:
                        next_data = {**data, **result_data}
                        next_data["retry_count"] = 0
                        await self.queue.enqueue(self.NEXT_QUEUE, next_data)
                        
                        if self.NEXT_STAGE_STATUS:
                            job.status = self.NEXT_STAGE_STATUS
                        job.current_stage = self.NEXT_QUEUE.split(":")[-1]
                    else:
                        # Terminal stage — mark completed
                        job.status = JobStatus.COMPLETED
                        job.finished_at = datetime.utcnow()
                        job.current_stage = None
                        
                        await self._emit_event(job_id, "review_completed", {
                            "duration_ms": duration_ms,
                        })
                        
                        # --- Sync Completion to GitHub ---
                        gh_client = GitHubClient()
                        await gh_client.set_commit_status(
                            job.repo_full_name, job.commit_sha, "success", 
                            "AgenticPR review complete. See PR comments."
                        )
                    
                    session.add(job)
                    await session.commit()
            
            logger.info(
                f"✓ {self.STAGE_NAME} completed for job {job_id} "
                f"in {duration_ms}ms"
            )
            
        except asyncio.TimeoutError:
            await self._handle_failure(
                job_id, data, retry_count,
                "timeout", f"{self.STAGE_NAME} timed out after {self.TIMEOUT_SECONDS}s"
            )
            
        except Exception as e:
            await self._handle_failure(
                job_id, data, retry_count,
                "error", str(e)
            )
    
    async def _handle_failure(
        self,
        job_id: int,
        data: Dict[str, Any],
        retry_count: int,
        error_code: str,
        error_detail: str,
    ):
        """Handle stage failure with retry or dead-letter."""
        logger.error(f"✗ {self.STAGE_NAME} failed for job {job_id}: {error_detail}")
        
        if retry_count < self.MAX_RETRIES:
            # Retry with exponential backoff
            backoff = self.BACKOFF_SECONDS[min(retry_count, len(self.BACKOFF_SECONDS) - 1)]
            logger.info(f"Retrying job {job_id} {self.STAGE_NAME} in {backoff}s (attempt {retry_count + 1}/{self.MAX_RETRIES})")
            
            await asyncio.sleep(backoff)
            
            retry_data = {**data, "retry_count": retry_count + 1}
            await self.queue.enqueue(self.QUEUE_NAME, retry_data)
            
            await self._emit_event(job_id, "stage_retrying", {
                "stage": self.STAGE_NAME,
                "retry_count": retry_count + 1,
                "error": error_detail,
            })
        else:
            # Max retries exhausted — mark failed & move to DLQ
            async with self.db_session_factory() as session:
                from models import Job, JobStatus
                result = await session.execute(select(Job).where(Job.id == job_id))
                job = result.scalars().first()
                if job:
                    job.status = JobStatus.FAILED
                    job.error_detail = f"[{error_code}] {error_detail}"
                    job.finished_at = datetime.utcnow()
                    job.retry_count = retry_count
                    session.add(job)
                    await session.commit()
            
            await self.queue.move_to_dlq(self.QUEUE_NAME, data, error_detail)
            
            await self._emit_event(job_id, "review_failed", {
                "stage": self.STAGE_NAME,
                "error_code": error_code,
                "error_detail": error_detail,
            })
            
            # --- Sync Failure to GitHub ---
            from core.github_client import GitHubClient
            gh_client = GitHubClient()
            repo = data.get("repo_full_name")
            sha = data.get("commit_sha") or data.get("sha")
            if repo and sha:
                await gh_client.set_commit_status(
                    repo, sha, "failure", 
                    f"Failed during {self.STAGE_NAME}: {error_code}"
                )
    
    async def _emit_event(self, job_id: int, event_type: str, data: Dict[str, Any]):
        """Emit an event for SSE consumers."""
        event = {
            "event": event_type,
            "job_id": job_id,
            "stage": self.STAGE_NAME,
            "worker_id": self.worker_id,
            "timestamp": time.time(),
            **data,
        }
        await self.queue.publish_event(f"review:{job_id}", event)
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute the stage-specific work.
        
        Args:
            data: Message data from the queue (includes job_id, repo, pr, sha, etc.)
            
        Returns:
            Optional dict of data to pass to the next stage.
            Return None if no additional data is needed.
        """
        raise NotImplementedError
