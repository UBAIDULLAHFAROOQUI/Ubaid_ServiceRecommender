"""
Celine Esthetique - Service Catalog
====================================
Owner: Ubaid Ullah Farooqui (AI Developer)

This catalog now mirrors the real Firestore `services` collection schema
(project doc Section 5.1):

    services: {
      serviceId, name, category, description,
      duration, price, oldPrice (optional),
      imageURL, isPopular, isAvailable,
      addOns: [{ name, price, duration }],
      staffIds
    }

Matching the schema means that when Ayesha/Mehwish populate the real `services`
collection, switching from this placeholder data to live Firestore data is a
single change inside `load_services()` — no rewrite of the recommender.

NOTE on data:
  - price / duration are PLACEHOLDERS (typical Swiss rates). Confirmed-from-doc
    values kept exact: Strengthening (65/45), Head Spa (120/60).
  - addOns are SAMPLE values to unblock the Price Estimator (Day 4). Replace with
    the salon's real add-ons when available.
  - `keywords` is a LOCAL-ONLY field (not in Firestore). It powers the offline
    fallback matcher and is simply ignored when real data is loaded.
"""

# ---------------------------------------------------------------------------
# Placeholder data shaped exactly like the Firestore `services` documents.
# ---------------------------------------------------------------------------
_SERVICES_DATA = [
    # ---------- NAIL CARE ----------
    {"serviceId": "manicure", "name": "Manicure", "category": "nails",
     "description": "Classic manicure: shaping, cuticle care, and polish.",
     "duration": 45, "price": 55, "oldPrice": None,
     "imageURL": "", "isPopular": True, "isAvailable": True,
     "addOns": [
         {"name": "Gel finish", "price": 15, "duration": 15},
         {"name": "Hand massage", "price": 15, "duration": 10},
         {"name": "Nail art (per nail)", "price": 5, "duration": 5},
     ],
     "staffIds": [],
     "keywords": ["manicure", "hands", "cuticle", "polish", "nail shape"]},

    {"serviceId": "pedicure", "name": "Pedicure", "category": "feet",
     "description": "Relaxing pedicure with soak, exfoliation, and polish.",
     "duration": 60, "price": 70, "oldPrice": None,
     "imageURL": "", "isPopular": True, "isAvailable": True,
     "addOns": [
         {"name": "Callus treatment", "price": 20, "duration": 15},
         {"name": "Foot massage", "price": 15, "duration": 10},
     ],
     "staffIds": [],
     "keywords": ["pedicure", "feet", "foot", "toes", "toenails"]},

    {"serviceId": "gel_application", "name": "Gel application", "category": "nails",
     "description": "Long-lasting, glossy gel colour application.",
     "duration": 60, "price": 75, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [{"name": "French tips", "price": 10, "duration": 10}],
     "staffIds": [],
     "keywords": ["gel", "long lasting", "shiny", "durable", "occasion"]},

    {"serviceId": "semi_permanent", "name": "Semi-permanent varnish", "category": "nails",
     "description": "Semi-permanent varnish that lasts up to two weeks.",
     "duration": 50, "price": 65, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [{"name": "Removal of old varnish", "price": 10, "duration": 15}],
     "staffIds": [],
     "keywords": ["semi permanent", "semi-permanent", "varnish", "lasting polish"]},

    {"serviceId": "nail_repair", "name": "Nail repair", "category": "nails",
     "description": "Repair of a broken, cracked, or damaged nail.",
     "duration": 30, "price": 35, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["repair", "broken nail", "cracked", "fix", "damaged"]},

    {"serviceId": "nail_biting", "name": "Nail biting treatment", "category": "nails",
     "description": "Restorative treatment for bitten or very short nails.",
     "duration": 45, "price": 60, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["biting", "bitten", "short nails", "habit", "chewed"]},

    {"serviceId": "babyboomer", "name": "Babyboomer installation", "category": "nails",
     "description": "Elegant babyboomer (French fade) nail installation.",
     "duration": 75, "price": 90, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [{"name": "Nail art (per nail)", "price": 5, "duration": 5}],
     "staffIds": [],
     "keywords": ["babyboomer", "baby boomer", "ombre", "french fade", "elegant"]},

    # ---------- HANDS ----------
    {"serviceId": "filling", "name": "Filling (2,3,4,5 weeks)", "category": "nails",
     "description": "Maintenance filling for grown-out enhancements.",
     "duration": 60, "price": 70, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["filling", "fill", "refill", "regrowth", "maintenance"]},

    {"serviceId": "strengthening", "name": "Strengthening natural nails", "category": "nails",
     "description": "Strengthening treatment for brittle or weak natural nails.",
     "duration": 45, "price": 65, "oldPrice": None,
     "imageURL": "", "isPopular": True, "isAvailable": True,
     "addOns": [{"name": "Hand massage", "price": 15, "duration": 10}],
     "staffIds": [],
     "keywords": ["strengthen", "strengthening", "brittle", "weak nails",
                  "thin nails", "natural nails", "breaking"]},

    {"serviceId": "removal_application", "name": "Removal + application", "category": "nails",
     "description": "Removal of old enhancements plus a fresh new set.",
     "duration": 75, "price": 80, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["removal", "remove", "redo", "reapply", "new set"]},

    # ---------- FEET ----------
    {"serviceId": "foot_beauty", "name": "Foot beauty", "category": "feet",
     "description": "Foot beauty care for soft, well-groomed feet.",
     "duration": 45, "price": 55, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["foot beauty", "feet care", "soft feet"]},

    {"serviceId": "foot_spa", "name": "Foot spa", "category": "feet",
     "description": "Soothing foot spa to relax tired feet.",
     "duration": 60, "price": 75, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [{"name": "Extended massage", "price": 20, "duration": 15}],
     "staffIds": [],
     "keywords": ["foot spa", "relax feet", "soak", "tired feet", "pamper"]},

    {"serviceId": "professional_pedicure", "name": "Professional pedicure", "category": "feet",
     "description": "Professional pedicure including callus and hard-skin care.",
     "duration": 70, "price": 85, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["professional pedicure", "medical pedicure", "callus", "hard skin"]},

    {"serviceId": "simple_foot_beauty", "name": "Simple foot beauty", "category": "feet",
     "description": "A quick, simple foot beauty session.",
     "duration": 30, "price": 40, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["simple foot", "quick feet", "basic pedicure"]},

    # ---------- HAIR REMOVAL ----------
    {"serviceId": "hr_upper_lip", "name": "Upper lip hair removal", "category": "hair removal",
     "description": "Gentle upper-lip hair removal.",
     "duration": 15, "price": 20, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["upper lip", "lip hair", "moustache", "facial hair"]},

    {"serviceId": "hr_chin", "name": "Chin hair removal", "category": "hair removal",
     "description": "Chin hair removal.",
     "duration": 15, "price": 20, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["chin", "chin hair"]},

    {"serviceId": "hr_cheek", "name": "Cheek hair removal", "category": "hair removal",
     "description": "Cheek and side-of-face hair removal.",
     "duration": 15, "price": 25, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["cheek", "cheeks", "side face"]},

    {"serviceId": "hr_full_face", "name": "Full face hair removal", "category": "hair removal",
     "description": "Complete full-face hair removal.",
     "duration": 30, "price": 45, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["full face", "face wax", "whole face"]},

    {"serviceId": "hr_eyebrow_shaping", "name": "Eyebrow shaping", "category": "hair removal",
     "description": "Eyebrow shaping for clean, defined brows.",
     "duration": 20, "price": 30, "oldPrice": None,
     "imageURL": "", "isPopular": True, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["eyebrow", "brows", "shaping", "brow shape", "threading"]},

    {"serviceId": "hr_half_leg", "name": "Half leg hair removal", "category": "hair removal",
     "description": "Half-leg (knee-down) hair removal.",
     "duration": 30, "price": 45, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["half leg", "lower leg", "knee down"]},

    {"serviceId": "hr_full_leg", "name": "Full leg hair removal", "category": "hair removal",
     "description": "Full-leg hair removal.",
     "duration": 45, "price": 70, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["full leg", "legs", "whole leg"]},

    {"serviceId": "hr_mid_arm", "name": "Mid-arm hair removal", "category": "hair removal",
     "description": "Mid-arm / forearm hair removal.",
     "duration": 20, "price": 35, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["mid arm", "mid-arm", "forearm", "half arm"]},

    {"serviceId": "hr_armpit", "name": "Armpit hair removal", "category": "hair removal",
     "description": "Underarm hair removal.",
     "duration": 15, "price": 25, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["armpit", "underarm", "underarms"]},

    {"serviceId": "hr_simple_bikini", "name": "Simple Bikini hair removal", "category": "hair removal",
     "description": "Simple bikini-line hair removal.",
     "duration": 20, "price": 40, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["simple bikini", "bikini line", "basic bikini"]},

    {"serviceId": "hr_full_bikini", "name": "Full Bikini hair removal", "category": "hair removal",
     "description": "Full bikini hair removal.",
     "duration": 30, "price": 60, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["full bikini", "brazilian", "intimate"]},

    {"serviceId": "hr_full_body", "name": "Full body wax", "category": "hair removal",
     "description": "Comprehensive full-body waxing.",
     "duration": 90, "price": 150, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["full body", "whole body wax", "all over"]},

    # ---------- EYES ----------
    {"serviceId": "lash_extensions", "name": "Eyelash extensions", "category": "eyes",
     "description": "Eyelash extensions for longer, fuller lashes.",
     "duration": 90, "price": 120, "oldPrice": None,
     "imageURL": "", "isPopular": True, "isAvailable": True,
     "addOns": [{"name": "Volume upgrade", "price": 30, "duration": 20}],
     "staffIds": [],
     "keywords": ["eyelash extensions", "lash extensions", "longer lashes",
                  "volume lashes", "fuller lashes"]},

    {"serviceId": "lash_lift", "name": "Eyelash lift", "category": "eyes",
     "description": "Eyelash lift for a natural, curled look.",
     "duration": 60, "price": 85, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [{"name": "Lash tint", "price": 20, "duration": 15}],
     "staffIds": [],
     "keywords": ["lash lift", "eyelash lift", "curl lashes", "natural lift"]},

    {"serviceId": "brow_lash_tint", "name": "Eyebrow & eyelash tinting", "category": "eyes",
     "description": "Tinting for darker, defined brows and lashes.",
     "duration": 30, "price": 45, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["tinting", "tint", "darker brows", "brow color", "lash tint"]},

    # ---------- HEAD & HAIR ----------
    {"serviceId": "head_spa", "name": "Head Spa Japanese", "category": "head",
     "description": "Japanese-inspired head spa for deep scalp relaxation.",
     "duration": 60, "price": 120, "oldPrice": None,
     "imageURL": "", "isPopular": True, "isAvailable": True,
     "addOns": [
         {"name": "Extended massage", "price": 30, "duration": 20},
         {"name": "Hair mask", "price": 25, "duration": 15},
     ],
     "staffIds": [],
     "keywords": ["head spa", "japanese", "scalp treatment", "relax", "stress",
                  "wellness", "headache", "tension"]},

    {"serviceId": "scalp_massage", "name": "Scalp massage", "category": "head",
     "description": "Relaxing scalp massage.",
     "duration": 30, "price": 55, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["scalp massage", "head massage", "relax scalp"]},

    {"serviceId": "hair_relaxation", "name": "Hair relaxation", "category": "head",
     "description": "Calming hair relaxation treatment.",
     "duration": 45, "price": 70, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["hair relaxation", "relax hair", "smooth", "calming"]},

    {"serviceId": "revitalization", "name": "Revitalization treatment", "category": "head",
     "description": "Revitalizing treatment for thinning or damaged hair.",
     "duration": 60, "price": 95, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [{"name": "Hair mask", "price": 25, "duration": 15}],
     "staffIds": [],
     "keywords": ["revitalization", "revitalize", "hair fall", "thinning",
                  "damaged hair", "nourish"]},

    {"serviceId": "scalp_moisturizing", "name": "Scalp moisturizing", "category": "head",
     "description": "Moisturizing treatment for dry or flaky scalp.",
     "duration": 45, "price": 75, "oldPrice": None,
     "imageURL": "", "isPopular": False, "isAvailable": True,
     "addOns": [],
     "staffIds": [],
     "keywords": ["scalp moisturizing", "dry scalp", "flaky", "dandruff", "hydrate"]},
]


