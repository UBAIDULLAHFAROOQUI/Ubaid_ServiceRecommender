"""
Quick offline test - runs WITHOUT an API key (exercises the fallback matcher).
    python test_recommender.py
Once you add GROQ_API_KEY to .env, the same calls will use the LLM instead.
"""

from recommender import recommend_service

cases = [
    ["What area? nails", "What concern? brittle nails", "Occasion? daily"],
    ["What area? feet", "What concern? tired feet", "Occasion? relax"],
    ["What area? face", "What concern? unwanted hair on upper lip"],
    ["What concern? stress and tension", "I want something relaxing"],
    ["I want longer fuller lashes for a wedding"],
]

for i, answers in enumerate(cases, 1):
    out = recommend_service(answers)
    print(f"\nCase {i}: {answers}")
    print(f"  -> {out['recommendedService']} "
          f"(CHF {out['price']}, {out['duration']} min)")
    print(f"     {out['reason']}")
