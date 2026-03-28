"""
SSE Router — Server-Sent Events for realtime review status updates.

Provides a long-lived HTTP connection where clients receive events as reviews
progress through stages. Falls back gracefully when Redis PubSub is unavailable.
"""

import json
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Job, JobStatus

logger = logging.getLogger("agenticpr.sse")

router = APIRouter(prefix="/api", tags=["SSE"])


@router.get("/reviews/{job_id}/events")
async def review_event_stream(
    job_id: int,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """
    SSE endpoint for realtime review status updates.
    
    Client connects with EventSource:
        const src = new EventSource('/api/reviews/42/events');
        src.onmessage = (e) => console.log(JSON.parse(e.data));
    
    Events include: stage_started, stage_completed, review_completed, review_failed
    """
    # Verify job exists
    result = await session.execute(select(Job).where(Job.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # If job is already terminal, send final state and close
    terminal_states = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.SUPERSEDED, JobStatus.CANCELED}
    if job.status in terminal_states:
        async def terminal_generator():
            data = {
                "event": "review_completed" if job.status == JobStatus.COMPLETED else "review_ended",
                "job_id": job_id,
                "status": job.status,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            }
            yield f"data: {json.dumps(data)}\n\n"
        
        return StreamingResponse(
            terminal_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    
    # Live stream — try Redis PubSub, fallback to polling
    async def event_generator():
        """Generate SSE events from Redis PubSub or polling fallback."""
        
        # Try Redis PubSub first
        try:
            queue = request.app.state.queue
            if queue.is_connected:
                async for event in _redis_pubsub_stream(queue, job_id, request):
                    yield event
                return
        except Exception as e:
            logger.debug(f"Redis PubSub not available: {e}")
        
        # Fallback: poll the database every 2 seconds
        last_status = job.status
        last_stage = job.current_stage
        
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            await asyncio.sleep(2)
            
            try:
                async with get_session_direct() as poll_session:
                    result = await poll_session.execute(select(Job).where(Job.id == job_id))
                    current_job = result.scalars().first()
                
                if not current_job:
                    break
                
                # Emit event if status or stage changed
                if current_job.status != last_status or current_job.current_stage != last_stage:
                    data = {
                        "event": "status_change",
                        "job_id": job_id,
                        "status": current_job.status,
                        "current_stage": current_job.current_stage,
                        "started_at": current_job.started_at.isoformat() if current_job.started_at else None,
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    last_status = current_job.status
                    last_stage = current_job.current_stage
                    
                    # Close on terminal states
                    if current_job.status in terminal_states:
                        final_data = {
                            "event": "review_completed" if current_job.status == JobStatus.COMPLETED else "review_ended",
                            "job_id": job_id,
                            "status": current_job.status,
                            "finished_at": current_job.finished_at.isoformat() if current_job.finished_at else None,
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                else:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
                    
            except Exception as e:
                logger.debug(f"SSE poll error: {e}")
                await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _redis_pubsub_stream(queue, job_id: int, request: Request):
    """Stream events from Redis PubSub channel."""
    import redis.asyncio as aioredis
    
    channel_name = f"review:{job_id}"
    pubsub = queue.redis.pubsub()
    
    try:
        await pubsub.subscribe(channel_name)
        
        while True:
            if await request.is_disconnected():
                break
            
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=5.0,
            )
            
            if message and message["type"] == "message":
                data = message["data"]
                yield f"data: {data}\n\n"
                
                # Check if this is a terminal event
                try:
                    parsed = json.loads(data)
                    if parsed.get("event") in ("review_completed", "review_failed", "review_ended"):
                        break
                except json.JSONDecodeError:
                    pass
            else:
                # Heartbeat
                yield f": heartbeat\n\n"
                
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()


async def get_session_direct():
    """Get a session without FastAPI dependency injection."""
    from database import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from contextlib import asynccontextmanager
    
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    @asynccontextmanager
    async def session_ctx():
        async with session_factory() as session:
            yield session
    
    return session_ctx()


@router.get("/queue/status")
async def queue_status(request: Request):
    """Get current queue depths for monitoring."""
    try:
        queue = request.app.state.queue
        if not queue.is_connected:
            return {"status": "redis_unavailable", "queues": {}}
        
        queues = {}
        for queue_name in ["review:fetch", "review:analyze", "review:llm", "review:publish", "review:dlq"]:
            length = await queue.get_queue_length(queue_name)
            queues[queue_name] = {"length": length}
        
        return {"status": "ok", "queues": queues}
    
    except Exception as e:
        return {"status": "error", "error": str(e), "queues": {}}
