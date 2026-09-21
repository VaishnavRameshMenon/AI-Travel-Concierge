import os
import requests
import streamlit as st
from dotenv import load_dotenv


def get_backend_url() -> str:
    """Return the non-secret FastAPI URL for local or deployed use."""
    try:
        return st.secrets.get("BACKEND_URL", os.getenv("BACKEND_URL", "http://localhost:8000"))
    except Exception:
        return os.getenv("BACKEND_URL", "http://localhost:8000")


def render_concierge() -> None:
    st.set_page_config(page_title="TripPilot", page_icon="Trip", layout="wide")
    st.title("TripPilot AI Travel Concierge")
    st.caption("Agentic trip planning with LangGraph and live travel research where available.")
    with st.sidebar:
        st.subheader("Backend service")
        st.code(get_backend_url(), language=None)
        if st.button("Check status"):
            try:
                health = requests.get(f"{get_backend_url().rstrip('/')}/health", timeout=10).json()
                st.success(f"Backend is {health['status']}.")
            except requests.RequestException:
                st.error("Cannot reach the FastAPI backend.")

    example = "Plan a 5-day food, culture, and photography trip from Delhi to Tokyo for 2 people with a budget of 150000 rupees."
    query = st.text_area("Describe your trip", value=example, height=130, max_chars=2000)
    if st.button("Generate trip plan", type="primary", use_container_width=True):
        if len(query.strip()) < 3:
            st.warning("Please enter a travel request of at least three characters.")
        else:
            try:
                with st.spinner("Planning your trip and researching available information..."):
                    response = requests.post(
                        f"{get_backend_url().rstrip('/')}/trips/generate",
                        json={"user_query": query.strip()}, timeout=120,
                    )
                if not response.ok:
                    try:
                        detail = response.json().get("detail", response.text)
                    except ValueError:
                        detail = response.text or f"HTTP {response.status_code}"
                    raise RuntimeError(f"HTTP {response.status_code}: {detail}")
                st.session_state.trip_result = response.json()
            except (requests.RequestException, RuntimeError, ValueError) as exc:
                st.error(f"Could not generate a trip plan: {exc}")

    result = st.session_state.get("trip_result")
    if not result:
        return
    st.divider()
    st.subheader(result.get("final_response") or "Your trip plan")
    for warning in result.get("tool_warnings", []):
        st.warning(warning)
    columns = st.columns(5)
    columns[0].metric("Destination", result.get("destination") or "Not specified")
    columns[1].metric("Duration", f"{result.get('trip_duration_days') or '-'} days")
    columns[2].metric("Travellers", result.get("travelers") or "-")
    columns[3].metric("Budget", result.get("budget") or "-")
    columns[4].metric("Estimated cost", result.get("estimated_cost") or "-")
    st.caption(f"Dates: {result.get('start_date') or 'Not specified'} to {result.get('end_date') or 'Not specified'} | Interests: {', '.join(result.get('interests') or []) or 'None specified'}")
    itinerary = result.get("itinerary") or {}
    st.subheader(itinerary.get("title", "Day-by-day itinerary"))
    st.write(itinerary.get("summary", ""))
    for index, day in enumerate(itinerary.get("days", []), start=1):
        with st.expander(day.get("title", f"Day {index}") if isinstance(day, dict) else f"Day {index}", expanded=index == 1):
            st.write(day)
    for title, data, note in [
        ("Weather research", result.get("weather_data"), "Weather is live data when available."),
        ("Attractions research", result.get("attraction_data"), "Fallback attraction suggestions are labelled in the data."),
        ("Flight research", result.get("flight_data"), "Flight information is informational only; no booking or price is implied."),
        ("Hotel research", result.get("hotel_data"), "Hotel recommendations may be estimated fallback data."),
    ]:
        with st.expander(title):
            if data:
                if title == "Weather research":
                    if data.get("trip_date_forecast_available") is False:
                        st.warning(data.get("warning", "Trip-date weather is not available."))
                    elif data.get("trip_date_forecast_available") is True:
                        st.success("Trip-date forecast is available within the provider's short forecast window.")
                st.json(data)
                st.caption(note)
            else:
                st.info("No data was available.")


render_concierge()

