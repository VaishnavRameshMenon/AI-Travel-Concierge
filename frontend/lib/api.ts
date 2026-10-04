const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export type FlightResult = Record<string, unknown> & {
  price?: number | null;
  currency?: string;
  travelers?: number;
  total_price?: number | null;
  price_per_traveler?: number | null;
  total_duration_minutes?: number | null;
  number_of_stops?: number;
  stop_label?: string;
  search_url?: string | null;
  segments?: Record<string, unknown>[];
};

export type HotelResult = Record<string, unknown> & {
  name?: string | null;
  description?: string | null;
  rating?: number | null;
  reviews?: number | null;
  price_per_night?: number | null;
  total_price?: number | null;
  image?: string | null;
  link?: string | null;
  maps_url?: string | null;
};

export type AttractionResult = Record<string, unknown> & {
  name?: string | null;
  description?: string | null;
  category?: string | null;
  image_url?: string | null;
  website?: string | null;
  wikipedia?: string | null;
  maps_url?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  xid?: string | null;
};

export type CostBreakdown = {
  floor?: number;
  flight_cost?: number;
  hotel_cost?: number;
  local_cost?: number;
  missing_flight_floor?: number;
  travelers?: number;
  duration_days?: number;
};

export type TripResponse = {
  success: boolean;
  persisted?: boolean;
  trip_id?: number | null;
  user_query?: string | null;
  origin?: string | null;
  destination?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  trip_duration_days?: number | null;
  travelers?: number | null;
  budget?: number | null;
  interests?: string[];
  itinerary?: {
    title?: string;
    summary?: string;
    estimated_cost?: number;
    cost_breakdown?: CostBreakdown;
    days?: Record<string, unknown>[];
    [key: string]: unknown;
  } | null;
  estimated_cost?: number | null;
  weather_data?: Record<string, any>;
  attraction_data?: AttractionResult[];
  flight_data?: FlightResult[];
  hotel_data?: HotelResult[];
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
  created_at: string;
};

async function parseResponse(response: Response, fallback: string): Promise<any> {
  let data: any = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const detail =
      typeof data?.detail === "string"
        ? data.detail
        : typeof data?.message === "string"
          ? data.message
          : fallback;
    throw new Error(detail);
  }

  return data;
}

export async function generateTrip(user_query: string): Promise<TripResponse> {
  const response = await fetch(`${API_BASE}/trips/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ user_query }),
  });
  return parseResponse(response, "Unable to generate the journey.");
}

export async function refineTrip(tripId: number, instruction: string): Promise<TripResponse> {
  const response = await fetch(`${API_BASE}/trips/${tripId}/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ instruction }),
  });
  return parseResponse(response, "Unable to refine the journey.");
}

export async function listTrips(): Promise<{ count: number; trips: TripSummary[] }> {
  const response = await fetch(`${API_BASE}/trips`, { cache: "no-store" });
  return parseResponse(response, "Unable to load saved journeys.");
}

export async function getTrip(id: number): Promise<TripDetail> {
  const response = await fetch(`${API_BASE}/trips/${id}`, { cache: "no-store" });
  return parseResponse(response, "Unable to load this journey.");
}
