"""
Celine Esthetique - AI API (FastAPI)
====================================
Owner: Ubaid Ullah Farooqui (AI Developer)

Run locally:
    uvicorn main:app --reload --port 8001

Endpoints:
    GET  /                         -> health check
    POST /api/ai/recommend-service -> Service Recommender (doc Section 10.4)

The response shape matches the project document exactly so the React web
(Sibgha) and React Native app (Sanaullah) can consume it without changes.
"""

from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommender import recommend_service

app = FastAPI(title="Celine Esthetique AI - Service Recommender", version="1.0.0")

# Allow the web + mobile frontends to call this API.
# Tighten allow_origins to the real domain(s) before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request / Response models (match the doc) ----------
class RecommendRequest(BaseModel):
    # doc format: {"answers": ["What area? nails", "What concern? brittle nails", ...]}
    answers: List[str] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    recommendedService: str
    serviceId: str
    price: float
    duration: int
    reason: str


# ---------- Routes ----------
@app.get("/")
def health():
    return {"status": "ok", "service": "Celine AI - Service Recommender"}


@app.post("/api/ai/recommend-service", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    return recommend_service(req.answers)


# Lets you start the server by clicking VS Code's "Run" button,
# or with:  python main.py   (same as: uvicorn main:app --port 8001)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)