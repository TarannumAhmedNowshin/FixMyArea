import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FixMyArea — make your next step clear",
  description: "Find the right next step for problems in your area.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
