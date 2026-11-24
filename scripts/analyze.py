"""Download GHCN-Daily and compare New England snowfall. Python 3.11+, stdlib only."""
import argparse
import calendar
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import random
import statistics as stats
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
BASE = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
STATES = ("CT", "MA", "ME", "NH", "RI", "VT")


def download(name):
    path = DATA / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(BASE + name, timeout=120) as response:
                    content = response.read()
                path.write_bytes(content)
                break
            except Exception:
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
    return path


def candidates():
    stations = {}
    for line in download("ghcnd-stations.txt").read_text().splitlines():
        if line[38:40] in STATES:
            stations[line[:11]] = dict(id=line[:11], state=line[38:40],
                                      name=line[41:71].strip(),
                                      lat=float(line[12:20]), lon=float(line[21:30]))
    selected = set()
    for line in download("ghcnd-inventory.txt").read_text().splitlines():
        if (line[:11] in stations and line[31:35] == "SNOW"
                and int(line[36:40]) <= 1960 and int(line[41:45]) >= 2013):
            selected.add(line[:11])
    return [stations[key] for key in sorted(selected)]


def parse_snow(path):
    """Missing, negative and QA-flagged values are not zeros; traces are zero mm."""
    months = {}
    for line in path.read_text().splitlines():
        year, month = int(line[11:15]), int(line[15:17])
        if line[17:21] != "SNOW" or not 1940 <= year <= 2019:
            continue
        values = []
        for day in range(calendar.monthrange(year, month)[1]):
            pos = 21 + 8 * day
            value, quality = int(line[pos:pos + 5]), line[pos + 6]
            if value >= 0 and quality == " ":
                values.append(value)
        months[year, month] = values
    return months


def annuals(months, threshold):
    result = {}
    for year in range(1940, 2020):
        # Apply the same monthly rule all year: missing summer zeros are not assumed.
        if all(len(months.get((year, m), [])) >=
               threshold * calendar.monthrange(year, m)[1] for m in range(1, 13)):
            result[year] = sum(sum(months[year, m]) for m in range(1, 13)) / 25.4
    return result


def panel(records, threshold):
    retained = []
    for station, months in records:
        years = annuals(months, threshold)
        old = [v for y, v in years.items() if y < 2000]
        new = [v for y, v in years.items() if y >= 2000]
        if len(old) >= 40 and len(new) >= 14 and stats.mean(old) > 0:
            retained.append(dict(**station, years=years, old=stats.mean(old),
                                 new=stats.mean(new), n_old=len(old), n_new=len(new)))
    return retained


def regional(panel, old_years=None, new_years=None):
    """State-balanced mean station percent changes, not a spatial snowfall total."""
    changes = {state: [] for state in STATES}
    for s in panel:
        old = s["old"] if old_years is None else stats.mean(
            s["years"][y] for y in old_years if y in s["years"])
        new = s["new"] if new_years is None else stats.mean(
            s["years"][y] for y in new_years if y in s["years"])
        changes[s["state"]].append(100 * (new / old - 1))
    if any(not values for values in changes.values()):
        return None, {}
    by_state = {state: stats.mean(values) for state, values in changes.items()}
    return stats.mean(by_state.values()), by_state


def bootstrap(panel, repetitions=5000, block=1):
    rng = random.Random(1939 + block)
    results = []
    def sample(start, count):
        # Circular blocks preserve short-range dependence; years shared across stations.
        starts = [rng.randrange(count) for _ in range((count + block - 1) // block)]
        return [start + (i + j) % count for i in starts for j in range(block)][:count]
    for _ in range(repetitions):
        value, _ = regional(panel, sample(1940, 60), sample(2000, 20))
        results.append(value)
    results.sort()
    return [results[int(repetitions * .025)], results[int(repetitions * .975)]]


def run(refresh=False):
    if refresh:
        raise SystemExit("For a fresh snapshot, remove the ignored data/ cache and rerun.")
    DATA.mkdir(exist_ok=True)
    download("ghcnd-version.txt")
    stations = candidates()
    print(f"Downloading {len(stations)} candidate station files...", flush=True)
    def load(s):
        return s, parse_snow(download(f'all/{s["id"]}.dly'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(load, stations))
    primary = panel(records, .95)
    change, by_state = regional(primary)
    if change is None:
        raise RuntimeError("Primary panel does not represent every state.")
    sensitivities = []
    for threshold in (.90, .95, 1.0):
        p = panel(records, threshold)
        value, _ = regional(p)
        sensitivities.append(dict(monthly_coverage=threshold, stations=len(p), change=value,
                                  states=sorted({s["state"] for s in p})))
    series = []
    for year in range(1940, 2020):
        states = {}
        for state in STATES:
            values = [100 * (s["years"][year] / s["old"] - 1) for s in primary
                      if s["state"] == state and year in s["years"]]
            if values:
                states[state] = stats.mean(values)
        series.append(dict(year=year, anomaly=stats.mean(states.values())
                           if len(states) == 6 else None,
                           stations=sum(year in s["years"] for s in primary)))
    manifest = []
    for path in sorted(DATA.rglob("*")):
        if path.is_file():
            manifest.append(dict(file=str(path.relative_to(DATA)).replace("\\", "/"),
                                 bytes=path.stat().st_size,
                                 sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    output = dict(retrieved=dt.date.today().isoformat(),
                  version=(DATA / "ghcnd-version.txt").read_text().strip(),
                  candidate_count=len(stations), station_count=len(primary),
                  change=change, states=by_state, ci=bootstrap(primary),
                  block_ci=bootstrap(primary, block=5), sensitivity=sensitivities,
                  series=series,
                  stations=[{k: v for k, v in s.items() if k != "years"} for s in primary])
    out = ROOT / "docs" / "assets"
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with (out / "station-years.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["station", "state", "year", "snowfall_inches"])
        for s in primary:
            for year, value in sorted(s["years"].items()):
                writer.writerow([s["id"], s["state"], year, round(value, 4)])
    print(json.dumps({k: output[k] for k in
                      ("candidate_count", "station_count", "change", "states", "ci",
                       "block_ci", "sensitivity")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    run(parser.parse_args().refresh)
