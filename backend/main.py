"""Small FastAPI entry point for the first FixMyArea location lookup."""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .classification import ClassificationError, classify_image
from .location import (
    find_local_authority,
    find_nearby_facilities,
    find_nearest_streetlight,
    load_recycling_centres,
    load_streetlights,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

app = FastAPI(title="FixMyArea API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
DATA_PATH = Path(os.environ.get("FIXMYAREA_STREETLIGHTS", PROJECT_ROOT / "data/streetlights.geojson"))
BOUNDARIES_PATH = Path(os.environ.get("FIXMYAREA_BOUNDARIES", PROJECT_ROOT / "data/dcc_admin_areas.geojson"))
FACILITIES_PATH = Path(os.environ.get("FIXMYAREA_FACILITIES", PROJECT_ROOT / "data/recycling-centers-dcc.geojson"))
ROUTING_RULES_PATH = Path(os.environ.get("FIXMYAREA_ROUTING_RULES", PROJECT_ROOT / "data/routing_rules.json"))
SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ROUTING_RULES = json.loads(ROUTING_RULES_PATH.read_text(encoding="utf-8"))


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


@app.post("/api/analyse")
async def analyse(
    image: UploadFile = File(...),
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    description: str = Form(default="", max_length=1000),
) -> dict:
    """Classify a submitted photo, then enrich supported categories with local data."""
    content_type = (image.content_type or "").split(";")[0].strip().lower()
    if content_type not in SUPPORTED_IMAGE_TYPES:
        await image.close()
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, WebP, or GIF image.")
    image_bytes = await image.read(MAX_IMAGE_BYTES + 1)
    await image.close()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The selected image is empty.")
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Images must be 10 MB or smaller.")

    try:
        classification = classify_image(image_bytes, content_type, description)
    except ClassificationError as error:
        raise HTTPException(status_code=503 if "OPENAI_API_KEY" in str(error) else 502, detail=str(error))

    result = {
        **classification,
        "latitude": latitude,
        "longitude": longitude,
        "route_status": "route_unavailable",
        "next_action": None,
        "authority": None,
        "administrative_area": None,
        "destination": None,
        "asset": None,
        "facilities": [],
        "draft_report": None,
        "message": "We identified the issue type. Verified service routing for this category is not connected yet.",
    }

    if not BOUNDARIES_PATH.is_file():
        result.update(route_status="boundary_data_unavailable", message="Dublin City coverage data is unavailable.")
        return result
    try:
        authority = find_local_authority(latitude, longitude, BOUNDARIES_PATH)
    except (OSError, ValueError, RuntimeError):
        result.update(route_status="boundary_data_unavailable", message="Dublin City coverage data could not be read.")
        return result
    if authority is None:
        result.update(
            route_status="outside_supported_area",
            message="This prototype currently supports locations within Dublin City Council's area only.",
        )
        return result
    result.update(authority=authority["authority"], administrative_area=authority["administrative_area"])

    if classification["category"] == "street_light":
        if not DATA_PATH.is_file():
            result.update(route_status="dataset_unavailable", message="Streetlight data is currently unavailable.")
            return result
        try:
            assets = load_streetlights(DATA_PATH)
        except (OSError, ValueError):
            result.update(route_status="dataset_unavailable", message="Streetlight data could not be read.")
            return result
        asset = find_nearest_streetlight(latitude, longitude, assets)
        result.update(
            route_status="ready_to_report" if asset else "asset_not_found",
            next_action="report" if asset else None,
            destination={**ROUTING_RULES["street_light"]["destination"], "guidance": ROUTING_RULES["street_light"]["guidance"]},
            asset=asset,
            draft_report=(
                f"Possible streetlight fault at {latitude:.6f}, {longitude:.6f}. "
                f"The submitted photo shows: {classification['label']}. "
                + (
                    f"Nearest identified public-lighting asset: {asset.get('asset_id') or 'unknown'} "
                    f"({asset.get('distance_m')} m away)."
                    if asset
                    else "No nearby lighting asset could be identified."
                )
            ),
            message=(
                "We found the nearest public-lighting asset and the official reporting route."
                if asset
                else "No usable streetlight assets were found for this location."
            ),
        )
    elif classification["category"] == "illegal_dumping":
        rule = ROUTING_RULES["illegal_dumping"]
        result.update(
            route_status="ready_to_report",
            next_action=rule["next_action"],
            destination={**rule["destination"], "guidance": rule["guidance"]},
            draft_report=(
                f"Possible illegal dumping at {latitude:.6f}, {longitude:.6f}. "
                f"The submitted photo shows: {classification['label']}."
            ),
            message="We identified Dublin City Council and the official dumping report form.",
        )
    elif classification["category"] == "electronic_waste":
        rule = ROUTING_RULES["electronic_waste"]
        if not FACILITIES_PATH.is_file():
            result.update(route_status="facility_data_unavailable", message="Recycling-centre data is unavailable.")
            return result
        try:
            facilities = load_recycling_centres(FACILITIES_PATH)
        except (OSError, ValueError):
            result.update(route_status="facility_data_unavailable", message="Recycling-centre data could not be read.")
            return result
        nearby = find_nearby_facilities(latitude, longitude, facilities)
        result.update(
            route_status="ready_to_recycle" if nearby else "facility_not_found",
            next_action=rule["next_action"] if nearby else None,
            destination={**rule["destination"], "guidance": rule["guidance"]},
            facilities=nearby,
            message=(
                "Dublin City Council accepts household WEEE at its recycling centres. Check current opening hours before travelling."
                if nearby
                else "No recycling centres were found in the connected dataset."
            ),
        )
    else:
        result.update(
            route_status="unsupported_issue",
            message="We couldn't match this photo to a supported FixMyArea issue type.",
        )
    return result
