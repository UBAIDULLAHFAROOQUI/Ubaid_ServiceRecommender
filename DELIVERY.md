# Celine Esthetique — AI Module Delivery & Handoff

**Owner:** Ubaid Ullah Farooqui (AI Developer, Intern #8)
**Module:** AI Service Recommender · Price Estimator · Review Sentiment Analysis
**Repo:** https://github.com/UBAIDULLAHFAROOQUI/Ubaid_ServiceRecommender

---

## 1. Assigned scope vs. delivered

Per the project document, my assignment was:
> **Service Recommender** (chat questionnaire) + **Price Estimator** (total with add-ons) + **Sentiment Analysis** on reviews.

| Feature | Endpoint | Status |
|---------|----------|--------|
| Service Recommender | `POST /api/ai/recommend-service` | ✅ Delivered |
| Questionnaire | `GET /api/ai/recommend-service/questions` | ✅ Delivered |
| Price Estimator | `POST /api/ai/price-estimate` | ✅ Delivered |
| Recommend + Price (combined) | `POST /api/ai/recommend-and-price` | ✅ Delivered |
| Sentiment (free text) | `POST /api/ai/analyze-sentiment` | ✅ Delivered |
| Sentiment (stored review → Firestore) | `POST /api/ai/analyze-review` | ✅ Delivered |
| Reviews list | `GET /api/ai/reviews` | ✅ Delivered |
| Health / info | `GET /` | ✅ Delivered |

**All three assigned features are complete, tested, and working.**

---

## 2. Functional requirements coverage (doc SRS §6.1)

| FR | Requirement | Status |
|----|-------------|--------|
| FR36 | AI asks questions to recommend the best service | ✅ Questionnaire + recommender |
| FR37 | AI estimates total price with add-ons | ✅ Itemised estimator (+ discounts, deposit, VAT) |
| FR38 | AI automatically analyses review sentiment | ✅ Classifier + Firestore write-back |

## 3. AI checklist (doc §11.3)

| Item | Status |
|------|--------|
| API keys in `.env` | ✅ `GROQ_API_KEY` via `.env`, never committed |
| Service recommender functional | ✅ Verified (EN/FR) |
| Price estimator functional | ✅ Verified (add-ons, discounts, deposit, VAT) |
| Review sentiment functional | ✅ Verified (EN/FR, rating-aware) |
| Response < 4 seconds (NFR-02) | ✅ Timeout + instant fallback bound the worst case |
| Fallback responses implemented | ✅ Every feature has an offline fallback |

## 4. Non-functional requirements

| NFR | Target | Status |
|-----|--------|--------|
| NFR-02 | AI response < 4s (sentiment < 2s) | ✅ Timeouts (3.5s/1.8s) + fallback; logged via `X-Response-Time-ms` |
| NFR-04 | API keys in `.env` | ✅ |
| Fallback | Always return a valid result | ✅ |

---

## 5. Beyond the brief (extra value)

- **English + French** across all three features (Lausanne is French-speaking).
- **Discounts & deposit** per supervisor rules (VIP 10%, first-time 15%, luxury 20% deposit).
- **Swiss VAT (8.1%)** broken out, inclusive.
- **Firestore-shaped catalog** + single swap-point: drop in real data, zero code change.
- **Real services loader** (Excel/JSON) ready for the salon's file.
- **Combined endpoint**, **deployment-ready** (Procfile/PORT), **request logging**.
- **Frontend integration guide** (`API_GUIDE.md`) + **live demo page** (`demo.html`).

---

## 6. Pending (external dependencies, not blockers)

These flip on with no code change when the inputs arrive:

| Item | What happens when it arrives |
|------|------------------------------|
| Salon services Excel/JSON | Drop file in root (or set `SERVICES_FILE`) → real prices everywhere |
| Firebase Service Account JSON | Drop `serviceAccount.json` in root → review store flips `mock` → `firestore` |

---

## 7. How to run (for evaluators / teammates)

```bash
pip install -r requirements.txt
cp .env.example .env        # add a free Groq key (console.groq.com/keys)
uvicorn main:app --port 8001
```
- Interactive docs: http://127.0.0.1:8001/docs
- Live demo: open `demo.html` in a browser
- Run all tests: `python run_all_tests.py`

---

## 8. Demo script (for the video / screenshots)

1. **Health** — open `GET /` → show version, services loaded, languages, store mode.
2. **Recommender (EN)** — `recommend-service` with brittle-nails answers → Strengthening natural nails.
3. **Recommender (FR)** — same with `"language":"fr"` → French reason.
4. **Price Estimator** — `price-estimate` Head Spa + Hair mask, first-time → show subtotal, discount, VAT, deposit.
5. **Combined** — `recommend-and-price` → one call, both results.
6. **Sentiment (EN + FR)** — `analyze-sentiment` positive English + negative French.
7. **Firestore pipeline** — `analyze-review` on `rev_002` → then `GET /reviews` shows sentiment written back.
8. **Demo page** — open `demo.html`, run a recommendation and a sentiment analysis live.
9. **Tests** — run `python run_all_tests.py` → `ALL SUITES PASSED`.
