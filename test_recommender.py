"""
Offline tests - run WITHOUT an API key (exercise the fallback matcher).
    python test_recommender.py
With GROQ_API_KEY set, the same calls use the LLM and reasons are AI-written
(and in French when language='fr').
"""

from recommender import recommend_service, get_questions

print("=" * 60)
print("ENGLISH cases")
print("=" * 60)
en_cases = [
    ["What area? nails", "What concern? brittle nails", "Occasion? daily"],
    ["area: feet", "concern: tired feet", "occasion: relax"],
    ["I want longer fuller lashes for a wedding"],
    ["concern: stress and tension"],
    ["concern: my nails feel kind of weird"],   # unknown -> graceful default
    [],                                          # blank -> safe default
]
for ans in en_cases:
    out = recommend_service(ans, language="en")
    print(f"\n{ans}")
    print(f"  -> {out['recommendedService']} ({out['serviceId']}) "
          f"CHF {out['price']}, {out['duration']}min")
    print(f"     {out['reason']}")

print("\n" + "=" * 60)
print("FRENCH cases (language='fr')")
print("=" * 60)
fr_cases = [
    ["zone: ongles", "souci: ongles cassants", "occasion: quotidien"],
    ["zone: pieds", "souci: pieds fatigués"],
    ["je veux des cils plus longs pour un mariage"],
    ["souci: stress et tension"],
]
for ans in fr_cases:
    out = recommend_service(ans, language="fr")
    print(f"\n{ans}")
    print(f"  -> {out['recommendedService']} ({out['serviceId']}) "
          f"CHF {out['price']}, {out['duration']}min")
    print(f"     {out['reason']}")

print("\n" + "=" * 60)
print("QUESTIONS endpoint")
print("=" * 60)
for lang in ("en", "fr"):
    q = get_questions(lang)
    print(f"\n[{lang}] first question: {q['questions'][0]['question']}")
    print(f"        options: {q['questions'][0]['options']}")