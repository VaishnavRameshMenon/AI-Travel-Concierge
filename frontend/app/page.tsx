"use client";

import { CSSProperties, useEffect, useMemo, useState } from "react";
import {
  generateTrip,
  getTrip,
  listTrips,
  refineTrip,
  type TripDetail,
  type TripResponse,
  type TripSummary,
} from "../lib/api";

type Trip = TripResponse | TripDetail;
type Obj = Record<string, any>;

const DESTINATION_IMAGES: Record<string, string> = {
  tokyo: "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1800&q=85",
  kyoto: "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1800&q=85",
  bali: "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1800&q=85",
  goa: "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1800&q=85",
  switzerland: "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1800&q=85",
  paris: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1800&q=85",
  london: "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1800&q=85",
  default: "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1800&q=85",
};

const DAY_IMAGES: Record<string, string[]> = {
  tokyo: [
    "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1528360983277-13d401cdc186?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1513407030348-c983a97b98d8?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1503899036084-c55cdd92da26?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1542051841857-5f90071e7989?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1492571350019-22de08371fd3?auto=format&fit=crop&w=1200&q=82",
  ],
  default: [
    "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1470770841072-f978cf4d019e?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=82",
    "https://images.unsplash.com/photo-1494783367193-149034c05e8f?auto=format&fit=crop&w=1200&q=82",
  ],
};

const PLANNING_STAGES = [
  "Understanding your travel request",
  "Researching destination information",
  "Checking flights, stays & weather",
  "Building your day-by-day itinerary",
  "Validating your trip constraints",
];

function str(v: any): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "string" || typeof v === "number") return String(v);
  if (typeof v === "boolean") return v ? "Yes" : "No";
  if (Array.isArray(v)) return v.map(str).filter(Boolean).join(", ");
  if (typeof v === "object") {
    for (const k of ["name", "title", "description", "text", "value", "location", "city", "summary"]) {
      if (v[k] !== undefined && v[k] !== null) {
        const s = str(v[k]);
        if (s) return s;
      }
    }
    return Object.entries(v).slice(0, 4).map(([k, x]) => `${pretty(k)}: ${str(x)}`).join(" · ");
  }
  return "";
}

function pretty(k: string): string {
  return k.replace(/_/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2").replace(/\b\w/g, c => c.toUpperCase());
}

function money(v: any): string {
  const n = Number(v);
  return Number.isFinite(n) ? `₹${Math.round(n).toLocaleString("en-IN")}` : "—";
}

function flag(v: any): boolean {
  return v === true || v === "true" || v === "yes" || v === 1;
}

function arrayOf(v: any): Obj[] {
  return Array.isArray(v) ? v.filter(x => x && typeof x === "object") : [];
}

function destinationImage(destination?: string | null): string {
  const d = (destination || "").toLowerCase();
  const key = Object.keys(DESTINATION_IMAGES).find(k => k !== "default" && d.includes(k));
  return DESTINATION_IMAGES[key || "default"];
}

function dayImage(destination: string | null | undefined, index: number): string {
  const d = (destination || "").toLowerCase();
  const key = Object.keys(DAY_IMAGES).find(k => k !== "default" && d.includes(k)) || "default";
  const images = DAY_IMAGES[key];
  return images[index % images.length];
}

function mapsUrl(name: string, destination?: string | null): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${name} ${destination || ""}`)}`;
}

function externalStyle(): CSSProperties {
  return {
    display: "inline-flex", alignItems: "center", gap: 6, marginTop: 12,
    padding: "8px 12px", border: "1px solid #d9e0d9", borderRadius: 999,
    color: "#285c45", background: "#f8faf7", fontSize: 12, fontWeight: 700,
    textDecoration: "none",
  };
}

function placeLink(place: Obj, destination?: string | null) {
  const website = str(place.website);
  if (website) return { href: website, label: "Learn more" };
  const wiki = str(place.wikipedia);
  if (wiki) return { href: wiki, label: "Read more" };
  const maps = str(place.maps_url);
  if (maps) return { href: maps, label: "Open in Maps" };
  return { href: mapsUrl(str(place.name) || "Attraction", destination), label: "Open in Maps" };
}

