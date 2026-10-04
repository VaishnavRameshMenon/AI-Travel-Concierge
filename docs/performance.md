# TripPilot Performance and Monitoring

## Performance Scope

TripPilot performance depends on several components:

- LLM response time
- External travel API response time
- Database operations
- LangGraph workflow execution
- Network latency
- Frontend rendering

Because several operations depend on external providers, latency can vary between requests.

## Current Monitoring

The backend exposes:

```http
GET /metrics
```

Application monitoring code is located in:

```text
backend/app/monitoring/
```

The monitoring layer is intended to provide visibility into request behaviour, errors, and execution performance.

## Test Validation

The project includes automated tests covering:

- Graph behaviour
- API contracts
- Persistence
- Resilience
- Travel tools
- Weather handling
- Flight handling

Run:

```bash
pytest -q
```

The latest local project validation completed with the automated test suite passing before the final documentation phase.

## Performance Benchmark Methodology

For a meaningful benchmark, use the same test prompt multiple times and record:

| Metric | Measurement |
|---|---|
| Total request latency | Time from API request to response |
| LLM latency | Time spent waiting for model responses |
| Research latency | Time spent on external travel APIs |
| Database latency | Persistence/retrieval time |
| Error rate | Failed requests / total requests |
| Replanning rate | Requests requiring itinerary replanning |

External API latency should be reported separately from application processing time because provider response times are outside the application's direct control.

## Suggested Benchmark Procedure

Start the backend:

```bash
uvicorn backend.app.main:app --reload
```

Send the same representative request several times:

```text
Plan a 7 day trip to Japan with a moderate budget.
```

Record the response time for each request.

For example:

```text
Run 1: ______ ms
Run 2: ______ ms
Run 3: ______ ms
Run 4: ______ ms
Run 5: ______ ms
```

Then calculate:

```text
Average latency = sum of request latencies / number of runs
```

For a stronger benchmark, report median and p95 latency as well.

## Monitoring Data

During the final demonstration, capture the `/metrics` response after several requests and use it as evidence of application monitoring.

Recommended evidence:

1. One successful trip-generation request.
2. One refinement request.
3. One request involving an unavailable/failing external service if safely reproducible.
4. Corresponding monitoring output.

## Reliability Metrics

Useful reliability measurements include:

```text
Successful requests
Failed requests
External API failures
LLM fallback events
Replanning events
Average request duration
```

These metrics help demonstrate that the system is more than a simple single-call chatbot.

## Performance Optimization Opportunities

### Parallel Research

Independent travel research tasks can be executed independently, reducing unnecessary sequential waiting.

### LLM Fallbacks

Fallback models allow the workflow to continue when a preferred model is temporarily unavailable.

### Bounded Replanning

Limiting replanning prevents runaway execution and excessive API usage.

### Database Persistence

Persisting completed trips avoids unnecessary regeneration when users only need to retrieve an existing journey.

## Production Improvements

For higher traffic deployments, consider:

- Redis caching
- Background task processing
- Connection pooling
- API response caching
- Provider-specific timeouts
- Circuit breakers
- Distributed tracing
- Prometheus/Grafana monitoring
- Load testing
- CDN delivery for frontend assets

## Benchmark Reporting Template

Use the following table for the final report or presentation after running the benchmark:

| Test | Runs | Average | Median | P95 | Errors |
|---|---:|---:|---:|---:|---:|
| Trip generation | 5 | ___ ms | ___ ms | ___ ms | ___ |
| Trip refinement | 5 | ___ ms | ___ ms | ___ ms | ___ |
| Trip retrieval | 5 | ___ ms | ___ ms | ___ ms | ___ |

Do not fill benchmark values with estimates. Use measurements from the running application.

## Conclusion

TripPilot includes application-level monitoring, automated testing, resilient external integrations, and a workflow designed to limit unnecessary agent execution. Additional load testing and production observability should be added before operating the system at significant scale.
