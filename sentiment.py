"""
Celine Esthetique - AI Review Sentiment Analysis (core logic)
=============================================================
Owner: Ubaid Ullah Farooqui (AI Developer)
Endpoint served by main.py:  POST /api/ai/analyze-sentiment

Classifies a customer review as positive / neutral / negative, with a confidence
score and a short reason. Writes into the `reviews.sentiment` field (doc 5.1).

Architecture mirrors the recommender:
  1. Try Groq LLM (accurate, handles sarcasm, EN/FR). Must run < 2s (supervisor).
  2. If unavailable -> offline keyword + rating fallback, so it ALWAYS returns a
     result (AI checklist: "fallback responses implemented").

Rating-aware: reviews have a 1-5 `rating` as well as `comment` text. We feed the
rating to the model as a signal, and the fallback combines keyword hits with the
rating so a 5-star "ok" reads positive and a 1-star rant reads negative.
"""

import os
import json

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from groq import Groq
except ImportError:
    Groq = None

MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
LLM_TIMEOUT = 1.8   # seconds; keeps sentiment under the 2s target (falls back if slow)

VALID = {"positive", "neutral", "negative"}
LANGUAGE_NAMES = {"en": "English", "fr": "French"}

SYSTEM_PROMPT = """You analyse customer reviews for Celine Esthetique, a luxury
beauty & nail salon in Lausanne. Classify the review's sentiment.

You receive the review text (which may be English or French) and sometimes a
star rating (1-5). Use both. If the text is sarcastic or disagrees with the
rating, trust the overall meaning of the text.

Return ONLY a JSON object, no markdown:
{{"sentiment": "positive|neutral|negative", "confidence": <0-100 integer>, "reason": "<one short sentence in {language_name}>"}}
The reason must be one short sentence (max 18 words)."""

# --- Offline fallback lexicons (EN + FR) ---
POSITIVE_WORDS = {
    # EN
    "love", "loved", "great", "amazing", "excellent", "perfect", "wonderful",
    "fantastic", "best", "happy", "friendly", "clean", "relaxing", "professional",
    "recommend", "beautiful", "lovely", "good", "nice", "satisfied", "gentle",
    "welcoming", "pleased", "pleasant", "awesome", "superb", "delighted",
    # FR
    "adore", "adoré", "génial", "geniale", "excellent", "parfait", "magnifique",
    "super", "merveilleux", "meilleur", "content", "contente", "propre",
    "professionnel", "recommande", "agréable", "gentil", "accueillant", "ravi",
    "ravie", "satisfait", "satisfaite", "génial",
}
NEGATIVE_WORDS = {
    # EN
    "bad", "terrible", "awful", "worst", "rude", "dirty", "painful", "pain",
    "disappointed", "disappointing", "late", "unprofessional", "horrible",
    "poor", "waste", "hate", "hated", "unhappy", "slow", "cold", "never",
    "rushed", "overpriced", "ruined",
    # FR
    "mauvais", "terrible", "horrible", "pire", "impoli", "sale", "douloureux",
    "déçu", "deçu", "déçue", "déception", "deception", "retard", "jamais",
    "nul", "déteste", "deteste", "lent", "froid", "gâché", "gache",
}

FALLBACK_REASON = {
    "en": {
        "positive": "The review expresses clear satisfaction.",
        "negative": "The review expresses clear dissatisfaction.",
        "neutral": "The review is mixed or neutral in tone.",
    },
    "fr": {
        "positive": "L'avis exprime une nette satisfaction.",
        "negative": "L'avis exprime un net mécontentement.",
        "neutral": "L'avis est mitigé ou neutre.",
    },
}


def _get_client():
    if Groq is None:
        return None
    key = os.getenv("GROQ_API_KEY")
    return Groq(api_key=key) if key else None


def _llm_sentiment(comment, rating, language):
    client = _get_client()
    if client is None:
        return None
    language_name = LANGUAGE_NAMES.get(language, "English")
    user = f"Review text: {comment}"
    if rating is not None:
        user += f"\nStar rating: {rating}/5"
    try:
        resp = client.with_options(
            timeout=LLM_TIMEOUT, max_retries=0
        ).chat.completions.create(
            model=MODEL, temperature=0.0, max_tokens=120,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": SYSTEM_PROMPT.format(language_name=language_name)},
                {"role": "user", "content": user},
            ],
        )
        data = json.loads(resp.choices[0].message.content)
        sentiment = str(data.get("sentiment", "")).lower().strip()
        if sentiment not in VALID:
            return None
        confidence = int(data.get("confidence", 70))
        confidence = max(0, min(100, confidence))
        reason = str(data.get("reason", "")).strip()
        return {"sentiment": sentiment, "confidence": confidence,
                "reason": reason or FALLBACK_REASON[language][sentiment]}
    except Exception as e:
        print(f"[sentiment] LLM failed, using fallback: {e}")
        return None


def _fallback_sentiment(comment, rating, language):
    text = (comment or "").lower()
    words = set(text.replace(".", " ").replace(",", " ").split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)

    score = pos - neg
    if rating is not None:        # rating is a strong signal
        if rating >= 4:
            score += 2
        elif rating <= 2:
            score -= 2

    if score > 0:
        sentiment = "positive"
    elif score < 0:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # confidence grows with the margin; neutral stays modest
    confidence = 50 if sentiment == "neutral" else min(90, 55 + abs(score) * 12)
    reasons = FALLBACK_REASON.get(language, FALLBACK_REASON["en"])
    return {"sentiment": sentiment, "confidence": confidence,
            "reason": reasons[sentiment]}


def analyze_sentiment(comment, rating=None, language="en"):
    """
    Public entry point.
    Returns: {sentiment, confidence, reason}
      sentiment   : 'positive' | 'neutral' | 'negative'
      confidence  : 0-100
      reason      : one short sentence (in `language`)
    """
    if language not in LANGUAGE_NAMES:
        language = "en"
    if rating is not None:
        try:
            rating = int(rating)
            if not 1 <= rating <= 5:
                rating = None
        except (TypeError, ValueError):
            rating = None
    if comment and len(comment) > 4000:
        comment = comment[:4000]   # guard against oversized input
    if not comment and rating is None:
        return {"sentiment": "neutral", "confidence": 50,
                "reason": FALLBACK_REASON[language]["neutral"]}

    return (_llm_sentiment(comment, rating, language)
            or _fallback_sentiment(comment, rating, language))