"""
Convert Opportunity Atlas CSV to compact JSON for frontend.
Input:  Table_1_county_trends_estimates.csv
Output: data/counties.json
Values: kfr = income rank percentile (0-1 scale) -> multiply by 100 for display
"""
import csv, json, os, statistics

os.makedirs("data", exist_ok=True)
INPUT = "Table_1_county_trends_estimates.csv"
OUTPUT = "data/counties.json"

rows = []
with open(INPUT, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            st = row.get("state", "").strip()
            co = row.get("county", "").strip()
            if not st or not co:
                continue
            fips = str(int(st)).zfill(2) + str(int(co)).zfill(3)

            p1_raw = row.get("kfr_pooled_pooled_p1_1978", "").strip()
            p100_raw = row.get("kfr_pooled_pooled_p100_1978", "").strip()
            change_raw = row.get("change_kfr_pooled_pooled_p1", "").strip()

            if not p1_raw or not p100_raw or not change_raw:
                continue
            if p1_raw == "." or p100_raw == "." or change_raw == ".":
                continue

            p1 = float(p1_raw)
            p100 = float(p100_raw)
            change = float(change_raw)

            # Values are 0-1 percentile ranks; convert to 0-100
            p1_pct = round(p1 * 100, 1)
            p100_pct = round(p100 * 100, 1)
            change_pct = round(change * 100, 1)  # change in pctile points

            # Sanity check
            if p1_pct < 5 or p1_pct > 95 or p100_pct < 5 or p100_pct > 95:
                continue

            rows.append({
                "fips": fips,
                "sf": str(int(st)).zfill(2),
                "name": row.get("county_name", "").strip(),
                "state": row.get("state_name", "").strip(),
                "p1": p1_pct,
                "p100": p100_pct,
                "ch": change_pct,
            })
        except (ValueError, KeyError):
            continue

print(f"Parsed {len(rows)} counties")
print(f"p1 range: {min(r['p1'] for r in rows):.1f} - {max(r['p1'] for r in rows):.1f}")
print(f"p100 range: {min(r['p100'] for r in rows):.1f} - {max(r['p100'] for r in rows):.1f}")
print(f"change range: {min(r['ch'] for r in rows):.1f} - {max(r['ch'] for r in rows):.1f}")

# State-level aggregation
state_data = {}
for r in rows:
    s = r["state"]
    if s not in state_data:
        state_data[s] = {"p1": [], "p100": [], "ch": [], "sf": r["sf"]}
    state_data[s]["p1"].append(r["p1"])
    state_data[s]["p100"].append(r["p100"])
    state_data[s]["ch"].append(r["ch"])

states = []
for name, d in state_data.items():
    if len(d["p1"]) < 3:
        continue  # skip tiny states
    states.append({
        "state": name,
        "sf": d["sf"],
        "p1": round(statistics.mean(d["p1"]), 1),
        "p100": round(statistics.mean(d["p100"]), 1),
        "ch": round(statistics.mean(d["ch"]), 1),
        "n": len(d["p1"]),
    })

states.sort(key=lambda x: x["ch"], reverse=True)

output = {"counties": rows, "states": states}
with open(OUTPUT, "w") as f:
    json.dump(output, f)

sz = os.path.getsize(OUTPUT)
print(f"Saved {OUTPUT}: {len(rows)} counties, {len(states)} states, {sz/1024:.0f} KB")
