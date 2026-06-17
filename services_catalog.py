"""
Celine Esthetique - Service Catalog
====================================
Built from the 30+ real services listed in the project document (Section 3.1).

IMPORTANT: prices (CHF) and durations are PLACEHOLDERS based on typical Swiss
salon rates. Before final submission, replace these with the real values from
the `services` Firestore collection (fields: price, duration). The two confirmed
values from the doc are kept exact:
  - "Strengthening natural nails"  -> price 65, duration 45   (Section 10.4)
  - "Head Spa Japanese"            -> price 120, duration 60  (Section 10.1)

Each service has `keywords` used by the offline fallback matcher when the LLM
is unavailable (required by the AI checklist: "Fallback responses implemented").
"""

SERVICES = [
    # ---------- NAIL CARE ----------
    {"id": "manicure", "name": "Manicure", "category": "nails",
     "duration": 45, "price": 55,
     "keywords": ["manicure", "hands", "cuticle", "polish", "nail shape"]},
    {"id": "pedicure", "name": "Pedicure", "category": "feet",
     "duration": 60, "price": 70,
     "keywords": ["pedicure", "feet", "foot", "toes", "toenails"]},
    {"id": "gel_application", "name": "Gel application", "category": "nails",
     "duration": 60, "price": 75,
     "keywords": ["gel", "long lasting", "shiny", "durable", "occasion"]},
    {"id": "semi_permanent", "name": "Semi-permanent varnish", "category": "nails",
     "duration": 50, "price": 65,
     "keywords": ["semi permanent", "semi-permanent", "varnish", "lasting polish"]},
    {"id": "nail_repair", "name": "Nail repair", "category": "nails",
     "duration": 30, "price": 35,
     "keywords": ["repair", "broken nail", "cracked", "fix", "damaged"]},
    {"id": "nail_biting", "name": "Nail biting treatment", "category": "nails",
     "duration": 45, "price": 60,
     "keywords": ["biting", "bitten", "short nails", "habit", "chewed"]},
    {"id": "babyboomer", "name": "Babyboomer installation", "category": "nails",
     "duration": 75, "price": 90,
     "keywords": ["babyboomer", "baby boomer", "ombre", "french fade", "elegant"]},

    # ---------- HANDS ----------
    {"id": "filling", "name": "Filling (2,3,4,5 weeks)", "category": "nails",
     "duration": 60, "price": 70,
     "keywords": ["filling", "fill", "refill", "regrowth", "maintenance"]},
    {"id": "strengthening", "name": "Strengthening natural nails", "category": "nails",
     "duration": 45, "price": 65,
     "keywords": ["strengthen", "strengthening", "brittle", "weak nails",
                  "thin nails", "natural nails", "breaking"]},
    {"id": "removal_application", "name": "Removal + application", "category": "nails",
     "duration": 75, "price": 80,
     "keywords": ["removal", "remove", "redo", "reapply", "new set"]},

    # ---------- FEET ----------
    {"id": "foot_beauty", "name": "Foot beauty", "category": "feet",
     "duration": 45, "price": 55,
     "keywords": ["foot beauty", "feet care", "soft feet"]},
    {"id": "foot_spa", "name": "Foot spa", "category": "feet",
     "duration": 60, "price": 75,
     "keywords": ["foot spa", "relax feet", "soak", "tired feet", "pamper"]},
    {"id": "professional_pedicure", "name": "Professional pedicure", "category": "feet",
     "duration": 70, "price": 85,
     "keywords": ["professional pedicure", "medical pedicure", "callus", "hard skin"]},
    {"id": "simple_foot_beauty", "name": "Simple foot beauty", "category": "feet",
     "duration": 30, "price": 40,
     "keywords": ["simple foot", "quick feet", "basic pedicure"]},

    # ---------- HAIR REMOVAL ----------
    {"id": "hr_upper_lip", "name": "Upper lip hair removal", "category": "hair removal",
     "duration": 15, "price": 20,
     "keywords": ["upper lip", "lip hair", "moustache", "facial hair"]},
    {"id": "hr_chin", "name": "Chin hair removal", "category": "hair removal",
     "duration": 15, "price": 20,
     "keywords": ["chin", "chin hair"]},
    {"id": "hr_cheek", "name": "Cheek hair removal", "category": "hair removal",
     "duration": 15, "price": 25,
     "keywords": ["cheek", "cheeks", "side face"]},
    {"id": "hr_full_face", "name": "Full face hair removal", "category": "hair removal",
     "duration": 30, "price": 45,
     "keywords": ["full face", "face wax", "whole face"]},
    {"id": "hr_eyebrow_shaping", "name": "Eyebrow shaping", "category": "hair removal",
     "duration": 20, "price": 30,
     "keywords": ["eyebrow", "brows", "shaping", "brow shape", "threading"]},
    {"id": "hr_half_leg", "name": "Half leg hair removal", "category": "hair removal",
     "duration": 30, "price": 45,
     "keywords": ["half leg", "lower leg", "knee down"]},
    {"id": "hr_full_leg", "name": "Full leg hair removal", "category": "hair removal",
     "duration": 45, "price": 70,
     "keywords": ["full leg", "legs", "whole leg"]},
    {"id": "hr_mid_arm", "name": "Mid-arm hair removal", "category": "hair removal",
     "duration": 20, "price": 35,
     "keywords": ["mid arm", "mid-arm", "forearm", "half arm"]},
    {"id": "hr_armpit", "name": "Armpit hair removal", "category": "hair removal",
     "duration": 15, "price": 25,
     "keywords": ["armpit", "underarm", "underarms"]},
    {"id": "hr_simple_bikini", "name": "Simple Bikini hair removal", "category": "hair removal",
     "duration": 20, "price": 40,
     "keywords": ["simple bikini", "bikini line", "basic bikini"]},
    {"id": "hr_full_bikini", "name": "Full Bikini hair removal", "category": "hair removal",
     "duration": 30, "price": 60,
     "keywords": ["full bikini", "brazilian", "intimate"]},
    {"id": "hr_full_body", "name": "Full body wax", "category": "hair removal",
     "duration": 90, "price": 150,
     "keywords": ["full body", "whole body wax", "all over"]},

    # ---------- EYES ----------
    {"id": "lash_extensions", "name": "Eyelash extensions", "category": "eyes",
     "duration": 90, "price": 120,
     "keywords": ["eyelash extensions", "lash extensions", "longer lashes",
                  "volume lashes", "fuller lashes"]},
    {"id": "lash_lift", "name": "Eyelash lift", "category": "eyes",
     "duration": 60, "price": 85,
     "keywords": ["lash lift", "eyelash lift", "curl lashes", "natural lift"]},
    {"id": "brow_lash_tint", "name": "Eyebrow & eyelash tinting", "category": "eyes",
     "duration": 30, "price": 45,
     "keywords": ["tinting", "tint", "darker brows", "brow color", "lash tint"]},

    # ---------- HEAD & HAIR ----------
    {"id": "head_spa", "name": "Head Spa Japanese", "category": "head",
     "duration": 60, "price": 120,
     "keywords": ["head spa", "japanese", "scalp treatment", "relax", "stress",
                  "wellness", "headache", "tension"]},
    {"id": "scalp_massage", "name": "Scalp massage", "category": "head",
     "duration": 30, "price": 55,
     "keywords": ["scalp massage", "head massage", "relax scalp"]},
    {"id": "hair_relaxation", "name": "Hair relaxation", "category": "head",
     "duration": 45, "price": 70,
     "keywords": ["hair relaxation", "relax hair", "smooth", "calming"]},
    {"id": "revitalization", "name": "Revitalization treatment", "category": "head",
     "duration": 60, "price": 95,
     "keywords": ["revitalization", "revitalize", "hair fall", "thinning",
                  "damaged hair", "nourish"]},
    {"id": "scalp_moisturizing", "name": "Scalp moisturizing", "category": "head",
     "duration": 45, "price": 75,
     "keywords": ["scalp moisturizing", "dry scalp", "flaky", "dandruff", "hydrate"]},
]

# Fast lookup by exact name (used to validate LLM output)
SERVICES_BY_NAME = {s["name"]: s for s in SERVICES}


def catalog_for_prompt() -> str:
    """Compact catalog string injected into the LLM prompt."""
    lines = []
    for s in SERVICES:
        lines.append(f'- "{s["name"]}" [{s["category"]}] '
                     f'(CHF {s["price"]}, {s["duration"]} min)')
    return "\n".join(lines)
