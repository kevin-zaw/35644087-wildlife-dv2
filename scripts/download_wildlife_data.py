#!/usr/bin/env python3
"""
download_wildlife_data.py  (FIT3179 Data Visualisation 2)

Downloads COUNTS of wildlife records in Australia from the Atlas of Living
Australia (ALA) biocache web service, with the GBIF API as an automatic
fallback. It never downloads individual records, only facet counts, so it is
quick, needs no login and no API key, and uses only the Python standard library.

What it produces (in data/ala/):
  groups.csv              records per species group, all years and recent decade
  basis_by_group.csv      records per group and basis of record (human observation, specimen ...)
  year_by_group.csv       records per group and year, all records and human observations only
  month_by_group.csv      records per group and month (recent decade)
  state_by_group.csv      records per group and state or territory (recent decade)
  state_by_month.csv      records per state and month (recent decade, all wildlife)
  grid1_by_group.csv      records per 1-degree square and group (recent decade)
  grid1_by_month.csv      records per 1-degree square and month (recent decade, all wildlife)
  resource_by_group.csv   top data sources per group (recent decade, human observations)
  species_by_group.csv    distinct species recorded per group (all years and recent decade)
  manifest.json           every query URL, the filters used, timestamps and row counts
  SUMMARY.txt             a short human-readable summary
It also writes download_log.txt and results_for_claude.zip in the project folder.

Usage (from the project folder, in the VS Code terminal):
  python scripts/download_wildlife_data.py            full download (about 5-15 minutes)
  python scripts/download_wildlife_data.py --test     30-second connection test
  python scripts/download_wildlife_data.py --fresh    ignore cached answers and download again
  python scripts/download_wildlife_data.py --years 2016-2025
  python scripts/download_wildlife_data.py --source gbif   force the GBIF fallback
  python scripts/download_wildlife_data.py --insecure      only if you get SSL certificate errors
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

try:  # avoid crashes on Windows consoles that are not UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "ala"
RAW = OUT / "raw"
LOG_PATH = ROOT / "download_log.txt"
ZIP_PATH = ROOT / "results_for_claude.zip"

ALA = "https://biocache-ws.ala.org.au/ws"
GBIF = "https://api.gbif.org/v1"
USER_AGENT = "FIT3179-DV2-student-visualisation/1.0 (Monash University; Python urllib)"

# Species groups to analyse (ALA "species group" labels), with accepted spellings.
TARGET_GROUPS = [
    ("Birds", ["birds"]),
    ("Mammals", ["mammals"]),
    ("Reptiles", ["reptiles"]),
    ("Amphibians", ["amphibians", "frogs"]),
    ("Fishes", ["fishes", "fish"]),
    ("Insects", ["insects"]),
    ("Arachnids", ["arachnids", "spiders"]),
    ("Molluscs", ["molluscs"]),
    ("Crustaceans", ["crustaceans"]),
    ("Plants", ["plants"]),
    ("Fungi", ["fungi"]),
]
# Taxa used for each group if the GBIF fallback is needed.
GBIF_TAXA = {
    "Birds": ["Aves"], "Mammals": ["Mammalia"], "Reptiles": ["Squamata", "Testudines", "Crocodylia"],
    "Amphibians": ["Amphibia"], "Fishes": ["Actinopterygii", "Elasmobranchii"], "Insects": ["Insecta"],
    "Arachnids": ["Arachnida"], "Molluscs": ["Mollusca"], "Crustaceans": ["Malacostraca"],
    "Plants": ["Plantae"], "Fungi": ["Fungi"],
}
STATES = ["New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia",
          "Tasmania", "Northern Territory", "Australian Capital Territory"]

FIELD_CANDIDATES = {
    "group": ["speciesGroup", "species_group"],
    "state": ["stateProvince", "state"],
    "month": ["month"],
    "year": ["year"],
    "basis": ["basisOfRecord", "basis_of_record"],
    "resource": ["dataResourceName", "data_resource", "dataResourceUid", "data_resource_uid"],
    "grid": ["point-1", "point_1"],
    "species": ["speciesID", "species_guid", "species", "taxonConceptID"],
}

STATS = {"queries": 0, "cached": 0, "failures": []}
QUERY_LOG = []
SSL_CONTEXT = None


# ----------------------------------------------------------------------------- utilities
def log(msg):
    stamp = dt.datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def get_json(url, fresh=False, tries=4, pause=0.35):
    """GET a URL and parse JSON, with on-disk caching, retries and back-off."""
    RAW.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode("utf-8")).hexdigest()[:20]
    cache = RAW / f"{key}.json"
    if cache.exists() and not fresh:
        STATS["cached"] += 1
        return json.loads(cache.read_text(encoding="utf-8"))
    last_err = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=90, context=SSL_CONTEXT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            cache.write_text(json.dumps(data), encoding="utf-8")
            STATS["queries"] += 1
            time.sleep(pause)
            return data
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}"
            if e.code in (400, 404):
                break  # bad parameter, retrying will not help
        except urllib.error.URLError as e:
            last_err = f"network error: {e.reason}"
            if isinstance(e.reason, ssl.SSLError) or "CERTIFICATE" in str(e.reason).upper():
                log("SSL certificate problem. On a Mac run 'Install Certificates.command' from your "
                    "Python folder, or rerun this script with --insecure.")
                break
        except Exception as e:  # timeouts, bad JSON
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(2 ** attempt)
    raise RuntimeError(f"{last_err} for {url}")


def write_csv(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    log(f"  wrote {name}: {len(rows)} rows")
    return len(rows)


def quote(value):
    return '"' + str(value).replace('"', '\\"') + '"'


# ----------------------------------------------------------------------------- ALA
def ala_search(fqs, facets=(), flimit=-1, fresh=False, label=""):
    params = [("q", "*:*"), ("pageSize", "0"), ("facet", "true" if facets else "false"),
              ("flimit", str(flimit))]
    if facets:
        params.append(("facets", ",".join(facets)))
    for fq in fqs:
        params.append(("fq", fq))
    url = ALA + "/occurrences/search?" + urllib.parse.urlencode(params)
    data = get_json(url, fresh=fresh)
    QUERY_LOG.append({"source": "ALA", "label": label, "url": url, "totalRecords": data.get("totalRecords")})
    out = {}
    for fr in data.get("facetResults", []) or []:
        out[fr.get("fieldName")] = [(r.get("label"), int(r.get("count", 0)), r.get("fq")) for r in fr.get("fieldResult", [])]
    return data.get("totalRecords", 0), out


def facet_values(result, field):
    """Facet results may come back under the requested name or a legacy alias."""
    if field in result:
        return result[field]
    return next(iter(result.values()), []) if len(result) == 1 else []


def detect_fields(base, fresh):
    chosen = {}
    for dim, cands in FIELD_CANDIDATES.items():
        for cand in cands:
            try:
                _, res = ala_search(base, [cand], flimit=5, fresh=fresh, label=f"detect {dim}")
                if facet_values(res, cand):
                    chosen[dim] = cand
                    break
            except RuntimeError:
                continue
        log(f"  field for {dim}: {chosen.get(dim, 'NOT FOUND')}")
    return chosen


def detect_country_filter(fresh):
    total_all, _ = ala_search([], fresh=fresh, label="total, no filter")
    for fq in ["countryCode:AU", 'country:"Australia"', "country_code:AU"]:
        try:
            n, _ = ala_search([fq], fresh=fresh, label=f"country test {fq}")
            if n and n > 0:
                log(f"  country filter '{fq}': {n:,} of {total_all:,} records")
                return [fq], total_all
        except RuntimeError:
            continue
    log("  no country filter accepted; using all ALA records")
    return [], total_all


def run_ala(args):
    log("Source: Atlas of Living Australia biocache web service")
    y0, y1 = args.years
    base, total_all = detect_country_filter(args.fresh)
    F = detect_fields(base, args.fresh)
    if "group" not in F:
        raise RuntimeError("ALA species group field not found")
    yr = [f"{F['year']}:[{y0} TO {y1}]"] if "year" in F else []
    human = [f"{F['basis']}:HUMAN_OBSERVATION"] if "basis" in F else []
    files = {}

    # 1. groups: all years and recent decade
    log("Step 1/9: species groups")
    tot_base, res = ala_search(base, [F["group"]], fresh=args.fresh, label="groups all years")
    all_groups = facet_values(res, F["group"])
    tot_recent, res_r = ala_search(base + yr, [F["group"]], fresh=args.fresh, label="groups recent")
    recent = {lab: c for lab, c, _ in facet_values(res_r, F["group"])}
    _, res_h = ala_search(base + yr + human, [F["group"]], fresh=args.fresh, label="groups recent human")
    recent_h = {lab: c for lab, c, _ in facet_values(res_h, F["group"])}
    files["groups.csv"] = write_csv(
        "groups.csv", ["group", "records_all_years", f"records_{y0}_{y1}", f"human_observations_{y0}_{y1}", "fq"],
        [[lab, c, recent.get(lab, 0), recent_h.get(lab, 0), fq] for lab, c, fq in all_groups])

    # map our target groups onto the labels the ALA actually uses
    label_fq = {lab.lower(): (lab, fq) for lab, _, fq in all_groups if lab}
    groups = []
    for name, spellings in TARGET_GROUPS:
        for sp in spellings:
            if sp in label_fq:
                lab, fq = label_fq[sp]
                groups.append((name, fq or f"{F['group']}:{quote(lab)}"))
                break
        else:
            log(f"  group '{name}' not offered by the ALA; skipped")
    log(f"  analysing {len(groups)} groups: {', '.join(g for g, _ in groups)}")
    targets = [("All wildlife", None)] + groups

    def run(fqs, facet, label, flimit=-1):
        try:
            _, r = ala_search(fqs, [facet], flimit=flimit, fresh=args.fresh, label=label)
            return facet_values(r, facet)
        except RuntimeError as e:
            STATS["failures"].append(f"{label}: {e}")
            log(f"  FAILED {label}: {e}")
            return []

    def gfq(g):
        return [g] if g else []

    # 2. basis of record by group
    log("Step 2/9: basis of record by group")
    rows = []
    for name, g in targets:
        for lab, c, _ in run(base + gfq(g), F["basis"], f"basis {name}"):
            rows.append([name, lab, c])
    files["basis_by_group.csv"] = write_csv("basis_by_group.csv", ["group", "basis_of_record", "records"], rows)

    # 3. year by group (all records, and human observations)
    log("Step 3/9: records per year by group")
    rows = []
    for name, g in targets:
        span = [f"{F['year']}:[1950 TO {y1}]"]
        for kind, extra in [("all records", []), ("human observations", human)]:
            for lab, c, _ in run(base + gfq(g) + span + extra, F["year"], f"year {name} {kind}"):
                rows.append([name, kind, lab, c])
    files["year_by_group.csv"] = write_csv("year_by_group.csv", ["group", "records_type", "year", "records"], rows)

    # 4. month by group (recent decade)
    log("Step 4/9: records per month by group")
    rows = []
    for name, g in targets:
        for lab, c, _ in run(base + gfq(g) + yr, F["month"], f"month {name}"):
            rows.append([name, lab, c])
    files["month_by_group.csv"] = write_csv("month_by_group.csv", ["group", "month", "records"], rows)

    # 5. state by group (recent decade)
    log("Step 5/9: records per state by group")
    rows = []
    state_fqs = {}
    for name, g in targets:
        for lab, c, fq in run(base + gfq(g) + yr, F["state"], f"state {name}"):
            rows.append([name, lab, c])
            if name == "All wildlife" and lab in STATES:
                state_fqs[lab] = fq or f"{F['state']}:{quote(lab)}"
    files["state_by_group.csv"] = write_csv("state_by_group.csv", ["group", "state", "records"], rows)

    # 6. state by month (recent decade, all wildlife)
    log("Step 6/9: records per state and month")
    rows = []
    for st in STATES:
        fq = state_fqs.get(st, f"{F['state']}:{quote(st)}")
        for lab, c, _ in run(base + yr + [fq], F["month"], f"state-month {st}"):
            rows.append([st, lab, c])
    files["state_by_month.csv"] = write_csv("state_by_month.csv", ["state", "month", "records"], rows)

    # 7. 1-degree grid by group, and by month for all wildlife
    if "grid" in F:
        log("Step 7/9: 1-degree grid by group and by month (largest step)")
        rows = []
        for name, g in targets:
            for lab, c, _ in run(base + gfq(g) + yr, F["grid"], f"grid {name}"):
                rows.append([name, lab, c])
        files["grid1_by_group.csv"] = write_csv("grid1_by_group.csv", ["group", "cell", "records"], rows)
        rows = []
        month_vals = run(base + yr, F["month"], "months available")
        for lab, _, fq in month_vals:
            mfq = fq or f"{F['month']}:{quote(lab)}"
            for cell, c, _ in run(base + yr + [mfq], F["grid"], f"grid month {lab}"):
                rows.append([lab, cell, c])
        files["grid1_by_month.csv"] = write_csv("grid1_by_month.csv", ["month", "cell", "records"], rows)
    else:
        log("Step 7/9: skipped, no 1-degree grid field on this server")

    # 8. top data sources (human observations, recent decade)
    log("Step 8/9: top data sources by group")
    rows = []
    if "resource" in F:
        for name, g in targets:
            for lab, c, _ in run(base + gfq(g) + yr + human, F["resource"], f"resource {name}", flimit=25):
                rows.append([name, lab, c])
    files["resource_by_group.csv"] = write_csv("resource_by_group.csv", ["group", "data_resource", "records"], rows)

    # 9. distinct species recorded per group
    log("Step 9/9: distinct species per group")
    rows = []
    if "species" in F:
        for name, g in targets:
            counts = []
            for period, fq_extra in [("all_years", []), ("recent", yr)]:
                params = [("q", "*:*"), ("facets", F["species"]), ("flimit", "0")]
                params += [("fq", f) for f in base + gfq(g) + fq_extra]
                url = ALA + "/occurrence/facets?" + urllib.parse.urlencode(params)
                try:
                    data = get_json(url, fresh=args.fresh)
                    QUERY_LOG.append({"source": "ALA", "label": f"species {name} {period}", "url": url})
                    n = data[0].get("count") if isinstance(data, list) and data else None
                except Exception as e:
                    STATS["failures"].append(f"species {name} {period}: {e}")
                    n = None
                counts.append(n)
            rows.append([name] + counts)
    files["species_by_group.csv"] = write_csv(
        "species_by_group.csv", ["group", "species_all_years", f"species_{y0}_{y1}"], rows)

    meta = {"source": "Atlas of Living Australia biocache web service", "base_url": ALA,
            "base_filters": base, "fields": F, "total_records_unfiltered": total_all,
            "total_records_base_filter": tot_base, f"records_{y0}_{y1}": tot_recent,
            "groups": [g for g, _ in groups]}
    return meta, files


# ----------------------------------------------------------------------------- GBIF fallback
def gbif_search(params, label, fresh):
    url = GBIF + "/occurrence/search?" + urllib.parse.urlencode(params, doseq=True)
    data = get_json(url, fresh=fresh)
    QUERY_LOG.append({"source": "GBIF", "label": label, "url": url, "count": data.get("count")})
    out = {}
    for f in data.get("facets", []) or []:
        out[f["field"].lower()] = [(c["name"], int(c["count"])) for c in f.get("counts", [])]
    return data.get("count", 0), out


def run_gbif(args):
    log("Source: GBIF occurrence API (fallback, no 1-degree grid available)")
    y0, y1 = args.years
    keys = {}
    for group, names in GBIF_TAXA.items():
        ks = []
        for nm in names:
            m = get_json(GBIF + "/species/match?" + urllib.parse.urlencode({"name": nm, "strict": "true"}), fresh=args.fresh)
            if m.get("usageKey") and m.get("matchType") != "NONE":
                ks.append(m["usageKey"])
        keys[group] = ks
        log(f"  {group}: taxon keys {ks}")
    targets = [("All wildlife", [1, 6, 5])] + [(g, k) for g, k in keys.items() if k]  # Animalia, Plantae, Fungi
    base = [("country", "AU"), ("limit", "0")]
    recent = [("year", f"{y0},{y1}")]
    files = {}

    def facet(name, ks, extra, field, label, limit=400):
        params = base + [("taxonKey", k) for k in ks] + extra + [("facet", field), ("facetLimit", str(limit))]
        try:
            _, r = gbif_search(params, label, args.fresh)
            return r.get(field.lower(), [])
        except RuntimeError as e:
            STATS["failures"].append(f"{label}: {e}")
            return []

    rows_g = []
    for name, ks in targets:
        params_all = base + [("taxonKey", k) for k in ks]
        n_all, _ = gbif_search(params_all, f"count {name}", args.fresh)
        n_rec, _ = gbif_search(params_all + recent, f"count {name} recent", args.fresh)
        n_h, _ = gbif_search(params_all + recent + [("basisOfRecord", "HUMAN_OBSERVATION")], f"count {name} human", args.fresh)
        rows_g.append([name, n_all, n_rec, n_h, ""])
    files["groups.csv"] = write_csv("groups.csv", ["group", "records_all_years", f"records_{y0}_{y1}",
                                                   f"human_observations_{y0}_{y1}", "fq"], rows_g)
    rows = [[n, l, c] for n, ks in targets for l, c in facet(n, ks, [], "basisOfRecord", f"basis {n}")]
    files["basis_by_group.csv"] = write_csv("basis_by_group.csv", ["group", "basis_of_record", "records"], rows)
    rows = []
    for n, ks in targets:
        for kind, extra in [("all records", []), ("human observations", [("basisOfRecord", "HUMAN_OBSERVATION")])]:
            for l, c in facet(n, ks, [("year", f"1950,{y1}")] + extra, "year", f"year {n} {kind}", 200):
                rows.append([n, kind, l, c])
    files["year_by_group.csv"] = write_csv("year_by_group.csv", ["group", "records_type", "year", "records"], rows)
    rows = [[n, l, c] for n, ks in targets for l, c in facet(n, ks, recent, "month", f"month {n}", 12)]
    files["month_by_group.csv"] = write_csv("month_by_group.csv", ["group", "month", "records"], rows)
    rows = [[n, l, c] for n, ks in targets for l, c in facet(n, ks, recent, "stateProvince", f"state {n}", 60)]
    files["state_by_group.csv"] = write_csv("state_by_group.csv", ["group", "state", "records"], rows)
    rows = [[n, l, c] for n, ks in targets
            for l, c in facet(n, ks, recent + [("basisOfRecord", "HUMAN_OBSERVATION")], "datasetKey", f"datasets {n}", 25)]
    files["resource_by_group.csv"] = write_csv("resource_by_group.csv", ["group", "dataset_key", "records"], rows)
    meta = {"source": "GBIF occurrence API", "base_url": GBIF, "base_filters": ["country=AU"],
            "taxon_keys": keys, "groups": list(keys)}
    return meta, files


# ----------------------------------------------------------------------------- packaging
def summarise(meta, files, args, started):
    y0, y1 = args.years
    lines = [f"Wildlife data download for FIT3179 DV2, {dt.datetime.now().isoformat(timespec='seconds')}",
             f"Source: {meta.get('source')}", f"Years for recent tables: {y0}-{y1}",
             f"Queries sent: {STATS['queries']}  (answered from cache: {STATS['cached']})",
             f"Failures: {len(STATS['failures'])}", ""]
    for name, n in files.items():
        lines.append(f"{name:<24} {n:>7} rows")
    for name in ["groups.csv", "month_by_group.csv"]:
        p = OUT / name
        if p.exists():
            lines += ["", f"--- first lines of {name} ---"] + p.read_text(encoding="utf-8").splitlines()[:15]
    if STATS["failures"]:
        lines += ["", "--- failures ---"] + STATS["failures"][:40]
    (OUT / "SUMMARY.txt").write_text("\n".join(lines), encoding="utf-8")
    manifest = dict(meta, generated_at=dt.datetime.now().isoformat(timespec="seconds"),
                    years=[y0, y1], python=sys.version.split()[0], files=files,
                    failures=STATS["failures"], minutes=round((time.time() - started) / 60, 1),
                    queries=QUERY_LOG)
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.glob("*.csv")) + [OUT / "manifest.json", OUT / "SUMMARY.txt"]:
            z.write(p, arcname=f"ala/{p.name}")
        if LOG_PATH.exists():
            z.write(LOG_PATH, arcname="download_log.txt")
    size_kb = ZIP_PATH.stat().st_size / 1024
    log(f"Done. Upload this file to Claude: {ZIP_PATH}  ({size_kb:,.0f} KB)")


def connection_test(args):
    log("Connection test")
    ok = False
    try:
        n, _ = ala_search([], fresh=True, label="test ALA")
        log(f"  ALA OK: {n:,} records reachable")
        ok = True
    except RuntimeError as e:
        log(f"  ALA FAILED: {e}")
    try:
        d = get_json(GBIF + "/occurrence/search?country=AU&limit=0", fresh=True)
        log(f"  GBIF OK: {d.get('count', 0):,} records about Australia")
        ok = True
    except RuntimeError as e:
        log(f"  GBIF FAILED: {e}")
    log("Test passed: run the script again without --test." if ok else
        "Both sources failed: check your internet connection, VPN or firewall, then try again.")


def main():
    global SSL_CONTEXT
    ap = argparse.ArgumentParser(description="Download wildlife record counts for Australia (ALA, GBIF fallback).")
    ap.add_argument("--test", action="store_true", help="quick connection test only")
    ap.add_argument("--fresh", action="store_true", help="ignore cached answers")
    ap.add_argument("--years", default="2016-2025", help="recent period, e.g. 2016-2025")
    ap.add_argument("--source", choices=["auto", "ala", "gbif"], default="auto")
    ap.add_argument("--insecure", action="store_true", help="skip SSL certificate checks (only if needed)")
    args = ap.parse_args()
    y0, y1 = (int(x) for x in args.years.split("-"))
    args.years = (y0, y1)
    if args.insecure:
        SSL_CONTEXT = ssl._create_unverified_context()
    if sys.version_info < (3, 8):
        print("Python 3.8 or newer is needed. Download it from https://www.python.org/downloads/")
        sys.exit(1)
    LOG_PATH.write_text("", encoding="utf-8")
    log(f"Project folder: {ROOT}")
    if args.test:
        connection_test(args)
        return
    started = time.time()
    meta, files = None, None
    if args.source in ("auto", "ala"):
        try:
            meta, files = run_ala(args)
        except Exception as e:
            log(f"ALA download stopped: {e}")
            if args.source == "ala":
                raise
    if meta is None:
        meta, files = run_gbif(args)
    summarise(meta, files, args, started)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Run the script again to resume: answers already received are cached.")
