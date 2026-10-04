from pathlib import Path

import geopandas as gpd
from shapely.geometry import Point


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "streetlights"


def _load_streetlights():
    shapefiles = list(DATA_DIR.glob("*.shp"))

    if not shapefiles:
        raise FileNotFoundError(
            f"No streetlight shapefile found in {DATA_DIR}"
        )

    lights = gpd.read_file(shapefiles[0])

    # Remove records without geometry
    lights = lights[
        lights.geometry.notna()
        & ~lights.geometry.is_empty
    ].copy()

    # GPS coordinates use WGS84
    if lights.crs is None:
        raise ValueError("Streetlight dataset has no CRS.")

    return lights


def find_nearest_streetlight(lat, lon):
    lights = _load_streetlights()

    # User GPS point
    user = gpd.GeoSeries(
        [Point(lon, lat)],
        crs="EPSG:4326"
    )

    # Irish Transverse Mercator.
    # Distances are measured in metres.
    lights_metric = lights.to_crs("EPSG:2157")
    user_metric = user.to_crs("EPSG:2157").iloc[0]

    lights_metric = lights_metric.copy()

    lights_metric["distance_m"] = (
        lights_metric.geometry.distance(user_metric)
    )

    nearest_index = lights_metric["distance_m"].idxmin()

    nearest_original = lights.loc[nearest_index]
    nearest_metric = lights_metric.loc[nearest_index]

    result = {
        "distance_m": round(
            float(nearest_metric["distance_m"]),
            1
        )
    }

    # Return useful attributes without depending on
    # exact capitalization in the source dataset.
    for column in lights.columns:
        if column != "geometry":
            value = nearest_original[column]

            if value is not None:
                result[str(column)] = str(value)

    geometry = nearest_original.geometry

    # Convert geometry to normal GPS coordinates for frontend/map
    geometry_wgs84 = gpd.GeoSeries(
        [geometry],
        crs=lights.crs
    ).to_crs("EPSG:4326").iloc[0]

    result["latitude"] = float(geometry_wgs84.y)
    result["longitude"] = float(geometry_wgs84.x)

    return result