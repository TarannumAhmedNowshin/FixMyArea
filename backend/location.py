"""Location lookups over the public-lighting dataset."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Iterable


EARTH_RADIUS_M = 6_371_000


def _distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance between two WGS84 coordinates."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _number(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _first(properties: dict[str, Any], names: Iterable[str]) -> Any:
    normalized = {
        str(key).strip().casefold().replace("_", " "): value
        for key, value in properties.items()
    }
    for name in names:
        value = normalized.get(name.casefold().replace("_", " "))
        if value not in (None, ""):
            return value
    return None


def _asset(properties: dict[str, Any], latitude: Any, longitude: Any) -> dict[str, Any] | None:
    lat, lon = _number(latitude), _number(longitude)
    if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    asset_id = _first(
        properties,
        ("asset_id", "asset id", "id", "unit number", "unit no", "unit_no", "unit"),
    )
    location = _first(properties, ("location", "site name", "road", "street"))
    return {
        "asset_id": str(asset_id) if asset_id is not None else None,
        "location": str(location) if location is not None else None,
        "latitude": lat,
        "longitude": lon,
    }


def load_streetlights(path: str | Path) -> list[dict[str, Any]]:
    """Load point assets from GeoJSON or a CSV with latitude/longitude columns."""
    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix in {".json", ".geojson"}:
        data = json.loads(source.read_text(encoding="utf-8"))
        features = data.get("features", []) if data.get("type") == "FeatureCollection" else []
        assets = []
        for feature in features:
            geometry = feature.get("geometry") or {}
            if geometry.get("type") != "Point":
                continue
            coordinates = geometry.get("coordinates") or []
            if len(coordinates) < 2:
                continue
            properties = feature.get("properties") or {}
            # GeoJSON coordinates are longitude, latitude (RFC 7946).
            item = _asset(properties, coordinates[1], coordinates[0])
            if item:
                assets.append(item)
        return assets

    if suffix == ".csv":
        assets = []
        with source.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                latitude = _first(row, ("latitude", "lat", "y"))
                longitude = _first(row, ("longitude", "long", "lon", "lng", "x"))
                item = _asset(row, latitude, longitude)
                if item:
                    assets.append(item)
        return assets

    raise ValueError("Streetlight data must be a .csv, .json, or .geojson file")


def find_nearest_streetlight(
    latitude: float, longitude: float, assets: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Find the nearest loaded asset and report its approximate distance in metres."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude or longitude is outside the valid range")
    if not assets:
        return None
    nearest = min(
        assets,
        key=lambda asset: _distance_m(
            latitude, longitude, asset["latitude"], asset["longitude"]
        ),
    )
    return {
        **nearest,
        "distance_m": round(
            _distance_m(latitude, longitude, nearest["latitude"], nearest["longitude"])
        ),
    }
