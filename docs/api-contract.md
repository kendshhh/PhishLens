
# PhishLens History API Contract

Status: Contract awaiting agreement with Trixia and Andrei. Backend behavior below is implemented locally; approval and deployed integration are not claimed.

## Endpoint

GET /api/analyses

## Successful Response (200 OK)

```json
{
  "items": [
    {
      "id": "29d80c39-ec0d-4db8-a6e5-87444ba2600c",
      "subject": "Synthetic account notice",
      "prediction": "phishing",
      "confidence": 0.93,
      "risk_level": "high",
      "threat_indicators": [
        {
          "type": "link",
          "detail": "Synthetic lookalike login link"
        }
      ],
      "explanation": "Demo only: the message requests an account action through a link.",
      "created_at": "2026-10-14T04:00:00Z"
    }
  ]
}
```

## Empty Response

```json
{
  "items": []
}
```

## Field Definitions

- `id`: UUID string identifying the saved analysis.
- `subject`: Subject of the analyzed email.
- `prediction`: "phishing", "legitimate", "spam", or null when unavailable. Week 2 saved records preserve the AI label rather than relabeling spam as phishing.
- `confidence`: Number from 0 to 1, or null.
- `risk_level`: "low", "medium", "high", "critical", or null.
- `threat_indicators`: Array of indicator objects with type and detail. Week 2 evidence indicators may also include a string quote; existing indicators without quote remain supported.
- `explanation`: Text explaining the result, or null.
- `created_at`: UTC ISO 8601 timestamp.

## Request and Security

- No request body is required.
- This Week 1 endpoint returns synthetic records for the fixed demo user.
- Real-user authentication and history isolation are future work.
- The Chrome extension calls FastAPI, never PostgreSQL directly.

## Error Handling

- HTTP 200: Successful response, including empty history.
- HTTP 500: Unexpected server error.
- HTTP 503: Database connection/query failure or missing/invalid database configuration.

```json
{"detail": "History temporarily unavailable"}
```

Database exception details and connection strings are not returned. The history router initializes database infrastructure only when a request needs it. `/health` can start without database configuration; `/ready` and history return 503 when configuration is missing or invalid.

## Integration

- Trixia provides the AnalyzedEmail model and database session.
- Leyan implements GET /api/analyses and the API client.
- Andrei provides the history UI container.
- Kendra provides the deployed backend URL.

## Verification Required

- Real synthetic database records are returned.
- Empty results return an empty items array.
- Updating a seeded database record changes the API result.
- Frontend handles loading, empty results, and errors.
- Deployed backend and extension are verified.

## Current implementation and handoff

- History returns up to 100 synthetic demo-user records, newest first with an ID tie-breaker. Timestamps are serialized in UTC.
- Synthetic examples and mocked HTTP tests are preparation, not evidence of a real PostgreSQL read or AI inference.
- History failure tests cover both database queries. Startup tests cover missing and invalid database URLs without changing main.py.
- The PostgreSQL HTTP test requires RUN_DATABASE_TESTS=1, a migrated/seeded localhost database named phishlens_dev, and uses a transaction that rolls test changes back. It verifies read, changed subject, user filtering and empty history.
- Local verification: 11 Python tests passed and 2 PostgreSQL tests skipped; Ruff passed. Verify again after subsequent changes.
- Trixia: review lazy session initialization, 503 policy and run/verify the PostgreSQL test in existing CI.
- Andrei: confirm UI targets and connect the existing history client/renderer with Leyan. Frontend files and main.py are outside this repair.
- Remaining: recorded contract agreement, successful real PostgreSQL/CI evidence and installed-extension verification against the deployed backend. Keep issue #7 open until its full criteria are met.
