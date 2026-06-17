"""
Data-driven tyre recommendation engine built on recommend.json.
Every filter and score maps directly to a JSON field.
"""
import json
import os
from functools import lru_cache
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
CATALOGUE_PATH = os.path.join(BASE_DIR, "recommend.json")
MICHELIN_BASE_URL = "https://www.michelin.fr/bicycle/tyres"

# ---------------------------------------------------------------------------
# Field-level mappings  (JSON value → user input)
# ---------------------------------------------------------------------------

# CYCLE TYPE WEB contains comma-separated tags; we match substrings
_WEB_TYPE_TAGS: dict[str, list[str]] = {
    "road":    ["ROAD"],
    "gravel":  ["GRAVEL"],
    "mtb":     ["MTB"],
    "city":    ["COMMUTING & TOUR"],
    "ebike":   ["E-BIKE"],
}

# Segment in JSON
_BUDGET_SEGMENT: dict[str, str] = {
    "racing":      "PREMIUM RACING LINE",
    "competition": "PREMIUM COMPETITION LINE",
    "performance": "PREMIUM PERFORMANCE LINE",
    "access":      "ACCESS LINE",
}

# Use keywords per riding style (matched against "Use" field)
_STYLE_USE_KW: dict[str, list[str]] = {
    "racing":        ["RACING"],
    "endurance":     ["ENDURANCE"],
    "all_road":      ["ALL ROAD"],
    "touring":       ["TOURING"],
    "trekking":      ["TREKKING"],
    "urban":         ["URBAN"],
    "cross_country": ["CROSS COUNTRY"],
    "trail":         ["TRAIL", "ALL MOUNTAIN"],
    "enduro":        ["ENDURO", "ALL MOUNTAIN"],
    "downhill":      ["DOWNHILL", "ENDURO"],
}

# Terrain keywords per user terrain input
_TERRAIN_KW: dict[str, list[str]] = {
    "asphalt":       ["ASPHALT"],
    "mixed":         ["ASPHALT", "OFFROAD HARD PACKED", "MIXED"],
    "offroad_hard":  ["OFFROAD HARD PACKED", "HARD PACKED", "HARD/DRY"],
    "offroad_mixed": ["OFFROAD MIXED", "MIXED", "OFFROAD HARD PACKED"],
    "offroad_soft":  ["OFFROAD SOFT", "OFFROAD MUD", "MUD", "SOFT"],
}

# Sealing filter
_SEALING: dict[bool, str] = {
    True:  "TUBELESS READY",
    False: "TUBE TYPE",
}

# E-bike technology keywords
_EBIKE_TECH_KW = ["E-BIKE", "E-BIKE READY", "E-50"]


@lru_cache(maxsize=1)
def _load() -> list[dict[str, Any]]:
    with open(CATALOGUE_PATH, encoding="utf-8") as f:
        return json.load(f)


def _web_type_matches(tyre: dict, bike_type: str, e_bike: bool) -> bool:
    """Check CYCLE TYPE WEB contains the required bike-type tags."""
    web = (tyre.get("CYCLE TYPE WEB") or "").upper()
    if not web:
        return False
    required_tags = _WEB_TYPE_TAGS.get(bike_type, [])
    if not any(tag in web for tag in required_tags):
        return False
    if e_bike and "E-BIKE" not in web:
        return False
    return True


def _score(
    tyre: dict,
    bike_type: str,
    riding_style: str,
    terrain: str,
    budget_level: str,
    tubeless: bool,
    e_bike: bool,
) -> int:
    s = 0
    t_terrain = (tyre.get("Terrain Types") or "").upper()
    t_use     = (tyre.get("Use") or "").upper()
    t_segment = (tyre.get("Segment") or "").upper()
    t_sealing = (tyre.get("Sealing") or "").upper()
    t_ebike   = (tyre.get("E-Bike Technologies") or "").upper()

    # Terrain match (high weight — most decisive)
    for kw in _TERRAIN_KW.get(terrain, []):
        if kw in t_terrain:
            s += 4

    # Riding style → Use match
    for kw in _STYLE_USE_KW.get(riding_style, []):
        if kw in t_use:
            s += 3

    # Budget → Segment exact match
    target_seg = _BUDGET_SEGMENT.get(budget_level, "")
    if target_seg and target_seg in t_segment:
        s += 3
    # Partial segment penalty (adjacent levels score less)
    elif "RACING LINE" in t_segment and budget_level == "competition":
        s += 1
    elif "COMPETITION LINE" in t_segment and budget_level == "racing":
        s += 1

    # Tubeless match
    preferred_sealing = _SEALING[tubeless]
    if preferred_sealing in t_sealing:
        s += 2

    # E-bike technologies
    if e_bike:
        if any(kw in t_ebike for kw in _EBIKE_TECH_KW):
            s += 3
    else:
        # Penalise e-bike-only tyres for non-e-bike riders
        if t_ebike and not any(kw in t_use for kw in _STYLE_USE_KW.get(riding_style, [])):
            s -= 1

    return s


