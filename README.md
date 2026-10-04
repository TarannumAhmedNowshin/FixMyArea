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
coordinates and calls the FastAPI nearest-streetlight endpoint. Photo
classification and official-service routing are later steps in the prototype.
