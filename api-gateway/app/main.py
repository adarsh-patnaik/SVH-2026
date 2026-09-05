"""
app/main.py

Entrypoint for the ETA inference API.

Run locally:
    uvicorn app.main:app --reload --port 8000

Then visit http://localhost:8000/docs for interactive Swagger UI, or call:
    POST http://localhost:8000/predict-eta
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import eta
from app.services.eta_service import eta_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gatisync-eta-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load the model ONCE, not per-request
    try:
        eta_service.load()
    except FileNotFoundError as e:
        logger.error(str(e))
        logger.error(
            "API will start, but /predict-eta will return 503 until the model "
            "file is placed at app/ml_models/eta_lightgbm.txt"
        )
    yield
    # Shutdown: nothing to clean up currently


app = FastAPI(
    title="GatiSync ETA Inference API",
    description="LightGBM-backed bus segment ETA prediction service",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the commuter PWA (and local dev servers) to call this directly.
# Tighten allow_origins to your actual PWA domain before production deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(eta.router, tags=["eta"])


@app.get("/")
def root():
    return {"service": "GatiSync ETA Inference API", "docs": "/docs"}