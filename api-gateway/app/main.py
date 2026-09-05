from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import gtfs_rt, websocket
from app.state import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis_client()
    await app.state.redis.ping()
    yield
    await app.state.redis.aclose()


app = FastAPI(title="GatiSync API", version="0.1.0", lifespan=lifespan)
app.include_router(gtfs_rt.router)
app.include_router(websocket.router)


@app.get("/healthz", tags=["operational"])
async def healthz():
    return {"status": "ok"}
