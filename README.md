# Celine Esthetique — AI Service Recommender

**Owner:** Ubaid Ullah Farooqui (AI Developer)
**Endpoint:** `POST /api/ai/recommend-service` (doc Section 10.4)
**Stack:** Python · FastAPI · Groq (free, OpenAI-compatible)

The Service Recommender asks the client a short questionnaire and returns the
single best-matching salon service, with price, duration, and a reason. If the
LLM is unavailable it falls back to an offline keyword matcher, so it **always**
returns a valid service (meets the "fallback responses" checklist item).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # then paste your free Groq key
```

Get a free Groq key: https://console.groq.com/keys

## Run

```bash
uvicorn main:app --reload --port 8001
```

Open http://localhost:8001/docs for the interactive Swagger UI.

## Test the endpoint

```bash
curl -X POST http://localhost:8001/api/ai/recommend-service \
  -H "Content-Type: application/json" \
  -d '{"answers": ["What area? nails", "What concern? brittle nails", "Occasion? daily"]}'
```

Response:

```json
{
  "recommendedService": "Strengthening natural nails",
  "price": 65,
  "duration": 45,
  "reason": "This treatment will strengthen your brittle nails"
}
```

Run the offline logic test (no key needed):

```bash
python test_recommender.py
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app + the `/api/ai/recommend-service` route |
| `recommender.py` | LLM call, validation, offline fallback |
| `services_catalog.py` | The 30+ real salon services |
| `test_recommender.py` | Offline test of the fallback matcher |

## Notes for the team

- **Prices/durations are placeholders** (typical Swiss rates). Replace with the
  real values from the `services` Firestore collection before final submission.
  The two confirmed-from-doc values are exact: Strengthening (65/45), Head Spa (120/60).
- **Swap to OpenAI** later: change only `_get_client()` in `recommender.py`.
- **NFR-02 (<4s):** Groq typically responds in well under a second.
- Next up in my module: **Price Estimator** (`/api/ai/price-estimate`) and
  **Sentiment Analysis** on reviews.
```
