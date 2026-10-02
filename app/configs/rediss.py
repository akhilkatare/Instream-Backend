import os
import redis.asyncio as redis


redis_url = os.getenv("REDIS_URL")

redis_client = redis.from_url(redis_url, decode_responses = True)


async def get_redis_client() -> redis.Redis:
    return redis_client
