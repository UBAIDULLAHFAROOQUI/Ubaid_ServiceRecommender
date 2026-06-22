"""
Offline tests for the Price Estimator (no API key needed).
    python test_price_estimator.py
Covers: regular/vip/first-time discounts, luxury deposit, VAT breakout,
add-on quantities, duplicates, invalid input, unknown service.
"""

from price_estimator import estimate_price, VAT_PERCENT


def line(label, ok):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return ok


all_ok = True

# 1) Regular manicure, no add-ons
r = estimate_price("manicure")
print("\n1) Manicure, regular, no add-ons")
all_ok &= line("subtotal 55", r["subtotal"] == 55.0)
all_ok &= line("no discount", r["discount"]["amount"] == 0.0)
all_ok &= line("not luxury, no deposit", r["isLuxury"] is False and r["deposit"]["required"] is False)
all_ok &= line("VAT included flag", r["vat"]["included"] is True and r["vat"]["percent"] == VAT_PERCENT)

# 2) Manicure + 2 add-ons, regular
r = estimate_price("manicure", ["Gel finish", "Hand massage"])
print("\n2) Manicure + Gel finish + Hand massage, regular")
all_ok &= line("subtotal 85", r["subtotal"] == 85.0)
all_ok &= line("duration 70", r["totalDuration"] == 70)

# 3) Head Spa + Hair mask, first-time (luxury)
r = estimate_price("head_spa", ["Hair mask"], "first_time")
print("\n3) Head Spa + Hair mask, first_time (luxury)")
all_ok &= line("subtotal 145", r["subtotal"] == 145.0)
all_ok &= line("discount 21.75", r["discount"]["amount"] == 21.75)
all_ok &= line("total 123.25", r["total"] == 123.25)
all_ok &= line("deposit 24.65", r["deposit"]["amount"] == 24.65)
all_ok &= line("deposit reason present", bool(r["deposit"]["reason"]))
# VAT inclusive: net + vat == total
all_ok &= line("net + VAT == total", round(r["vat"]["net"] + r["vat"]["amount"], 2) == r["total"])

# 4) VIP on luxury
r = estimate_price("lash_extensions", customer_type="vip")
print("\n4) Eyelash extensions, vip (luxury)")
all_ok &= line("discount 12", r["discount"]["amount"] == 12.0)
all_ok &= line("total 108", r["total"] == 108.0)

# 5) Add-on QUANTITY: 5x Nail art (per nail) on babyboomer (5 each)
r = estimate_price("babyboomer", [{"name": "Nail art (per nail)", "quantity": 5}])
print("\n5) Babyboomer + 5x Nail art")
nail_line = [i for i in r["items"] if i["name"] == "Nail art (per nail)"][0]
all_ok &= line("quantity 5", nail_line["quantity"] == 5)
all_ok &= line("line total 25 (5x5)", nail_line["lineTotal"] == 25.0)
all_ok &= line("subtotal 115 (90+25)", r["subtotal"] == 115.0)

# 6) DUPLICATE add-ons merge
r = estimate_price("manicure", ["Hand massage", "Hand massage"])
print("\n6) Manicure + Hand massage x2 (duplicates merge)")
hm = [i for i in r["items"] if i["name"] == "Hand massage"][0]
all_ok &= line("merged quantity 2", hm["quantity"] == 2)

# 7) INVALID quantity clamps to 1
r = estimate_price("manicure", [{"name": "Gel finish", "quantity": -3}])
print("\n7) Manicure + Gel finish quantity -3 (clamped)")
gf = [i for i in r["items"] if i["name"] == "Gel finish"][0]
all_ok &= line("quantity clamped to 1", gf["quantity"] == 1)

# 8) Unknown add-on reported, not charged
r = estimate_price("manicure", ["Diamond polish"])
print("\n8) Manicure + unknown add-on")
all_ok &= line("subtotal still 55", r["subtotal"] == 55.0)
all_ok &= line("unmatched reported", "diamond polish" in r["unmatchedAddOns"])

# 9) Unknown service
r = estimate_price("not_a_service")
print("\n9) Unknown service")
all_ok &= line("returns error", "error" in r)

print("\n" + ("ALL TESTS PASSED" if all_ok else "SOME TESTS FAILED"))
