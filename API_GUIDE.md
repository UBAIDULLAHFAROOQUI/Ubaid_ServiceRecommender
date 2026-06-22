# Celine Esthetique — AI API Integration Guide

**For:** Frontend (Sibgha — React web) & Mobile (Sanaullah — React Native)
**Owner:** Ubaid Ullah Farooqui (AI Developer)
**Base URL (local):** `http://127.0.0.1:8001`
**Base URL (deployed):** _set once hosted on Render/Railway_

All endpoints accept and return JSON. CORS is open, so the web and mobile apps
can call them directly. Every response shape below is a **fixed contract** —
build against these field names.

---

## Quick reference

| Method | Path | Use |
|--------|------|-----|
| `GET`  | `/` | Health / info |
| `GET`  | `/api/ai/recommend-service/questions?language=en\|fr` | Get the questionnaire to render |
| `POST` | `/api/ai/recommend-service` | Recommend one service |
| `POST` | `/api/ai/price-estimate` | Price a service + add-ons |
| `POST` | `/api/ai/recommend-and-price` | Recommend **and** price in one call |
| `POST` | `/api/ai/analyze-sentiment` | Classify free review text |
| `GET`  | `/api/ai/reviews` | List reviews from the store |
| `POST` | `/api/ai/analyze-review` | Classify a stored review by id and save it |

---

## 1. Questionnaire — `GET /api/ai/recommend-service/questions`

Render these as the chat questionnaire. Pass `language=en` or `language=fr`.

**Response**
```json
{
  "language": "en",
  "questions": [
    { "key": "area",     "question": "Which area would you like to focus on?", "options": ["Nails", "Hands", "Feet", "Face / hair removal", "Eyes / lashes", "Head / scalp"] },
    { "key": "concern",  "question": "What is your main concern?", "options": ["Brittle / weak nails", "..."] },
    { "key": "occasion", "question": "What is the occasion?", "options": ["Daily / everyday", "..."] }
  ]
}
```

---

## 2. Recommend — `POST /api/ai/recommend-service`

**Request**
```json
{ "answers": ["area: nails", "concern: brittle nails", "occasion: daily"], "language": "en" }
```
- `answers`: the user's chosen options (any text works; `"area: nails"` or full sentences).
- `language`: `"en"` (default) or `"fr"`.

**Response (contract)**
```json
{
  "recommendedService": "Strengthening natural nails",
  "serviceId": "strengthening",
  "price": 65,
  "duration": 45,
  "reason": "Strengthen your brittle nails."
}
```
Use `serviceId` to link to the service detail page.

---

## 3. Price estimate — `POST /api/ai/price-estimate`

**Request**
```json
{ "serviceId": "head_spa", "addOns": ["Hair mask"], "customerType": "first_time" }
```
- `addOns`: names, or `[{ "name": "Nail art (per nail)", "quantity": 5 }]`.
- `customerType`: `"regular"` | `"vip"` (10% off) | `"first_time"` (15% off).

**Response (contract)**
```json
{
  "service": "Head Spa Japanese",
  "serviceId": "head_spa",
  "currency": "CHF",
  "items": [
    { "name": "Head Spa Japanese", "unitPrice": 120, "quantity": 1, "lineTotal": 120, "unitDuration": 60, "lineDuration": 60 }
  ],
  "subtotal": 145,
  "discount": { "type": "first_time", "percent": 15, "amount": 21.75 },
  "total": 123.25,
  "vat": { "included": true, "percent": 8.1, "net": 114.01, "amount": 9.24 },
  "isLuxury": true,
  "deposit": { "required": true, "percent": 20, "amount": 24.65, "reason": "Luxury treatment (CHF 100+) requires a 20% deposit." },
  "totalDuration": 75,
  "unmatchedAddOns": []
}
```
Unknown `serviceId` → HTTP **404**.

---

## 4. Recommend AND price — `POST /api/ai/recommend-and-price`

One call for the whole flow. Same inputs as recommend + add-ons/customerType.

**Request**
```json
{ "answers": ["area: nails", "concern: brittle nails"], "addOns": ["Hand massage"], "customerType": "vip", "language": "en" }
```

**Response**
```json
{ "recommendation": { ...recommend contract... }, "estimate": { ...price contract... } }
```

---

## 5. Sentiment (free text) — `POST /api/ai/analyze-sentiment`

**Request**
```json
{ "comment": "Loved it, staff were amazing!", "rating": 5, "language": "en" }
```

**Response (contract)**
```json
{ "sentiment": "positive", "confidence": 100, "reason": "Staff were amazing." }
```
`sentiment` is always one of `positive` | `neutral` | `negative`.

---

## 6. Stored reviews — `GET /api/ai/reviews` and `POST /api/ai/analyze-review`

`GET /api/ai/reviews` → `{ "source": "mock", "reviews": [ ... ] }`

`POST /api/ai/analyze-review` with `{ "reviewId": "rev_002" }` reads that review,
classifies it, and writes `sentiment` back into the store.
```json
{ "reviewId": "rev_002", "sentiment": "negative", "confidence": 90, "reason": "...", "writtenToStore": true, "storeMode": "mock" }
```

---

## Code snippets

### React / web (fetch) — Sibgha

```js
const API = "http://127.0.0.1:8001";

// Recommend + price in one call
async function recommendAndPrice(answers, addOns = [], customerType = "regular", language = "en") {
  const res = await fetch(`${API}/api/ai/recommend-and-price`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers, addOns, customerType, language }),
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json(); // { recommendation, estimate }
}

// Usage
const data = await recommendAndPrice(["area: nails", "concern: brittle nails"], ["Hand massage"], "vip");
console.log(data.recommendation.recommendedService, data.estimate.total);
```

### React Native (fetch) — Sanaullah

```js
const API = "http://127.0.0.1:8001"; // use the deployed URL on device

export async function analyzeReview(reviewId) {
  const res = await fetch(`${API}/api/ai/analyze-review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewId }),
  });
  return res.json();
}
```

### axios (either)

```js
import axios from "axios";
const api = axios.create({ baseURL: "http://127.0.0.1:8001" });

const { data } = await api.post("/api/ai/price-estimate", {
  serviceId: "head_spa",
  addOns: [{ name: "Hair mask", quantity: 1 }],
  customerType: "vip",
});
```

---

## Notes
- On a real device, `127.0.0.1` points at the phone, not your laptop — use the
  deployed URL (or your machine's LAN IP) for React Native testing.
- Errors: unknown service → 404; malformed body → 422 with a `detail` array.
- Prices are placeholder until the salon's real data file is loaded (same contract either way).
