
# PhishLens History API Contract

Status: Proposed - awaiting agreement with Trixia and Andrei.

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
- `prediction`: "phishing", "legitimate", or null when unavailable.
- `confidence`: Number from 0 to 1, or null.
- `risk_level`: "low", "medium", "high", "critical", or null.
- `threat_indicators`: Array of indicator objects with type and detail.
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
- HTTP 503: Database temporarily unavailable.

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
```