# ---------------------------------------------------------------------------
# SINGLE SWAP POINT for going live.
# Today this returns the in-memory placeholder data above. When the real
# `services` Firestore collection is ready, replace the body of this function
# with a Firestore fetch (returning docs in the SAME shape) and nothing else
# in the codebase needs to change.
# ---------------------------------------------------------------------------
def load_services():
    """Return all services as a list of dicts shaped like Firestore `services`.

    Swap-point for going live:
      - If a real services file is present (env SERVICES_FILE, or ./services.json
        or ./services.xlsx), load REAL data from it and keep our local `keywords`
        (matched by serviceId/name) so the offline fallback still works.
      - Otherwise, return the in-memory placeholder data below.
    """
    import os
    candidates = [os.getenv("SERVICES_FILE"), "services.json", "services.xlsx"]
    for path in candidates:
        if path and os.path.exists(path):
            try:
                from services_loader import read_services_file
                real = read_services_file(path)
                if real:
                    return _merge_keywords(real)
            except Exception as e:
                print(f"[catalog] could not load {path} ({e}); using placeholders.")
    return _SERVICES_DATA


def _merge_keywords(real_services):
    """Attach our local `keywords` to real data by matching serviceId or name,
    so the offline fallback keeps working once real prices/durations are loaded."""
    by_id = {s["serviceId"]: s for s in _SERVICES_DATA}
    by_name = {s["name"].lower(): s for s in _SERVICES_DATA}
    for s in real_services:
        match = by_id.get(s["serviceId"]) or by_name.get(s["name"].lower())
        if match and not s.get("keywords"):
            s["keywords"] = match["keywords"]
        s.setdefault("keywords", [])
    return real_services


# Load once at import. Call refresh_catalog() if the source changes at runtime.
SERVICES = load_services()
SERVICES_BY_NAME = {s["name"]: s for s in SERVICES}
SERVICES_BY_ID = {s["serviceId"]: s for s in SERVICES}


def refresh_catalog():
    """Reload services and rebuild lookups (useful once data is live)."""
    global SERVICES, SERVICES_BY_NAME, SERVICES_BY_ID
    SERVICES = load_services()
    SERVICES_BY_NAME = {s["name"]: s for s in SERVICES}
    SERVICES_BY_ID = {s["serviceId"]: s for s in SERVICES}
    return SERVICES


def get_service_by_id(service_id):
    """Look up one service by its serviceId (used by the Price Estimator)."""
    return SERVICES_BY_ID.get(service_id)


def catalog_for_prompt() -> str:
    """Compact catalog string injected into the LLM prompt."""
    lines = []
    for s in SERVICES:
        if not s.get("isAvailable", True):
            continue  # never recommend an unavailable service
        lines.append(f'- "{s["name"]}" [{s["category"]}] '
                     f'(CHF {s["price"]}, {s["duration"]} min)')
    return "\n".join(lines)