export type AnalysisResult = {
  category: "street_light" | "illegal_dumping" | "electronic_waste" | "other";
  confidence?: number;
  description: string;
  authority?: string;
  nearest_asset?: string;
  distance_m?: number;
  facility?: { name: string; address: string; distance_km?: number };
  next_action: string;
  report?: string;
};

const mockStreetlight: AnalysisResult = {
  category: "street_light",
  confidence: 0.94,
  description: "Possible damaged or non-operational streetlight",
  authority: "Dublin City Council",
  nearest_asset: "Public Light 31140 · O'Connell Street Lower",
  distance_m: 20.3,
  next_action: "report",
  report: "A streetlight near the selected location appears to be damaged or non-operational. Nearest identified public-lighting asset: 31140.",
};

export async function analyseIssue(file: File, latitude: number, longitude: number): Promise<AnalysisResult> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!apiUrl) {
    await new Promise((resolve) => setTimeout(resolve, 900));
    return mockStreetlight;
  }

  const form = new FormData();
  form.append("photo", file);
  form.append("latitude", String(latitude));
  form.append("longitude", String(longitude));

  const response = await fetch(`${apiUrl}/api/analyse`, { method: "POST", body: form });
  if (!response.ok) throw new Error("We couldn't analyse this issue. Please try again.");
  return response.json();
}