function flightSearchUrl(flight: Obj, trip: Trip): string | null {
  if (str(flight.search_url)) return str(flight.search_url);
  const segments = arrayOf(flight.segments);
  const first = segments[0] || {};
  const last = segments[segments.length - 1] || first;
  const origin = str(first.departure_airport) || str(first.departure?.airport_code) || str(first.departure?.airport);
  const destination = str(last.arrival_airport) || str(last.arrival?.airport_code) || str(last.arrival?.airport);
  if (!origin || !destination || !trip.start_date) return null;
  let q = `Flights from ${origin} to ${destination} on ${trip.start_date}`;
  if (trip.end_date) q += ` returning ${trip.end_date}`;
  if (trip.travelers) q += ` ${trip.travelers} passengers`;
  return `https://www.google.com/travel/flights?q=${encodeURIComponent(q)}&hl=en&gl=in&curr=INR`;
}

function getDays(trip: Trip): Obj[] {
  const source = trip.itinerary?.days;
  if (Array.isArray(source)) return arrayOf(source);
  if (source && typeof source === "object") {
    return Object.entries(source)
      .filter(([k]) => /day\s*\d+|\d+/.test(k.toLowerCase()))
      .sort(([a], [b]) => (Number(a.match(/\d+/)?.[0] || 0) - Number(b.match(/\d+/)?.[0] || 0)))
      .map(([, v]) => (v && typeof v === "object" ? v as Obj : { description: v }));
  }
  return [];
}

function activities(day: Obj): string[] {
  const keys = ["activities", "activity", "morning", "afternoon", "evening", "things_to_do", "highlights"];
  const out: string[] = [];
  for (const k of keys) {
    const v = day[k];
    if (Array.isArray(v)) out.push(...v.map(str).filter(Boolean));
    else if (v) { const s = str(v); if (s) out.push(s); }
  }
  if (!out.length) {
    for (const [k, v] of Object.entries(day)) {
      if (!["title", "name", "description", "summary", "theme", "day"].includes(k)) {
        const s = str(v); if (s) out.push(s);
      }
    }
  }
  return [...new Set(out)].slice(0, 8);
}

function weatherRows(weather: any): Obj[] {
  if (!weather || typeof weather !== "object") return [];
  const daily = weather.daily;
  if (daily && !Array.isArray(daily) && typeof daily === "object" && Array.isArray(daily.time)) {
    const dates = daily.time as any[];
    return dates.map((date, i) => ({
      date,
      temperature_max: daily.temperature_2m_max?.[i],
      temperature_min: daily.temperature_2m_min?.[i],
      precipitation_probability: daily.precipitation_probability_max?.[i],
    }));
  }
  for (const k of ["daily", "forecast", "forecasts", "days", "weather"]) {
    const rows = arrayOf(weather[k]);
    if (rows.length) return rows;
  }
  return [];
}

function segmentAirport(segment: Obj, side: "departure" | "arrival"): string {
  const flat = side === "departure" ? segment.departure_airport : segment.arrival_airport;
  const nested = segment[side];
  return str(flat) || str(nested?.airport_code) || str(nested?.airport) || "—";
}

function segmentTime(segment: Obj, side: "departure" | "arrival"): string {
  const flat = side === "departure" ? segment.departure_time : segment.arrival_time;
  const nested = segment[side];
  return str(flat) || str(nested?.time) || "—";
}

function durationText(minutes: any): string {
  const n = Number(minutes);
  if (!Number.isFinite(n) || n <= 0) return "—";
  const h = Math.floor(n / 60), m = n % 60;
  return `${h}h ${m}m`;
}

