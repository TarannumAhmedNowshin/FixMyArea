import requests


# Official Tailte Éireann ArcGIS item
ITEM_ID = "74b839e09e1c48f2b2fe4efccb52a73d"

# Local Authorities layer inside the ArcGIS service
SUBLAYER_ID = 3

# ArcGIS item metadata endpoint
ITEM_INFO_URL = (
    f"https://www.arcgis.com/sharing/rest/content/items/"
    f"{ITEM_ID}?f=json"
)


def _get_layer_url():
    """
    Get the current ArcGIS FeatureServer URL
    from the official Tailte Éireann item.
    """

    response = requests.get(
        ITEM_INFO_URL,
        timeout=10
    )

    response.raise_for_status()

    item = response.json()

    service_url = item.get("url")

    if not service_url:
        raise RuntimeError(
            "Could not find the Local Authority service URL."
        )

    return f"{service_url}/{SUBLAYER_ID}"


def find_local_authority(lat, lon):
    """
    Find the Irish local authority responsible
    for a given GPS coordinate.

    Example:
        find_local_authority(53.3498, -6.2603)

    Returns:
        {
            "found": True,
            "authority": "Dublin City Council",
            "authority_ga": "Comhairle Cathrach Bhaile Átha Cliath"
        }
    """

    layer_url = _get_layer_url()

    query_url = f"{layer_url}/query"

    params = {
        "f": "json",

        # ArcGIS expects longitude,latitude
        "geometry": f"{lon},{lat}",

        "geometryType": "esriGeometryPoint",

        # WGS84 / standard GPS coordinates
        "inSR": "4326",

        # Find the authority polygon containing the point
        "spatialRel": "esriSpatialRelIntersects",

        # Only request fields FixMyArea needs
        "outFields": "ENG_NAME_VALUE,GLE_NAME_VALUE",

        # Geometry isn't needed in the response
        "returnGeometry": "false",
    }

    response = requests.get(
        query_url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    # ArcGIS may return HTTP 200 even when
    # the query itself contains an error.
    if "error" in data:
        raise RuntimeError(
            f"Authority API error: {data['error']}"
        )

    features = data.get("features", [])

    # No authority found for supplied coordinates
    if not features:
        return {
            "found": False,
            "authority": None,
            "authority_ga": None
        }

    attributes = features[0]["attributes"]

    return {
        "found": True,
        "authority": attributes.get("ENG_NAME_VALUE"),
        "authority_ga": attributes.get("GLE_NAME_VALUE")
    }