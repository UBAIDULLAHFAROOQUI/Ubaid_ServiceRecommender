# Celine Esthetique — AI Service Recommender

**Owner:** Ubaid Ullah Farooqui (AI Developer)
**Endpoint:** `POST /api/ai/recommend-service` (doc Section 10.4)
**Stack:** Python · FastAPI · Groq (free, OpenAI-compatible)

The Service Recommender asks the client a short questionnaire and returns the
single best-matching salon service — with `serviceId`, price, duration, and a
reason. It supports **English and French** (Lausanne is French-speaking). If the
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

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/` | Health check |
| `GET`  | `/api/ai/recommend-service/questions?language=en\|fr` | Chat questionnaire (area → concern → occasion) for the frontend to render |
| `POST` | `/api/ai/recommend-service` | Returns the best-matching service |

### Recommend — request

```json
{
  "answers": ["area: nails", "concern: brittle nails", "occasion: daily"],
  "language": "en"
}
```

- `answers` accepts both styles: `"What area? nails"` and `"area: nails"`.
- `language` is `"en"` (default) or `"fr"`. French answers are understood too,
  e.g. `["zone: ongles", "souci: ongles cassants"]`.

### Recommend — response

```json
{
  "recommendedService": "Strengthening natural nails",
  "serviceId": "strengthening",
  "price": 65,
  "duration": 45,
  "reason": "Strengthen your brittle nails."
}
```

`recommendedService` is always the English catalog name (matches the database);
`reason` is written in the requested language (e.g. *"Pour renforcer vos ongles cassants."* in French).

## Test

```bash
# curl (English)
curl -X POST http://localhost:8001/api/ai/recommend-service \
  -H "Content-Type: application/json" \
  -d '{"answers": ["area: nails", "concern: brittle nails", "occasion: daily"]}'

# curl (French)
curl -X POST http://localhost:8001/api/ai/recommend-service \
  -H "Content-Type: application/json" \
  -d '{"answers": ["zone: ongles", "souci: ongles cassants"], "language": "fr"}'

# offline logic tests (no key needed)
python test_recommender.py
```

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app + routes |
| `recommender.py` | LLM call, EN/FR handling, questions, offline fallback |
| `services_catalog.py` | The 30+ real salon services |
| `test_recommender.py` | Offline tests (EN, FR, edge cases, questions) |

## Notes for the team

- **Prices/durations are placeholders** (typical Swiss rates). Replace with the
  real values from the `services` Firestore collection before final submission.
  The two confirmed-from-doc values are exact: Strengthening (65/45), Head Spa (120/60).
- **`serviceId`** uses readable slugs (`strengthening`, `manicure`) for now;
  swap these to the real Firestore `serviceId`s once that collection is populated.
- **Swap to OpenAI** later: change only `_get_client()` in `recommender.py`.
- **NFR-02 (<4s):** Groq typically responds in well under a second.
- Next in my module: **Price Estimator** (`/api/ai/price-estimate`, itemised
  add-on breakdown) and **Sentiment Analysis** on reviews.

## Progress

- **17Jun_2026 — Day 1:** Service Recommender (FastAPI + Groq, serviceId, fallback, edge cases)
- **18Jun_2026 — Day 2:** EN/FR multilingual support + chat questionnaire endpoint + expanded tests