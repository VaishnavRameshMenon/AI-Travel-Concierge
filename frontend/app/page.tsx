"use client";

import { useEffect, useMemo, useState } from "react";
import {
  generateTrip,
  getTrip,
  listTrips,
  type TripDetail,
  type TripResponse,
  type TripSummary,
} from "../lib/api";

const destinationImages: Record<string, string> = {
  bali:
    "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=85",
  tokyo:
    "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=85",
  kyoto:
    "https://images.unsplash.com/photo-1493976040374-85c8e12f0c0e?auto=format&fit=crop&w=1200&q=85",
  goa:
    "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?auto=format&fit=crop&w=1200&q=85",
  switzerland:
    "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?auto=format&fit=crop&w=1200&q=85",
  paris:
    "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1200&q=85",
  london:
    "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?auto=format&fit=crop&w=1200&q=85",
  default:
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=85",
};

function imageFor(destination?: string | null) {
  if (!destination) return destinationImages.default;

  const key = destination.toLowerCase();

  for (const name of Object.keys(destinationImages)) {
    if (name !== "default" && key.includes(name)) {
      return destinationImages[name];
    }
  }

  return destinationImages.default;
}

function money(value?: number | null) {
  if (value === null || value === undefined) return "—";

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function cleanTitle(value: string) {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function findDays(itinerary: unknown): Array<Record<string, unknown>> {
  if (!itinerary || typeof itinerary !== "object") return [];

  const source = itinerary as Record<string, unknown>;

  const possible =
    source.days ||
    source.itinerary ||
    source.daily_plan ||
    source.plan;

  if (Array.isArray(possible)) {
    return possible.filter(
      (item): item is Record<string, unknown> =>
        !!item && typeof item === "object"
    );
  }

  const numbered = Object.entries(source)
    .filter(([key]) => /day\s*\d+/i.test(key))
    .map(([, value]) => value)
    .filter(
      (item): item is Record<string, unknown> =>
        !!item && typeof item === "object"
    );

  return numbered;
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined) return "";

  if (typeof value === "string") return value;

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => stringifyValue(item))
      .filter(Boolean)
      .join(" • ");
  }

  return "";
}

function dayTitle(day: Record<string, unknown>, index: number) {
  return (
    stringifyValue(day.title) ||
    stringifyValue(day.name) ||
    stringifyValue(day.theme) ||
    `Day ${index + 1}`
  );
}

function dayDescription(day: Record<string, unknown>) {
  return (
    stringifyValue(day.description) ||
    stringifyValue(day.summary) ||
    stringifyValue(day.overview) ||
    ""
  );
}

function dayActivities(day: Record<string, unknown>) {
  const possible =
    day.activities ||
    day.experiences ||
    day.items ||
    day.events ||
    day.highlights;

  if (Array.isArray(possible)) {
    return possible.map((item) => {
      if (typeof item === "string") {
        return { title: item, description: "" };
      }

      if (item && typeof item === "object") {
        const record = item as Record<string, unknown>;

        return {
          title:
            stringifyValue(record.title) ||
            stringifyValue(record.name) ||
            stringifyValue(record.activity) ||
            "Experience",
          description:
            stringifyValue(record.description) ||
            stringifyValue(record.details) ||
            stringifyValue(record.notes),
        };
      }

      return { title: "Experience", description: "" };
    });
  }

  return [];
}

