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
LLM_TIMEOUT = 3.5   # seconds; keeps recommender under the 4s NFR (falls back if slow)

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
- The "recommendedService" value is ALWAYS the exact English catalog name.
- Write the "reason" in {language_name}.
- Reply with ONLY a JSON object, no markdown, no extra text:
  {{"recommendedService": "<exact english name>", "reason": "<one warm sentence in {language_name}>"}}
- The reason must be one short, professional, friendly sentence (max 20 words).

Catalog:
{catalog}
"""

# Lausanne is French-speaking, so French is fully supported.
LANGUAGE_NAMES = {"en": "English", "fr": "French"}

# French -> English hints so the OFFLINE fallback can still match French input.
# (When the LLM is available it handles French natively; this is the safety net.)
FR_HINTS = {
    "ongles": "nails", "ongle": "nails", "cassants": "brittle", "cassant": "brittle",
    "fragiles": "brittle", "faibles": "weak nails", "abîmés": "damaged",
    "mains": "hands", "pieds": "feet", "pied": "feet",
    "cils": "lash extensions", "extension": "extensions", "extensions de cils": "lash extensions",
    "sourcils": "eyebrow", "épilation": "hair removal", "epilation": "hair removal",
    "lèvre": "upper lip", "levre": "upper lip", "menton": "chin", "jambe": "leg",
    "jambes": "legs", "aisselles": "armpit", "maillot": "bikini", "visage": "face",
    "cuir chevelu": "scalp", "cheveux": "hair", "stress": "stress", "détente": "relax",
    "detente": "relax", "relaxant": "relax", "tête": "head", "tete": "head",
    "manucure": "manicure", "pédicure": "pedicure", "pedicure": "pedicure",
    "vernis": "varnish", "gel": "gel", "fatigués": "tired", "fatigues": "tired",
    "mariage": "wedding", "occasion": "occasion", "pellicules": "dandruff",
}

# Localised reason templates for the offline fallback.
FALLBACK_REASONS = {
    "en": {
        "match": "Based on your answers, our {name} is a great fit.",
        "default": "We weren't sure of your exact need, so our classic manicure is "
                   "a lovely place to start — tell us more anytime.",
    },
    "fr": {
        "match": "D'après vos réponses, notre prestation {name} est idéale pour vous.",
        "default": "Nous n'étions pas sûrs de votre besoin exact ; notre manucure "
                   "classique est un excellent point de départ — dites-nous en plus.",
    },
}


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


def _llm_recommend(answers, language="en"):
    """Call the LLM. Returns a service dict + reason, or None on any failure."""
    client = _get_client()
    if client is None:
        return None
    language_name = LANGUAGE_NAMES.get(language, "English")
    try:
        resp = client.with_options(timeout=LLM_TIMEOUT, max_retries=0).chat.completions.create(
            model=MODEL,
            temperature=0.3,
            max_tokens=200,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": SYSTEM_PROMPT.format(catalog=catalog_for_prompt(),
                                                 language_name=language_name)},
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
                "reason": reason or "This treatment is well suited to your needs."}
    except Exception as e:  # network, parse, auth, rate limit -> fallback
        print(f"[recommender] LLM failed, using fallback: {e}")
        return None


def _keyword_fallback(answers, language="en"):
    """Offline matcher: score each service by keyword hits in the answers.
    Strips the question label (text before ':' or '?') so scaffolding words like
    'area', 'concern', 'occasion' don't pollute the match. Handles both request
    styles ('What area? nails' and 'area: nails') and French input via FR_HINTS."""
    reasons = FALLBACK_REASONS.get(language, FALLBACK_REASONS["en"])
    values = []
    for a in answers:
        v = a
        for sep in ("?", ":"):
            if sep in v:
                v = v.split(sep, 1)[1]
                break
        values.append(v)
    text = " ".join(values).lower()

    # Add English equivalents of any French terms so the matcher can score them.
    for fr, en in FR_HINTS.items():
        if fr in text:
            text += " " + en

    best, best_score = None, 0
    for s in SERVICES:
        score = sum(1 for kw in s["keywords"] if kw in text)
        if score > best_score:
            best, best_score = s, score
    if best is None:  # nothing matched -> safe, inviting default
        return {"service": SERVICES_BY_NAME["Manicure"], "reason": reasons["default"]}
    return {"service": best,
            "reason": reasons["match"].format(name=best["name"].lower())}


def recommend_service(answers, language="en"):
    """
    Public entry point.
    Returns the response shape from the project doc (Section 10.4) plus serviceId:
      {recommendedService, serviceId, price, duration, reason}
    `language` is 'en' or 'fr' (Lausanne is French-speaking).
    """
    if language not in LANGUAGE_NAMES:
        language = "en"
    if not answers:
        answers = []

    result = _llm_recommend(answers, language) or _keyword_fallback(answers, language)
    s = result["service"]
    return {
        "recommendedService": s["name"],
        "serviceId": s["serviceId"],   # matches Firestore `services.serviceId`
        "price": s["price"],
        "duration": s["duration"],
        "reason": result["reason"],
    }


# ---------------------------------------------------------------------------
# Chat-based questionnaire (doc: "chat-based questionnaire").
# The frontend calls get_questions() to render the step-by-step flow instead
# of hard-coding the questions. Returns EN + FR so it works for both audiences.
# ---------------------------------------------------------------------------
QUESTIONS = [
    {
        "key": "area",
        "en": {"question": "Which area would you like to focus on?",
               "options": ["Nails", "Hands", "Feet", "Face / hair removal",
                           "Eyes / lashes", "Head / scalp"]},
        "fr": {"question": "Quelle zone souhaitez-vous traiter ?",
               "options": ["Ongles", "Mains", "Pieds", "Visage / épilation",
                           "Yeux / cils", "Tête / cuir chevelu"]},
    },
    {
        "key": "concern",
        "en": {"question": "What is your main concern?",
               "options": ["Brittle / weak nails", "Long-lasting colour",
                           "Unwanted hair", "Fuller lashes", "Stress / tension",
                           "Dry or itchy scalp", "Just pampering"]},
        "fr": {"question": "Quelle est votre principale préoccupation ?",
               "options": ["Ongles cassants / faibles", "Couleur longue tenue",
                           "Pilosité indésirable", "Cils plus fournis",
                           "Stress / tension", "Cuir chevelu sec", "Juste se faire plaisir"]},
    },
    {
        "key": "occasion",
        "en": {"question": "What is the occasion?",
               "options": ["Daily / everyday", "Special event", "Wedding", "Relaxation"]},
        "fr": {"question": "Quelle est l'occasion ?",
               "options": ["Quotidien", "Événement spécial", "Mariage", "Détente"]},
    },
]


def get_questions(language="en"):
    """Return the ordered questionnaire in the requested language ('en'/'fr')."""
    if language not in LANGUAGE_NAMES:
        language = "en"
    return {
        "language": language,
        "questions": [
            {"key": q["key"],
             "question": q[language]["question"],
             "options": q[language]["options"]}
            for q in QUESTIONS
        ],
    }