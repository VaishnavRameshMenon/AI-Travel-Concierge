# TripPilot Architecture

## 1. System Overview

TripPilot is an AI travel concierge built around a LangGraph workflow. A natural-language travel request enters through the FastAPI backend, is converted into structured travel requirements, researched through multiple external services, transformed into an itinerary, validated against constraints, and persisted in PostgreSQL.

The frontend is implemented with Next.js and communicates with the backend through HTTP APIs.

## 2. High-Level Architecture

```text
+-------------------+
|   Next.js Client  |
|  React / TypeScript|
+---------+---------+
          |
          | HTTP
          v
+-------------------+
|    FastAPI API    |
+---------+---------+
          |
          v
+-------------------+
|    LangGraph      |
|   Agent Workflow  |
+---------+---------+
          |
    +-----+-----------------------------+
    |     |        |        |           |
    v     v        v        v           v
 Flights Hotels Weather Attractions  LLM
    |     |        |        |           |
    +-----+--------+--------+-----------+
                     |
                     v
              Itinerary Builder
                     |
                     v
              Constraint Checker
                     |
               +-----+-----+
               |           |
             Valid       Replan
               |           |
               +-----<-----+
                     |
                     v
              PostgreSQL DB
```

## 3. Backend Components

### FastAPI

The FastAPI application exposes the public HTTP interface for:

- Health checks
- Metrics
- Trip generation
- Trip retrieval
- Trip listing
- Trip refinement

### LangGraph Agent

The agent workflow coordinates the travel-planning process through shared state.

The main responsibilities are:

- Requirement extraction
- Travel research
- Itinerary generation
- Cost estimation
- Constraint validation
- Bounded replanning
- Final response construction

### Tool Layer

The tool layer isolates external travel integrations:

```text
backend/app/tools/
├── attractions.py
├── flights.py
├── hotels.py
└── weather.py
```

This separation keeps external API logic independent from the core agent workflow.

### Database Layer

The database layer contains:

```text
backend/app/database/
├── database.py
├── models.py
├── crud.py
└── init_db.py
```

SQLAlchemy is used for PostgreSQL persistence.

### Monitoring Layer

Monitoring and logging are separated into:

```text
backend/app/monitoring/
├── logger.py
└── metrics.py
```

The backend exposes a `/metrics` endpoint for operational visibility.

## 4. LangGraph Workflow

The workflow operates on a shared `TravelState`.

A simplified execution path is:

```text
User Query
    |
    v
Requirements Extraction
    |
    v
Planning / Normalization
    |
    v
Research Fanout
    |
    +----> Geocoding
    +----> Weather
    +----> Attractions
    +----> Flights
    +----> Hotels
    |
    v
Cost Estimation
    |
    v
Itinerary Generation
    |
    v
Constraint Validation
    |
    +---- valid ------> Final Response
    |
    +---- violations -> Bounded Replanning
                              |
                              v
                       Itinerary Generation
```

Independent research tasks are separated from itinerary construction so that the planner can use collected information as grounded inputs.

## 5. Shared State

The agent state stores information such as:

- Original user query
- Refinement instructions
- Origin and destination
- IATA information
- Coordinates
- Travel dates and duration
- Number of travelers
- Budget
- Interests and preferences
- Flight, hotel, weather, and attraction research
- Warnings
- Generated itinerary
- Estimated cost
- Constraint violations
- Required tools
- Next action
- Error information
- Replan count
- Final response

Using a shared state allows individual nodes to contribute information without coupling all logic into a single function.

## 6. External Integrations

### Google Gemini

Gemini is used for language understanding, planning, and itinerary generation.

The LLM layer also contains fallback handling for model availability and quota-related failures.

### SerpApi

SerpApi provides travel search information for:

- Flights
- Hotels

### Open-Meteo

Open-Meteo provides weather information for the destination.

### OpenTripMap

OpenTripMap is used for attraction research. Fallback handling is used when live attraction information is unavailable.

## 7. Reliability Design

The system does not assume that every external service will always be available.

Reliability mechanisms include:

- External API exception handling
- Response validation
- Fallback attraction data
- LLM fallback models
- Warnings for unavailable information
- Bounded replanning
- Constraint validation

The replanning loop is intentionally bounded to avoid uncontrolled agent execution.

## 8. Persistence Flow

For a generated trip:

```text
Request
  |
  v
Agent Workflow
  |
  v
Generated Trip State
  |
  v
SQLAlchemy CRUD Layer
  |
  v
PostgreSQL
```

Saved trips can subsequently be retrieved or refined through the API.

## 9. Frontend Architecture

The frontend uses Next.js, React, TypeScript, and Tailwind CSS.

Its responsibilities include:

- Travel request input
- Trip generation interaction
- Itinerary presentation
- Flight/hotel/travel information presentation
- Saved-trip interaction
- Trip refinement

The frontend does not directly contain the agent logic. Agent execution remains in the backend.

## 10. Design Decisions

### LangGraph Instead of a Single LLM Call

A graph-based workflow provides explicit control over:

- State
- Tool execution
- Validation
- Conditional routing
- Replanning

This is more suitable for a multi-step travel agent than a single prompt-response interaction.

### Separate Tool Modules

Each external integration is isolated in its own module. This makes failures easier to handle and allows individual integrations to be replaced independently.

### Bounded Replanning

The system validates generated itineraries and can replan when constraints are violated, but the number of replanning attempts is bounded.

### PostgreSQL Persistence

Persistent storage allows generated journeys to survive beyond a single request and supports retrieval and refinement.

## 11. Deployment Architecture

The backend is Docker-ready and can be started with Docker Compose.

A production deployment can separate:

```text
Frontend
   |
   v
Backend API
   |
   +---- PostgreSQL
   |
   +---- External Travel APIs
   |
   +---- Gemini
```

Environment variables are used for service configuration and credentials.
