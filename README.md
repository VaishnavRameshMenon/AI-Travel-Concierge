# ✈️ TripPilot — AI Travel Concierge

> An AI-powered travel planning agent that combines LangGraph orchestration, real-world travel APIs, persistent trip storage, constraint validation, and intelligent itinerary replanning.

## Overview

TripPilot is an advanced AI Travel Concierge built as a Track B project for the AI Agent Development program.

The system accepts natural-language travel requests and produces personalized itineraries using a multi-step LangGraph workflow. It researches real-world travel information, combines external API data with LLM reasoning, validates the generated itinerary against user constraints, and can replan when constraints are violated.

The application provides a professional Next.js interface backed by a FastAPI API and PostgreSQL persistence layer.

## ✨ Key Features

- 🤖 AI-powered travel planning
- 🧠 LangGraph multi-node agent workflow
- ✈️ Live flight research
- 🏨 Hotel research
- 🌦️ Weather information
- 📍 Attraction and destination research
- 💰 Budget-aware itinerary generation
- 🔄 Constraint validation and automatic replanning
- 💾 Persistent trip history using PostgreSQL
- 🔧 External API fallback handling
- 📊 Application logging and metrics
- 🛡️ Input validation and secure API-key handling
- 🧪 Automated test suite
- 🎨 Professional Next.js frontend
- 🚀 Docker-ready backend deployment

## 🏗️ Architecture

```text
┌───────────────────────────────┐
│       Next.js Frontend        │
│  Trip Planner / Results / UI  │
└───────────────┬───────────────┘
                │ HTTP / REST
                ▼
┌───────────────────────────────┐
│         FastAPI Backend       │
│  API Validation / Persistence │
│  Logging / Metrics            │
└───────────────┬───────────────┘
                ▼
┌───────────────────────────────┐
│       LangGraph Agent         │
│                               │
│ Requirements Extraction       │
│          ↓                    │
│ Planning / State Management  │
│          ↓                    │
│ Research Fan-out             │
│ Flights / Hotels / Weather   │
│ Attractions                  │
│          ↓                    │
│ Cost Grounding               │
│          ↓                    │
│ Itinerary Generation         │
│          ↓                    │
│ Constraint Validation        │
│          ↓                    │
│ Replanning Loop              │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│ Travel APIs  │  │ PostgreSQL   │
│ Flights      │  │ Trips        │
│ Hotels       │  │ Itineraries  │
│ Weather      │  │ History      │
│ Attractions  │  │              │
└──────────────┘  └──────────────┘
```

## 🧠 Agent Workflow

1. **Trip Requirements** — extracts origin, destination, dates, duration, travelers, budget, interests, and preferences.
2. **Planning** — normalizes requirements and resolves dates and duration.
3. **Research** — determines which external tools are required.
4. **Geocoding** — resolves destination coordinates and airport information.
5. **Parallel Research** — gathers weather, flights, hotels, and attractions.
6. **Cost Grounding** — combines researched travel costs with local expenses.
7. **Itinerary Generation** — creates the itinerary using researched data and preferences.
8. **Constraint Validation** — checks duration, travelers, budget, destination, and researched cost constraints.
9. **Replanning** — revises the itinerary when constraints are violated, with a bounded replanning loop.
10. **Final Response** — returns the itinerary and supporting research data.

## 🔌 External Integrations

| Integration | Purpose |
|---|---|
| Gemini | LLM reasoning and itinerary generation |
| SerpApi / Google Flights | Flight research |
| SerpApi / Google Hotels | Hotel research |
| Open-Meteo | Weather information |
| OpenTripMap | Attraction research |
| PostgreSQL / Supabase | Persistent trip storage |

The system includes fallback behavior when selected external providers are unavailable.

## 🛠️ Technology Stack

### Frontend
- Next.js
- React
- TypeScript
- Tailwind CSS

### Backend
- Python
- FastAPI
- LangChain
- LangGraph
- Pydantic
- SQLAlchemy

