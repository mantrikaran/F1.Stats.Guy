# ═══════════════════════════════════════════════════════════════════════
# F1 STATS GUY — CONSTRUCTOR CONFIG
# Updated manually only when a team rebrand occurs
# ═══════════════════════════════════════════════════════════════════════

# Maps current constructor name to all historical Jolpica IDs
CONSTRUCTOR_ID_MAP = {
    "McLaren":      ["mclaren"],
    "Mercedes":     ["mercedes"],
    "Ferrari":      ["ferrari"],
    "Red Bull":     ["red_bull"],
    "Alpine":       ["alpine", "renault"],
    "Aston Martin": ["aston_martin"],
    "Williams":     ["williams"],
    "RB":           ["rb", "alphatauri", "toro_rosso"],
    "Haas":         ["haas"],
    "Sauber":       ["sauber", "alfa"],
}

# Maps any Jolpica constructor ID to current team name
# Auto-derived from CONSTRUCTOR_ID_MAP — do not edit manually
JOLPICA_TO_CURRENT = {
    jolpica_id: current_name
    for current_name, jolpica_ids in CONSTRUCTOR_ID_MAP.items()
    for jolpica_id in jolpica_ids
}
