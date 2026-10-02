"use client";

import { useState } from "react";
import type { Trip } from "../../lib/api";

type Day = Record<string, unknown>;

const genericTravelImages = [
  "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1800&q=85",
  "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1800&q=85",
  "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1800&q=85",
];

function destinationImage(trip: Trip, destination: string) {
  const source = trip as Trip & { image_url?: unknown; imageUrl?: unknown; destination_image?: unknown };
  const provided = [source.image_url, source.imageUrl, source.destination_image].find((value) => typeof value === "string" && value.trim());
  if (provided) return provided as string;
  const hash = [...destination].reduce((total, character) => total + character.charCodeAt(0), 0);
  return genericTravelImages[hash % genericTravelImages.length];
}

const value = (v: unknown) => typeof v === "string" || typeof v === "number" ? String(v) : "";
const money = (v: number | null | undefined) => v == null ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(v);
const date = (v?: string | null) => v ? new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(`${v}T00:00:00`)) : "Dates flexible";

function research(title: string, count: number, unavailable: string) { return <article className="research-card"><div className="section-kicker">{title}</div>{count ? <strong>{count} options found</strong> : <><strong>{unavailable}</strong><p>Your itinerary is still available.</p></>}</article>; }

function TripNotes({ violations, warnings }: { violations: string[]; warnings: string[] }) {
  if (!violations.length && !warnings.length) return null;
  return <section className="trip-notes" aria-label="Trip notes">
    <div className="section-heading"><div><div className="section-kicker">TRAVEL NOTES</div><h2>Trip notes</h2></div><span>Worth knowing</span></div>
    <div className="trip-notes-grid">
      {violations.length > 0 && <article className="trip-note trip-note-warning"><strong>Some constraints need attention</strong><p>This itinerary may not fully satisfy one or more of your requested constraints.</p><ul>{violations.map((notice, index) => <li key={`violation-${index}`}>{notice}</li>)}</ul></article>}
      {warnings.length > 0 && <article className="trip-note"><strong>Research notes</strong><p>These non-blocking notices reflect the data available while planning.</p><ul>{warnings.map((notice, index) => <li key={`warning-${index}`}>{notice}</li>)}</ul></article>}
    </div>
  </section>;
}

export function TripPage({ trip, onBack }: { trip: Trip; onBack: () => void }) {
  const [openDay, setOpenDay] = useState(0);
  const days = Array.isArray((trip.itinerary as { days?: Day[] } | null)?.days) ? (trip.itinerary as { days: Day[] }).days : [];
  const weather = trip.weather_data as Record<string, unknown>;
  const destination = trip.destination || "Your destination";
  const violations = trip.constraint_violations ?? [];
  const warnings = trip.tool_warnings ?? [];
  return <div className="trip-page">
    <button className="back-link" onClick={onBack}>← Back to planning</button>
    <section className="trip-intro"><div><div className="section-kicker">DESTINATION</div><h1>{destination}</h1><p>{trip.trip_duration_days ?? "—"} days · {trip.travelers ?? "—"} travelers · {date(trip.start_date)}{trip.end_date ? ` — ${date(trip.end_date)}` : ""}</p></div><div className="concierge-pill"><span className="status-dot" /> TripPilot concierge<br /><small>Ready to help refine the details</small></div></section>
    <div className="destination-image" style={{ backgroundImage: `url(${destinationImage(trip, destination)})` }} role="img" aria-label={`${destination} destination`} />
    <section className="summary-bar"><div><span>Estimated cost</span><strong>{money(trip.estimated_cost)}</strong></div><div><span>Budget</span><strong>{money(trip.budget)}</strong></div><div><span>Travelers</span><strong>{trip.travelers ?? "—"}</strong></div><div><span>Duration</span><strong>{trip.trip_duration_days ?? "—"} days</strong></div><div><span>Weather</span><strong>{weather.warning ? "Check forecast" : "Available"}</strong></div></section>
    <TripNotes violations={violations} warnings={warnings} />
    <div className="trip-layout"><main><div className="section-heading"><div><div className="section-kicker">THE PLAN</div><h2>Itinerary</h2></div><span>{days.length} days mapped out</span></div><div className="itinerary-list">{days.length ? days.map((day, index) => { const activities = Array.isArray(day.activities) ? day.activities : [...(Array.isArray(day.morning) ? day.morning : []), ...(Array.isArray(day.afternoon) ? day.afternoon : []), ...(Array.isArray(day.evening) ? day.evening : [])]; return <article className={`day-row ${openDay === index ? "is-open" : ""}`} key={index}><button onClick={() => setOpenDay(openDay === index ? -1 : index)} aria-expanded={openDay === index}><span className="day-number">DAY {String(index + 1).padStart(2, "0")}</span><span><strong>{value(day.title) || `Day ${index + 1}`}</strong><small>{value(day.summary)}</small></span><span aria-hidden="true">{openDay === index ? "−" : "+"}</span></button>{openDay === index && <div className="day-details">{activities.map((activity, activityIndex) => <p key={activityIndex}>{value(activity)}</p>)}</div>}</article>; }) : <p className="empty-state">Your itinerary details are being prepared.</p>}</div></main><aside><div className="section-kicker">RESEARCH SNAPSHOT</div><div className="research-grid">{research("Flights", trip.flight_data.length, "Live flight data unavailable")}{research("Hotels", trip.hotel_data.length, "Hotel research unavailable")}{research("Places", trip.attraction_data.length, "Attraction research unavailable")}</div></aside></div>
  </div>;
}

