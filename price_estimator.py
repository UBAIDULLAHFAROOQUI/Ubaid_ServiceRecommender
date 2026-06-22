"""
Celine Esthetique - AI Price Estimator (core logic)
===================================================
Owner: Ubaid Ullah Farooqui (AI Developer)
Endpoint served by main.py:  POST /api/ai/price-estimate

Calculates the total cost of a service + selected add-ons, applies the business
rules confirmed by the supervisor (20 June), and breaks out Swiss VAT.

Business rules:
  - Discounts:  VIP = 10% off,  First-time = 15% off,  Regular = 0%
  - Deposit:    Luxury services require a 20% deposit
  - VAT:        Swiss standard rate 8.1%, INCLUSIVE (see note below)

Deterministic arithmetic (NOT an LLM call) so totals are always exact and fast.
Returns an ITEMISED breakdown (team-hub requirement), not just a total.

VAT NOTE (confirm with salon):
  In Switzerland, consumer prices shown are legally VAT-INCLUSIVE — the listed
  price already contains the tax. So we do NOT add VAT on top; we reveal how much
  of the total already IS VAT. Rate kept in one constant (VAT_PERCENT) for easy
  change. Verified current standard rate: 8.1% (in force 2026).
"""

from services_catalog import get_service_by_id

CURRENCY = "CHF"

# --- Business rules (confirmed 20 June) ---
DISCOUNTS = {"regular": 0, "vip": 10, "first_time": 15}   # percent off subtotal
DEPOSIT_PERCENT = 20            # required on luxury services
LUXURY_THRESHOLD_CHF = 100      # base price at/above this counts as "luxury"
# NOTE: luxury is defined by a price threshold as a placeholder. Confirm whether
# the salon prefers an explicit per-service flag (services.isLuxury) instead.

# --- Tax ---
VAT_PERCENT = 8.1               # Swiss standard rate (2026); prices are VAT-inclusive


def _money(x):
    """Round to 2 decimals for clean currency values."""
    return round(float(x), 2)


def _is_luxury(service):
    return service["price"] >= LUXURY_THRESHOLD_CHF


def _normalise_addons(addon_input):
    """Accept add-ons as either:
         ["Gel finish", "Hand massage"]              (quantity defaults to 1)
       or
         [{"name": "Nail art (per nail)", "quantity": 5}, ...]
    Returns a {name_lower: quantity} dict with duplicates merged and quantities
    validated (anything < 1 is clamped to 1)."""
    merged = {}
    for entry in addon_input or []:
        if isinstance(entry, dict):
            name = str(entry.get("name", "")).strip()
            try:
                qty = int(entry.get("quantity", 1))
            except (TypeError, ValueError):
                qty = 1
        else:
            name, qty = str(entry).strip(), 1
        if not name:
            continue
        if qty < 1:
            qty = 1
        merged[name.lower()] = merged.get(name.lower(), 0) + qty
    return merged


def estimate_price(service_id, addon_input=None, customer_type="regular"):
    """
    Build an itemised price estimate.

    Args:
      service_id    : serviceId from the catalog (e.g. "head_spa")
      addon_input   : list of add-on names, or list of {name, quantity}
      customer_type : "regular" | "vip" | "first_time"

    Returns a dict, or {"error": ...} if the service id is unknown.
    """
    service = get_service_by_id(service_id)
    if service is None:
        return {"error": f"Unknown serviceId '{service_id}'."}

    if customer_type not in DISCOUNTS:
        customer_type = "regular"

    # --- Base service line ---
    items = [{
        "name": service["name"],
        "unitPrice": _money(service["price"]),
        "quantity": 1,
        "lineTotal": _money(service["price"]),
        "unitDuration": service["duration"],
        "lineDuration": service["duration"],
    }]
    subtotal = service["price"]
    total_duration = service["duration"]

    # --- Add-on lines (match by name, case-insensitive, with quantities) ---
    available = {a["name"].lower(): a for a in service.get("addOns", [])}
    requested = _normalise_addons(addon_input)
    unmatched = []
    for name_lower, qty in requested.items():
        a = available.get(name_lower)
        if a is None:
            unmatched.append(name_lower)   # unknown add-on -> reported, not charged
            continue
        line_total = a["price"] * qty
        line_duration = a["duration"] * qty
        items.append({
            "name": a["name"],
            "unitPrice": _money(a["price"]),
            "quantity": qty,
            "lineTotal": _money(line_total),
            "unitDuration": a["duration"],
            "lineDuration": line_duration,
        })
        subtotal += line_total
        total_duration += line_duration

    subtotal = _money(subtotal)

    # --- Discount ---
    percent = DISCOUNTS[customer_type]
    discount_amount = _money(subtotal * percent / 100)
    total = _money(subtotal - discount_amount)
    discount = {"type": customer_type, "percent": percent, "amount": discount_amount}

    # --- VAT (inclusive: revealed from the total, not added on top) ---
    net = _money(total / (1 + VAT_PERCENT / 100))
    vat_amount = _money(total - net)
    vat = {"included": True, "percent": VAT_PERCENT,
           "net": net, "amount": vat_amount}

    # --- Deposit (luxury services only; based on the service, not discounted price) ---
    luxury = _is_luxury(service)
    deposit = {
        "required": luxury,
        "percent": DEPOSIT_PERCENT if luxury else 0,
        "amount": _money(total * DEPOSIT_PERCENT / 100) if luxury else 0.0,
        "reason": (f"Luxury treatment (CHF {LUXURY_THRESHOLD_CHF}+) requires a "
                   f"{DEPOSIT_PERCENT}% deposit." if luxury else ""),
    }

    return {
        "service": service["name"],
        "serviceId": service["serviceId"],
        "currency": CURRENCY,
        "items": items,
        "subtotal": subtotal,
        "discount": discount,
        "total": total,
        "vat": vat,
        "isLuxury": luxury,
        "deposit": deposit,
        "totalDuration": total_duration,
        "unmatchedAddOns": unmatched,
    }