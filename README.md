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
| `POST` | `/api/ai/price-estimate` | Itemised price estimate with add-ons, discounts, and deposit |
| `POST` | `/api/ai/recommend-and-price` | Recommend a service **and** price it in one call |
| `POST` | `/api/ai/analyze-sentiment` | Classify a review: positive/neutral/negative + confidence + reason |
| `GET`  | `/api/ai/reviews` | List reviews from the store (Firestore or mock) |
| `POST` | `/api/ai/analyze-review` | Read a review by id, classify it, write sentiment back to the store |

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

### Price estimate — request

```json
{
  "serviceId": "head_spa",
  "addOns": ["Hair mask"],
  "customerType": "first_time"
}
```

- `customerType` is `"regular"` (default), `"vip"` (10% off), or `"first_time"` (15% off).
- `addOns` are matched by name against the service's add-ons; unknown ones are
  returned in `unmatchedAddOns` and not charged.

### Price estimate — response

```json
{
  "service": "Head Spa Japanese",
  "serviceId": "head_spa",
  "currency": "CHF",
  "items": [
    { "name": "Head Spa Japanese", "price": 120, "duration": 60 },
    { "name": "Hair mask", "price": 25, "duration": 15 }
  ],
  "subtotal": 145,
  "discount": { "type": "first_time", "percent": 15, "amount": 21.75 },
  "total": 123.25,
  "isLuxury": true,
  "deposit": { "required": true, "percent": 20, "amount": 24.65 },
  "totalDuration": 75,
  "unmatchedAddOns": []
}
```

Business rules (confirmed 20 June): VIP 10% / first-time 15% discount; luxury
services (CHF 100+) require a 20% deposit.

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

## Deploy (Render / Railway free tier)

The app reads the host `PORT` env var and binds `0.0.0.0`, so it runs as-is on
most free hosts. A `Procfile` is included:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Steps (Render): New > Web Service > connect this repo > Build `pip install -r
requirements.txt` > Start `uvicorn main:app --host 0.0.0.0 --port $PORT` > add
env var `GROQ_API_KEY`. The frontend then calls the public URL instead of localhost.

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app + routes |
| `recommender.py` | LLM call, EN/FR handling, questions, offline fallback |
| `price_estimator.py` | Itemised price math: add-ons, quantities, discounts, deposit, VAT |
| `test_price_estimator.py` | Full offline test suite for the estimator |
| `sentiment.py` | Review sentiment: EN/FR, rating-aware, LLM + fallback |
| `firestore_client.py` | Firestore data layer with local mock fallback |
| `services_loader.py` | Reads real services from Excel/JSON into the catalog schema |
| `run_all_tests.py` | Runs all test suites in one command |
| `API_GUIDE.md` | Endpoint contracts + JS/React Native snippets for the frontend team |
| `demo.html` | Self-contained live demo page (on-brand) |
| `DELIVERY.md` | Delivery checklist, requirement coverage, demo script |
| `test_sentiment.py` | Offline test suite for sentiment |
| `Procfile` / `runtime.txt` | Deployment config (Render/Railway) |
| `services_catalog.py` | The 30+ real salon services |
| `test_recommender.py` | Offline tests (EN, FR, edge cases, questions) |

## Notes for the team

- **Prices/durations are placeholders** (typical Swiss rates). Replace with the
  real values from the `services` Firestore collection before final submission.
  The two confirmed-from-doc values are exact: Strengthening (65/45), Head Spa (120/60).
- **`serviceId`** uses readable slugs (`strengthening`, `manicure`) for now;
  swap these to the real Firestore `serviceId`s once that collection is populated.
- **Swap to OpenAI** later: change only `_get_client()` in `recommender.py`.
- **VAT:** Swiss prices are VAT-inclusive (standard rate 8.1%, 2026). The estimator
  reveals VAT from the total rather than adding it on top; confirm with the salon.
- **Real services data:** drop the salon's `services.json` or `services.xlsx` in the
  project root (or set `SERVICES_FILE`). `load_services()` loads it and keeps the
  local keywords for fallback. Until then, placeholders are used.
- **NFR-02 (<4s):** Groq typically responds in well under a second. LLM calls now
  have timeouts (3.5s recommend / 1.8s sentiment); if the model is slow the offline
  fallback returns instantly, so the latency targets always hold.
- **Observability:** every response carries an `X-Response-Time-ms` header and is
  logged with method, path, status, and latency.
- **On latency:** end-to-end time depends on the network round-trip to Groq.
  On a fast/server connection this is typically 300-800 ms (well under target);
  on a slow dev connection it can be higher. The timeout + offline fallback bound
  the worst case, and production hosting (Render/Railway) meets the <2s/<4s targets.
- **Firestore:** the review pipeline reads/writes via `firestore_client.py`. With no
  credentials it uses an in-memory mock; drop `serviceAccount.json` in the project
  root (or set `GOOGLE_APPLICATION_CREDENTIALS`) and restart to use real Firestore.

## Progress

- **17Jun_2026 — Day 1:** Service Recommender (FastAPI + Groq, serviceId, fallback, edge cases)
- **18Jun_2026 — Day 2:** EN/FR multilingual support + chat questionnaire endpoint + expanded tests
- **19Jun_2026 — Day 3:** Catalog aligned to Firestore `services` schema + sample add-ons + single data swap-point for going live
- **20Jun_2026 — Day 4:** Price Estimator endpoint — itemised add-ons, VIP/first-time discounts, 20% luxury deposit
- **21Jun_2026 — Day 5:** Estimator hardening — VAT breakout (8.1%), add-on quantities, duplicate/invalid handling, deposit reason, full test suite
- **22Jun_2026 — Day 6:** Integration & polish — combined recommend-and-price endpoint, upgraded health/info, deployment-ready (Procfile, PORT)
- **23Jun_2026 — Day 7:** Sentiment Analysis classifier — EN/FR, rating-aware, confidence + reason, LLM + fallback, full test suite
- **24Jun_2026 — Day 8:** Firestore data layer + review pipeline (read → classify → write sentiment), with mock fallback until credentials land
- **25Jun_2026 — Day 9:** Real services loader (Excel/JSON → catalog, keyword merge) wired into the swap-point + master test runner (all suites pass)
- **26Jun_2026 — Day 10:** Frontend integration guide (contracts + JS/React Native snippets) + on-brand live demo page
- **27Jun_2026 — Day 11:** Hardening — LLM timeouts to guarantee latency NFRs, request timing/logging, input-size guards
- **28Jun_2026 — Day 12:** Delivery & handoff — requirement coverage (FR36/37/38), AI checklist, demo script, run guide