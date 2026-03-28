"""
Worker Runner — starts all workers in a single process.

Usage:
  python run_workers.py                    # All workers
  python run_workers.py --workers fetch    # Only fetch worker
  python run_workers.py --workers fetch,review  # Specific workers
  
For production with separate processes:
  python run_workers.py --workers fetch &
  python run_workers.py --workers analyze &
  python run_workers.py --workers review &
  python run_workers.py --workers publish &
"""

import os
import sys
import signal
import asyncio
import logging
import argparse

# Ensure the webhooks directory is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from config import config

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("agenticpr.runner")


async def create_db_session_factory():
    """Create an async session factory for workers."""
    from database import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from contextlib import asynccontextmanager
    
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    @asynccontextmanager
    async def get_session():
        async with session_factory() as session:
            yield session
    
    return get_session


async def cleanup_stale_jobs(db_session_factory):
    """On startup, mark any jobs that were left in active states as FAILED.
    This handles cases where the worker was killed mid-processing."""
    from models import Job, JobStatus
    from sqlmodel import select
    
    active_statuses = [
        JobStatus.QUEUED, JobStatus.PROCESSING,
        JobStatus.FETCHING, JobStatus.ANALYZING, JobStatus.REVIEWING
    ]
    
    async with db_session_factory() as session:
        result = await session.execute(
            select(Job).where(Job.status.in_(active_statuses))
        )
        stale_jobs = result.scalars().all()
        
        if stale_jobs:
            logger.info(f"🧹 Found {len(stale_jobs)} stale job(s) from previous run — marking as FAILED")
            from datetime import datetime
            for job in stale_jobs:
                job.status = JobStatus.FAILED
                job.error_detail = "[startup_cleanup] Worker restarted while job was active"
                job.finished_at = datetime.utcnow()
                session.add(job)
                logger.info(f"   → Job {job.id} ({job.repo_full_name}#{job.pr_number}) was {job.current_stage} → FAILED")
            await session.commit()
        else:
            logger.info("🧹 No stale jobs found — clean startup")


async def main(worker_types: list):
    """Start selected workers."""
    from workers.queue import QueueManager
    from database import init_db
    
    # Initialize database
    await init_db()
    
    # Connect to Redis
    queue = QueueManager()
    await queue.connect()
    
    if not queue.is_connected:
        logger.error("Redis not available — workers cannot start without a queue!")
        logger.info("Make sure Redis is running (docker-compose up redis)")
        return
    
    # Create DB session factory
    db_session_factory = await create_db_session_factory()
    
    # Cleanup stale jobs from previous run
    await cleanup_stale_jobs(db_session_factory)
    
    # Build worker instances
    workers = []
    worker_tasks = []
    
    if "fetch" in worker_types:
        from workers.fetch import FetchWorker
        w = FetchWorker(queue, db_session_factory)
        workers.append(w)
        worker_tasks.append(
            asyncio.create_task(w.start(concurrency=config.WORKER_CONCURRENCY_FETCH))
        )
        logger.info(f"  ✓ Fetch worker (concurrency={config.WORKER_CONCURRENCY_FETCH})")
    
    if "analyze" in worker_types:
        from workers.analyze import AnalyzeWorker
        w = AnalyzeWorker(queue, db_session_factory)
        workers.append(w)
        worker_tasks.append(
            asyncio.create_task(w.start(concurrency=config.WORKER_CONCURRENCY_ANALYZE))
        )
        logger.info(f"  ✓ Analyze worker (concurrency={config.WORKER_CONCURRENCY_ANALYZE})")
    
    if "review" in worker_types:
        from workers.review import ReviewWorker
        w = ReviewWorker(queue, db_session_factory)
        workers.append(w)
        worker_tasks.append(
            asyncio.create_task(w.start(concurrency=config.WORKER_CONCURRENCY_REVIEW))
        )
        logger.info(f"  ✓ Review worker (concurrency={config.WORKER_CONCURRENCY_REVIEW})")
    
    if "publish" in worker_types:
        from workers.publish import PublishWorker
        w = PublishWorker(queue, db_session_factory)
        workers.append(w)
        worker_tasks.append(
            asyncio.create_task(w.start(concurrency=config.WORKER_CONCURRENCY_PUBLISH))
        )
        logger.info(f"  ✓ Publish worker (concurrency={config.WORKER_CONCURRENCY_PUBLISH})")
    
    if not worker_tasks:
        logger.error("No workers selected! Use --workers fetch,analyze,review,publish")
        return
    
    logger.info(f"\n{'='*50}")
    logger.info(f"AgenticPR Workers running — {len(worker_tasks)} worker(s)")
    logger.info(f"Redis: {config.REDIS_URL}")
    logger.info(f"Press Ctrl+C to stop")
    logger.info(f"{'='*50}\n")
    
    # Handle graceful shutdown
    shutdown_event = asyncio.Event()
    
    def signal_handler():
        logger.info("\nShutdown signal received...")
        for w in workers:
            w.stop()
        shutdown_event.set()
    
    loop = asyncio.get_event_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
    except NotImplementedError:
        # Windows doesn't support add_signal_handler
        pass
    
    try:
        await asyncio.gather(*worker_tasks)
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        for w in workers:
            w.stop()
    finally:
        # Graceful shutdown: mark any remaining active jobs as failed
        logger.info("🧹 Cleaning up active jobs before shutdown...")
        await cleanup_stale_jobs(db_session_factory)
        await queue.disconnect()
        logger.info("Workers stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgenticPR Worker Runner")
    parser.add_argument(
        "--workers",
        type=str,
        default="fetch,analyze,review,publish",
        help="Comma-separated list of workers to start (default: all)"
    )
    args = parser.parse_args()
    
    worker_types = [w.strip().lower() for w in args.workers.split(",")]
    
    print(f"\n🚀 Starting AgenticPR Workers: {', '.join(worker_types)}\n")
    
    asyncio.run(main(worker_types))
