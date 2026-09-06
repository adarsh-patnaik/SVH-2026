"""
app/main.py

CHANGELOG (second review round):
- CORS no longer silently falls back to "*" outside local dev. A new
  ENVIRONMENT env var (defaults to "development") gates this: if
  ENVIRONMENT=production (or "staging") and ALLOWED_ORIGINS is unset, the
  app now REFUSES TO START with a clear error, instead of quietly serving
  every origin. A comment warning about this was not enforcement — someone
  deploying under time pressure could easily miss it. Now it's a hard stop.

Run locally (dev — CORS defaults to "*", no setup needed):
    uvicorn app.main:app --reload --port 8000

Run for any real deployment:
    set ENVIRONMENT=production
    set ALLOWED_ORIGINS=https://your-pwa-domain.com
    uvicorn app.main:app --port 8000
"""

import logging
import os
import sys
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


def _resolve_cors_origins() -> list[str]:
    environment = os.getenv("ENVIRONMENT", "development").lower()
    origins_env = os.getenv("ALLOWED_ORIGINS")

    if origins_env:
        return [o.strip() for o in origins_env.split(",") if o.strip()]

    if environment in ("production", "staging"):
        # Fail loudly and refuse to start, rather than silently serving "*"
        # in an environment where that's a real exposure. This is the fix
        # for "a comment isn't enforcement" — now it's a hard startup error.
        logger.critical(
            f"ENVIRONMENT={environment} but ALLOWED_ORIGINS is not set. "
            f"Refusing to start with a wide-open CORS policy in a non-dev "
            f"environment. Set ALLOWED_ORIGINS to a comma-separated list of "
            f"allowed origins (e.g. https://your-pwa-domain.com)."
        )
        sys.exit(1)

    # Local dev only: no ALLOWED_ORIGINS set, ENVIRONMENT is dev/unset.
    logger.warning(
        "ALLOWED_ORIGINS not set — defaulting to '*' (allowed only because "
        "ENVIRONMENT is not 'production'/'staging'). Do not deploy this "
        "configuration publicly."
    )
    return ["*"]


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
    version="1.2.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Max 20 requests/minute per IP."},
    )


allowed_origins = _resolve_cors_origins()

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