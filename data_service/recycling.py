import math
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "recycling" / "recycling-centers-dcc.csv"


def _load_recycling_centres():
    df = pd.read_csv(DATA_FILE)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Ensure coordinates are numeric
    df["Latitude"] = pd.to_numeric(df["Latitude"], errors="coerce")
    df["Longitude"] = pd.to_numeric(df["Longitude"], errors="coerce")

    # We cannot route to a centre without valid coordinates
    df = df.dropna(subset=["Latitude", "Longitude"])

    return df


def _haversine(lat1, lon1, lat2, lon2):
    """Distance between two GPS coordinates in kilometres."""

    radius = 6371.0

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return radius * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


def find_nearest_recycling_centre(lat, lon):
    centres = _load_recycling_centres()

    centres["distance_km"] = centres.apply(
        lambda row: _haversine(
            lat,
            lon,
            row["Latitude"],
            row["Longitude"]
        ),
        axis=1
    )

    nearest = centres.loc[centres["distance_km"].idxmin()]

    return {
        "name": str(nearest["Name"]),
        "address": str(nearest["Address"]),
        "eircode": str(nearest["Eircode"]),
        "telephone": str(nearest["Telephone"]),
        "email": str(nearest["Email"]),
        "latitude": float(nearest["Latitude"]),
        "longitude": float(nearest["Longitude"]),
        "distance_km": round(float(nearest["distance_km"]), 2)
    }