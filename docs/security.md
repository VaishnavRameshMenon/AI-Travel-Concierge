# TripPilot Security Assessment

## Security Scope

This document describes the current security practices of TripPilot and identifies additional controls recommended for a production deployment.

## Current Security Controls

### Environment-Based Secrets

API credentials are supplied through environment variables.

Sensitive values are not intended to be committed to GitHub.

The repository provides example environment files:

```text
.env.example
frontend/.env.example
```

These files document configuration without containing real credentials.

### Git Ignore Rules

Local environment files and development artifacts are excluded from version control through `.gitignore`.

Developers should verify that real API keys are never committed.

### Input Validation

FastAPI request models use Pydantic validation.

This provides structured validation for API inputs before they enter the application workflow.

### Database Access

Database operations are isolated through the SQLAlchemy database layer.

The application does not construct database queries directly from raw user input.

### External API Isolation

External travel providers are accessed through dedicated tool modules.

This limits the scope of external-service logic and makes failures easier to contain.

### LLM Reliability

The LLM layer includes handling for quota and temporary service failures, including fallback model selection.

This reduces dependence on a single model endpoint.

## Sensitive Data

Potentially sensitive values include:

- Gemini API keys
- SerpApi credentials
- OpenTripMap credentials
- Database credentials
- Deployment configuration

These values must remain in environment variables or a dedicated secret-management system.

## Production Hardening

The current project is primarily an advanced project/demo implementation. A production deployment should additionally implement:

### Authentication

Require authenticated users before allowing access to personal trips.

### Authorization

Ensure a user can only retrieve or modify trips belonging to that user.

### HTTPS

All production frontend-to-backend communication should use HTTPS.

### CORS Restrictions

Production CORS configuration should allow only trusted frontend origins.

### Rate Limiting

Rate limits should be applied to:

- Trip generation
- Trip refinement
- External API-consuming endpoints

This protects both the application and paid API quotas.

### Secret Management

Production credentials should be stored in a managed secret store rather than plain deployment configuration where possible.

### Database Security

Recommended controls include:

- TLS connections
- Restricted database network access
- Least-privilege database users
- Regular backups
- Credential rotation

### Logging

Logs should avoid exposing:

- API keys
- Database passwords
- Authentication tokens
- Unnecessary personal information

### External API Validation

Responses from external services should continue to be validated before being used in itinerary generation.

### SSRF and URL Validation

If future features allow users to provide arbitrary URLs, strict URL validation and allow-listing should be added to prevent server-side request forgery.

## Security Checklist

Before a production deployment:

- [ ] Remove all real credentials from source code.
- [ ] Verify `.env` files are ignored.
- [ ] Configure HTTPS.
- [ ] Restrict CORS.
- [ ] Add authentication.
- [ ] Add authorization for trip ownership.
- [ ] Add rate limiting.
- [ ] Use managed secrets.
- [ ] Restrict database access.
- [ ] Review application logs for secret leakage.
- [ ] Rotate compromised credentials immediately.
- [ ] Validate external API responses.
- [ ] Run dependency/security scans.

## Threat Considerations

### Prompt Injection

Travel requests are untrusted user input. The application should avoid treating user-provided text as trusted instructions for internal system behaviour.

Future improvements should include stronger tool permissions and explicit separation between user content and agent instructions.

### API Abuse

Trip generation can trigger multiple external API calls. Rate limiting, caching, quotas, and authenticated access should be used to prevent abuse.

### Data Exposure

Persisted trips may contain travel plans and user-provided preferences. Access control should therefore be implemented before treating the system as a multi-user production service.

## Security Status

The project implements baseline security practices appropriate for a student Track B system while documenting the additional controls required for production deployment.
