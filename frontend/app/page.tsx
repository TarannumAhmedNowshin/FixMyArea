"use client";

import { ChangeEvent, FormEvent, useState } from "react";

type NearbyPlace = {
  asset_id: string | null;
  location: string | null;
  latitude: number;
  longitude: number;
  distance_m: number;
  name?: string;
  address?: string;
  eircode?: string;
};

type Destination = { name: string; official_url: string; guidance: string };

type Analysis = {
  category: "street_light" | "illegal_dumping" | "electronic_waste" | "other";
  label: string;
  confidence: number;
  visible_evidence: string;
  needs_more_information: boolean;
  route_status: string;
  message: string;
  authority: string | null;
  administrative_area: string | null;
  destination: Destination | null;
  asset: NearbyPlace | null;
  facilities: NearbyPlace[];
  draft_report: string | null;
};

const categoryLabels: Record<Analysis["category"], string> = {
  street_light: "Streetlight issue",
  illegal_dumping: "Possible illegal dumping",
  electronic_waste: "Electronic waste",
  other: "Other issue",
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [latitude, setLatitude] = useState("53.3498");
  const [longitude, setLongitude] = useState("-6.2603");
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function choosePhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (photoPreview) URL.revokeObjectURL(photoPreview);
    setPhotoFile(file ?? null);
    setPhotoPreview(file ? URL.createObjectURL(file) : null);
    setAnalysis(null);
    setError("");
  }

  function useMyLocation() {
    setError("");
    if (!navigator.geolocation) {
      setError("Location is not available in this browser. Enter coordinates instead.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setLatitude(coords.latitude.toFixed(6));
        setLongitude(coords.longitude.toFixed(6));
      },
      () => setError("We couldn't get your location. Check browser permissions or enter it manually."),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function analyse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAnalysis(null);
    setError("");
    if (!photoFile) {
      setError("Add a photo before analysing the issue.");
      return;
    }
    setLoading(true);
    try {
      const form = new FormData();
      form.append("image", photoFile);
      form.append("latitude", latitude);
      form.append("longitude", longitude);
      const response = await fetch(`${API_URL}/api/analyse`, {
        method: "POST",
        body: form,
      });
      const result = await response.json();
      if (!response.ok) {
        const detail = Array.isArray(result.detail) ? "Check the selected photo and coordinates." : result.detail;
        throw new Error(detail ?? "We couldn't analyse this report.");
      }
      setAnalysis(result as Analysis);
      setCopied(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The service could not be reached.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="FixMyArea home">
          <span className="brand-mark">f</span><span>fixmyarea</span>
        </a>
        <span className="availability"><span /> Dublin prototype</span>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow">A clearer way to take action</p>
          <h1>See something<br />that needs attention?</h1>
          <p className="intro">Start with a photo and a place. We’ll help you figure out the next step.</p>
          <div className="step-line"><span>01</span><i /><span>02</span><i /><span>03</span></div>
          <div className="step-labels"><span>Capture</span><span>Locate</span><span>Take action</span></div>
        </div>

        <form className="report-card" onSubmit={analyse}>
          <div className="card-heading">
            <div><p className="eyebrow">New report</p><h2>Show us what’s wrong</h2></div>
            <span className="card-icon">↗</span>
          </div>

          <label className={`upload-box ${photoPreview ? "has-photo" : ""}`}>
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" capture="environment" onChange={choosePhoto} />
            {photoPreview ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={photoPreview} alt="Selected report" />
            ) : (
              <span className="upload-prompt">
                <span className="upload-icon">＋</span>
                <strong>Add a photo</strong>
                <small>Take a photo or choose one from your device</small>
              </span>
            )}
          </label>

          <div className="location-heading">
            <div><p className="eyebrow">Where is it?</p><strong>Choose the problem location</strong></div>
            <button className="text-button" type="button" onClick={useMyLocation}>◎ Use my location</button>
          </div>
          <div className="coordinate-grid">
            <label>Latitude<input type="number" step="any" min="-90" max="90" inputMode="decimal" value={latitude} onChange={e => setLatitude(e.target.value)} required /></label>
            <label>Longitude<input type="number" step="any" min="-180" max="180" inputMode="decimal" value={longitude} onChange={e => setLongitude(e.target.value)} required /></label>
          </div>

          <button className="submit-button" type="submit" disabled={loading}>
            {loading ? "Analysing your photo…" : "Analyse this issue"}<span aria-hidden="true">→</span>
          </button>
          {error && <p className="error-message" role="alert">{error}</p>}

          {analysis && (
            <section className="result-card" aria-live="polite">
              <div className="result-top"><span className="result-check">✓</span><span className="eyebrow">Photo analysis · {Math.round(analysis.confidence * 100)}% confidence</span></div>
              <h3>{categoryLabels[analysis.category]}</h3>
              <p>{analysis.label}</p>
              <p className="evidence">Visible evidence: {analysis.visible_evidence}</p>
              {analysis.authority && <p className="authority-line">Responsible authority: <strong>{analysis.authority}</strong>{analysis.administrative_area && ` · ${analysis.administrative_area}`}</p>}
              {analysis.asset && (
                <div className="asset-result">
                  <strong>{analysis.asset.location ?? "Nearby streetlight"}</strong>
                  <span>Asset {analysis.asset.asset_id ?? "identified"} · approximately {analysis.asset.distance_m} m away</span>
                  <a target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${analysis.asset.latitude},${analysis.asset.longitude}`}>View asset on map <span>↗</span></a>
                </div>
              )}
              {analysis.facilities.length > 0 && (
                <div className="facility-list">
                  <strong>Nearby WEEE recycling centres</strong>
                  {analysis.facilities.map(place => (
                    <div className="facility-item" key={place.name}>
                      <b>{place.name}</b>
                      <span>{place.address}{place.eircode ? ` · ${place.eircode}` : ""}</span>
                      <span>About {place.distance_m} m away</span>
                      <a target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`}>Get directions <span>↗</span></a>
                    </div>
                  ))}
                </div>
              )}
              {analysis.draft_report && (
                <div className="draft-report">
                  <strong>Report draft</strong>
                  <p>{analysis.draft_report}</p>
                  <button type="button" onClick={() => { navigator.clipboard.writeText(analysis.draft_report!); setCopied(true); }}>
                    {copied ? "Copied" : "Copy report"}
                  </button>
                </div>
              )}
              {analysis.destination && (
                <div className="destination-block">
                  <p>{analysis.destination.guidance}</p>
                  <a className="destination-link" target="_blank" rel="noreferrer" href={analysis.destination.official_url}>{analysis.destination.name}<span>↗</span></a>
                </div>
              )}
              <p className="route-message">{analysis.message}</p>
            </section>
          )}
          <p className="prototype-note">Photos are analysed by OpenAI. Location routing uses Dublin City Council data and official service links. Reports are prepared here; they are not submitted automatically.</p>
        </form>
      </section>

      <footer><span>FIXMYAREA <b>·</b> DUBLIN</span><span>AI understands the issue. Local data helps find the next step.</span></footer>
    </main>
  );
}
