from redis.asyncio import Redis
from app.configs.rediss import get_redis_client
from fastapi import Request, Depends, HTTPException, status


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int, prefix: str = "rl"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.prefix = prefix


    async def __call__(self, request: Request, reds: Redis = Depends(get_redis_client)):
        ip = request.client.host
        key = f"{self.prefix}:{request.url.path}:{ip}"

        count = await reds.incr(key)

        if count == 1:
            await reds.expire(key, self.window_seconds)
    
        if count > self.max_requests:
            ttl = await reds.ttl(key)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry in {ttl} seconds.",
                headers={"Retry-After": str(ttl)},
            )
