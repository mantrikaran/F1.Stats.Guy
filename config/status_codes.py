# ═══════════════════════════════════════════════════════════════════════
# F1 STATS GUY — JOLPICA STATUS CLASSIFICATION
# ═══════════════════════════════════════════════════════════════════════

FINISHED_STATUSES = {
    "Finished", "+1 Lap", "+2 Laps", "+3 Laps", "Lapped"
}

DNFS_STATUSES = {
    "Retired", "Accident", "Collision", "Collision damage",
    "Brakes", "Debris", "Did not start", "Driveshaft",
    "Electrical", "Electronics", "Engine", "Exhaust",
    "Front wing", "Fuel pressure", "Fuel pump", "Fuel system",
    "Gearbox", "Hydraulics", "Mechanical", "Oil leak",
    "Oil pressure", "Overheating", "Power Unit", "Power loss",
    "Puncture", "Radiator", "Spun off", "Suspension",
    "Transmission", "Turbo", "Tyre", "Water pressure",
    "Wheel", "Withdrew"
}

DSQ_STATUSES = {"Disqualified"}


def classify_status(status):
    if status in FINISHED_STATUSES: return "finished"
    if status in DNFS_STATUSES:     return "dnfs"
    if status in DSQ_STATUSES:      return "dsq"
    return "unknown"
