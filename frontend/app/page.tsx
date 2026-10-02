"use client";



import { FormEvent, useEffect, useMemo, useState } from "react";

import { listTrips, getTrip, type TripSummary, type TripDetail } from "../lib/api";



type Activity = string | {



  time?: string;



  description?: string;



  location?: string;



};







type ItineraryDay = {



  day?: number;



  date?: string;



  title?: string;



  summary?: string;



  activities?: Activity[];



  morning?: string[];



  afternoon?: string[];



  evening?: string[];



};







type TripResponse = {



  success?: boolean;



  persisted?: boolean;



  trip_id?: number;



  destination?: string;



  start_date?: string;



  end_date?: string;



  trip_duration_days?: number | null;



  travelers?: number;



  budget?: number;



  interests?: string[];



  itinerary?: {



    title?: string;



    summary?: string;



    estimated_cost?: number;



    days?: ItineraryDay[];



  };



  estimated_cost?: number;



  weather_data?: Record<string, unknown>;



  attraction_data?: Array<Record<string, unknown>>;



  flight_data?: Array<Record<string, unknown>>;



  hotel_data?: Array<Record<string, unknown>>;



  tool_warnings?: string[];



  constraint_violations?: string[];



  final_response?: string;



};







const API_BASE =



  process.env.NEXT_PUBLIC_API_BASE_URL || "http\\://localhost:8000";







const examplePrompts = [



  {



    city: "TOKYO",



    title: "Anime, food & late-night ramen",



    prompt:



      "I want to travel from Delhi to Tokyo from October 10 to October 16, 2026 for 3 people. My budget is 150000 rupees. I love anime, Japanese food and photography.",



  },



  {



    city: "KYOTO",



    title: "Food, gardens & old Japan",



    prompt:



      "Plan a 5 day trip from Bangalore to Kyoto for 2 people with a budget of 100000 rupees. We love Japanese food, temples and photography.",



  },



  {



    city: "GOA",



    title: "Beaches & a relaxed escape",



    prompt:



      "Plan a 4 day trip from Bangalore to Goa for 2 people with a budget of 30000 rupees. We want beaches, good food and relaxing places.",



  },



];







function formatCurrency(value?: number | null) {



  if (value === undefined || value === null || Number.isNaN(value)) {



    return "—";



  }







  return new Intl.NumberFormat("en-IN", {



    style: "currency",



    currency: "INR",



    maximumFractionDigits: 0,



  }).format(value);



}







function formatDate(value?: string) {



  if (!value) return "";







  const date = new Date(`${value}T00:00:00`);







  if (Number.isNaN(date.getTime())) return value;







  return new Intl.DateTimeFormat("en-IN", {



    day: "2-digit",



    month: "short",



    year: "numeric",



  }).format(date);



}







function formatShortDate(value?: string) {



  if (!value) return "";







  const date = new Date(`${value}T00:00:00`);







  if (Number.isNaN(date.getTime())) return value;







  return new Intl.DateTimeFormat("en-IN", {



    day: "2-digit",



    month: "short",



  }).format(date);



}







function cleanLabel(value: unknown) {



  if (typeof value !== "string") return "";







  return value



    .replace(/_/g, " ")



    .replace(/\b\w/g, (letter) => letter.toUpperCase());



}







function activityItems(day: ItineraryDay) {



  if (Array.isArray(day.activities) && day.activities.length > 0) {



    return day.activities.map((activity) => {



      if (typeof activity === "string") {



        return {



          time: "",



          description: activity,



          location: "",



        };



      }







      return {



        time: activity.time || "",



        description: activity.description || "",



        location: activity.location || "",



      };



    });



  }







  const result: {



    time: string;



    description: string;



    location: string;



  }[] = [];







  if (Array.isArray(day.morning)) {



    day.morning.forEach((item) =>



      result.push({



        time: "Morning",



        description: item,



        location: "",



      }),



    );



  }







  if (Array.isArray(day.afternoon)) {



    day.afternoon.forEach((item) =>



      result.push({



        time: "Afternoon",



        description: item,



        location: "",



      }),



    );



  }







  if (Array.isArray(day.evening)) {



    day.evening.forEach((item) =>



      result.push({



        time: "Evening",



        description: item,



        location: "",



      }),



    );



  }







  return result;



}







