# Public lighting data

The first lookup expects a point dataset from Dublin City Council's public
lighting open data. The API reads a GeoJSON file at
`data/streetlights.geojson` by default. Set `FIXMYAREA_STREETLIGHTS` to a CSV,
JSON, or GeoJSON path to use another export.

Source: [Public Lighting DCC](https://data.gov.ie/dataset/street-lighting-dublin-city),
published by Dublin City Council under CC BY 4.0. The dataset description says
it contains public-lighting asset locations and latitude/longitude, and includes
DCC, ESB Networks, and LUAS assets within the DCC administrative area.

Before using an export, check that its coordinates are WGS84 latitude and
longitude. GeoJSON must use standard `[longitude, latitude]` point coordinates;
CSV must have latitude and longitude (or `lat` and `lon`) columns. Keep the
downloaded source file in this directory and retain its attribution.

## DCC coverage polygons

`dcc_5committeeareas_2019_2157.geojson` contains five Dublin City Council
administrative-area polygons, published by Dublin City Council under Creative
Commons Attribution. Its geometries use Irish Transverse Mercator (EPSG:2157);
the backend transforms submitted WGS84 coordinates before checking them. This
older administrative-area dataset is used as the POC's Dublin City coverage
proxy, so locations outside the polygons are reported as unsupported rather
than assigned to another authority.

Source: [Administrative Areas DCC](https://data.smartdublin.ie/dataset/administrative-areas-dcc).

## Recycling-centre data

`recycling-centers-dcc.geojson` contains the three DCC recycling-centre
locations, addresses, and Eircodes. Dublin City Council's current WEEE guidance
says household electrical and electronic equipment is accepted at these
centres. Opening hours are not embedded in this dataset, so the app links to
the Council's current information page instead of displaying hours from a
static export.

Dataset source: [Recycling Centers DCC](https://data.gov.ie/en_GB/dataset/recycling-centers-dcc),
published by Dublin City Council under CC BY 4.0.

Service guidance: [Electrical and Electronic Recycling](https://www.dublincity.ie/waste-and-recycling/find-out-about-recycling/electrical-and-electronic-recycling)
and [Learn About Bring Centres](https://www.dublincity.ie/waste-and-recycling/find-out-about-recycling/learn-about-bring-centres).

## Verified reporting routes

The deterministic mappings in `routing_rules.json` point to Dublin City
Council's official streetlight-fault information page, the Council's Illegal
Dumping Citizen Hub form, and the Council's WEEE recycling guidance. The
classifier returns an issue category only; this file and the geographic/data
lookups select the next action.
