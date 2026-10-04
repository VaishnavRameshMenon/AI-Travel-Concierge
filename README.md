# TripPilot — AI Travel Concierge

TripPilot is an AI-powered travel concierge that generates personalized travel plans from natural-language requests. It combines a LangGraph-based agent workflow, live travel APIs, persistent trip storage, and a modern web interface.

## Overview

The system accepts a natural-language travel request such as:

> "Plan a 7-day trip to Japan with a moderate budget."

It extracts the travel requirements, researches relevant real-world data, builds an itinerary, validates constraints, and returns a structured travel plan.

The project is implemented as a Track B advanced Agentic AI project.

## Key Features

- Natural-language travel planning
- LangGraph-based multi-step agent workflow
- Parallel research across multiple travel services
- Live weather data
- Flight research through SerpApi
- Hotel research through SerpApi
- Attraction research through OpenTripMap with fallback handling
- Budget estimation and constraint validation
- Bounded itinerary replanning
- PostgreSQL persistence
- Trip history and retrieval
- Trip refinement
- FastAPI backend
- Next.js frontend
- Monitoring and application metrics
- Resilient LLM fallback handling
- Automated tests
- Docker support

## Architecture

```text
                        User
                         |
                         v
                Next.js / React UI
                         |
                         v
                    FastAPI API
                         |
                         v
                 LangGraph Agent
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
  Requirement       Research Fanout   Previous Trip
   Extraction            |              / Refinement
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       Flights        Hotels         Weather
          |              |              |
          +--------------+--------------+
                         |
                         v
                    Attractions
                         |
                         v
                Itinerary Builder
                         |
                         v
                Constraint Checker
                         |
                    +----+----+
                    |         |
                  Valid     Replan
                    |         |
                    +----<----+
                         |
                         v
                  Final Trip Plan
                         |
              +----------+----------+
              |                     |
              v                     v
        PostgreSQL DB          API Response
```

## LangGraph Workflow

The agent workflow is built around shared travel state and multiple specialized nodes:

1. Extract travel requirements
2. Validate and normalize the request
3. Research destination information
4. Geocode destination/origin when required
5. Fetch weather information
6. Research flights
7. Research hotels
8. Research attractions
9. Estimate trip cost
10. Generate an itinerary
11. Validate constraints
12. Replan when required within a bounded limit
13. Persist the generated trip
14. Return the final response

Research tasks are designed to run independently where possible, reducing unnecessary sequential processing.

## External Integrations

| Integration | Purpose |
|---|---|
| Google Gemini | LLM reasoning and itinerary generation |
| SerpApi | Flight and hotel research |
| Open-Meteo | Weather information |
| OpenTripMap | Attraction research |
| PostgreSQL / Supabase | Persistent trip storage |

External API failures are handled through validation, fallbacks, warnings, and bounded retries where appropriate.

## Tech Stack

### Backend

- Python
- FastAPI
- LangGraph
- LangChain
- Google Gemini
- SQLAlchemy
- PostgreSQL
- Pydantic

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Infrastructure

- Docker
- Docker Compose
- GitHub

## Project Structure

```text
AI-Travel-Concierge/
├── backend/
│   └── app/
│       ├── agent/
│       ├── api/
│       ├── database/
│       ├── monitoring/
│       └── tools/
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/VaishnavRameshMenon/AI-Travel-Concierge.git
cd AI-Travel-Concierge
```

### 2. Backend setup

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` and configure the required API keys and database connection.

### 3. Start the backend

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Health check:

```text
http://localhost:8000/health
```

Metrics:

```text
http://localhost:8000/metrics
```

### 4. Frontend setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:3000
```

Configure the frontend API URL through the frontend environment file when required.

## Docker

The backend can also be run using Docker:

```bash
docker compose up --build
```

Environment variables should be configured through the appropriate environment files before starting the services.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/metrics` | Application metrics |
| POST | `/trips/generate` | Generate a new trip |
| GET | `/trips` | Retrieve saved trips |
| GET | `/trips/{trip_id}` | Retrieve a specific trip |
| POST | `/trips/{trip_id}/refine` | Refine an existing trip |

Detailed API documentation is available in `docs/api.md`.

## Persistence

Trip data is stored using PostgreSQL through SQLAlchemy.

The persistence layer supports:

- Creating trips
- Retrieving individual trips
- Listing saved trips
- Updating/refining trips
- Storing generated itinerary information

The database configuration is provided through environment variables.

## Reliability and Error Handling

TripPilot is designed to continue operating when individual services fail.

Examples include:

- LLM fallback models
- External API error handling
- Attraction fallback data
- Validation of external API responses
- Bounded replanning
- Constraint validation
- Warning collection instead of silently failing
- Request and application monitoring

The system avoids unbounded agent loops by limiting replanning attempts.

## Monitoring

The backend exposes a metrics endpoint at:

```text
GET /metrics
```

Application logging and request monitoring are implemented under:

```text
backend/app/monitoring/
```

Monitoring information can be used during testing and demonstrations to evaluate request behaviour, failures, and performance.

## Testing

Run the backend test suite from the project root:

```bash
pytest -q
```

The repository includes tests covering:

- Agent graph behaviour
- Travel tools
- API contracts
- Database persistence
- Resilience and fallback behaviour
- Weather and flight integrations

## Security

Security measures include:

- API keys stored through environment variables
- Secrets excluded from version control
- `.env.example` for configuration documentation
- Input validation using Pydantic
- Controlled external API access
- Database access through SQLAlchemy
- Separation of frontend and backend configuration

Production deployments should additionally use HTTPS, restricted CORS origins, secret management, authentication/authorization, rate limiting, and infrastructure-level monitoring.

See `docs/security.md` for the security assessment and recommended hardening measures.

## Documentation

Additional technical documentation:

- `docs/architecture.md` — System architecture and LangGraph workflow
- `docs/api.md` — API endpoints and request/response behaviour
- `docs/security.md` — Security assessment and hardening
- `docs/performance.md` — Testing, performance methodology, and monitoring

## Track B Coverage

The project is designed around the advanced Track B requirements:

- Complex LangGraph workflow
- Multiple external API integrations
- State management
- PostgreSQL persistence
- Error handling and fallbacks
- Constraint validation and replanning
- Professional React/Next.js frontend
- FastAPI backend
- Monitoring and metrics
- Automated testing
- Docker support
- Security practices
- Technical documentation

## Limitations

- External API availability depends on provider limits and credentials.
- Some travel data may fall back to alternative or static information when live providers are unavailable.
- Production-scale authentication and authorization are not currently implemented.
- Performance results depend on network conditions and third-party API response times.

## Future Improvements

- User authentication and profiles
- Redis caching
- Background task processing
- More travel providers
- Real-time flight monitoring
- Advanced cost optimization
- Voice-based travel planning
- Production-grade observability
- Automated deployment pipelines

## Repository

GitHub:

https://github.com/VaishnavRameshMenon/AI-Travel-Concierge

## Project Status

Track B advanced implementation completed with an agentic travel-planning workflow, external API integrations, persistence, monitoring, testing, and a Next.js frontend.
