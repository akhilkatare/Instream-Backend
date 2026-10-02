from redis.asyncio import Redis


async def revoke_all_user_sessions(reds: Redis, user_id: str) -> None:
    async for key in reds.scan_iter(match="refresh:*"):
        
        if await reds.get(key) == user_id:
            await reds.unlink(key)
