"""
Celine Esthetique - Real services data loader
=============================================
Owner: Ubaid Ullah Farooqui (AI Developer)

Reads the salon's real services file (Excel .xlsx or JSON) and normalises each
row/record into the Firestore `services` schema used across the AI module.

This is the concrete implementation behind the Day-3 swap-point: when the salon's
Excel/JSON arrives, `services_catalog.load_services()` calls this loader, and the
recommender + price estimator immediately use REAL prices, durations, and add-ons
instead of placeholders. No other code changes.

Column / key mapping is flexible (case-insensitive, common aliases) so it tolerates
small differences in how the salon labels their spreadsheet.
"""

import json
import os

# Accept several common header spellings for each schema field.
ALIASES = {
    "serviceId": ["serviceid", "id", "service id", "service_id"],
    "name": ["name", "service", "service name", "title"],
    "category": ["category", "type", "group"],
    "description": ["description", "desc", "details"],
    "duration": ["duration", "minutes", "mins", "time"],
    "price": ["price", "cost", "amount", "chf"],
    "oldPrice": ["oldprice", "old price", "was", "previous price"],
    "imageURL": ["imageurl", "image", "image url", "photo"],
    "isPopular": ["ispopular", "popular"],
    "isAvailable": ["isavailable", "available", "active"],
    "addOns": ["addons", "add-ons", "add ons", "extras"],
    "staffIds": ["staffids", "staff", "staff ids"],
}


def _slug(text):
    return (str(text).strip().lower()
            .replace(" ", "_").replace("/", "_").replace("-", "_"))


def _to_bool(v, default=True):
    if isinstance(v, bool):
        return v
    if v is None or v == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "oui")


def _to_number(v, default=0):
    if v in (None, ""):
        return default
    try:
        n = float(v)
        return int(n) if n == int(n) else n
    except (TypeError, ValueError):
        return default


def _parse_addons(v):
    """Add-ons may be a list, a JSON string, or empty."""
    if not v:
        return []
    if isinstance(v, list):
        return v
    try:
        parsed = json.loads(v)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, ValueError):
        return []


def _build_header_map(headers):
    """Map actual file headers -> schema field names using ALIASES."""
    lowered = {h.strip().lower(): h for h in headers if h}
    mapping = {}
    for field, names in ALIASES.items():
        for n in names:
            if n in lowered:
                mapping[field] = lowered[n]
                break
    return mapping


def _normalise(raw):
    """Turn one raw record (dict of file-values) into a schema-shaped service."""
    name = str(raw.get("name", "")).strip()
    service_id = str(raw.get("serviceId", "")).strip() or _slug(name)
    return {
        "serviceId": service_id,
        "name": name,
        "category": str(raw.get("category", "")).strip().lower(),
        "description": str(raw.get("description", "")).strip(),
        "duration": _to_number(raw.get("duration"), 0),
        "price": _to_number(raw.get("price"), 0),
        "oldPrice": (_to_number(raw["oldPrice"]) if raw.get("oldPrice") not in (None, "") else None),
        "imageURL": str(raw.get("imageURL", "")).strip(),
        "isPopular": _to_bool(raw.get("isPopular"), default=False),
        "isAvailable": _to_bool(raw.get("isAvailable"), default=True),
        "addOns": _parse_addons(raw.get("addOns")),
        "staffIds": _parse_addons(raw.get("staffIds")),
        "keywords": [],   # filled later by services_catalog from the placeholder map
    }


def _read_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):                 # allow {"services": [...]}
        data = data.get("services", [])
    return [_normalise(rec) for rec in data]


def _read_excel(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    hmap = _build_header_map(headers)
    out = []
    for row in rows[1:]:
        if all(c is None or c == "" for c in row):
            continue
        record = {field: row[headers.index(col)] for field, col in hmap.items()}
        out.append(_normalise(record))
    return out


def read_services_file(path):
    """Read a services file (.json or .xlsx) into a list of schema-shaped dicts."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        return _read_json(path)
    if ext in (".xlsx", ".xlsm"):
        return _read_excel(path)
    raise ValueError(f"Unsupported services file type: {ext}")
