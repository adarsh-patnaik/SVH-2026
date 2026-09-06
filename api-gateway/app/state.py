import json
import os
from collections.abc import AsyncIterator

from redis.asyncio import Redis


def redis_client() -> Redis:
    return Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)


async def live_buses(redis: Redis, route_id: str | None = None) -> AsyncIterator[dict]:
    if route_id:
        ids = await redis.smembers(f"route:{route_id}:buses")
        keys = [f"bus:{bus_id}:live" for bus_id in ids]
    else:
        keys = [key async for key in redis.scan_iter(match="bus:*:live", count=100)]
    if not keys:
        return
    for raw in await redis.mget(keys):
        if raw:
            yield json.loads(raw)
