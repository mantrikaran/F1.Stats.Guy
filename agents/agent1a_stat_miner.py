# ═══════════════════════════════════════════════════════════════════════
# F1 STATS GUY — AGENT 1A: CATEGORY 1 (V4 — CORRECT STATUS CLASSIFICATION)
# ═══════════════════════════════════════════════════════════════════════

import requests
import time
from datetime import datetime

# ── CONFIG ───────────────────────────────────────────────────────────────
CURRENT_SEASON       = 2026
LAST_COMPLETED_ROUND = 4
BASE                 = "https://api.jolpi.ca/ergast/f1"
SLEEP                = 0.8

RACE_DRIVERS = [
    "albon", "alonso", "antonelli", "bearman", "bortoleto",
    "colapinto", "doohan", "gasly", "hadjar", "hamilton",
    "hulkenberg", "lawson", "leclerc", "norris", "ocon",
    "piastri", "russell", "sainz", "stroll", "max_verstappen"
]

# ── STATUS SETS ───────────────────────────────────────────────────────────
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

# ── THRESHOLDS ───────────────────────────────────────────────────────────
T_GROUP1        = [1,2,5,10,25,50,75,100,125,150,175,200,225,250,275,300]
T_GROUP2        = [1,50,100,150,200,250,300]
T_GROUP3_DNFS   = [1,2,5,10,25,50,75,100]
T_GROUP3_DSQ    = [1,2,5,10,25,50]
T_GROUP5_SEASON = [12,16,20]
T_PRERACE       = [25,50,100,150,200,250,300]
PRERACE_WINDOW  = 1

# ── HELPERS ──────────────────────────────────────────────────────────────
def safe_get(url, retries=3):
    for i in range(retries):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200 and r.text.strip():
                return r.json()
        except Exception as e:
            print(f"  ⚠ Error: {e}")
        time.sleep(2)
    return None

def get_total(path):
    data = safe_get(f"{BASE}/{path}")
    time.sleep(SLEEP)
    return int(data["MRData"]["total"]) if data else 0

def crossed_threshold(before, after, thresholds):
    for t in thresholds:
        if before < t <= after:
            return True, t
    return False, None

def approaching_threshold(current, thresholds, window):
    for t in thresholds:
        if t - current == window:
            return True, t
    return False, None

def classify_status(status):
    if status in FINISHED_STATUSES:  return "finished"
    if status in DNFS_STATUSES:      return "dnfs"
    if status in DSQ_STATUSES:       return "dsq"
    return "unknown"

# ── FETCH SHARED DATA ─────────────────────────────────────────────────────
def fetch_race_and_quali(season, round_num):
    race_data = safe_get(f"{BASE}/{season}/{round_num}/results/")
    time.sleep(SLEEP)
    if not race_data or not race_data["MRData"]["RaceTable"]["Races"]:
        return None, {}, {}, {}
    race = race_data["MRData"]["RaceTable"]["Races"][0]

    constructor_map = {}
    for r in race["Results"]:
        cid = r["Constructor"]["constructorId"]
        if cid not in constructor_map:
            constructor_map[cid] = []
        constructor_map[cid].append(r)

    quali_map = {}
    quali_data = safe_get(f"{BASE}/{season}/{round_num}/qualifying/")
    time.sleep(SLEEP)
    if quali_data and quali_data["MRData"]["RaceTable"]["Races"]:
        for q in quali_data["MRData"]["RaceTable"]["Races"][0].get(
                "QualifyingResults", []):
            quali_map[q["Driver"]["driverId"]] = int(q["position"])

    constructor_quali_map = {}
    for driver_id, qp in quali_map.items():
        for r in race["Results"]:
            if r["Driver"]["driverId"] == driver_id:
                cid = r["Constructor"]["constructorId"]
                if cid not in constructor_quali_map:
                    constructor_quali_map[cid] = {}
                constructor_quali_map[cid][driver_id] = qp
                break

    return race, quali_map, constructor_map, constructor_quali_map

