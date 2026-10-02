"use client";
import { FormEvent, useEffect, useState } from "react";
import { generateTrip, getTrip, listTrips, type Trip, type TripDetail, type TripSummary } from "../lib/api";
import { Header, LoadingState, Planner } from "../components/planner/planner";
import { TripPage } from "../components/trip/trip-page";

export default function Home() {
  const [query, setQuery] = useState(""); const [trip, setTrip] = useState<Trip | null>(null); const [journeys, setJourneys] = useState<TripSummary[]>([]); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  useEffect(() => { if (!trip && !loading) listTrips().then((data) => setJourneys(data.trips)).catch(() => undefined); }, [trip, loading]);
  async function submit(event: FormEvent) { event.preventDefault(); if (!query.trim()) { setError("Tell TripPilot what kind of journey you have in mind."); return; } setLoading(true); setError(""); try { setTrip(await generateTrip(query.trim())); window.scrollTo({ top: 0, behavior: "smooth" }); } catch (err) { setError(err instanceof Error ? err.message : "Something went wrong while planning your trip."); } finally { setLoading(false); } }
  async function loadJourney(id: number) { setLoading(true); setError(""); try { const detail: TripDetail = await getTrip(id); setTrip({ success: true, persisted: true, trip_id: detail.id, destination: detail.destination, start_date: detail.start_date, end_date: detail.end_date, trip_duration_days: detail.trip_duration_days, travelers: detail.travelers, budget: detail.budget, interests: detail.interests, itinerary: detail.itinerary, estimated_cost: detail.estimated_cost, weather_data: detail.weather_data, attraction_data: detail.attraction_data, flight_data: detail.flight_data, hotel_data: detail.hotel_data, tool_warnings: detail.tool_warnings, constraint_violations: detail.constraint_violations, final_response: null }); window.scrollTo({ top: 0, behavior: "smooth" }); } catch (err) { setError(err instanceof Error ? err.message : "Could not load the saved journey."); } finally { setLoading(false); } }
  const home = () => { setTrip(null); setError(""); window.scrollTo({ top: 0, behavior: "smooth" }); };
  return <main className="site-shell"><Header onHome={home} onJourneys={() => document.getElementById("journeys-title")?.scrollIntoView({ behavior: "smooth" })} />{loading && <LoadingState />}{trip ? <TripPage trip={trip} onBack={home} /> : <Planner query={query} setQuery={setQuery} onSubmit={submit} loading={loading} error={error} journeys={journeys} onLoadJourney={loadJourney} onExample={setQuery} />}</main>;
}
