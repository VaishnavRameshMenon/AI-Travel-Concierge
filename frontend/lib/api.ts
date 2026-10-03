const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export type TripResponse = {
  success: boolean;
  persisted?: boolean;
  trip_id?: number | null;
  destination?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  trip_duration_days?: number | null;
  travelers?: number | null;
  budget?: number | null;
  interests?: string[];
  itinerary?: Record<string, unknown> | null;
  estimated_cost?: number | null;
  weather_data?: Record<string, unknown>;
  attraction_data?: Record<string, unknown>[];
  flight_data?: Record<string, unknown>[];
  hotel_data?: Record<string, unknown>[];
  tool_warnings?: string[];
  constraint_violations?: string[];
  final_response?: string | null;
};

export type TripSummary = {
  id: number;
  destination: string;
  trip_duration_days?: number | null;
  travelers?: number | null;
  budget?: number | null;
  estimated_cost?: number | null;
  created_at: string;
};

export type TripDetail = TripResponse & {
  id: number;
  user_query?: string | null;
  origin?: string | null;
  created_at: string;
};
export type Trip = {
  id?: number;
  user_query?: string | null;
  origin?: string | null;
  destination?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  trip_duration_days?: number | null;
  travelers?: number | null;
  budget?: number | null;
  interests?: string[];
  itinerary?: Record<string, unknown> | null;
  estimated_cost?: number | null;
  weather_data?: Record<string, unknown>;
  flight_data?: Record<string, unknown>[];
  hotel_data?: Record<string, unknown>[];
  attraction_data?: Record<string, unknown>[];
  tool_warnings?: string[];
  constraint_violations?: string[];
  final_response?: string | null;
};
export async function generateTrip(
  user_query: string
): Promise<TripResponse> {
  const response = await fetch(`${API_BASE}/trips/generate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_query }),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      typeof data?.detail === "string"
        ? data.detail
        : "Unable to generate the journey."
    );
  }

  return data;
}

export async function listTrips(): Promise<{
  count: number;
  trips: TripSummary[];
}> {
  const response = await fetch(`${API_BASE}/trips`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load saved journeys.");
  }

  return response.json();
}

export async function getTrip(id: number): Promise<TripDetail> {
  const response = await fetch(`${API_BASE}/trips/${id}`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Unable to load this journey.");
  }

  return response.json();
}