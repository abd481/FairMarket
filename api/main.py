import pandas as pd
import joblib
import sys
import time
import os
from datetime import datetime, timezone
from pathlib import Path
from logging import getLogger
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.db import get_pg_engine
from api.services.location import build_location_cache, resolve_location
from api.services.predictor import predict
from api.services.recommender import recommend
from api.schemas import (
    RecommendRequest,
    RecommendResponse,
    Recommendation,
    PredictRequest,
    PredictResponse,
    Status,
    HealthResponse,
)

LOGGER = getLogger()


def _load_all():
    df = pd.read_sql(
        """
        SELECT location, district, city, compound, AVG(price_per_sqm) AS price_per_sqm
        FROM clean_properties
        GROUP BY location, district, city, compound
        """,
        get_pg_engine(),
    )
    location_caches = build_location_cache(df)
    models = {}

    for mode in ["only_villas", "no_villas"]:

        pps = joblib.load(f"{PROJECT_ROOT}/artifacts/models/{mode}_district_pps.joblib")
        models[mode] = {
            "pipeline": joblib.load(
                f"{PROJECT_ROOT}/artifacts/pipelines/{mode}_pipeline.joblib"
            ),
            "model": joblib.load(
                f"{PROJECT_ROOT}/artifacts/models/{mode}_xgb_model.joblib"
            ),
            "calib": joblib.load(
                f"{PROJECT_ROOT}/artifacts/models/{mode}_calib.joblib"
            ),
            "district_pps": pps["district_pps"],
            "global_pps": pps["global_pps"],
            "knn": joblib.load(
                f"{PROJECT_ROOT}/artifacts/recommendations/{mode}_knn.joblib"
            ),
            "stored_ids": joblib.load(
                f"{PROJECT_ROOT}/artifacts/recommendations/{mode}_property_ids.joblib"
            ),
            "metadata": joblib.load(
                f"{PROJECT_ROOT}/artifacts/recommendations/{mode}_metadata.joblib"
            ),
        }

    return models, location_caches


@asynccontextmanager
async def lifespan(app):
    try:
        models, caches = _load_all()
        app.state.location_caches = caches
        app.state.models = models
        app.state.started_at = datetime.now(timezone.utc).isoformat()
        app.state._monotonic = time.monotonic()
        LOGGER.info(
            "Startup complete: %d modes loaded, %d known locations",
            len(models),
            len(app.state.location_caches["locations"]),
        )
    except Exception as e:
        LOGGER.critical("Startup failed: %s", e)
        raise
    yield


app = FastAPI(title="FairMarket Real estate API.", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/locations")
async def list_locations(request: Request):
    return request.app.state.location_caches["locations"]


@app.get("/health")
async def health(request: Request):
    return HealthResponse(
        status=Status.READY,
        models_loaded=list(request.app.state.models.keys()),
        recommend_loaded=list(request.app.state.models.keys()),
        uptime_seconds=time.monotonic() - request.app.state._monotonic,
        started_at=request.app.state.started_at,
        known_locations=len(request.app.state.location_caches["locations"]),
    )


@app.post("/api/predict", response_model=PredictResponse)
def predict_price(body: PredictRequest, request: Request):
    loc = resolve_location(body.location, request.app.state.location_caches)
    if not loc.matched:
        raise HTTPException(
            400,
            detail=f"Location {body.location} not found. Choose from the dropdown list.",
        )

    return predict(body, loc, request.app.state.models)


@app.post("/api/recommend", response_model=RecommendResponse)
def recommend_properties(body: RecommendRequest, request: Request):
    loc = resolve_location(body.location, request.app.state.location_caches)
    if not loc.matched:
        raise HTTPException(
            400,
            detail=f"Location {body.location} not found. Choose from the dropdown list.",
        )

    return recommend(body, loc, request.app.state.models)
