import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FixMyArea | See it. Send it. Sort it.",
  description: "Turn public-space problems into the right next action using AI, location and Irish public data.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
