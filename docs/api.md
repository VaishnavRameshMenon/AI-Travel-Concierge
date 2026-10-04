# TripPilot API Documentation

## Base URL

Local backend:

```text
http://localhost:8000
```

The FastAPI service can also be deployed behind a production reverse proxy or hosting platform.

## Authentication

The current project does not implement end-user authentication or authorization.

Production deployments should add authentication before exposing trip data publicly.

## Endpoints

### GET /

Returns basic API information.

Example:

```http
GET /
```

### GET /health

Returns the backend health status.

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### GET /metrics

Returns application monitoring information.

```http
GET /metrics
```

This endpoint is intended for operational visibility and performance analysis.

## Trip Generation

### POST /trips/generate

Generates a travel plan from a natural-language request.

```http
POST /trips/generate
Content-Type: application/json
```

Request:

```json
{
  "user_query": "Plan a 7 day trip to Japan with a moderate budget"
}
```

The backend:

1. Parses the request.
2. Extracts travel requirements.
3. Runs the agent workflow.
4. Researches external travel information.
5. Generates an itinerary.
6. Validates constraints.
7. Persists the trip.
8. Returns the generated result.

The response contains the generated trip information, itinerary, research results, cost information, and relevant warnings where applicable.

## Retrieve a Trip

### GET /trips/{trip_id}

Retrieves a previously saved trip.

```http
GET /trips/{trip_id}
```

Example:

```text
GET /trips/123
```

The exact identifier format is determined by the database model.

## List Trips

### GET /trips

Returns saved trips.

```http
GET /trips
```

This endpoint is useful for displaying previously generated journeys.

## Refine a Trip

### POST /trips/{trip_id}/refine

Refines an existing trip using a natural-language instruction.

```http
POST /trips/{trip_id}/refine
Content-Type: application/json
```

Example request:

```json
{
  "instruction": "Make the itinerary cheaper and add more cultural activities."
}
```

The backend uses the existing trip context together with the refinement instruction to regenerate the relevant parts of the plan.

## Error Handling

The API uses structured HTTP errors for invalid requests and server-side failures.

Potential causes include:

- Invalid request data
- Missing trip records
- External API failures
- LLM failures
- Database errors
- Unexpected workflow errors

External service failures may also appear as warnings in the generated trip rather than causing the entire workflow to fail.

## API Documentation During Development

FastAPI provides interactive API documentation automatically.

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

These interfaces can be used to inspect and manually test the available endpoints.

## Example Workflow

```text
POST /trips/generate
        |
        v
LangGraph Agent
        |
        +--> Flight research
        +--> Hotel research
        +--> Weather research
        +--> Attraction research
        |
        v
Itinerary + Cost + Validation
        |
        v
PostgreSQL
        |
        v
API Response
```

## Frontend Integration

The Next.js frontend communicates with the backend through the API client in:

```text
frontend/lib/api.ts
```

The frontend should use the configured backend URL rather than embedding API credentials.
