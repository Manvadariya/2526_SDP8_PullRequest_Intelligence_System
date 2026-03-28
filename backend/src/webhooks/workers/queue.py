"""
Redis Queue Manager — durable task queue using Redis Streams.

Supports:
  - Multiple named queues (review:fetch, review:analyze, etc.)
  - Consumer groups for competing consumers
  - Message acknowledgment and reclaim
  - Graceful fallback when Redis is unavailable
"""

import json
import time
import logging
import asyncio
from typing import Optional, Dict, Any, Callable, Awaitable

logger = logging.getLogger("agenticpr.queue")


class QueueManager:
    """Manages Redis-backed durable queues using Redis Streams."""
    
    def __init__(self, redis_url: Optional[str] = None):
        from config import config
        self.redis_url = redis_url or config.REDIS_URL
        self.redis = None
        self._connected = False
    
    async def connect(self):
        """Connect to Redis. Logs warning and continues if unavailable."""
        try:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                retry_on_timeout=True,
            )
            await self.redis.ping()
            self._connected = True
            logger.info(f"✓ Redis connected ({self.redis_url})")
        except Exception as e:
            logger.warning(f"⚠ Redis unavailable ({e}) — will use in-process fallback")
            self.redis = None
            self._connected = False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self._connected = False
            logger.info("Redis disconnected")
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self.redis is not None
    
    async def ensure_consumer_group(self, queue_name: str, group_name: str):
        """Create consumer group if it doesn't exist."""
        if not self.is_connected:
            return
        try:
            await self.redis.xgroup_create(
                queue_name, group_name, id="0", mkstream=True
            )
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.error(f"Failed to create consumer group {group_name}: {e}")
    
    async def enqueue(self, queue_name: str, message: Dict[str, Any]) -> Optional[str]:
        """Add a message to the queue. Returns message ID or None if Redis unavailable."""
        if not self.is_connected:
            raise ConnectionError("Redis not connected")
        
        # Serialize the message
        payload = {
            "data": json.dumps(message),
            "enqueued_at": str(time.time()),
        }
        
        msg_id = await self.redis.xadd(queue_name, payload)
        logger.debug(f"Enqueued to {queue_name}: id={msg_id}")
        return msg_id
    
    async def dequeue(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block_ms: int = 5000,
    ) -> list:
        """
        Read messages from queue as a consumer in a group.
        Returns list of (message_id, data_dict) tuples.
        """
        if not self.is_connected:
            return []
        
        try:
            results = await self.redis.xreadgroup(
                group_name, consumer_name,
                {queue_name: ">"},
                count=count,
                block=block_ms,
            )
            
            messages = []
            if results:
                for stream_name, stream_messages in results:
                    for msg_id, msg_data in stream_messages:
                        try:
                            data = json.loads(msg_data.get("data", "{}"))
                            messages.append((msg_id, data))
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in queue message {msg_id}")
                            await self.ack(queue_name, group_name, msg_id)
            
            return messages
            
        except Exception as e:
            logger.error(f"Dequeue error on {queue_name}: {e}")
            return []
    
    async def ack(self, queue_name: str, group_name: str, message_id: str):
        """Acknowledge a message as processed."""
        if self.is_connected:
            await self.redis.xack(queue_name, group_name, message_id)
    
    async def get_queue_length(self, queue_name: str) -> int:
        """Get the number of messages in a queue."""
        if not self.is_connected:
            return 0
        try:
            return await self.redis.xlen(queue_name)
        except Exception:
            return 0
    
    async def get_pending_count(self, queue_name: str, group_name: str) -> int:
        """Get number of pending (unacknowledged) messages in a consumer group."""
        if not self.is_connected:
            return 0
        try:
            info = await self.redis.xpending(queue_name, group_name)
            return info.get("pending", 0) if isinstance(info, dict) else 0
        except Exception:
            return 0
    
    async def reclaim_stale(
        self,
        queue_name: str,
        group_name: str,
        consumer_name: str,
        min_idle_ms: int = 60000,
        count: int = 10,
    ) -> list:
        """
        Reclaim messages from dead consumers that haven't acked within min_idle_ms.
        This handles worker crashes — unfinished work gets picked up by another worker.
        """
        if not self.is_connected:
            return []
        
        try:
            results = await self.redis.xautoclaim(
                queue_name, group_name, consumer_name,
                min_idle_time=min_idle_ms,
                count=count,
            )
            if results and len(results) >= 2:
                messages = []
                for msg_id, msg_data in results[1]:
                    if msg_data:
                        try:
                            data = json.loads(msg_data.get("data", "{}"))
                            messages.append((msg_id, data))
                        except json.JSONDecodeError:
                            await self.ack(queue_name, group_name, msg_id)
                return messages
        except Exception as e:
            logger.debug(f"Autoclaim not available: {e}")
        return []
    
    async def move_to_dlq(self, queue_name: str, message: Dict[str, Any], error: str):
        """Move a failed message to the dead-letter queue."""
        dlq_message = {
            **message,
            "original_queue": queue_name,
            "error": error,
            "moved_at": time.time(),
        }
        try:
            await self.enqueue("review:dlq", dlq_message)
            logger.warning(f"Message moved to DLQ from {queue_name}: {error}")
        except Exception as e:
            logger.error(f"Failed to move to DLQ: {e}")
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]):
        """Publish an event for SSE consumers via Redis PubSub."""
        if not self.is_connected:
            return
        try:
            await self.redis.publish(channel, json.dumps(event_data))
        except Exception as e:
            logger.debug(f"Event publish failed: {e}")