function extractTextFromObject(
  object: Record<string, unknown>,
  ignored: string[] = []
) {
  return Object.entries(object)
    .filter(([key]) => !ignored.includes(key))
    .map(([key, value]) => {
      const text = stringifyValue(value);
      if (!text) return "";
      return `${cleanTitle(key)}: ${text}`;
    })
    .filter(Boolean);
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [trip, setTrip] = useState<TripResponse | null>(null);
  const [savedTrips, setSavedTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadHistory() {
    try {
      setHistoryLoading(true);
      const data = await listTrips();
      setSavedTrips(data.trips || []);
    } catch {
      // Database may be unavailable. The planner still works.
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function planJourney() {
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError("");
      setTrip(null);

      const result = await generateTrip(query.trim());
      setTrip(result);

      await loadHistory();

      setTimeout(() => {
        document
          .getElementById("trip-result")
          ?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to complete the journey."
      );
    } finally {
      setLoading(false);
    }
  }

  async function openSavedTrip(id: number) {
    try {
      setLoading(true);
      setError("");

      const detail = await getTrip(id);

      setTrip(detail);

      setTimeout(() => {
        document
          .getElementById("trip-result")
          ?.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to load this journey."
      );
    } finally {
      setLoading(false);
    }
  }

  const days = useMemo(
    () => findDays(trip?.itinerary),
    [trip?.itinerary]
  );

  const places = trip?.attraction_data || [];
  const flights = trip?.flight_data || [];
  const hotels = trip?.hotel_data || [];

  const tripImage = imageFor(trip?.destination);

  return (
    <main className="page">
      <nav className="nav">
        <div className="nav-inner">
          <div className="brand">
            <div className="brand-mark">↑</div>

            <div>
              <div className="brand-name">TRIPPILOT</div>
              <span className="brand-sub">TRAVEL CONCIERGE</span>
            </div>
          </div>

          <div className="nav-links">
            <button
              className="nav-link"
              onClick={() =>
                document
                  .getElementById("planner")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Plan a Journey
            </button>

            <button
              className="nav-link"
              onClick={() =>
                document
                  .getElementById("saved")
                  ?.scrollIntoView({ behavior: "smooth" })
              }
            >
              Saved Journeys
            </button>
          </div>

          <div className="status">
            <span className="status-dot" />
            Concierge Active
          </div>
        </div>
      </nav>

      {!trip && (
        <>
          <section className="hero">
            <div className="hero-inner">
              <div className="hero-copy">
                <div className="eyebrow">
                  Personalized Travel Concierge
                </div>

                <h1>
                  Go somewhere
                  <br />
                  worth remembering.
                </h1>

                <p>
                  Tell TripPilot where you want to go, what you love,
                  your dates and your budget. We research the journey
                  and turn it into a practical day-by-day travel plan.
                </p>
              </div>
            </div>
          </section>

          <div className="planner-wrap" id="planner">
            <section className="planner">
              <div className="planner-top">
                <div className="planner-label">
                  Describe your journey
                </div>

                <div className="planner-hint">
                  Natural language is enough
                </div>
              </div>

              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Example: Plan a 7-day trip from Bangalore to Japan for 2 travelers with a budget of ₹2,50,000. We love food, historic places, anime and scenic train journeys."
              />

              <div className="planner-bottom">
                <div className="quick-tags">
                  {[
                    "Flights",
                    "Hotels",
                    "Weather",
                    "Attractions",
                  ].map((tag) => (
                    <button
                      key={tag}
                      className="quick-tag"
                      onClick={() =>
                        setQuery((current) =>
                          current
                            ? `${current} Include ${tag.toLowerCase()} information.`
                            : `Plan a trip and include ${tag.toLowerCase()} information.`
                        )
                      }
                    >
                      {tag}
                    </button>
                  ))}
                </div>

                <button
                  className="primary-button"
                  disabled={loading || !query.trim()}
                  onClick={planJourney}
                >
                  {loading ? "Planning..." : "Plan My Journey →"}
                </button>
              </div>
            </section>
          </div>

          {error && <div className="alert">{error}</div>}

          <section className="section">
            <div className="container">
              <div className="section-heading">
                <div className="section-kicker">
                  Inspiration
                </div>

                <h2>Where will you go next?</h2>

                <p>
                  Start with a destination or describe something
                  completely your own.
                </p>
              </div>

              <div className="featured-grid">
                {[
                  ["Bali, Indonesia", "bali"],
                  ["Tokyo & Kyoto", "tokyo"],
                  ["Goa, India", "goa"],
                  ["Swiss Alps", "switzerland"],
                ].map(([name, key]) => (
                  <div
                    key={name}
                    className="destination-card"
                    style={{
                      backgroundImage: `url(${imageFor(key)})`,
                    }}
                    onClick={() =>
                      setQuery(
                        `Plan a 5-day trip to ${name} for 2 travelers with a comfortable budget. Include local food, important attractions, weather, hotels and a detailed day-by-day itinerary.`
                      )
                    }
                  >
                    <div className="destination-content">
                      <h3>{name}</h3>
                      <span>Use as starting point →</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="section" id="saved">
            <div className="container">
              <div className="section-heading">
                <div className="section-kicker">
                  Your Travel Archive
                </div>

                <h2>Saved Journeys</h2>

                <p>
                  Revisit trips you have already researched.
                </p>
              </div>

              {historyLoading ? (
                <div className="loading">Loading journeys...</div>
              ) : savedTrips.length === 0 ? (
                <div className="info-card">
                  No saved journeys yet. Your generated trips will
                  appear here.
                </div>
              ) : (
                <div className="saved-grid">
                  {savedTrips.slice(0, 6).map((saved) => (
                    <div
                      className="saved-card"
                      key={saved.id}
                      onClick={() => openSavedTrip(saved.id)}
                    >
                      <div
                        className="saved-image"
                        style={{
                          backgroundImage: `url(${imageFor(
                            saved.destination
                          )})`,
                        }}
                      />

                      <div className="saved-body">
                        <h3>{saved.destination}</h3>

                        <p>
                          {saved.trip_duration_days
                            ? `${saved.trip_duration_days} days`
                            : "Flexible duration"}
                          {" · "}
                          {saved.travelers || 1} traveler
                          {saved.travelers === 1 ? "" : "s"}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </section>
        </>
      )}

      {trip && (
        <div className="trip-page" id="trip-result">
          <div
            className="trip-hero"
            style={{ backgroundImage: `url(${tripImage})` }}
          >
            <div className="trip-hero-content">
              <div className="eyebrow">
                Your TripPilot Journey
              </div>

              <h1>{trip.destination || "Your Journey"}</h1>

              <div className="trip-meta">
                {trip.trip_duration_days && (
                  <span>
                    {trip.trip_duration_days} days
                  </span>
                )}

                {trip.travelers && (
                  <span>
                    {trip.travelers} traveler
                    {trip.travelers === 1 ? "" : "s"}
                  </span>
                )}

                {trip.start_date && (
                  <span>{trip.start_date}</span>
                )}

                {trip.budget && (
                  <span>Budget {money(trip.budget)}</span>
                )}
              </div>
            </div>
          </div>

          <div className="trip-content">
            <button
              className="quick-tag"
              onClick={() => {
                setTrip(null);
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              ← Plan another journey
            </button>

            {error && <div className="alert">{error}</div>}

            <section className="snapshot">
              <div className="snapshot-title">
                <strong>Trip Snapshot</strong>

                <span className="snapshot-small">
                  {trip.weather_data &&
                    Object.keys(trip.weather_data).length
                    ? "Research completed"
                    : "Travel research"}
                </span>
              </div>

              <div className="snapshot-grid">
                <div className="snapshot-item">
                  <div className="snapshot-label">
                    Estimated Cost
                  </div>

                  <div className="snapshot-value">
                    {money(trip.estimated_cost)}
                  </div>

                  <div className="snapshot-small">
                    Projected trip expenses
                  </div>
                </div>

                <div className="snapshot-item">
                  <div className="snapshot-label">
                    Your Budget
                  </div>

                  <div className="snapshot-value">
                    {money(trip.budget)}
                  </div>

                  <div className="snapshot-small">
                    Planned spending limit
                  </div>
                </div>

                <div className="snapshot-item">
                  <div className="snapshot-label">
                    Travelers
                  </div>

                  <div className="snapshot-value">
                    {trip.travelers || "—"}
                  </div>

                  <div className="snapshot-small">
                    People traveling
                  </div>
                </div>

                <div className="snapshot-item">
                  <div className="snapshot-label">
                    Duration
                  </div>

                  <div className="snapshot-value">
                    {trip.trip_duration_days
                      ? `${trip.trip_duration_days} days`
                      : "—"}
                  </div>

                  <div className="snapshot-small">
                    Journey length
                  </div>
                </div>
              </div>
            </section>

            <section className="itinerary">
              <div className="section-heading">
                <div className="section-kicker">
                  Your Travel Guide
                </div>

                <h2>Day-by-Day Itinerary</h2>

                <p>
                  A practical route built around your request,
                  interests and available travel research.
                </p>
              </div>

              {days.length === 0 ? (
                <div className="info-card">
                  <h3>Trip plan</h3>
                  <p>
                    {trip.final_response ||
                      "Your personalized journey has been generated."}
                  </p>
                </div>
              ) : (
                days.map((day, index) => {
                  const activities = dayActivities(day);

                  return (
                    <article className="day" key={index}>
                      <div className="day-header">
                        <div className="day-number">
                          DAY {String(index + 1).padStart(2, "0")}
                        </div>

                        <div>
                          <h3>
                            {dayTitle(day, index)}
                          </h3>

                          {dayDescription(day) && (
                            <p>{dayDescription(day)}</p>
                          )}
                        </div>
                      </div>

                      <div className="day-body">
                        {activities.length > 0 ? (
                          activities.map((activity, activityIndex) => (
                            <div
                              className="experience"
                              key={activityIndex}
                            >
                              <div className="experience-title">
                                {activity.title}
                              </div>

                              {activity.description && (
                                <div className="experience-text">
                                  {activity.description}
                                </div>
                              )}
                            </div>
                          ))
                        ) : (
                          extractTextFromObject(day, [
                            "title",
                            "name",
                            "theme",
                            "description",
                            "summary",
                            "overview",
                          ]).map((text, textIndex) => (
                            <div
                              className="experience"
                              key={textIndex}
                            >
                              <div className="experience-text">
                                {text}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </article>
                  );
                })
              )}
            </section>

            <section className="info-section">
              <div className="section-heading">
                <div className="section-kicker">
                  Local Discovery
                </div>

                <h2>Places to Experience</h2>

                <p>
                  Attractions and places discovered during trip
                  research.
                </p>
              </div>

              {places.length === 0 ? (
                <div className="info-card">
                  No attraction data was returned for this journey.
                </div>
              ) : (
                <div className="info-grid">
                  {places.slice(0, 9).map((place, index) => {
                    const title =
                      stringifyValue(place.name) ||
                      stringifyValue(place.title) ||
                      `Recommended Place ${index + 1}`;

                    const description =
                      stringifyValue(place.description) ||
                      stringifyValue(place.summary) ||
                      stringifyValue(place.details) ||
                      "A destination worth exploring during your journey.";

                    return (
                      <div
                        className="info-card"
                        key={index}
                      >
                        <h3>{title}</h3>
                        <p>{description}</p>

                        {stringifyValue(place.location) && (
                          <div className="place">
                            <span>{stringifyValue(place.location)}</span>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </section>

            <section className="info-section">
              <div className="info-grid">
                <div className="info-card">
                  <h3>Weather</h3>

                  {Object.keys(trip.weather_data || {}).length ===
                    0 ? (
                    <p>
                      No detailed forecast was returned for the
                      requested dates.
                    </p>
                  ) : (
                    <p>
                      {extractTextFromObject(
                        trip.weather_data || {}
                      )
                        .slice(0, 6)
                        .join(" · ")}
                    </p>
                  )}
                </div>

                <div className="info-card">
                  <h3>Flights</h3>

                  <p>
                    {flights.length
                      ? `${flights.length} flight option${flights.length === 1 ? "" : "s"
                      } researched.`
                      : "No live flight options were returned."}
                  </p>
                </div>

                <div className="info-card">
                  <h3>Stays</h3>

                  <p>
                    {hotels.length
                      ? `${hotels.length} accommodation option${hotels.length === 1 ? "" : "s"
                      } researched.`
                      : "No hotel options were returned."}
                  </p>
                </div>
              </div>
            </section>

            {(trip.tool_warnings?.length ||
              trip.constraint_violations?.length) && (
                <section className="info-section">
                  <div className="info-card">
                    <h3>Planning Notes</h3>

                    {trip.tool_warnings?.map((warning, index) => (
                      <div className="place" key={`w-${index}`}>
                        <span>{warning}</span>
                      </div>
                    ))}

                    {trip.constraint_violations?.map(
                      (warning, index) => (
                        <div className="place" key={`c-${index}`}>
                          <span>{warning}</span>
                        </div>
                      )
                    )}
                  </div>
                </section>
              )}
          </div>
        </div>
      )}

      <footer className="footer">
        TripPilot · AI Travel Concierge
      </footer>
    </main>
  );
}