"""
Offline tests for Sentiment Analysis (no API key needed -> exercises fallback).
    python test_sentiment.py
With GROQ_API_KEY set, the LLM handles sarcasm/nuance and reasons are AI-written.
"""

from sentiment import analyze_sentiment


def check(label, comment, rating, lang, expected):
    r = analyze_sentiment(comment, rating, lang)
    ok = r["sentiment"] == expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got {r['sentiment']} "
          f"(conf {r['confidence']}) — exp {expected}")
    return ok

all_ok = True
print("ENGLISH")
all_ok &= check("clear positive", "Absolutely loved it, the staff were amazing and friendly!", 5, "en", "positive")
all_ok &= check("clear negative", "Terrible service, rude staff and the place was dirty.", 1, "en", "negative")
all_ok &= check("neutral", "It was okay, nothing special.", 3, "en", "neutral")
all_ok &= check("positive text only", "Lovely relaxing experience, highly recommend.", None, "en", "positive")
all_ok &= check("negative text only", "Disappointed, my appointment was rushed and painful.", None, "en", "negative")

print("\nFRENCH")
all_ok &= check("positif", "J'adore, le personnel était génial et accueillant !", 5, "fr", "positive")
all_ok &= check("négatif", "Service horrible, personnel impoli et salon sale.", 1, "fr", "negative")
all_ok &= check("neutre", "C'était correct, sans plus.", 3, "fr", "neutral")

print("\nRATING-AWARE / EDGE")
all_ok &= check("5 stars short comment", "ok", 5, "en", "positive")
all_ok &= check("1 star short comment", "meh", 1, "en", "negative")
r = analyze_sentiment("", None, "en")
print(f"  [{'PASS' if r['sentiment']=='neutral' else 'FAIL'}] empty input -> neutral")
all_ok &= r["sentiment"] == "neutral"

print("\n" + ("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED"))
