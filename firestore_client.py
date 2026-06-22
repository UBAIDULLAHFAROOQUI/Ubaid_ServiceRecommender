"""
Celine Esthetique - Firestore data layer (with local mock fallback)
===================================================================
Owner: Ubaid Ullah Farooqui (AI Developer)

The Sentiment pipeline must READ a review's comment and WRITE the sentiment back
into reviews/{id}.sentiment (doc Section 5.1). That needs Firestore — but the
Service Account JSON isn't provisioned yet.

So this layer talks to an interface, not to Firestore directly:
  - If a Service Account JSON is available (env GOOGLE_APPLICATION_CREDENTIALS,
    or ./serviceAccount.json) AND firebase-admin is installed -> use real Firestore.
  - Otherwise -> use an in-memory MOCK seeded with sample reviews that behaves
    identically.

This means the FULL read -> classify -> write pipeline runs and is testable TODAY.
When the credentials land, drop the JSON in the project root (or set the env var)
and restart — nothing else changes. `get_store().live` tells you which mode you're in.
"""

import os

CRED_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "serviceAccount.json"


# ---------------------------------------------------------------------------
# Sample reviews for the mock (EN + FR, varied sentiment). These mimic documents
# in the `reviews` collection. Replaced by real data the moment Firestore is live.
# ---------------------------------------------------------------------------
SAMPLE_REVIEWS = {
    "rev_001": {"reviewId": "rev_001", "userName": "Sophie",
                "serviceId": "manicure", "rating": 5, "language": "en",
                "comment": "Absolutely loved it, the staff were so friendly and gentle!",
                "sentiment": None},
    "rev_002": {"reviewId": "rev_002", "userName": "Marc",
                "serviceId": "head_spa", "rating": 2, "language": "fr",
                "comment": "Service décevant, j'ai attendu très longtemps et personnel froid.",
                "sentiment": None},
    "rev_003": {"reviewId": "rev_003", "userName": "Lena",
                "serviceId": "lash_extensions", "rating": 3, "language": "en",
                "comment": "It was okay. Nice result but a bit pricey for what it is.",
                "sentiment": None},
    "rev_004": {"reviewId": "rev_004", "userName": "Claire",
                "serviceId": "pedicure", "rating": 5, "language": "fr",
                "comment": "Magnifique, salon très propre et personnel accueillant. Je recommande !",
                "sentiment": None},
}


class MockReviewStore:
    """In-memory stand-in for the Firestore `reviews` collection."""
    live = False
    mode = "mock"

    def __init__(self):
        # deep-ish copy so writes don't mutate the seed constant
        self._reviews = {k: dict(v) for k, v in SAMPLE_REVIEWS.items()}

    def get_review(self, review_id):
        r = self._reviews.get(review_id)
        return dict(r) if r else None

    def list_reviews(self):
        return [dict(r) for r in self._reviews.values()]

    def set_sentiment(self, review_id, sentiment):
        if review_id not in self._reviews:
            return False
        self._reviews[review_id]["sentiment"] = sentiment
        return True


class FirestoreReviewStore:
    """Real Firestore-backed store (used once credentials are provisioned)."""
    live = True
    mode = "firestore"

    def __init__(self, cred_path):
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(cred_path))
        self._db = firestore.client()

    def get_review(self, review_id):
        doc = self._db.collection("reviews").document(review_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["reviewId"] = doc.id
        return data

    def list_reviews(self):
        out = []
        for doc in self._db.collection("reviews").stream():
            d = doc.to_dict()
            d["reviewId"] = doc.id
            out.append(d)
        return out

    def set_sentiment(self, review_id, sentiment):
        self._db.collection("reviews").document(review_id).update(
            {"sentiment": sentiment}
        )
        return True


_store = None


def get_store():
    """Return the active store (real Firestore if configured, else mock)."""
    global _store
    if _store is not None:
        return _store
    if os.path.exists(CRED_PATH):
        try:
            _store = FirestoreReviewStore(CRED_PATH)
            print(f"[firestore] Connected to real Firestore via {CRED_PATH}")
            return _store
        except Exception as e:
            print(f"[firestore] Could not init Firestore ({e}); using mock.")
    _store = MockReviewStore()
    return _store
