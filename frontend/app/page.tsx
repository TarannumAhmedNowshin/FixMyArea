"use client";

import { ChangeEvent, FormEvent, useState } from "react";

type Asset = {
  asset_id: string | null;
  location: string | null;
  latitude: number;
  longitude: number;
  distance_m: number;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [latitude, setLatitude] = useState("53.3498");
  const [longitude, setLongitude] = useState("-6.2603");
  const [photo, setPhoto] = useState<string | null>(null);
  const [asset, setAsset] = useState<Asset | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function choosePhoto(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    setPhoto(file ? URL.createObjectURL(file) : null);
    setAsset(null);
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
    setAsset(null);
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/nearest-streetlight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ latitude: Number(latitude), longitude: Number(longitude) }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail ?? "We couldn't look up this location.");
      setAsset(result as Asset);
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

          <label className={`upload-box ${photo ? "has-photo" : ""}`}>
            <input type="file" accept="image/*" capture="environment" onChange={choosePhoto} />
            {photo ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={photo} alt="Selected report" />
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
            {loading ? "Finding nearby assets…" : "Find the next step"}<span aria-hidden="true">→</span>
          </button>
          {error && <p className="error-message" role="alert">{error}</p>}

          {asset && (
            <section className="result-card" aria-live="polite">
              <div className="result-top"><span className="result-check">✓</span><span className="eyebrow">Nearby public lighting</span></div>
              <h3>{asset.location ?? "Streetlight asset"}</h3>
              <p>Asset {asset.asset_id ?? "identified"} · approximately <strong>{asset.distance_m} m</strong> away</p>
              <a target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${asset.latitude},${asset.longitude}`}>View on map <span>↗</span></a>
            </section>
          )}
          <p className="prototype-note">This prototype currently finds nearby lighting assets. Photo understanding and council reporting are coming next.</p>
        </form>
      </section>

      <footer><span>FIXMYAREA <b>·</b> DUBLIN</span><span>AI understands the issue. Local data helps find the next step.</span></footer>
    </main>
  );
}
