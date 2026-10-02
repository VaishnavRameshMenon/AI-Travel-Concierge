"use client";

import { FormEvent } from "react";
import type { TripSummary } from "../../lib/api";

const examples = [
  "5 days in Bali from Bangalore for two, focused on beaches and food",
  "A week in Japan for food, temples and photography",
  "A relaxed Goa escape with beaches, local food and a small budget",
];

function money(value: number | null) {
  return value == null ? "Budget not set" : new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(value);
}

export function Planner({ query, setQuery, onSubmit, loading, error, journeys, onLoadJourney, onExample }: {
  query: string; setQuery: (value: string) => void; onSubmit: (event: FormEvent) => void; loading: boolean; error: string; journeys: TripSummary[]; onLoadJourney: (id: number) => void; onExample: (value: string) => void;
}) {
  return <div className="planner-page">
    <section className="planner-hero" aria-labelledby="planner-title">
      <div className="eyebrow"><span /> TRAVEL, THOUGHTFULLY PLANNED</div>
      <h1 id="planner-title">Where will you go next?</h1>
      <p>Tell TripPilot what you&apos;re imagining. We&apos;ll turn it into a practical journey.</p>
      <form className="prompt-form" onSubmit={onSubmit}>
        <label htmlFor="trip-prompt">Describe your ideal trip</label>
        <textarea id="trip-prompt" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="5 days in Bali from Bangalore for two, focused on beaches and food" rows={3} disabled={loading} />
        <div className="prompt-footer"><span>Natural language works best. Include dates, budget or interests if you have them.</span><button className="primary-button" type="submit" disabled={loading}>{loading ? "Planning…" : "Plan my trip →"}</button></div>
      </form>
      {error && <p className="error-message" role="alert">{error}</p>}
      <div className="example-row" aria-label="Example trip prompts">{examples.map((example) => <button key={example} type="button" onClick={() => onExample(example)}>{example}</button>)}</div>
    </section>
    <section className="journeys-section" aria-labelledby="journeys-title">
      <div className="section-heading"><div><div className="section-kicker">YOUR TRAVEL ARCHIVE</div><h2 id="journeys-title">Saved journeys</h2></div><span>{journeys.length ? `${journeys.length} journey${journeys.length === 1 ? "" : "s"}` : "Start your archive"}</span></div>
      {journeys.length ? <div className="journeys-grid">{journeys.map((journey) => <button className="journey-card" key={journey.id} onClick={() => onLoadJourney(journey.id)}><div><span className="card-kicker">JOURNEY {String(journey.id).padStart(2, "0")}</span><h3>{journey.destination}</h3></div><div className="journey-meta"><span>{journey.trip_duration_days ?? "—"} days</span><span>{journey.travelers ?? "—"} travelers</span><span>{money(journey.estimated_cost ?? journey.budget)}</span></div></button>)}</div> : <div className="empty-journeys">Your saved plans will appear here once you create a journey.</div>}
    </section>
  </div>;
}

export function Header({ onHome, onJourneys }: { onHome: () => void; onJourneys: () => void }) {
  return <header className="topbar"><button className="brand" onClick={onHome} aria-label="TripPilot home"><span className="brand-mark">T</span><span>TRIPPILOT</span></button><nav><button className="nav-link" onClick={onHome}>Plan a trip</button><button className="nav-link" onClick={onJourneys}>Journeys</button></nav><span className="service-status"><span className="status-dot" /> AI travel concierge</span></header>;
}

export function LoadingState() { return <div className="loading-state" role="status" aria-live="polite"><span className="loader" /> Building your journey with care…</div>; }
