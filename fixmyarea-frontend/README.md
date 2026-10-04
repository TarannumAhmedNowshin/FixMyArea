# FixMyArea Frontend

Next.js frontend for the FixMyArea hackathon POC.

## Run
npm install
npm run dev

By default the app uses a demo streetlight response. To connect FastAPI, copy `.env.example` to `.env.local` and set `NEXT_PUBLIC_API_URL`.

Expected backend endpoint: `POST /api/analyse` using multipart form fields `photo`, `latitude`, `longitude`.
