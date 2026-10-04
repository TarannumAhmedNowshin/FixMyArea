import geopandas as gpd
from shapely.geometry import Point


AUTHORITY_GEOJSON_URL = (
    "https://data-osi.opendata.arcgis.com/api/download/v1/items/"
    "74b839e09e1c48f2b2fe4efccb52a73d/"
    "geojson?layers=3"
)


_authorities = None


def _load_authorities():
    global _authorities

    if _authorities is None:
        print("Loading Local Authority boundaries...")

        _authorities = gpd.read_file(
            AUTHORITY_GEOJSON_URL
        )

        if _authorities.crs is None:
            _authorities = _authorities.set_crs(
                "EPSG:4326"
            )

        _authorities = _authorities.to_crs(
            "EPSG:4326"
        )

    return _authorities


def find_local_authority(lat, lon):
    """
    Find the Irish local authority containing
    the supplied GPS coordinates.
    """

    authorities = _load_authorities()

    # Shapely expects longitude first
    user_location = Point(lon, lat)

    match = authorities[
        authorities.geometry.intersects(
            user_location
        )
    ]

    if match.empty:
        return {
            "found": False,
            "authority": None
        }

    row = match.iloc[0]

    attributes = {}

    for column in authorities.columns:

        if column != "geometry":
            attributes[column] = str(
                row[column]
            )

    return {
        "found": True,
        "attributes": attributes
    }