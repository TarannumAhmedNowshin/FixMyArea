"""Location lookups over the public-lighting dataset."""

from __future__ import annotations

import csv
from functools import lru_cache
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


@lru_cache(maxsize=4)
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
                item["unit_no"] = _first(properties, ("unit_no", "unit number", "unit"))
                item["unit_type"] = _first(properties, ("unit_type", "type"))
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


@lru_cache(maxsize=4)
def _load_boundary_features(path: str) -> list[dict[str, Any]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ValueError("Authority boundary data must be a GeoJSON FeatureCollection")
    return data.get("features", [])


def _in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    inside = False
    if len(ring) < 3:
        return False
    previous = ring[-1]
    for current in ring:
        x1, y1 = float(previous[0]), float(previous[1])
        x2, y2 = float(current[0]), float(current[1])
        cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(cross) < 1e-5 and min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2):
            return True
        if (y1 > y) != (y2 > y):
            intersection_x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < intersection_x:
                inside = not inside
        previous = current
    return inside


def _in_polygon(x: float, y: float, rings: list[list[list[float]]]) -> bool:
    if not rings or not _in_ring(x, y, rings[0]):
        return False
    return not any(_in_ring(x, y, hole) for hole in rings[1:])


def _geometry_contains(geometry: dict[str, Any], x: float, y: float) -> bool:
    kind = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    if kind == "Polygon":
        return _in_polygon(x, y, coordinates)
    if kind == "MultiPolygon":
        return any(_in_polygon(x, y, polygon) for polygon in coordinates)
    return False


def find_local_authority(
    latitude: float, longitude: float, boundary_path: str | Path
) -> dict[str, str] | None:
    """Check whether a WGS84 coordinate falls within a DCC admin-area polygon.

    The source polygons use Irish Transverse Mercator (EPSG:2157), so the
    submitted longitude/latitude is transformed before the point-in-polygon check.
    """
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude or longitude is outside the valid range")
    try:
        from pyproj import Transformer
    except ImportError as error:
        raise RuntimeError("Install pyproj to use the authority boundary lookup") from error
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2157", always_xy=True)
    x, y = transformer.transform(longitude, latitude)
    features = _load_boundary_features(str(Path(boundary_path).resolve()))
    for feature in features:
        geometry = feature.get("geometry") or {}
        if _geometry_contains(geometry, x, y):
            properties = feature.get("properties") or {}
            return {
                "authority": "Dublin City Council",
                "administrative_area": str(_first(properties, ("name",)) or "Dublin City"),
            }
    return None


@lru_cache(maxsize=4)
def load_recycling_centres(path: str | Path) -> list[dict[str, Any]]:
    """Load DCC recycling-centre point locations from GeoJSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ValueError("Recycling-centre data must be a GeoJSON FeatureCollection")
    facilities = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if geometry.get("type") != "Point" or len(coordinates) < 2:
            continue
        properties = feature.get("properties") or {}
        name = _first(properties, ("name",))
        item = _asset(properties, coordinates[1], coordinates[0])
        if not item or not name:
            continue
        item.update(
            name=str(name),
            address=_first(properties, ("address",)),
            eircode=_first(properties, ("eircode",)),
            telephone=_first(properties, ("telephone", "phone")),
            email=_first(properties, ("email",)),
            accepted_materials=["household electrical and electronic equipment (WEEE)"],
        )
        facilities.append(item)
    return facilities


def find_nearby_facilities(
    latitude: float, longitude: float, facilities: list[dict[str, Any]], limit: int = 3
) -> list[dict[str, Any]]:
    """Return recycling centres ordered by great-circle distance."""
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Latitude or longitude is outside the valid range")
    ordered = sorted(
        facilities,
        key=lambda facility: _distance_m(
            latitude, longitude, facility["latitude"], facility["longitude"]
        ),
    )
    return [
        {
            **facility,
            "distance_m": round(
                _distance_m(latitude, longitude, facility["latitude"], facility["longitude"])
            ),
        }
        for facility in ordered[:limit]
    ]