export default function HomePage() {
  const [query, setQuery] = useState("");
  const [trip, setTrip] = useState<Trip | null>(null);
  const [savedTrips, setSavedTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState("");
  const [planningStage, setPlanningStage] = useState(0);
  const [refinement, setRefinement] = useState("");
  const [refining, setRefining] = useState(false);

  const days = useMemo(() => trip ? getDays(trip) : [], [trip]);

  async function loadHistory() {
    try {
      const r = await listTrips();
      setSavedTrips(r.trips || []);
    } catch { } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => { void loadHistory(); }, []);

  useEffect(() => {
    if (!loading) return;
    setPlanningStage(0);
    const timer = window.setInterval(() => setPlanningStage(x => Math.min(x + 1, PLANNING_STAGES.length - 1)), 1800);
    return () => window.clearInterval(timer);
  }, [loading]);

  async function planJourney() {
    const q = query.trim();
    if (!q) { setError("Tell TripPilot where you want to go and what you want to experience."); return; }
    setLoading(true); setError("");
    try {
      const result = await generateTrip(q);
      setTrip(result); setRefinement("");
      await loadHistory();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "TripPilot could not complete the journey research.");
    } finally { setLoading(false); }
  }

  async function refineJourney() {
    if (!trip || !("id" in trip) || !trip.id || !refinement.trim()) return;
    setRefining(true); setError("");
    try {
      const result = await refineTrip(trip.id, refinement.trim());
      setTrip(result);
      setRefinement("");
      await loadHistory();
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "TripPilot could not refine the journey.");
    } finally { setRefining(false); }
  }

  async function openSaved(id: number) {
    try {
      const result = await getTrip(id);
      setTrip(result); setQuery(result.user_query || "");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) { setError(e instanceof Error ? e.message : "Could not load this saved journey."); }
  }

  function home() {
    setTrip(null); setError(""); setRefinement("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (loading) {
    return <main className="planning-screen"><div className="planning-background" /><div className="planning-card">
      <div className="brand-mark">↑</div>
      <div className="eyebrow">TRIPPILOT AI TRAVEL CONCIERGE</div>
      <h1>Planning your journey.</h1>
      <p className="planning-lead">TripPilot is researching your request across multiple travel sources and assembling a personalized itinerary.</p>
      <div className="planning-progress">{PLANNING_STAGES.map((s, i) => <div className={`planning-step ${i < planningStage ? "complete" : ""} ${i === planningStage ? "active" : ""}`} key={s}><span className="planning-dot">{i < planningStage ? "✓" : i === planningStage ? "•" : ""}</span><span>{s}</span></div>)}</div>
      <div className="planning-bar"><span style={{ width: `${Math.max(12, ((planningStage + 1) / PLANNING_STAGES.length) * 100)}%` }} /></div>
      <div className="planning-meta"><span>LangGraph agent active</span><span>Live research</span></div>
    </div></main>;
  }

  if (!trip) {
    return <main>
      <nav className="navbar">
        <button className="brand" onClick={home}><span className="brand-icon">↑</span><span><strong>TRIPPILOT</strong><small>TRAVEL CONCIERGE</small></span></button>
        <div className="nav-links"><button onClick={home}>Plan a Journey</button><button onClick={() => document.getElementById("saved")?.scrollIntoView({ behavior: "smooth" })}>Saved Journeys</button></div>
        <div className="status"><span />Concierge Active</div>
      </nav>
      <section className="home-hero" style={{ backgroundImage: `url(${destinationImage("mountains")})` }}>
        <div className="hero-overlay" /><div className="hero-content">
          <div className="eyebrow light">PERSONALIZED TRAVEL CONCIERGE</div>
          <h1>Go somewhere<br />worth remembering.</h1>
          <p>Tell TripPilot where you want to go, what you love, your dates and your budget. We research the journey and turn it into a practical day-by-day travel plan.</p>
        </div>
        <div className="planner-card">
          <div className="planner-heading"><strong>Describe your journey</strong><span>Natural language is enough</span></div>
          <textarea value={query} onChange={e => setQuery(e.target.value)} placeholder="Example: Plan a 7-day trip from Bangalore to Japan for 2 travelers with a budget of ₹2,50,000. We love food, historic places, anime and scenic train journeys." />
          <div className="planner-bottom"><div className="planner-tags"><span>Flights</span><span>Hotels</span><span>Weather</span><span>Attractions</span></div><button className="primary-button" onClick={() => void planJourney()}>Plan My Journey →</button></div>
        </div>
      </section>
      <section className="home-section inspiration"><div className="section-heading"><div className="eyebrow">INSPIRATION</div><h2>Where will you go next?</h2><p>Start with a destination or describe something completely your own.</p></div>
        <div className="destination-grid">{[["Bali, Indonesia", "bali", "5-day tropical escape"], ["Tokyo & Kyoto", "tokyo", "Culture, food & neon"], ["Goa, India", "goa", "Beaches & slow travel"], ["Swiss Alps", "switzerland", "Mountains & scenic rail"]].map(([name, key, subtitle]) => <button className="destination-card" key={name} onClick={() => setQuery(`Plan a 5-day trip to ${name} for 2 travelers. ${subtitle}. Include attractions, weather, hotels and a practical day-by-day itinerary.`)}><img src={DESTINATION_IMAGES[key]} alt={name} /><div className="destination-gradient" /><div className="destination-text"><strong>{name}</strong><span>{subtitle} →</span></div></button>)}</div>
      </section>
      <section className="home-section" id="saved"><div className="section-heading"><div className="eyebrow">YOUR TRAVEL ARCHIVE</div><h2>Saved journeys</h2><p>Revisit trips you have already researched.</p></div>
        {historyLoading ? <div className="soft-message">Loading your travel archive…</div> : savedTrips.length ? <div className="saved-grid">{savedTrips.map(s => <button className="saved-card" key={s.id} onClick={() => void openSaved(s.id)}><img src={destinationImage(s.destination)} alt={s.destination} /><div className="saved-card-body"><strong>{s.destination}</strong><span>{s.trip_duration_days || "—"} days · {s.travelers || "—"} travelers</span>{s.estimated_cost ? <small>{money(s.estimated_cost)} estimated</small> : null}</div></button>)}</div> : <div className="empty-archive"><strong>No saved journeys yet.</strong><span>Your next AI-planned trip will appear here.</span></div>}
      </section>
      {error ? <div className="floating-error">{error}</div> : null}<footer>TripPilot · AI Travel Concierge</footer>
    </main>;
  }

  const flights = arrayOf(trip.flight_data);
  const hotels = arrayOf(trip.hotel_data);
  const attractions = arrayOf(trip.attraction_data);
  const weather = weatherRows(trip.weather_data);
  const budget = Number(trip.budget);
  const estimated = Number(trip.estimated_cost);
  const overBudget = Number.isFinite(budget) && Number.isFinite(estimated) && estimated > budget;
  const breakdown = (trip.itinerary?.cost_breakdown || {}) as Obj;
  const warnings = [...(trip.tool_warnings || []), ...(trip.constraint_violations || [])].filter(Boolean).filter((x, i, a) => a.indexOf(x) === i);
  const duration = trip.trip_duration_days || days.length;

  return <main>
    <nav className="navbar">
      <button className="brand" onClick={home}><span className="brand-icon">↑</span><span><strong>TRIPPILOT</strong><small>TRAVEL CONCIERGE</small></span></button>
      <div className="nav-links"><button onClick={home}>Plan a Journey</button><button onClick={() => document.getElementById("saved")?.scrollIntoView({ behavior: "smooth" })}>Saved Journeys</button></div>
      <div className="status"><span />Concierge Active</div>
    </nav>

    <section className="result-wrap">
      <button className="back-button" onClick={home}>← Plan another journey</button>
      <section className="trip-hero" style={{ backgroundImage: `url(${destinationImage(trip.destination)})` }}>
        <div className="trip-hero-overlay" /><div className="trip-hero-content"><div className="eyebrow light">YOUR TRIPPILOT JOURNEY</div><h1>{trip.destination || "Your Journey"}</h1><div className="trip-meta"><span>{duration || "—"} days</span><span>{trip.travelers || "—"} travelers</span>{trip.budget ? <span>Budget {money(trip.budget)}</span> : null}</div></div>
      </section>

      <section className="snapshot">
        <div className="snapshot-header"><div><div className="eyebrow">TRIP SNAPSHOT</div><h2>Your journey at a glance</h2></div><span className="completed-pill">Research completed</span></div>
        <div className="snapshot-grid">
          <div><small>Estimated cost</small><strong>{money(estimated)}</strong><span>Research-grounded projection</span></div>
          <div><small>Your budget</small><strong>{money(budget)}</strong><span>Planned spending limit</span></div>
          <div><small>Travelers</small><strong>{trip.travelers || "—"}</strong><span>People traveling</span></div>
          <div><small>Duration</small><strong>{duration || "—"} days</strong><span>Journey length</span></div>
        </div>
        {overBudget ? <div style={{ marginTop: 20, padding: "18px 20px", border: "1px solid #ead9b8", borderRadius: 16, background: "#fff9ed", display: "flex", flexDirection: "column", gap: 6 }}>
          <strong style={{ color: "#8a5b13" }}>Over budget by {money(estimated - budget)}</strong>
          <span style={{ color: "#6f624f", fontSize: 14, lineHeight: 1.5 }}>The researched flight and accommodation prices are higher than your stated budget. TripPilot is showing the real research result rather than hiding the mismatch.</span>
        </div> : null}
        {Object.keys(breakdown).length ? <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 12, marginTop: 16 }}>
          {[
            ["Flight", breakdown.flight_cost],
            ["Accommodation", breakdown.hotel_cost],
            ["Local spend", breakdown.local_cost],
            ["Research floor", breakdown.floor],
          ].map(([label, value]) => (
            <div key={String(label)} style={{ padding: "14px 16px", border: "1px solid #e2e8e2", borderRadius: 14, background: "#fafcf9" }}>
              <small style={{ display: "block", color: "#718077", marginBottom: 5 }}>{String(label)}</small>
              <strong>{money(value)}</strong>
            </div>
          ))}
        </div> : null}
      </section>

      <section className="research-section"><div className="section-heading"><div className="eyebrow">LIVE TRAVEL RESEARCH</div><h2>What TripPilot researched</h2><p>Multiple tools were queried to enrich your itinerary with real-world travel information.</p></div>
        <div className="research-grid">
          <ResearchCard icon="✈" title="Flights" count={flights.length} description={flights.length ? `${flights.length} live options returned` : "No live flight options returned"} />
          <ResearchCard icon="⌂" title="Stays" count={hotels.length} description={hotels.length ? `${hotels.length} accommodation options returned` : "No live hotel options returned"} />
          <ResearchCard icon="☀" title="Weather" count={weather.length} description={weather.length ? `${weather.length} forecast entries available` : flag(trip.weather_data?.trip_date_forecast_available) ? "Trip-date forecast available" : "Weather research completed"} />
          <ResearchCard icon="◉" title="Attractions" count={attractions.length} description={attractions.length ? `${attractions.length} places discovered` : "Destination research completed"} />
        </div>
      </section>

      {days.length ? <section className="itinerary-section"><div className="section-heading"><div className="eyebrow">YOUR TRAVEL GUIDE</div><h2>{trip.itinerary?.title || "Day-by-Day Itinerary"}</h2><p>{trip.itinerary?.summary || "A practical route built around your request, interests and available travel research."}</p></div>
        <div className="itinerary-list">{days.map((day, i) => <article className="day-card" key={i}><div className="day-image"><img src={dayImage(trip.destination, i)} alt={`${trip.destination || "Destination"} — Day ${i + 1}`} /><span>DAY {String(i + 1).padStart(2, "0")}</span></div><div className="day-content"><h3>{str(day.title) || str(day.name) || str(day.theme) || `Day ${i + 1}`}</h3>{str(day.description) || str(day.summary) ? <p className="day-description">{str(day.description) || str(day.summary)}</p> : null}<div className="activity-list">{activities(day).map((a, j) => <div className="activity" key={j}><span>{String(j + 1).padStart(2, "0")}</span><p>{a}</p></div>)}</div></div></article>)}</div>
      </section> : null}

      {attractions.length ? <section className="content-section"><div className="section-heading"><div className="eyebrow">LOCAL DISCOVERY</div><h2>Places to Experience</h2><p>Attractions discovered during destination research.</p></div><div className="place-grid">{attractions.map((p, i) => <article className="place-card" key={i}><div className="place-image"><img src={str(p.image_url) || dayImage(trip.destination, i)} alt={str(p.name) || "Attraction"} /><span>DISCOVERY</span></div><div className="place-body"><h3>{str(p.name) || "Local attraction"}</h3>{str(p.location) ? <div className="place-location">📍 {str(p.location)}</div> : null}<p>{str(p.description) || str(p.summary) || "A destination worth exploring during your journey."}</p><div className="place-footer">{str(p.category) || "Attraction"}</div>{(() => { const l = placeLink(p, trip.destination); return <a href={l.href} target="_blank" rel="noreferrer" style={externalStyle()}>{l.label} ↗</a> })()}</div></article>)}</div></section> : null}

      {weather.length ? <section className="content-section"><div className="section-heading"><div className="eyebrow">WEATHER INTELLIGENCE</div><h2>Weather during your journey</h2><p>Forecast information returned by TripPilot research.</p></div><div className="weather-grid">{weather.map((w, i) => <article className="weather-card" key={i}><span className="weather-day">{str(w.date) || `Day ${i + 1}`}</span><strong>{w.temperature_max !== undefined ? `${str(w.temperature_max)}°` : str(w.temperature) || "—"}</strong><span>{w.condition ? str(w.condition) : "Forecast data"}</span>{w.temperature_min !== undefined ? <small>Low {str(w.temperature_min)}°</small> : null}{w.precipitation_probability !== undefined ? <small>Rain chance: {str(w.precipitation_probability)}%</small> : null}</article>)}</div></section> : null}

      <section className="research-detail-grid">
        <ResearchDataSection icon="✈" title="Flight Research" subtitle="Live travel options discovered for your route." items={flights} trip={trip} empty="No live flight options were returned for this request." />
        <ResearchDataSection icon="⌂" title="Stay Research" subtitle="Accommodation options discovered for your journey." items={hotels} trip={trip} empty="No live hotel options were returned for this request." />
      </section>

      {warnings.length ? <section className="warnings-section"><div className="eyebrow">TRIP CHECK</div><h2>Things to know</h2><div className="warning-list">{warnings.map((w, i) => <div key={i}><span>!</span><p>{friendlyWarning(w)}</p></div>)}</div></section> : null}

      <section className="refine-section"><div><div className="eyebrow">AI REFINEMENT</div><h2>Want to change the journey?</h2><p>Ask TripPilot to modify this saved itinerary while keeping the original travel context.</p></div><div className="refine-box"><textarea value={refinement} onChange={e => setRefinement(e.target.value)} placeholder="Example: Make this cheaper, add more nature, remove shopping, or improve the food recommendations." /><button className="primary-button" disabled={!refinement.trim() || refining || !("id" in trip)} onClick={() => void refineJourney()}>{refining ? "Refining journey…" : "Refine Journey →"}</button></div></section>

      <section className="result-footer"><button className="secondary-button" onClick={home}>← Plan another journey</button><span>{"id" in trip && trip.id ? `Journey #${trip.id} saved to your travel archive` : "Journey researched by TripPilot"}</span></section>
      {error ? <div className="floating-error">{error}</div> : null}
    </section>
    <footer>TripPilot · AI Travel Concierge</footer>
  </main>;
}

