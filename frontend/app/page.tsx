"use client";

import { ChangeEvent, useEffect, useState } from "react";

type Coordinates = { latitude: number; longitude: number };
type Place = {
  asset_id?: string | null;
  location?: string | null;
  unit_no?: string | null;
  unit_type?: string | null;
  name?: string;
  address?: string;
  eircode?: string;
  telephone?: string;
  email?: string;
  latitude: number;
  longitude: number;
  distance_m: number;
};
type AnalysisResult = {
  category: "street_light" | "illegal_dumping" | "electronic_waste" | "other";
  label: string;
  confidence: number;
  visible_evidence: string;
  needs_more_information: boolean;
  route_status: string;
  next_action: string | null;
  message: string;
  authority: string | null;
  administrative_area: string | null;
  destination: { name: string; official_url: string; guidance: string } | null;
  asset: Place | null;
  facilities: Place[];
  draft_report: string | null;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const categories: Record<AnalysisResult["category"], string> = {
  street_light: "Streetlight issue",
  illegal_dumping: "Illegal dumping",
  electronic_waste: "Electronic waste",
  other: "Issue identified",
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [coords, setCoords] = useState<Coordinates>({ latitude: 53.3498, longitude: -6.2603 });
  const [locationStatus, setLocationStatus] = useState("Dublin city centre · edit coordinates or use your location");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function setPhoto(next: File) {
    setFile(next);
    setPreview(URL.createObjectURL(next));
    setResult(null);
    setError("");
  }

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    if (selected) setPhoto(selected);
  }

  async function chooseSample(name: string) {
    setError("");
    try {
      const response = await fetch(`/demo/${name}`);
      if (!response.ok) throw new Error("That demo image could not be loaded.");
      const blob = await response.blob();
      setPhoto(new File([blob], name, { type: blob.type || "image/jpeg" }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "That demo image could not be loaded.");
    }
  }

  function useLocation() {
    setError("");
    if (!navigator.geolocation) {
      setError("Location is not supported by this browser. Enter coordinates below.");
      return;
    }
    setLocationStatus("Finding your location…");
    navigator.geolocation.getCurrentPosition(
      ({ coords: location }) => {
        const next = { latitude: location.latitude, longitude: location.longitude };
        setCoords(next);
        setLocationStatus(`${next.latitude.toFixed(5)}, ${next.longitude.toFixed(5)}`);
      },
      () => {
        setLocationStatus("Location unavailable");
        setError("Please allow location access or enter the coordinates manually.");
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  async function analyse() {
    if (!file) {
      setError("Add a photo before analysing the issue.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("image", file);
      form.append("latitude", String(coords.latitude));
      form.append("longitude", String(coords.longitude));
      form.append("description", description);
      const response = await fetch(`${API_URL}/api/analyse`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) {
        const detail = typeof payload.detail === "string" ? payload.detail : "Check the selected photo and coordinates, then try again.";
        throw new Error(detail);
      }
      setResult(payload as AnalysisResult);
      setCopied(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The analysis service could not be reached.");
    } finally {
      setLoading(false);
    }
  }

  async function copyReport() {
    if (!result?.draft_report) return;
    try {
      await navigator.clipboard.writeText(result.draft_report);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setError("Clipboard access was blocked. Select and copy the report text instead.");
    }
  }

  function reset() {
    setResult(null);
    setFile(null);
    setPreview(null);
    setError("");
    setCopied(false);
  }

  if (result) return <ResultView result={result} preview={preview} onBack={reset} onCopy={copyReport} copied={copied} />;

  return (
    <main>
      <nav className="nav shell">
        <a href="#top" className="brand"><span className="brand-mark">⌖</span>FixMyArea</a>
        <span className="badge">Build for Ireland · Dublin prototype</span>
      </nav>
      <section className="hero shell" id="top">
        <div className="eyebrow"><span aria-hidden="true">✦</span> AI + Irish public data</div>
        <h1>See it. Send it.<br /><span>We’ll route it.</span></h1>
        <p className="lede">Photograph a public-space problem and FixMyArea finds the right next action, so you can focus on what needs attention.</p>
        <div className="flow"><span>See</span><b>→</b><span>Capture</span><b>→</b><span>Understand</span><b>→</b><span>Locate</span><b>→</b><span>Act</span></div>
      </section>

      <section className="workspace shell" aria-label="Create a report">
        <div className="panel">
          <div className="step"><span>1</span><div><h2>Show us the problem</h2><p>Add a clear photo. A short note can help explain what you noticed.</p></div></div>
          <label className={`dropzone ${preview ? "has-image" : ""}`}>
            {preview ? <img src={preview} alt="Selected issue" /> : <><div className="upload-icon">＋</div><strong>Upload a photo</strong><small>JPG, PNG, WEBP or GIF · up to 10 MB</small></>}
            <input type="file" accept="image/jpeg,image/png,image/webp,image/gif" capture="environment" onChange={chooseFile} />
          </label>
          {file && <div className="file-row"><span aria-hidden="true">✓</span><span>{file.name}</span><label>Change<input type="file" accept="image/*" onChange={chooseFile} /></label></div>}
          <div className="demo-samples"><span>Try a demo sample</span><div>
            <button type="button" onClick={() => void chooseSample("streetlight.jpeg")}>Streetlight</button>
            <button type="button" onClick={() => void chooseSample("dumping.png")}>Dumping</button>
            <button type="button" onClick={() => void chooseSample("ewaste.png")}>E-waste</button>
          </div></div>
          <label className="description-field">What did you notice? <span>Optional</span>
            <textarea rows={2} maxLength={1000} value={description} onChange={event => setDescription(event.target.value)} placeholder="For example, the light has been out for a few nights." />
          </label>
        </div>

        <div className="panel">
          <div className="step"><span>2</span><div><h2>Where is it?</h2><p>Location helps find the right local service or nearby public asset.</p></div></div>
          <button className="location-button" type="button" onClick={useLocation}><span className="location-icon">◎</span><span><strong>Use my current location</strong><small>{locationStatus}</small></span></button>
          <div className="coordinate-grid">
            <label>Latitude<input type="number" step="any" min="-90" max="90" value={coords.latitude} onChange={event => setCoords({ ...coords, latitude: Number(event.target.value) })} /></label>
            <label>Longitude<input type="number" step="any" min="-180" max="180" value={coords.longitude} onChange={event => setCoords({ ...coords, longitude: Number(event.target.value) })} /></label>
          </div>
          <button className="analyse-button" disabled={loading || !file} onClick={() => void analyse()}>{loading ? <><span className="spinner" />Analysing issue…</> : <>Analyse issue <span>→</span></>}</button>
          {error && <p className="error" role="alert">{error}</p>}
          <p className="privacy">Your photo is analyzed by a local model on the backend, not sent to an AI inference API. Location is used for nearby public-data lookup.</p>
        </div>
      </section>

      <section className="supported shell"><p>Currently routes</p><div><span>⚡ Streetlights</span><span>⌖ Illegal dumping</span><span>♻ E-waste</span></div></section>
    </main>
  );
}

function ResultView({ result, preview, onBack, onCopy, copied }: { result: AnalysisResult; preview: string | null; onBack: () => void; onCopy: () => void; copied: boolean }) {
  const title = categories[result.category] ?? categories.other;
  const routeReady = result.route_status === "ready_to_report" || result.route_status === "ready_to_recycle";
  return (
    <main className="result-page">
      <nav className="nav shell"><a href="#top" className="brand"><span className="brand-mark">⌖</span>FixMyArea</a><button className="back-button" onClick={onBack}><span aria-hidden="true">←</span> New report</button></nav>
      <section className="result-shell shell">
        <div className={`success ${routeReady ? "" : "notice"}`}><span>{routeReady ? "✓" : "i"}</span>{routeReady ? "Analysis complete" : "Analysis complete · routing needs attention"}</div>
        <h1>{title}</h1>
        <p className="result-description">{result.label}</p>
        <div className="result-grid">
          <div className="evidence-card">{preview && <img src={preview} alt="Submitted issue" />}<div><small>Local image match · {Math.round(result.confidence * 100)}% relative score</small><strong>{title}</strong><span>{result.visible_evidence}</span></div></div>
          <div className="details-card">
            <Detail label="Responsible authority" value={result.authority ? `${result.authority}${result.administrative_area ? ` · ${result.administrative_area}` : ""}` : "Not identified for this location"} />
            {result.asset && <Detail label="Nearest streetlight" value={`${result.asset.location ?? "Public lighting asset"} · ${result.asset.distance_m.toFixed(0)} m${result.asset.asset_id ? ` · asset ${result.asset.asset_id}` : ""}`} />}
            {result.asset && (result.asset.unit_no || result.asset.unit_type) && <Detail label="Asset details" value={[result.asset.unit_no && `Unit ${result.asset.unit_no}`, result.asset.unit_type].filter(Boolean).join(" · ")} />}
            {result.asset && <a className="map-link" target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${result.asset.latitude},${result.asset.longitude}`}>Open asset on map ↗</a>}
            {result.needs_more_information && <p className="more-info">The photo may need a closer view or more detail for a confident match.</p>}
            <p className="route-message">{result.message}</p>
          </div>
        </div>

        {result.facilities.length > 0 && <div className="facility-section"><h2>Nearby WEEE recycling centres</h2><div className="facility-grid">{result.facilities.map((place, index) => <article className="facility-card" key={`${place.name}-${index}`}><strong>{place.name}</strong><span>{place.address}{place.eircode ? ` · ${place.eircode}` : ""}</span><small>About {place.distance_m.toFixed(0)} m away</small><div>{place.telephone && <a href={`tel:${place.telephone}`}>Call</a>}{place.email && <a href={`mailto:${place.email}`}>Email</a>}<a target="_blank" rel="noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${place.latitude},${place.longitude}`}>Directions ↗</a></div></article>)}</div></div>}

        {result.destination && <div className="action-card"><div><small>Recommended next action</small><h2>{result.next_action === "recycle" ? "Take it to a recycling centre" : "Your report is ready"}</h2><p>{result.destination.guidance}</p></div><a href={result.destination.official_url} target="_blank" rel="noreferrer">{result.destination.name} ↗</a></div>}
        {result.draft_report && <div className="report-card"><div><small>Report draft</small><p>{result.draft_report}</p></div><button onClick={() => void onCopy()}>{copied ? "✓ Copied" : "Copy report"}</button></div>}
        <p className="source-note">AI identifies the issue. Public datasets help find the relevant service, asset or facility.</p>
      </section>
    </main>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return <div className="detail"><small>{label}</small><strong>{value}</strong></div>;
}
