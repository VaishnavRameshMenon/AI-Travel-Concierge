import { z } from "zod";

const api = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const tripSchema = z.object({
  success: z.boolean(),
  persisted: z.boolean(),
  trip_id: z.number().nullable(),
  destination: z.string().nullable(),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
  trip_duration_days: z.number().nullable(),
  travelers: z.number().nullable(),
  budget: z.number().nullable(),
  interests: z.array(z.string()),
  itinerary: z.record(z.unknown()).nullable(),
  estimated_cost: z.number().nullable(),
  weather_data: z.record(z.unknown()),
  attraction_data: z.array(z.record(z.unknown())),
  flight_data: z.array(z.record(z.unknown())),
  hotel_data: z.array(z.record(z.unknown())),
  tool_warnings: z.array(z.string()),
  constraint_violations: z.array(z.string()),
  final_response: z.string().nullable(),
});

export type Trip = z.infer<typeof tripSchema>;

export type TripSummary = {
  id: number;
  destination: string;
  trip_duration_days: number | null;
  travelers: number | null;
  budget: number | null;
  estimated_cost: number | null;
  created_at: string;
};

export type TripDetail = {
  id: number;
  user_query: string | null;
  origin: string | null;
  destination: string;
  start_date: string | null;
  end_date: string | null;
  trip_duration_days: number | null;
  travelers: number | null;
  budget: number | null;
  interests: string[];
  itinerary: Record<string, unknown> | null;
  estimated_cost: number | null;
  weather_data: Record<string, unknown>;
  flight_data: Array<Record<string, unknown>>;
  hotel_data: Array<Record<string, unknown>>;
  attraction_data: Array<Record<string, unknown>>;
  created_at: string;
};

async function request(path: string, init?: RequestInit) {
  const r = await fetch(`${api}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!r.ok) {
    const body = await r.json().catch(() => null);
    throw new Error(body?.detail || `Request failed (${r.status})`);
  }
  return r.json();
}

export async function generateTrip(user_query: string): Promise<Trip> {
  return tripSchema.parse(
    await request("/trips/generate", {
      method: "POST",
      body: JSON.stringify({ user_query }),
    })
  );
}

export async function listTrips(): Promise<{
  count: number;
  trips: TripSummary[];
}> {
  return (await request("/trips")) as { count: number; trips: TripSummary[] };
}

export async function getTrip(id: number | string): Promise<TripDetail> {
  return (await request(`/trips/${id}`)) as TripDetail;
}