function friendlyWarning(w: string): string {
  const x = w.toLowerCase();
  if (x.includes("estimated trip cost") && x.includes("exceeds the budget")) return `Your estimated trip cost exceeds the stated budget. This reflects the live researched prices rather than a hidden or invented discount.`;
  if (x.includes("estimated cost was raised")) return "The estimate was grounded against researched flight, accommodation and local-cost data.";
  if (x.includes("outside the available short forecast range") || x.includes("trip-date weather is unavailable")) return "A live forecast is not available this far ahead, so exact travel-date weather cannot be confirmed yet.";
  if (x.includes("opentripmap api key is not configured")) return "Some attraction suggestions are fallback recommendations rather than live attraction-provider results.";
  if (x.includes("serpapi_api_key") || x.includes("api key is not configured")) return "One external research provider was unavailable for this request.";
  return w;
}

function ResearchCard({ icon, title, count, description }: { icon: string; title: string; count: number; description: string }) {
  return <article className="research-card"><div className="research-icon">{icon}</div><div className="research-card-top"><span>{title}</span><strong>{count}</strong></div><p>{description}</p><div className="research-line"><span /></div></article>;
}

function ResearchDataSection({ icon, title, subtitle, items, trip, empty }: { icon: string; title: string; subtitle: string; items: Obj[]; trip: Trip; empty: string }) {
  const flights = title.toLowerCase().includes("flight");
  const hotels = title.toLowerCase().includes("stay");
  return <section className="research-detail"><div className="detail-heading"><div><div className="eyebrow">{icon} LIVE RESEARCH</div><h2>{title}</h2><p>{subtitle}</p></div><strong>{items.length}</strong></div>
    {items.length ? <div className="data-list">{items.slice(0, 8).map((item, i) => {
      const segs = arrayOf(item.segments), first = segs[0] || {}, last = segs[segs.length - 1] || first;
      const duration = Number(item.total_duration_minutes) > 0 ? Number(item.total_duration_minutes) : segs.reduce((s, x) => s + (Number(x.duration_minutes) || 0), 0);
      const route = flights ? `${segmentAirport(first, "departure")} → ${segmentAirport(last, "arrival")}` : "";
      const heading = flights ? (str(first.airline) || str(first.flight_number) || "Flight option") : (hotels ? (str(item.name) || "Accommodation option") : (str(item.name) || "Research option"));
      const entries = flights ? [
        ["route", route], ["fare", money(item.price)], ["stops", `${Number(item.number_of_stops) || 0}`], ["duration", durationText(duration)]
      ] : hotels ? [
        ["rating", item.rating !== undefined ? `${str(item.rating)} / 5` : "—"], ["per night", money(item.price_per_night)], ["total stay", money(item.total_price)], ["reviews", str(item.reviews) || "—"]
      ] : [];
      const href = flights ? flightSearchUrl(item, trip) : hotels ? (str(item.link) || str(item.maps_url) || mapsUrl(str(item.name) || "Hotel", trip.destination)) : null;
      return <article className="data-card" key={i}><div className="data-card-number">{String(i + 1).padStart(2, "0")}</div><div className="data-card-content"><h3>{heading}</h3><div className="data-values">{entries.map(([k, v]) => <span key={k}><small>{pretty(k)}</small>{v}</span>)}</div>{flights && segs.length ? <div style={{ marginTop: 10, fontSize: 12, color: "#6b756e" }}>{segmentTime(first, "departure")} · {segmentAirport(first, "departure")} → {segmentTime(last, "arrival")} · {segmentAirport(last, "arrival")}</div> : null}{href ? <a href={href} target="_blank" rel="noreferrer" style={externalStyle()}>{flights ? "Open Google Flights" : hotels ? (str(item.link) ? "View hotel" : "Open in Maps") : "Open"} ↗</a> : null}</div></article>;
    })}</div> : <div className="empty-research"><span>⌁</span><p>{empty}</p></div>}
  </section>;
}
