"""Small FastAPI entry point for the first FixMyArea location lookup."""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .location import find_nearest_streetlight, load_streetlights


app = FastAPI(title="FixMyArea API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
DATA_PATH = Path(os.environ.get("FIXMYAREA_STREETLIGHTS", "data/streetlights.geojson"))


class LocationRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/nearest-streetlight")
def nearest_streetlight(request: LocationRequest) -> dict:
    if not DATA_PATH.is_file():
        raise HTTPException(
            status_code=503,
            detail="Streetlight dataset is not installed. See data/README.md.",
        )
    try:
        assets = load_streetlights(DATA_PATH)
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=503, detail=f"Could not read streetlight data: {error}")
    result = find_nearest_streetlight(request.latitude, request.longitude, assets)
    if result is None:
        raise HTTPException(status_code=404, detail="No usable streetlight assets were found.")
    return result
