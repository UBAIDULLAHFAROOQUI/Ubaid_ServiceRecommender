# Celine Esthetique AI Module — One-Page Summary

**Ubaid Ullah Farooqui** · AI Developer (Intern #8) · 13-day internship
**Repo:** github.com/UBAIDULLAHFAROOQUI/Ubaid_ServiceRecommender

## What it is
A FastAPI service powering three AI features for a luxury Lausanne beauty salon,
consumed by the React web app and React Native mobile app.

## The three features
1. **Service Recommender** — a chat questionnaire (area → concern → occasion)
   returns the single best service from the salon's 30+ offerings, with price,
   duration, and a reason. *(FR36)*
2. **Price Estimator** — itemised cost of a service + add-ons, with VIP/first-time
   discounts, a 20% luxury deposit, and Swiss VAT (8.1%) broken out. *(FR37)*
3. **Review Sentiment** — classifies reviews positive/neutral/negative with a
   confidence score, and writes the result into Firestore. *(FR38)*

## Engineering highlights
- **Bilingual (EN/FR)** across all three features — built for Lausanne's audience.
- **Always-on reliability** — every feature has an offline fallback, so the API
  never returns nothing, even if the AI is down (AI-checklist requirement).
- **Swap-points for real data** — placeholder services and a mock review store
  flip to the salon's real Excel/JSON and Firebase with zero code change.
- **Free LLM** — Groq instead of paid OpenAI; one-line swap if that changes.
- **Production touches** — combined endpoint, request logging, latency header,
  timeouts, deployment config, and a full test suite (`run_all_tests.py`).
- **Handoff-ready** — `API_GUIDE.md` (contracts + snippets) and a live `demo.html`.

## Stack
Python · FastAPI · Groq (Llama 3.3) · firebase-admin · openpyxl · pytest-style suites

## Status
All three assigned features complete, tested, documented, and integration-ready.
Pending only external inputs (salon data file, Firebase credentials) that plug in
without code changes.
