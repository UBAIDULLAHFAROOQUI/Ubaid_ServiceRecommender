"""
Celine Esthetique - AI API (FastAPI)
====================================
Owner: Ubaid Ullah Farooqui (AI Developer)

Run locally:
    uvicorn main:app --reload --port 8001

Endpoints:
    GET  /                              -> health / info
    GET  /api/ai/recommend-service/questions  -> chat questionnaire (en/fr)
    POST /api/ai/recommend-service      -> Service Recommender (doc Section 10.4)
    POST /api/ai/price-estimate         -> Price Estimator (doc Section 10.4)
    POST /api/ai/recommend-and-price    -> Recommend + price in one call

Response shapes match the project document so the React web (Sibgha) and
React Native app (Sanaullah) can consume them without changes.
"""

import os
import time
import logging
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommender import recommend_service, get_questions, LANGUAGE_NAMES
from price_estimator import estimate_price
from sentiment import analyze_sentiment
from firestore_client import get_store
from services_catalog import SERVICES

APP_VERSION = "1.6.0"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("celine-ai")

app = FastAPI(title="Celine Esthetique AI - Service Recommender", version=APP_VERSION)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log method, path, status, and response time (ms) for every request,
    so we can verify the latency NFRs (<4s recommend, <2s sentiment)."""
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({ms:.0f} ms)")
    response.headers["X-Response-Time-ms"] = f"{ms:.0f}"
    return response

# Allow the web + mobile frontends to call this API.
# Tighten allow_origins to the real domain(s) before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Request / Response models
# ============================================================
class RecommendRequest(BaseModel):
    # doc format: {"answers": ["What area? nails", "What concern? brittle nails", ...]}
    answers: List[str] = Field(default_factory=list)
    language: Optional[str] = "en"          # 'en' (default) or 'fr'


class RecommendResponse(BaseModel):
    recommendedService: str
    serviceId: str
    price: float
    duration: int
    reason: str


class PriceEstimateRequest(BaseModel):
    serviceId: str
    # add-ons: either ["Gel finish"] or [{"name": "Nail art (per nail)", "quantity": 5}]
    addOns: List[Any] = Field(default_factory=list)
    customerType: Optional[str] = "regular"  # regular | vip | first_time


class RecommendAndPriceRequest(BaseModel):
    answers: List[str] = Field(default_factory=list)
    language: Optional[str] = "en"
    addOns: List[Any] = Field(default_factory=list)
    customerType: Optional[str] = "regular"


# ============================================================
# Routes
# ============================================================
@app.get("/")
def health():
    """Health / info: quick check that everything is wired up."""
    store = get_store()
    return {
        "status": "ok",
        "service": "Celine AI - Service Recommender & Price Estimator",
        "version": APP_VERSION,
        "servicesLoaded": len(SERVICES),
        "groqKeyDetected": bool(os.getenv("GROQ_API_KEY")),  # never exposes the key
        "reviewStore": store.mode,                           # "firestore" or "mock"
        "languages": list(LANGUAGE_NAMES.keys()),
        "endpoints": [
            "GET /api/ai/recommend-service/questions",
            "POST /api/ai/recommend-service",
            "POST /api/ai/price-estimate",
            "POST /api/ai/recommend-and-price",
            "POST /api/ai/analyze-sentiment",
            "GET /api/ai/reviews",
            "POST /api/ai/analyze-review",
        ],
    }


@app.get("/api/ai/recommend-service/questions")
def questions(language: str = "en"):
    """Chat-based questionnaire for the frontend to render (en/fr)."""
    return get_questions(language)


@app.post("/api/ai/recommend-service", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    return recommend_service(req.answers, req.language)


@app.post("/api/ai/price-estimate")
def price_estimate(req: PriceEstimateRequest):
    result = estimate_price(req.serviceId, req.addOns, req.customerType)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/api/ai/recommend-and-price")
def recommend_and_price(req: RecommendAndPriceRequest):
    """
    One call: recommend the best service, then price it (with any add-ons /
    customer type). Handy for the frontend so it doesn't have to chain two
    requests. The recommended serviceId always exists in the catalog, so the
    estimate step never 404s.
    """
    recommendation = recommend_service(req.answers, req.language)
    estimate = estimate_price(
        recommendation["serviceId"], req.addOns, req.customerType
    )
    return {"recommendation": recommendation, "estimate": estimate}


# ---------- Sentiment Analysis (doc Section 5.1: reviews.sentiment) ----------
class SentimentRequest(BaseModel):
    comment: str = ""
    rating: Optional[int] = None        # 1-5 star rating, used as a signal
    language: Optional[str] = "en"


@app.post("/api/ai/analyze-sentiment")
def analyze_review_sentiment(req: SentimentRequest):
    """Classify a review as positive/neutral/negative with confidence + reason.
    The `sentiment` value is written into reviews.{id}.sentiment (see /analyze-review)."""
    return analyze_sentiment(req.comment, req.rating, req.language)


# ---------- Review pipeline: read from store -> classify -> write back ----------
class AnalyzeReviewRequest(BaseModel):
    reviewId: str


@app.get("/api/ai/reviews")
def list_reviews():
    """List reviews from the store (real Firestore if configured, else mock)."""
    store = get_store()
    return {"source": store.mode, "reviews": store.list_reviews()}


@app.post("/api/ai/analyze-review")
def analyze_review(req: AnalyzeReviewRequest):
    """
    Full pipeline for one review:
      1. read the review (comment + rating) from the store
      2. classify sentiment
      3. write the result into reviews/{id}.sentiment
    Works against the mock today; against real Firestore once credentials exist.
    """
    store = get_store()
    review = store.get_review(req.reviewId)
    if review is None:
        raise HTTPException(status_code=404,
                            detail=f"Review '{req.reviewId}' not found.")
    result = analyze_sentiment(
        review.get("comment", ""), review.get("rating"),
        review.get("language", "en"),
    )
    written = store.set_sentiment(req.reviewId, result["sentiment"])
    return {
        "reviewId": req.reviewId,
        "sentiment": result["sentiment"],
        "confidence": result["confidence"],
        "reason": result["reason"],
        "writtenToStore": written,
        "storeMode": store.mode,   # "firestore" or "mock"
    }


# Lets you start the server by clicking VS Code's "Run" button,
# or with:  python main.py
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))   # respect host PORT (Render/Railway)
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)