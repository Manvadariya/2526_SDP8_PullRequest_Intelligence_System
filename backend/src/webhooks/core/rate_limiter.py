"""
Enterprise Redis-based Rate Limiter (Token Bucket).
Prevents LLM quota exhaustion.
"""

import time
import asyncio
import logging
from config import config

logger = logging.getLogger("agenticpr.ratelimit")

class TokenBucketRateLimiter:
    """
    Redis-backed Token Bucket for LLM RPM (Requests Per Minute).
    """
    def __init__(self, queue_manager):
        self.redis = queue_manager.redis
        self.capacity = getattr(config, "LLM_RPM_LIMIT", 30)
        self.refill_rate = self.capacity / 60.0  # tokens per second
        self.key = "ratelimit:llm_bucket"
    
    async def acquire(self, tokens: int = 1, timeout: int = 300) -> bool:
        """
        Wait until tokens are available (up to timeout seconds).
        Uses a Lua script for atomic bucket updates.
        """
        lua_script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])
        
        local bucket = redis.call("HMGET", key, "tokens", "last_refill")
        local tokens = tonumber(bucket[1])
        local last_refill = tonumber(bucket[2])
        
        if not tokens or not last_refill then
            tokens = capacity
            last_refill = now
        else
            local elapsed = math.max(0, now - last_refill)
            local refill = elapsed * refill_rate
            tokens = math.min(capacity, tokens + refill)
            last_refill = now
        end
        
        if tokens >= requested then
            tokens = tokens - requested
            redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
            redis.call("EXPIRE", key, 300)
            return {1, tokens}
        else
            redis.call("HMSET", key, "tokens", tokens, "last_refill", last_refill)
            redis.call("EXPIRE", key, 300)
            return {0, tokens}
        end
        """
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            now = time.time()
            logger.debug(f"Executing Redis Lua script: {lua_script.strip()}")
            logger.debug(f"Args: key={self.key}, capacity={self.capacity}, rate={self.refill_rate}, requested={tokens}, now={now}")
            
            try:
                result = await self.redis.eval(
                    lua_script, 1, self.key, 
                    self.capacity, self.refill_rate, tokens, now
                )
            except Exception as e:
                logger.error(f"Redis eval failed: {e}")
                logger.error(f"Failed script: {lua_script}")
                raise
            
            allowed = result[0] == 1
            if allowed:
                return True
                
            # Sleep if not enough tokens
            await asyncio.sleep(2)
            
        logger.warning("Timeout waiting for LLM tokens.")
        return False