def fetch_season_results(season):
    data = safe_get(f"{BASE}/{season}/results/?limit=1000")
    time.sleep(SLEEP)
    if not data:
        return {}
    season_map = {}
    for race in data["MRData"]["RaceTable"]["Races"]:
        rnd = int(race["round"])
        for r in race.get("Results", []):
            did = r["Driver"]["driverId"]
            cid = r["Constructor"]["constructorId"]
            if did not in season_map:
                season_map[did] = []
            season_map[did].append({
                "round":          rnd,
                "finish_pos":     int(r["position"]),
                "constructor_id": cid,
            })
    return season_map

def fetch_season_qualifying(season):
    data = safe_get(f"{BASE}/{season}/qualifying/?limit=1000")
    time.sleep(SLEEP)
    if not data:
        return {}
    quali_map = {}
    for race in data["MRData"]["RaceTable"]["Races"]:
        rnd = int(race["round"])
        for q in race.get("QualifyingResults", []):
            did = q["Driver"]["driverId"]
            quali_map[(rnd, did)] = int(q["position"])
    return quali_map

# ── EXTRACT RACE FACTS ────────────────────────────────────────────────────
def extract_race_facts(driver_id, race, quali_map,
                       constructor_map, constructor_quali_map):
    for r in race["Results"]:
        if r["Driver"]["driverId"] != driver_id:
            continue

        fp     = int(r["position"])
        qp     = quali_map.get(driver_id)
        cid    = r["Constructor"]["constructorId"]
        status = r["status"]
        cat    = classify_status(status)

        beat_tm_finish = False
        beat_tm_quali  = False
        teammates = [x for x in constructor_map.get(cid, [])
                     if x["Driver"]["driverId"] != driver_id]
        if teammates:
            tm = teammates[0]
            beat_tm_finish = fp < int(tm["position"])

        tm_quali = constructor_quali_map.get(cid, {})
        my_qp    = tm_quali.get(driver_id)
        for tid, tqp in tm_quali.items():
            if tid != driver_id and my_qp and my_qp < tqp:
                beat_tm_quali = True

        return {
            "finish_pos":     fp,
            "quali_pos":      qp,
            "status_cat":     cat,
            "dnfs":           1 if cat == "dnfs" else 0,
            "dsq":            1 if cat == "dsq"  else 0,
            "beat_tm_finish": beat_tm_finish,
            "beat_tm_quali":  beat_tm_quali,
            "constructor_id": cid,
        }

    return {"finish_pos": None, "quali_pos": None, "status_cat": "unknown",
            "dnfs": 0, "dsq": 0, "beat_tm_finish": False,
            "beat_tm_quali": False, "constructor_id": None}

# ── CAREER STATS ──────────────────────────────────────────────────────────
def get_career_stats(driver_id):
    all_res = safe_get(f"{BASE}/drivers/{driver_id}/results/?limit=1000")
    time.sleep(SLEEP)
    wins = podiums = top2 = top10 = dnfs = dsq = 0
    if all_res:
        for race in all_res["MRData"]["RaceTable"]["Races"]:
            for r in race.get("Results", []):
                pos    = int(r.get("position", 99))
                status = r.get("status", "")
                cat    = classify_status(status)
                if pos == 1:         wins    += 1
                if pos <= 3:         podiums += 1
                if pos <= 2:         top2    += 1
                if pos <= 10:        top10   += 1
                if cat == "dnfs":    dnfs    += 1
                if cat == "dsq":     dsq     += 1

    all_q = safe_get(f"{BASE}/drivers/{driver_id}/qualifying/?limit=1000")
    time.sleep(SLEEP)
    poles = front_rows = q3 = 0
    if all_q:
        for race in all_q["MRData"]["RaceTable"]["Races"]:
            for q in race.get("QualifyingResults", []):
                pos = int(q.get("position", 99))
                if pos == 1:  poles      += 1
                if pos <= 2:  front_rows += 1
                if pos <= 10: q3         += 1

    return {
        "wins": wins, "poles": poles, "podiums": podiums,
        "top2": top2, "front_rows": front_rows,
        "top10": top10, "q3": q3,
        "dnfs": dnfs, "dsq": dsq,
    }

