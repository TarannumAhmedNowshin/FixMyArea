"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { analyseIssue, AnalysisResult } from "../lib/api";
import { ArrowLeft, CheckCircle2, Copy, LocateFixed, MapPin, Recycle, Sparkles, Upload, Zap } from "lucide-react";

type Coordinates = { latitude: number; longitude: number };

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [coords, setCoords] = useState<Coordinates | null>(null);
  const [locationStatus, setLocationStatus] = useState("No location selected");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview); }, [preview]);

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0];
    if (!selected) return;
    if (preview) URL.revokeObjectURL(preview);
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
    setResult(null);
    setError("");
  }

  function useLocation() {
    setError("");
    if (!navigator.geolocation) return setError("Location is not supported by this browser.");
    setLocationStatus("Finding your location…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ latitude: position.coords.latitude, longitude: position.coords.longitude });
        setLocationStatus(`${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`);
      },
      () => { setLocationStatus("Location unavailable"); setError("Please allow location access and try again."); },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  async function analyse() {
    if (!file || !coords) return setError("Add a photo and select the problem location first.");
    setLoading(true); setError("");
    try { setResult(await analyseIssue(file, coords.latitude, coords.longitude)); }
    catch (e) { setError(e instanceof Error ? e.message : "Something went wrong."); }
    finally { setLoading(false); }
  }

  async function copyReport() {
    const text = result?.report || result?.description;
    if (!text) return;
    await navigator.clipboard.writeText(text);
    setCopied(true); setTimeout(() => setCopied(false), 1800);
  }

  function reset() { setResult(null); setFile(null); setPreview(null); setCoords(null); setLocationStatus("No location selected"); setError(""); }

  if (result) return <ResultView result={result} preview={preview} onBack={reset} onCopy={copyReport} copied={copied} />;

  return (
    <main>
      <nav className="nav shell"><div className="brand"><span className="brandMark"><MapPin size={18}/></span>FixMyArea</div><span className="badge">Build for Ireland</span></nav>
      <section className="hero shell">
        <div className="eyebrow"><Sparkles size={15}/> AI + Irish public data</div>
        <h1>See it. Send it.<br/><span>We’ll route it.</span></h1>
        <p className="lede">Photograph a public-space problem and FixMyArea finds the right next action—without making you figure out which service is responsible.</p>
        <div className="flow"><span>See</span><b>→</b><span>Capture</span><b>→</b><span>Understand</span><b>→</b><span>Locate</span><b>→</b><span>Act</span></div>
      </section>

      <section className="workspace shell">
        <div className="panel">
          <div className="step"><span>1</span><div><h2>Show us the problem</h2><p>Upload a clear photo of what you can see.</p></div></div>
          <label className={`dropzone ${preview ? "hasImage" : ""}`}>
            {preview ? <img src={preview} alt="Selected issue"/> : <><div className="uploadIcon"><Upload size={28}/></div><strong>Upload a photo</strong><small>JPG, PNG or WEBP</small></>}
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={chooseFile}/>
          </label>
          {file && <div className="fileRow"><CheckCircle2 size={17}/><span>{file.name}</span><label>Change<input type="file" accept="image/*" onChange={chooseFile}/></label></div>}
        </div>

        <div className="panel">
          <div className="step"><span>2</span><div><h2>Where is it?</h2><p>We use this only to find the relevant public service or asset.</p></div></div>
          <button className="locationButton" onClick={useLocation}><LocateFixed size={21}/><div><strong>Use my current location</strong><small>{locationStatus}</small></div></button>
          {coords && <div className="locationOk"><CheckCircle2 size={17}/> Location ready</div>}
          <button className="analyse" disabled={loading || !file || !coords} onClick={analyse}>{loading ? <><span className="spinner"/>Analysing issue…</> : <>Analyse issue <span>→</span></>}</button>
          {error && <p className="error">{error}</p>}
          <p className="privacy">Your photo and location are used only to analyse this report.</p>
        </div>
      </section>

      <section className="supported shell"><p>Currently routes</p><div><span><Zap size={16}/> Streetlights</span><span><MapPin size={16}/> Illegal dumping</span><span><Recycle size={16}/> E-waste</span></div></section>
    </main>
  );
}

function ResultView({ result, preview, onBack, onCopy, copied }: { result: AnalysisResult; preview: string | null; onBack: () => void; onCopy: () => void; copied: boolean }) {
  const eWaste = result.category === "electronic_waste";
  const dumping = result.category === "illegal_dumping";
  const title = eWaste ? "Electronic waste" : dumping ? "Illegal dumping" : result.category === "street_light" ? "Streetlight issue" : "Issue identified";
  return <main className="resultPage"><nav className="nav shell"><div className="brand"><span className="brandMark"><MapPin size={18}/></span>FixMyArea</div><button className="back" onClick={onBack}><ArrowLeft size={17}/> New report</button></nav>
    <section className="resultShell shell">
      <div className="success"><CheckCircle2 size={18}/> Analysis complete</div><h1>{title}</h1><p className="resultDescription">{result.description}</p>
      <div className="resultGrid">
        <div className="evidenceCard">{preview && <img src={preview} alt="Submitted issue"/>}<div><small>AI classification</small><strong>{title}</strong>{result.confidence && <span>{Math.round(result.confidence * 100)}% confidence</span>}</div></div>
        <div className="detailsCard">
          {result.authority && <Detail label="Responsible authority" value={result.authority}/>} 
          {result.nearest_asset && <Detail label="Nearest public asset" value={result.nearest_asset}/>} 
          {result.distance_m !== undefined && <Detail label="Distance from location" value={`${result.distance_m} metres`}/>} 
          {result.facility && <><Detail label="Nearest recycling centre" value={result.facility.name}/><Detail label="Address" value={result.facility.address}/>{result.facility.distance_km !== undefined && <Detail label="Distance" value={`${result.facility.distance_km} km`}/>}</>}
        </div>
      </div>
      <div className="actionCard"><div><small>Recommended next action</small><h2>{eWaste ? "Take it to the appropriate recycling service" : "Your report is ready"}</h2><p>{eWaste ? "Check accepted materials before travelling to the facility." : "We’ve combined the issue, location and public-data result into a useful report."}</p></div><button onClick={onCopy}><Copy size={18}/>{copied ? "Copied" : "Copy report"}</button></div>
      <p className="sourceNote">AI identifies the issue. Verified public data determines the place, asset or service.</p>
    </section>
  </main>;
}

function Detail({ label, value }: { label: string; value: string }) { return <div className="detail"><small>{label}</small><strong>{value}</strong></div>; }
