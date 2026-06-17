"""
Celine Esthetique - AI Service Recommender (core logic)
=======================================================
Owner: Ubaid Ullah Farooqui (AI Developer)
Endpoint served by main.py:  POST /api/ai/recommend-service

Flow:
  1. Try the LLM (Groq, OpenAI-compatible). It must pick ONE service name
     that exists in the catalog and give a short reason.
  2. Validate the returned name against SERVICES_BY_NAME.
  3. If the LLM is unavailable or returns garbage -> keyword fallback matcher.
This guarantees a valid recommendation every time (AI checklist requirement).

Swap to OpenAI later: change the client init in `_get_client()` only.
"""

import os
import json

# Load variables from a local .env file (GROQ_API_KEY, GROQ_MODEL) if present.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from services_catalog import SERVICES, SERVICES_BY_NAME, catalog_for_prompt

# Groq's Python SDK is OpenAI-compatible. `pip install groq`
try:
    from groq import Groq
except ImportError:  # keeps fallback working even if groq isn't installed yet
    Groq = None

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are Celine AI, the service recommender for Celine Esthetique,
a luxury beauty & nail salon in Lausanne, Switzerland.

You are given a list of the ONLY services the salon offers, and a short
questionnaire the client answered. Recommend the SINGLE best-matching service.

Rules:
- You MUST choose a service name EXACTLY as written in the catalog. Do not invent.
- If the client mentions SEVERAL needs at once, pick the ONE that best fits their
  main concern, and acknowledge the others briefly in the reason.
- If the concern is unclear or not covered by any service, choose the closest
  reasonable option and keep the reason gentle and inviting (do not refuse).
- Reply with ONLY a JSON object, no markdown, no extra text:
  {{"recommendedService": "<exact name>", "reason": "<one warm sentence>"}}
- The reason must be one short, professional, friendly sentence (max 20 words).

Catalog:
{catalog}
"""


def _get_client():
    """Return a Groq client, or None if unavailable (triggers fallback)."""
    if Groq is None:
        return None
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    return Groq(api_key=api_key)


def _build_user_message(answers):
    """answers: list[str] like ['What area? nails', 'What concern? brittle nails']"""
    joined = "\n".join(f"- {a}" for a in answers)
    return f"Client questionnaire answers:\n{joined}\n\nRecommend one service."


def _llm_recommend(answers):
    """Call the LLM. Returns a service dict + reason, or None on any failure."""
    client = _get_client()
    if client is None:
        return None
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": SYSTEM_PROMPT.format(catalog=catalog_for_prompt())},
                {"role": "user", "content": _build_user_message(answers)},
            ],
        )
        raw = resp.choices[0].message.content
        data = json.loads(raw)
        name = data.get("recommendedService", "").strip()
        reason = data.get("reason", "").strip()
        service = SERVICES_BY_NAME.get(name)
        if service is None:
            return None  # LLM hallucinated a name -> fall back
        return {"service": service,
                "reason": reason or f"This treatment is well suited to your needs."}
    except Exception as e:  # network, parse, auth, rate limit -> fallback
        print(f"[recommender] LLM failed, using fallback: {e}")
        return None


def _keyword_fallback(answers):
    """Offline matcher: score each service by keyword hits in the answers.
    Strips the question label (text before ':' or '?') so scaffolding words like
    'area', 'concern', 'occasion' don't pollute the match. Handles both request
    styles: 'What area? nails' and 'area: nails'."""
    values = []
    for a in answers:
        v = a
        for sep in ("?", ":"):
            if sep in v:
                v = v.split(sep, 1)[1]
                break
        values.append(v)
    text = " ".join(values).lower()
    best, best_score = None, 0
    for s in SERVICES:
        score = sum(1 for kw in s["keywords"] if kw in text)
        if score > best_score:
            best, best_score = s, score
    if best is None:  # nothing matched -> safe, inviting default
        best = SERVICES_BY_NAME["Manicure"]
        return {
            "service": best,
            "reason": "We weren't sure of your exact need, so our classic "
                      "manicure is a lovely place to start — tell us more anytime.",
        }
    return {
        "service": best,
        "reason": f"Based on your answers, our {best['name'].lower()} is a great fit.",
    }


def recommend_service(answers):
    """
    Public entry point.
    Returns the exact response shape from the project doc (Section 10.4):
      {recommendedService, price, duration, reason}
    """
    if not answers:
        answers = []

    result = _llm_recommend(answers) or _keyword_fallback(answers)
    s = result["service"]
    return {
        "recommendedService": s["name"],
        "serviceId": s["id"],          # lets the frontend deep-link to the detail page
        "price": s["price"],
        "duration": s["duration"],
        "reason": result["reason"],
    }