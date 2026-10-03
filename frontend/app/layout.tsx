import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TripPilot — Your AI Travel Concierge",
  description:
    "Plan intelligent, personalized journeys with TripPilot.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}