export default function Home() {



  const [query, setQuery] = useState("");

  const [trip, setTrip] = useState<TripResponse | null>(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");

  const [activeDay, setActiveDay] = useState<number | null>(null);



  // ── Saved journeys state ────────────────────────────────────────────

  const [savedJourneys, setSavedJourneys] = useState<TripSummary[]>([]);

  const [historyLoading, setHistoryLoading] = useState(false);

  const [historyError, setHistoryError] = useState("");



  // Fetch trip history whenever the landing page is shown

  useEffect(() => {

    async function fetchHistory() {

      setHistoryLoading(true);

      setHistoryError("");

      try {

        const data = await listTrips();

        setSavedJourneys(data.trips);

      } catch {

        setHistoryError("Could not load saved journeys.");

      } finally {

        setHistoryLoading(false);

      }

    }

    if (!trip && !loading) {

      fetchHistory();

    }

    // eslint-disable-next-line react-hooks/exhaustive-deps

  }, [trip, loading]);





  const days = trip?.itinerary?.days || [];







  const destination = trip?.destination || "Your destination";







  const weather = trip?.weather_data || {};



  const forecastAvailable =



    weather.trip_date_forecast_available === true;







  const weatherWarning =



    typeof weather.warning === "string"



      ? weather.warning



      : "";







  const weatherCurrent =



    weather.current && typeof weather.current === "object"



      ? (weather.current as Record<string, unknown>)



      : null;







  const currentTemperature =



    weatherCurrent &&



      typeof weatherCurrent.temperature_2m === "number"



      ? weatherCurrent.temperature_2m



      : null;







  const attractionCount = trip?.attraction_data?.length || 0;



  const hotelCount = trip?.hotel_data?.length || 0;



  const flightCount = trip?.flight_data?.length || 0;







  const flightWarning = (trip?.tool_warnings || []).find((warning) =>



    warning.toLowerCase().includes("flight"),



  );







  const heroDateRange = useMemo(() => {



    if (!trip?.start_date || !trip?.end_date) return "";







    return `${formatDate(trip.start_date)} — ${formatDate(trip.end_date)}`;



  }, [trip?.start_date, trip?.end_date]);







  async function loadSavedJourney(id: number) {

    setLoading(true);

    setError("");

    setTrip(null);

    setActiveDay(null);

    try {

      const detail: TripDetail = await getTrip(id);

      // Map TripDetail -> TripResponse shape the UI expects

      setTrip({

        success: true,

        persisted: true,

        trip_id: detail.id,

        destination: detail.destination,

        start_date: detail.start_date ?? undefined,

        end_date: detail.end_date ?? undefined,

        trip_duration_days: detail.trip_duration_days ?? undefined,

        travelers: detail.travelers ?? undefined,

        budget: detail.budget ?? undefined,

        interests: detail.interests ?? undefined,

        itinerary: detail.itinerary as TripResponse["itinerary"],

        estimated_cost: detail.estimated_cost ?? undefined,

        weather_data: detail.weather_data,

        attraction_data: detail.attraction_data,

        flight_data: detail.flight_data,

        hotel_data: detail.hotel_data,

        tool_warnings: [],

        constraint_violations: [],

        final_response: undefined,

      });

      window.scrollTo({ top: 0, behavior: "smooth" });

    } catch (err) {

      setError(

        err instanceof Error

          ? err.message

          : "Could not load the saved journey."

      );

    } finally {

      setLoading(false);

    }

  }



  async function generateTrip(event?: FormEvent) {



    event?.preventDefault();







    if (!query.trim()) {



      setError("Tell TripPilot what kind of journey you have in mind.");



      return;



    }







    setLoading(true);



    setError("");



    setTrip(null);



    setActiveDay(null);







    try {



      const response = await fetch(`${API_BASE}/trips/generate`, {



        method: "POST",



        headers: {



          "Content-Type": "application/json",



          Accept: "application/json",



        },



        body: JSON.stringify({



          user_query: query.trim(),



        }),



      });







      let data: TripResponse | null = null;







      try {



        data = await response.json();



      } catch {



        data = null;



      }







      if (!response.ok) {



        const detail =



          data &&



            typeof data === "object" &&



            "detail" in data



            ? String((data as Record<string, unknown>).detail)



            : `Request failed with HTTP ${response.status}.`;







        throw new Error(detail);



      }







      if (!data) {



        throw new Error("The backend returned an empty response.");



      }







      setTrip(data);



      // Return the user to the top of the newly generated journey.

      window.setTimeout(() => {

        window.scrollTo({

          top: 0,

          left: 0,

          behavior: "smooth",

        });

      }, 50);



    } catch (err) {



      setError(



        err instanceof Error



          ? err.message



          : "Something went wrong while planning your trip.",



      );



    } finally {



      setLoading(false);



    }



  }







  function useExample(prompt: string) {



    setQuery(prompt);



    window.scrollTo({



      top: 0,



      behavior: "smooth",



    });



  }







  function resetTrip() {



    setTrip(null);



    setError("");



    setActiveDay(null);







    window.scrollTo({



      top: 0,



      behavior: "smooth",



    });



  }







  return (



    <main className="site-shell">



      <header className="topbar">



        <button



          className="brand"



          onClick={resetTrip}



          aria-label="TripPilot home"



        >



          <span className="brand-mark">T</span>



          <span>TRIPPILOT</span>



        </button>







        <div className="topbar-right">



          <span className="service-status">



            <span className="status-dot" />



            AI travel concierge



          </span>







          <button



            className="nav-link"



            onClick={() => {



              document



                .getElementById("examples")



                ?.scrollIntoView({ behavior: "smooth" });



            }}



          >



            Explore



          </button>



        </div>



      </header>







      {!trip && !loading && (



        <>



          <section className="hero">



            <div className="hero-image" />







            <div className="hero-overlay" />







            <div className="hero-content">



              <div className="eyebrow">



                <span />



                AI-POWERED JOURNEY PLANNING



              </div>







              <h1>



                Travel,



                <br />



                thoughtfully planned.



              </h1>







              <p className="hero-copy">



                Tell TripPilot what you are imagining.



                <br />



                We&apos;ll shape it into a practical journey.



              </p>







              <form



                className="planner"



                onSubmit={generateTrip}



              >



                <div className="planner-label">



                  WHERE SHOULD WE TAKE YOU?



                </div>







                <textarea



                  value={query}



                  onChange={(event) =>



                    setQuery(event.target.value)



                  }



                  placeholder="Try: Tokyo for 7 days, anime, food and photography..."



                  rows={3}



                />







                <div className="planner-footer">



                  <span>



                    Natural language is enough. TripPilot



                    extracts the details it needs.



                  </span>







                  <button



                    type="submit"



                    className="primary-button"



                  >



                    Plan my trip



                    <span>→</span>



                  </button>



                </div>



              </form>







              {error && (



                <div className="error-banner">



                  <strong>We couldn&apos;t plan that trip.</strong>



                  <span>{error}</span>



                </div>



              )}



            </div>



          </section>







          <section



            id="examples"



            className="examples-section"



          >



            <div className="section-heading">



              <div>



                <span className="section-kicker">



                  START SOMEWHERE



                </span>



                <h2>Journeys worth imagining.</h2>



              </div>







              <p>



                Give TripPilot a direction.



                <br />



                Refine the details later.



              </p>



            </div>







            <div className="example-grid">



              {examplePrompts.map((example, index) => (



                <button



                  key={example.city}



                  className={`example-card example-${index + 1}`}



                  onClick={() =>



                    useExample(example.prompt)



                  }



                >



                  <div className="example-card-top">



                    <span>0{index + 1}</span>



                    <span>→</span>



                  </div>







                  <div className="example-card-content">



                    <span className="example-city">



                      {example.city}



                    </span>







                    <span className="example-title">



                      {example.title}



                    </span>



                  </div>



                </button>



              ))}



            </div>



          </section>







          <section className="process-section">



            <div className="process-intro">



              <span className="section-kicker">



                HOW TRIPPILOT WORKS



              </span>







              <h2>



                From an idea



                <br />



                to a journey.



              </h2>



            </div>







            <div className="process-grid">



              <div>



                <span className="process-number">01</span>



                <h3>Understand</h3>



                <p>



                  TripPilot turns your natural-language



                  request into structured travel requirements.



                </p>



              </div>







              <div>



                <span className="process-number">02</span>



                <h3>Research</h3>



                <p>



                  The agent coordinates destination,



                  weather, attractions, flights and stay



                  research.



                </p>



              </div>







              <div>



                <span className="process-number">03</span>



                <h3>Shape</h3>



                <p>



                  Your itinerary is generated, checked



                  against your constraints, and replanned



                  when necessary.



                </p>



              </div>



            </div>



          </section>







          {/* ── Saved Journeys ──────────────────────────────────────── */}

          <section className="examples-section" id="saved-journeys">

            <div className="section-heading">

              <div>

                <span className="section-kicker">YOUR HISTORY</span>

                <h2>Saved journeys.</h2>

              </div>

              <p>

                Pick up where you left off.

                <br />

                Every trip TripPilot planned is stored here.

              </p>

            </div>



            {historyLoading && (

              <p style={{ color: "var(--muted)", fontSize: "0.875rem", marginTop: "1.5rem" }}>

                Loading saved journeys&hellip;

              </p>

            )}



            {historyError && !historyLoading && (

              <div className="error-banner" style={{ marginTop: "1.5rem" }}>

                <strong>Could not load history.</strong>

                <span>{historyError}</span>

              </div>

            )}



            {!historyLoading && !historyError && savedJourneys.length === 0 && (

              <p style={{ color: "var(--muted)", fontSize: "0.875rem", marginTop: "1.5rem" }}>

                No saved journeys yet. Generate your first trip above!

              </p>

            )}



            {!historyLoading && savedJourneys.length > 0 && (

              <div className="example-grid" style={{ marginTop: "2rem" }}>

                {savedJourneys.slice(0, 6).map((journey, index) => (

                  <button

                    key={journey.id}

                    id={`saved-journey-${journey.id}`}

                    className={`example-card example-${(index % 3) + 1}`}

                    onClick={() => loadSavedJourney(journey.id)}

                    style={{ textAlign: "left" }}

                  >

                    <div className="example-card-top">

                      <span style={{ fontSize: "0.65rem", opacity: 0.6 }}>

                        #{journey.id}

                      </span>

                      <span>&#8594;</span>

                    </div>

                    <div className="example-card-content">

                      <span className="example-city">

                        {journey.destination.toUpperCase()}

                      </span>

                      <span className="example-title">

                        {journey.trip_duration_days

                          ? `${journey.trip_duration_days} days`

                          : ""}

                        {journey.travelers

                          ? ` · ${journey.travelers} traveller${journey.travelers === 1 ? "" : "s"}`

                          : ""}

                      </span>

                      {journey.estimated_cost != null && (

                        <span

                          style={{

                            fontSize: "0.7rem",

                            opacity: 0.55,

                            marginTop: "0.25rem",

                            display: "block",

                          }}

                        >

                          Est.{" "}

                          {new Intl.NumberFormat("en-IN", {

                            style: "currency",

                            currency: "INR",

                            maximumFractionDigits: 0,

                          }).format(journey.estimated_cost)}

                        </span>

                      )}

                    </div>

                  </button>

                ))}

              </div>

            )}

          </section>





        </>



      )}







      {loading && (



        <section className="planning-screen">



          <div className="planning-orbit">



            <div className="orbit-ring ring-one" />



            <div className="orbit-ring ring-two" />



            <div className="orbit-core">T</div>



          </div>







          <span className="section-kicker">



            TRIPPILOT IS PLANNING



          </span>







          <h1>



            Shaping your



            <br />



            journey.



          </h1>







          <p>



            TripPilot is understanding your request,



            researching the destination and assembling



            your itinerary.



          </p>







          <div className="planning-steps">



            <div className="planning-step active">



              <span>01</span>



              Understanding your trip



              <b>✓</b>



            </div>







            <div className="planning-step active">



              <span>02</span>



              Researching the destination



              <b>✓</b>



            </div>







            <div className="planning-step active">



              <span>03</span>



              Shaping your itinerary



              <i />



            </div>







            <div className="planning-step">



              <span>04</span>



              Checking constraints



              <i />



            </div>



          </div>



        </section>



      )}







      {trip && !loading && (



        <>



          <section className="trip-hero">



            <div className="trip-hero-image" />



            <div className="trip-hero-overlay" />







            <div className="trip-hero-content">



              <button



                className="back-button"



                onClick={resetTrip}



              >



                ← Plan another journey



              </button>







              <div className="trip-hero-bottom">



                <div>



                  <span className="section-kicker light">



                    YOUR JOURNEY



                  </span>







                  <h1>{destination}</h1>







                  <p>



                    {trip.itinerary?.title ||



                      "A journey shaped around you."}



                  </p>



                </div>







                <div className="trip-meta">



                  <span>{heroDateRange}</span>



                  <span>



                    {trip.trip_duration_days ||



                      days.length ||



                      "—"}{" "}



                    days · {trip.travelers || "—"} travellers



                  </span>



                </div>



              </div>



            </div>



          </section>







          <section className="trip-summary">



            <div className="summary-intro">



              <span className="section-kicker">



                AT A GLANCE



              </span>



              <p>



                {trip.itinerary?.summary ||



                  trip.final_response ||



                  "A personalized travel plan created by TripPilot."}



              </p>



            </div>







            <div className="summary-stats">



              <div>



                <span>ESTIMATED COST</span>



                <strong>



                  {formatCurrency(



                    trip.estimated_cost ||



                    trip.itinerary?.estimated_cost,



                  )}



                </strong>



              </div>







              <div>



                <span>YOUR BUDGET</span>



                <strong>



                  {formatCurrency(trip.budget)}



                </strong>



              </div>







              <div>



                <span>TRAVELLERS</span>



                <strong>{trip.travelers || "—"}</strong>



              </div>







              <div>



                <span>INTERESTS</span>



                <strong className="interest-value">



                  {(trip.interests || []).join(" · ") ||



                    "Personalized"}



                </strong>



              </div>



            </div>



          </section>







          {(trip.tool_warnings || []).length > 0 && (



            <section className="notice-strip">



              <div className="notice-icon">!</div>







              <div>



                <span className="section-kicker">



                  DATA AVAILABILITY



                </span>







                <div className="notice-list">



                  {trip.tool_warnings?.map(



                    (warning, index) => (



                      <span key={`${warning}-${index}`}>



                        {warning}



                      </span>



                    ),



                  )}







                  {weatherWarning &&

                    !(trip.tool_warnings || []).includes(

                      weatherWarning,

                    ) && (

                      <span>{weatherWarning}</span>

                    )}



                </div>



              </div>



            </section>



          )}







          <section className="trip-layout">



            <div className="itinerary-column">



              <div className="content-heading">



                <div>



                  <span className="section-kicker">



                    THE JOURNEY



                  </span>



                  <h2>Your itinerary.</h2>



                </div>







                <span className="day-count">



                  {days.length} days



                </span>



              </div>







              <div className="itinerary">



                {days.map((day, index) => {



                  const dayNumber =



                    day.day || index + 1;







                  const activities = activityItems(day);







                  const isOpen =



                    activeDay === null



                      ? index === 0



                      : activeDay === index;







                  return (



                    <article



                      className={`day-card ${isOpen ? "is-open" : ""



                        }`}



                      key={`${dayNumber}-${day.date}`}



                    >



                      <button



                        className="day-header"



                        onClick={() =>



                          setActiveDay(



                            isOpen ? null : index,



                          )



                        }



                      >



                        <div className="day-number">



                          <span>DAY</span>



                          <strong>



                            {String(dayNumber).padStart(



                              2,



                              "0",



                            )}



                          </strong>



                        </div>







                        <div className="day-title-wrap">



                          <span>



                            {formatShortDate(day.date)}



                          </span>







                          <h3>



                            {day.title ||



                              `Day ${dayNumber}`}



                          </h3>



                        </div>







                        <div className="day-toggle">



                          {isOpen ? "−" : "+"}



                        </div>



                      </button>







                      {isOpen && (



                        <div className="day-body">



                          {day.summary && (



                            <p className="day-summary">



                              {day.summary}



                            </p>



                          )}







                          <div className="activity-list">



                            {activities.map(



                              (activity, activityIndex) => (



                                <div



                                  className="activity"



                                  key={`${dayNumber}-${activityIndex}`}



                                >



                                  <div className="activity-marker">



                                    <span />



                                  </div>







                                  <div className="activity-content">



                                    <div className="activity-top">



                                      <span>



                                        {activity.time ||



                                          "Activity"}



                                      </span>







                                      {activity.location && (



                                        <small>



                                          {



                                            activity.location



                                          }



                                        </small>



                                      )}



                                    </div>







                                    <p>



                                      {



                                        activity.description



                                      }



                                    </p>



                                  </div>



                                </div>



                              ),



                            )}



                          </div>



                        </div>



                      )}



                    </article>



                  );



                })}



              </div>



            </div>







            <aside className="research-column">



              <div className="content-heading research-heading">



                <div>



                  <span className="section-kicker">



                    RESEARCH



                  </span>



                  <h2>Trip intelligence.</h2>



                </div>



              </div>







              <div className="research-stack">



                <section className="research-card">



                  <div className="research-card-head">



                    <span>WEATHER</span>



                    <span



                      className={`data-badge ${forecastAvailable



                          ? "live"



                          : "unavailable"



                        }`}



                    >



                      {forecastAvailable



                        ? "LIVE"



                        : "UNAVAILABLE"}



                    </span>



                  </div>







                  {forecastAvailable ? (



                    <div className="weather-live">



                      {currentTemperature !== null && (



                        <strong>



                          {Math.round(



                            currentTemperature,



                          )}



                          °



                        </strong>



                      )}







                      <p>



                        Trip-date forecast available for



                        your journey.



                      </p>



                    </div>



                  ) : (



                    <div className="research-message">



                      <strong>



                        Trip-date forecast isn&apos;t available yet.



                      </strong>







                      <p>



                        The weather service is working, but the



                        requested dates are outside its current



                        short-range forecast window. Current



                        conditions are shown only as reference.



                      </p>



                    </div>



                  )}



                </section>







                <section className="research-card">

                  <div className="research-card-head">

                    <span>FLIGHTS</span>



                    <span className={`data-badge ${flightCount > 0 ? "live" : "unavailable"}`}>

                      {flightCount > 0 ? "LIVE SEARCH" : "UNAVAILABLE"}

                    </span>

                  </div>



                  {flightCount > 0 ? (

                    <div className="flight-list">

                      {(trip.flight_data || []).slice(0, 4).map((flight, index) => {

                        const segments = Array.isArray(flight.segments) ? flight.segments as Record<string, unknown>[] : [];

                        const firstSegment: Record<string, unknown> = segments[0] || {};

                        const lastSegment: Record<string, unknown> = segments[segments.length - 1] || firstSegment;

                        const price = typeof flight.price === "number" ? flight.price : null;

                        const duration = typeof flight.total_duration_minutes === "number"

                          ? flight.total_duration_minutes

                          : null;

                        const stops = typeof flight.number_of_stops === "number"

                          ? flight.number_of_stops

                          : Math.max(0, segments.length - 1);



                        return (

                          <div className="flight-item" key={`flight-${index}`}>

                            <div className="flight-main">

                              <div className="flight-airline">

                                {firstSegment.airline_logo ? (

                                  <img

                                    src={String(firstSegment.airline_logo)}

                                    alt=""

                                    className="flight-airline-logo"

                                  />

                                ) : null}

                                <div>

                                  <strong>{String(firstSegment.airline || "Flight option")}</strong>

                                  <span>{String(firstSegment.flight_number || "")}</span>

                                </div>

                              </div>



                              <div className="flight-route">

                                <div>

                                  <strong>{String(firstSegment.departure_airport || "—")}</strong>

                                  <span>{String(firstSegment.departure_time || "").slice(-5)}</span>

                                </div>

                                <span className="flight-arrow">→</span>

                                <div>

                                  <strong>{String(lastSegment.arrival_airport || "—")}</strong>

                                  <span>{String(lastSegment.arrival_time || "").slice(-5)}</span>

                                </div>

                              </div>



                              <div className="flight-price">

                                <strong>{formatCurrency(price)}</strong>

                                <span>

                                  {stops === 0 ? "Non-stop" : `${stops} stop${stops === 1 ? "" : "s"}`}

                                </span>

                              </div>

                            </div>



                            <div className="flight-meta">

                              <span>

                                {duration !== null ? `${Math.floor(duration / 60)}h ${duration % 60}m` : "Duration unavailable"}

                              </span>

                              <span>{String(firstSegment.travel_class || "Economy")}</span>

                              <span>{Number(flight.travelers || trip.travelers || 1)} travellers</span>

                            </div>

                          </div>

                        );

                      })}



                      {flightCount > 4 && (

                        <p className="research-footnote">Showing 4 of {flightCount} available flight options.</p>

                      )}

                    </div>

                  ) : (

                    <div className="research-message">

                      <strong>Flight information unavailable.</strong>

                      <p>

                        {flightWarning || "Live flight information could not be retrieved from the current provider."}

                      </p>

                    </div>

                  )}

                </section>







                <section className="research-card">

                  <div className="research-card-head">

                    <span>STAYS</span>



                    <span className={`data-badge ${hotelCount > 0 ? "live" : "unavailable"}`}>

                      {hotelCount > 0 ? "LIVE SEARCH" : "UNAVAILABLE"}

                    </span>

                  </div>



                  {hotelCount > 0 ? (

                    <div className="hotel-list">

                      {(trip.hotel_data || []).slice(0, 4).map((hotel, index) => {

                        const nightly = typeof hotel.price_per_night === "number"

                          ? hotel.price_per_night

                          : null;

                        const total = typeof hotel.total_price === "number"

                          ? hotel.total_price

                          : null;

                        const rating = typeof hotel.rating === "number" ? hotel.rating : null;

                        const reviews = typeof hotel.reviews === "number" ? hotel.reviews : null;

                        const image = typeof hotel.image === "string" ? hotel.image : null;

                        const amenities = Array.isArray(hotel.amenities) ? hotel.amenities.slice(0, 3) : [];

                        const propertyLink = typeof hotel.link === "string" ? hotel.link : null;



                        return (

                          <div className="hotel-item" key={`${String(hotel.name || "hotel")}-${index}`}>

                            {image && (

                              <img src={image} alt="" className="hotel-image" />

                            )}



                            <div className="hotel-info">

                              <strong>{String(hotel.name || "Hotel option")}</strong>

                              <span className="hotel-rating">

                                {rating !== null ? `★ ${rating.toFixed(1)}` : "Rating unavailable"}

                                {reviews !== null ? ` · ${reviews} reviews` : ""}

                              </span>



                              {typeof hotel.hotel_class === "string" && hotel.hotel_class && (

                                <span className="hotel-class">{hotel.hotel_class}</span>

                              )}



                              {amenities.length > 0 && (

                                <span className="hotel-amenities">

                                  {amenities.map((item) => cleanLabel(item)).join(" · ")}

                                </span>

                              )}



                              {propertyLink && (

                                <a href={propertyLink} target="_blank" rel="noreferrer" className="hotel-link">

                                  View property →

                                </a>

                              )}

                            </div>



                            <div className="hotel-price">

                              <strong>{formatCurrency(nightly)}</strong>

                              <span>/ night</span>

                              {total !== null && <small>{formatCurrency(total)} total</small>}

                            </div>

                          </div>

                        );

                      })}



                      {hotelCount > 4 && (

                        <p className="research-footnote">Showing 4 of {hotelCount} available stays.</p>

                      )}

                    </div>

                  ) : (

                    <div className="research-message">

                      <strong>No live hotel results.</strong>

                      <p>Hotel information could not be retrieved from the current provider.</p>

                    </div>

                  )}

                </section>







                <section className="research-card">



                  <div className="research-card-head">



                    <span>PLACES</span>







                    <span className="data-badge fallback">



                      SUGGESTIONS



                    </span>



                  </div>







                  <div className="place-list">



                    {(trip.attraction_data || [])



                      .slice(0, 8)



                      .map((place, index) => (



                        <div



                          className="place-item"



                          key={`${String(



                            place.name || "place",



                          )}-${index}`}



                        >



                          <div className="place-index">



                            {String(index + 1).padStart(



                              2,



                              "0",



                            )}



                          </div>







                          <div>



                            <strong>



                              {String(



                                place.name ||



                                "Suggested place",



                              )}



                            </strong>







                            <span>



                              {cleanLabel(



                                place.category ||



                                place.kinds ||



                                "Travel",



                              )}



                            </span>



                          </div>



                        </div>



                      ))}







                    {attractionCount === 0 && (



                      <p className="muted">



                        No attraction suggestions were



                        returned.



                      </p>



                    )}



                  </div>



                </section>



              </div>



            </aside>



          </section>







          <section className="closing-section">



            <span className="section-kicker">



              TRIPPILOT



            </span>







            <h2>



              The journey starts



              <br />



              before you leave.



            </h2>







            <button



              className="secondary-button"



              onClick={resetTrip}



            >



              Plan another journey →



            </button>



          </section>



        </>



      )}







      <footer className="footer">



        <span>TRIPPILOT</span>



        <span>AI TRAVEL CONCIERGE</span>



        <span>LANGGRAPH · FASTAPI · NEXT.JS</span>



      </footer>



    </main>



  );



}