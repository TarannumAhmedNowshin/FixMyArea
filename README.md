# FixMyArea

The first working slice looks up the nearest public-lighting asset in
Dublin City Council's open dataset.

## Run the API

From the project root:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

To enable photo analysis, copy `.env.example` to `.env`, create an API key at
<https://platform.openai.com/api-keys>, and set `OPENAI_API_KEY` in `.env`.
Keep `.env` private and restart the backend after adding the key. The default
vision model is `gpt-6-luna`; change `OPENAI_MODEL` in `.env` to override it.

Then send a location:

```sh
curl -X POST http://127.0.0.1:8000/api/nearest-streetlight \
  -H 'Content-Type: application/json' \
  -d '{"latitude": 53.34, "longitude": -6.27}'
```

The response contains the nearest asset's identifier, location, coordinates,
and approximate distance in metres. The source dataset and attribution are
documented in [data/README.md](data/README.md).

## Run the web app

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. The page can use browser geolocation or entered
coordinates. It uploads the selected image and location to `/api/analyse`,
which classifies the image, checks whether its location is within the DCC
coverage polygons, and selects a deterministic next action. Streetlight reports
include the nearest public-lighting asset; dumping reports link to DCC's
Citizen Hub; electronic waste reports list nearby DCC recycling centres.
Reports are prepared for copying and are not submitted by the prototype. Data
sources, licensing, and geographic limitations are described in
[data/README.md](data/README.md).
