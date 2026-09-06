"""
app/main.py

CHANGELOG (post-review fixes):
- Rate limiter registered on the app (slowapi) with a 429 handler.
- CORS origins now read from an env var (ALLOWED_ORIGINS) instead of "*".
  Defaults to "*" ONLY for local dev convenience — set ALLOWED_ORIGINS in
  your deployment environment before this goes anywhere public.
- load() now runs a self-test at startup (see eta_service.py) — if the
  model loads but predicts garbage, you'll see it in the startup logs
  immediately instead of discovering it live during a demo.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.routers import eta
from app.services.eta_service import eta_service
from app.rate_limit import limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gatisync-eta-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        eta_service.load()  # this also runs a self-test internally now
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error(
            "API will start, but /predict-eta will return 503 until the "
            "model files are placed at app/ml_models/"
        )
    except Exception as e:
        logger.error(f"Model failed to load or failed self-test: {e}")
    yield


app = FastAPI(
    title="GatiSync ETA Inference API",
    description="LightGBM-backed bus segment ETA prediction service",
    version="1.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Max 20 requests/minute per IP."},
    )


# Read allowed origins from env, defaulting to "*" for local dev only.
# Set ALLOWED_ORIGINS="https://your-pwa-domain.com,https://another.com"
# before any public deployment.
_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = ["*"] if _origins_env == "*" else _origins_env.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(eta.router, tags=["eta"])


@app.get("/")
def root():
    return {"service": "GatiSync ETA Inference API", "docs": "/docs"}