### AI
- Google Gemini

### Database
- PostgreSQL
- Supabase-compatible PostgreSQL connection

### APIs
- SerpApi
- Open-Meteo
- OpenTripMap

### Testing
- Pytest

### Infrastructure
- Docker
- Docker Compose

## 📁 Project Structure

```text
AI-Travel-Concierge/
├── backend/
│   └── app/
│       ├── agent/
│       ├── api/
│       ├── database/
│       ├── monitoring/
│       ├── tools/
│       └── main.py
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── tests/
│   ├── test_api_contracts.py
│   ├── test_persistence.py
│   ├── test_resilience.py
│   └── test_tools.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Local Setup

### 1. Clone

```bash
git clone https://github.com/VaishnavRameshMenon/AI-Travel-Concierge.git
cd AI-Travel-Concierge
```

### 2. Python environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create `.env` from `.env.example`.

Never commit `.env` or real API keys.

## ▶️ Run Backend

```bash
uvicorn backend.app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

FastAPI docs:

```text
http://127.0.0.1:8000/docs
```

## ▶️ Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:3000
```

Configure the backend URL using `frontend/.env.example`.

## 🐳 Docker

```bash
docker compose up --build
```

## 🧪 Testing

Run:

```bash
pytest -q
```

The test suite covers API contracts, database persistence, tool behavior, resilience/fallback behavior, and agent workflow behavior.

## 💾 Persistent Trip History

Generated trips can be stored in PostgreSQL, including:

- User query
- Origin and destination
- Dates and duration
- Travelers and budget
- Interests
- Generated itinerary
- Estimated cost
- Weather, flight, hotel, and attraction research

## 🔄 Itinerary Refinement

Previously generated trips can be refined with instructions such as:

```text
Make the trip more budget friendly.
```

or:

```text
Add more traditional Japanese cultural experiences.
```

## 🛡️ Reliability & Error Handling

The application handles API failures, missing data, weather limitations, attraction-provider unavailability, LLM quota exhaustion, and invalid input using controlled fallbacks and warnings.

The LLM layer supports fallback model handling when the primary model cannot be used.

## 📊 Monitoring

TripPilot includes custom monitoring components for:

- Request logging
- API request timing
- Application metrics
- Error tracking
- Backend health information

## 🔐 Security

Security measures include:

- Environment-variable based secret management
- No API keys hardcoded in source
- `.env` excluded from version control
- Pydantic request validation
- Controlled CORS
- SQLAlchemy database access
- External API failure handling
- Separate frontend/backend configuration

See `docs/security.md` for the detailed security assessment.

## 📚 Documentation

Additional documentation:

```text
docs/
├── architecture.md
├── api.md
├── security.md
└── performance.md
```

## 📈 Track B Features

TripPilot implements the advanced Track B direction through:

- LangGraph workflow
- Multi-step agent reasoning
- State management
- Conditional routing
- Constraint validation
- Automatic replanning
- Multiple travel integrations
- PostgreSQL persistence
- FastAPI backend
- Next.js frontend
- Docker configuration
- Monitoring and logging
- Automated testing
- Security practices
- API documentation

## 🚧 Known Limitations

Travel information depends on third-party providers.

- Flight and hotel prices can change rapidly.
- Weather forecasts have limited future availability.
- Some attraction information may use fallback data.
- LLM availability can depend on provider quotas and rate limits.

The system therefore presents researched information with appropriate warnings rather than treating generated information as guaranteed bookings.

## 🔮 Future Improvements

- Redis caching
- More travel providers
- Real booking integrations
- Voice-based travel planning
- Multilingual support
- Advanced observability dashboards
- User authentication
- Collaborative trip planning
- Calendar integration
- More sophisticated cost optimization
- Distributed production deployment

## 👨‍💻 Project

**TripPilot — AI Travel Concierge**

Built as an Advanced Track B AI Agent project.

GitHub: https://github.com/VaishnavRameshMenon/AI-Travel-Concierge