# ── SEASON TEAMMATE STATS ─────────────────────────────────────────────────
def compute_season_teammate_stats(driver_id, current_round,
                                  season_results, season_quali):
    driver_races = season_results.get(driver_id, [])
    finish_ahead = quali_ahead = 0

    for race in driver_races:
        rnd = race["round"]
        if rnd > current_round:
            continue
        cid       = race["constructor_id"]
        driver_fp = race["finish_pos"]

        for other_id, other_races in season_results.items():
            if other_id == driver_id:
                continue
            for other_race in other_races:
                if other_race["round"] == rnd and \
                   other_race["constructor_id"] == cid:
                    if driver_fp < other_race["finish_pos"]:
                        finish_ahead += 1

        driver_qp = season_quali.get((rnd, driver_id))
        if driver_qp:
            for other_id, other_races in season_results.items():
                if other_id == driver_id:
                    continue
                for other_race in other_races:
                    if other_race["round"] == rnd and \
                       other_race["constructor_id"] == cid:
                        other_qp = season_quali.get((rnd, other_id))
                        if other_qp and driver_qp < other_qp:
                            quali_ahead += 1

    return quali_ahead, finish_ahead

# ── ROW BUILDERS ──────────────────────────────────────────────────────────
def post_row(driver, metric, before, after, threshold, race_name, season):
    return {
        "Date Generated":   datetime.now().strftime("%Y-%m-%d"),
        "Race Year":        season,
        "Stat Description": f"{driver} reached {threshold} career {metric} "
                            f"(was {before}, now {after})",
        "Category":         "Category 1",
        "Driver":           driver,
        "Metric":           metric,
        "Value":            after,
        "Mode":             "Post-Race",
        "Race Name":        race_name,
    }

def pre_row(driver, metric, current, target, race_name, season):
    return {
        "Date Generated":   datetime.now().strftime("%Y-%m-%d"),
        "Race Year":        season,
        "Stat Description": f"{driver} is {PRERACE_WINDOW} {metric} away "
                            f"from {target} ({current} so far)",
        "Category":         "Category 1",
        "Driver":           driver,
        "Metric":           metric,
        "Value":            current,
        "Mode":             "Pre-Race",
        "Race Name":        race_name,
    }

def season_row(driver, metric, before, after, threshold, race_name, season):
    return {
        "Date Generated":   datetime.now().strftime("%Y-%m-%d"),
        "Race Year":        season,
        "Stat Description": f"{driver} has beaten teammate {threshold} times "
                            f"in {metric} in {season} (was {before}, now {after})",
        "Category":         "Category 1",
        "Driver":           driver,
        "Metric":           metric,
        "Value":            after,
        "Mode":             "Post-Race",
        "Race Name":        race_name,
    }

