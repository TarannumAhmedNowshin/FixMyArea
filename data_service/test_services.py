from recycling import find_nearest_recycling_centre
from streetlights import find_nearest_streetlight
from authorities import find_local_authority


# Test location:
# Central Dublin / O'Connell Street area
LAT = 53.3498
LON = -6.2603


print("\n==============================")
print("FIXMYAREA DATA SERVICE TEST")
print("==============================")

print(f"\nTest location: {LAT}, {LON}")


# --------------------------------------------------
# 1. RECYCLING CENTRE TEST
# --------------------------------------------------

print("\n==============================")
print("RECYCLING TEST")
print("==============================")

try:
    recycling = find_nearest_recycling_centre(
        LAT,
        LON,
    )

    print("Name:", recycling["name"])
    print("Address:", recycling["address"])
    print("Eircode:", recycling["eircode"])
    print("Telephone:", recycling["telephone"])
    print("Email:", recycling["email"])
    print("Latitude:", recycling["latitude"])
    print("Longitude:", recycling["longitude"])
    print("Distance:", recycling["distance_km"], "km")

except Exception as error:
    print("Recycling test FAILED")
    print("Error:", error)


# --------------------------------------------------
# 2. STREETLIGHT TEST
# --------------------------------------------------

print("\n==============================")
print("STREETLIGHT TEST")
print("==============================")

try:
    streetlight = find_nearest_streetlight(
        LAT,
        LON,
    )

    print("ID:", streetlight.get("ID"))
    print("Site:", streetlight.get("site_name"))
    print("Unit Number:", streetlight.get("unit_no"))
    print("Unit Type:", streetlight.get("unit_type"))
    print("Latitude:", streetlight.get("latitude"))
    print("Longitude:", streetlight.get("longitude"))
    print("Distance:", streetlight.get("distance_m"), "metres")

except Exception as error:
    print("Streetlight test FAILED")
    print("Error:", error)


# --------------------------------------------------
# 3. LOCAL AUTHORITY TEST
# --------------------------------------------------

print("\n==============================")
print("LOCAL AUTHORITY TEST")
print("==============================")

try:
    authority = find_local_authority(
        LAT,
        LON,
    )

    print(authority)

except Exception as error:
    print("Local authority test FAILED")
    print("Error:", error)


print("\n==============================")
print("TESTING COMPLETE")
print("==============================")