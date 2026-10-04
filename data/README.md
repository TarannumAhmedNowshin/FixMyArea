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