# ── MAIN ──────────────────────────────────────────────────────────────────
def run_category_1(season, round_num):
    print(f"\n{'='*60}")
    print(f"AGENT 1A — CATEGORY 1  |  Season {season}  Round {round_num}")
    print(f"{'='*60}\n")

    print("Fetching shared race data...")
    race, quali_map, constructor_map, constructor_quali_map = \
        fetch_race_and_quali(season, round_num)
    if not race:
        print("❌ Could not fetch race data.")
        return []

    print("Fetching full season results...")
    season_results = fetch_season_results(season)

    print("Fetching full season qualifying...")
    season_quali = fetch_season_qualifying(season)

    race_name    = race["raceName"]
    participants = [r["Driver"]["driverId"] for r in race["Results"]
                    if r["Driver"]["driverId"] in RACE_DRIVERS]

    print(f"\nRace : {race_name}")
    print(f"Checking {len(participants)} drivers...\n")

    found = []

    for driver in participants:
        print(f"→ {driver}")

        facts  = extract_race_facts(driver, race, quali_map,
                                    constructor_map, constructor_quali_map)
        career = get_career_stats(driver)

        fp = facts["finish_pos"]
        qp = facts["quali_pos"]

        inc = {
            "wins":       1 if fp == 1          else 0,
            "poles":      1 if qp == 1          else 0,
            "podiums":    1 if fp and fp <= 3   else 0,
            "top2":       1 if fp and fp <= 2   else 0,
            "front_rows": 1 if qp and qp <= 2  else 0,
            "top10":      1 if fp and fp <= 10  else 0,
            "q3":         1 if qp and qp <= 10  else 0,
            "dnfs":       facts["dnfs"],
            "dsq":        facts["dsq"],
        }

        # ── GROUP 1 ───────────────────────────────────────────────────
        for metric in ["wins","poles","podiums","top2","front_rows"]:
            after  = career[metric]
            before = after - inc[metric]

            hit, t = crossed_threshold(before, after, T_GROUP1)
            if hit:
                found.append(post_row(driver, metric, before, after,
                                      t, race_name, season))
                print(f"  ✅ [POST] {metric}: {before}→{after} (hit {t})")

            near, t = approaching_threshold(after, T_PRERACE, PRERACE_WINDOW)
            if near:
                found.append(pre_row(driver, metric, after, t,
                                     race_name, season))
                print(f"  🔜 [PRE]  {metric}: {after} (1 away from {t})")

        # ── GROUP 2 ───────────────────────────────────────────────────
        for metric, key in [("top10_finishes","top10"),
                             ("q3_appearances","q3")]:
            after  = career[key]
            before = after - inc[key]

            hit, t = crossed_threshold(before, after, T_GROUP2)
            if hit:
                found.append(post_row(driver, metric, before, after,
                                      t, race_name, season))
                print(f"  ✅ [POST] {metric}: {before}→{after} (hit {t})")

            near, t = approaching_threshold(after, T_PRERACE, PRERACE_WINDOW)
            if near:
                found.append(pre_row(driver, metric, after, t,
                                     race_name, season))
                print(f"  🔜 [PRE]  {metric}: {after} (1 away from {t})")

        # ── GROUP 3: DNF/S ────────────────────────────────────────────
        after  = career["dnfs"]
        before = after - inc["dnfs"]
        hit, t = crossed_threshold(before, after, T_GROUP3_DNFS)
        if hit:
            found.append(post_row(driver, "dnfs", before, after,
                                  t, race_name, season))
            print(f"  ✅ [POST] dnfs: {before}→{after} (hit {t})")

        # ── GROUP 3: DSQ ──────────────────────────────────────────────
        after  = career["dsq"]
        before = after - inc["dsq"]
        hit, t = crossed_threshold(before, after, T_GROUP3_DSQ)
        if hit:
            found.append(post_row(driver, "dsq", before, after,
                                  t, race_name, season))
            print(f"  ✅ [POST] dsq: {before}→{after} (hit {t})")

        # ── GROUP 5: Season teammate ──────────────────────────────────
        s_quali_total, s_finish_total = compute_season_teammate_stats(
            driver, round_num, season_results, season_quali)

        s_quali_before  = s_quali_total  - (1 if facts["beat_tm_quali"]  else 0)
        s_finish_before = s_finish_total - (1 if facts["beat_tm_finish"] else 0)

        hit, t = crossed_threshold(s_quali_before, s_quali_total,
                                   T_GROUP5_SEASON)
        if hit:
            found.append(season_row(driver, "season_quali_vs_teammate",
                                    s_quali_before, s_quali_total,
                                    t, race_name, season))
            print(f"  ✅ [POST] season_quali_vs_teammate: "
                  f"{s_quali_before}→{s_quali_total} (hit {t})")

        hit, t = crossed_threshold(s_finish_before, s_finish_total,
                                   T_GROUP5_SEASON)
        if hit:
            found.append(season_row(driver, "season_finish_vs_teammate",
                                    s_finish_before, s_finish_total,
                                    t, race_name, season))
            print(f"  ✅ [POST] season_finish_vs_teammate: "
                  f"{s_finish_before}→{s_finish_total} (hit {t})")

    print(f"\n{'='*60}")
    print(f"TOTAL INSIGHTS FOUND: {len(found)}")
    print(f"{'='*60}")
    for row in found:
        print(f"  [{row['Mode']}] [{row['Metric']}] {row['Stat Description']}")

    return found

# ── RUN ───────────────────────────────────────────────────────────────────
results = run_category_1(CURRENT_SEASON, LAST_COMPLETED_ROUND)