def _build_reasons(
    tyre: dict, bike_type: str, riding_style: str, terrain: str, tubeless: bool, e_bike: bool
) -> list[str]:
    reasons = []

    seg = (tyre.get("Segment") or "").title()
    if seg:
        reasons.append(f"Gamme {seg}")

    use = tyre.get("Use") or ""
    if use:
        reasons.append(f"Usage : {use}")

    t_terrain = tyre.get("Terrain Types") or ""
    if t_terrain:
        reasons.append(f"Terrain : {t_terrain.lower()}")

    rubber = tyre.get("Rubber Technologies") or ""
    if rubber:
        reasons.append(f"Gomme : {rubber}")

    casing = tyre.get("Casing Technologies") or ""
    if casing:
        reasons.append(f"Carcasse : {casing}")

    tread = tyre.get("Tread Pattern Technologies") or ""
    if tread:
        reasons.append(f"Sculpture : {tread}")

    reinf = tyre.get("Reinforcement Technologies") or ""
    if reinf:
        reasons.append(f"Renfort : {reinf}")

    sealing = tyre.get("Sealing") or ""
    if sealing:
        reasons.append(f"Montage : {sealing.lower()}")

    ebike_tech = tyre.get("E-Bike Technologies") or ""
    if e_bike and ebike_tech:
        reasons.append(f"Technologie e-bike : {ebike_tech}")

    return reasons[:5]


def find_best_tyres(
    bike_type: str,
    riding_style: str,
    terrain: str,
    budget_level: str,
    tubeless: bool,
    e_bike: bool = False,
    top_n: int = 3,
) -> list[dict]:
    catalogue = _load()

    # Step 1 — hard filter: bike type (and e-bike flag)
    candidates = [
        t for t in catalogue
        if t.get("Web Range Name")
        and t.get("Product Type") == "TYRE"
        and _web_type_matches(t, bike_type, e_bike)
    ]

    # Step 2 — optional soft filter by tubeless (don't apply if it would leave 0 results)
    tubeless_filtered = [t for t in candidates if _SEALING[tubeless] in (t.get("Sealing") or "").upper()]
    if tubeless_filtered:
        candidates = tubeless_filtered

    # Step 3 — deduplicate by Web Range Name (keep first occurrence per range)
    seen: dict[str, dict] = {}
    for t in candidates:
        name = t["Web Range Name"]
        if name not in seen:
            seen[name] = t
    unique = list(seen.values())

    # Step 4 — score and rank
    scored = sorted(
        unique,
        key=lambda t: _score(t, bike_type, riding_style, terrain, budget_level, tubeless, e_bike),
        reverse=True,
    )

    # Step 5 — build output dicts
    results = []
    for t in scored[:top_n]:
        web_range = t["Web Range Name"]
        slug = web_range.lower().replace(" ", "-")
        results.append({
            "brand": "Michelin",
            "model": web_range,
            "category": bike_type,
            "segment": t.get("Segment") or "",
            "use": t.get("Use") or "",
            "terrain_types": t.get("Terrain Types") or "",
            "sealing": t.get("Sealing") or "",
            "reasons": _build_reasons(t, bike_type, riding_style, terrain, tubeless, e_bike),
            "product_url": f"{MICHELIN_BASE_URL}/{slug}",
            "pic1": t.get("PIC1") or None,
            "pic2": t.get("PIC2") or None,
        })

    return results
