"""
Prepare compact data files for the DV2 web page.

Sources
  1. FrogID dataset 6.0 (Australian Museum), 2023 records, via TidyTuesday 2025-09-02
  2. Australian Society of Herpetologists official species list (frog_names.csv, same TidyTuesday week)
  3. ABS National, state and territory population, June 2023 (ERP at 30 June 2023)
  4. Natural Earth 1:50m admin-1 boundaries (public domain)

Only light aggregation is done here (counts by state, grid cell, month, hour) so the
page loads quickly; no values are created or altered.
"""
import json, math
import numpy as np
import pandas as pd

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = str(ROOT / "data" / "raw") + "/"   # put frogID_data.csv and frog_names.csv here
OUT = str(ROOT / "data") + "/"

d = pd.read_csv(RAW + "frogID_data.csv")
n = pd.read_csv(RAW + "frog_names.csv")
for c in n.columns:
    n[c] = n[c].astype(str).str.strip()
n = n.drop_duplicates("scientificName")

# ---------- taxonomy join ----------
# Six FrogID names are listed in the ASH list at subspecies level or with a
# corrected Latin ending; map them to the matching ASH entry.
alias = {
    "Limnodynastes dumerilii": "Limnodynastes dumerilii dumerilii",
    "Cyclorana platycephala": "Cyclorana platycephalus",
    "Philoria sphagnicola": "Philoria sphagnicolus",
    "Litoria verreauxii": "Litoria verreauxii verreauxii",
    "Heleioporus australiacus": "Heleioporus australiacus australiacus",
}
d["ashName"] = d.scientificName.replace(alias)
names = n.set_index("scientificName")
d["tribe"] = d.ashName.map(names.tribe)
d["commonName"] = d.ashName.map(names.commonName)
# Lechriodus fletcheri (Fletcher's Frog) is absent from the list; it belongs to Limnodynastidae
d.loc[d.scientificName == "Lechriodus fletcheri", ["tribe", "commonName"]] = ["Limnodynastidae", "Fletcher’s Frog"]
assert d.tribe.notna().all(), d[d.tribe.isna()].scientificName.unique()

group_of = {
    "Pelodryadidae": "Tree frogs",
    "Limnodynastidae": "Ground frogs",
    "Myobatrachidae": "Froglets and toadlets",
    "Asterophryninae": "Narrow-mouthed frogs",
    "Ranidae": "Wood frog",
    "Bufonidae": "Cane toad (introduced)",
}
d["group"] = d.tribe.map(group_of)
d["commonName"] = d.commonName.str.replace("'", "’")

# ---------- local time ----------
tz_of = {
    "New South Wales": "Australia/Sydney", "Australian Capital Territory": "Australia/Sydney",
    "Victoria": "Australia/Melbourne", "Queensland": "Australia/Brisbane",
    "South Australia": "Australia/Adelaide", "Western Australia": "Australia/Perth",
    "Tasmania": "Australia/Hobart", "Northern Territory": "Australia/Darwin",
    "Other Territories": "Australia/Sydney",
}
stamp = pd.to_datetime(d.eventDate + " " + d.eventTime)
local = pd.Series(index=d.index, dtype="datetime64[ns]")
is_utc = d.timezone == "UTC"
for state, tz in tz_of.items():
    m = is_utc & (d.stateProvince == state)
    local[m] = stamp[m].dt.tz_localize("UTC").dt.tz_convert(tz).dt.tz_localize(None)
local[~is_utc] = stamp[~is_utc]          # GMT+hhmm rows are already in local time
d["local"] = local
d["hour"] = d.local.dt.hour
d["ldate"] = d.local.dt.normalize()
d["month"] = d.local.dt.month
d = d[d.local.dt.year == 2023].copy()     # drop a handful of UTC rows that roll back into 2022

state_code = {
    "New South Wales": "NSW", "Victoria": "Vic.", "Queensland": "Qld", "Western Australia": "WA",
    "South Australia": "SA", "Tasmania": "Tas.", "Northern Territory": "NT",
    "Australian Capital Territory": "ACT", "Other Territories": "Other",
}
d["state"] = d.stateProvince.map(state_code)

print("records", len(d), "recordings", d.eventID.nunique(), "people", d.recordedBy.nunique(),
      "species", d.scientificName.nunique(), "dates", d.ldate.min().date(), d.ldate.max().date())

mainland = d[d.state != "Other"].copy()   # remote island territories fall outside the maps

# ---------- 1. state summary (FrogID + ABS) ----------
pop = {  # ABS ERP at 30 June 2023 (National, state and territory population, June 2023)
    "NSW": 8339000, "Vic.": 6812000, "Qld": 5459000, "SA": 1852000,
    "WA": 2879000, "Tas.": 573000, "NT": 252000, "ACT": 467000,
}
s = mainland.groupby(["stateProvince", "state"]).agg(
    records=("occurrenceID", "size"), recordings=("eventID", "nunique"),
    people=("recordedBy", "nunique"), species=("scientificName", "nunique")).reset_index()
s["population"] = s.state.map(pop)
s["records_per_100k"] = (s.records / s.population * 1e5).round(1)
s["people_per_100k"] = (s.people / s.population * 1e5).round(1)
s["pop_share"] = (s.population / s.population.sum() * 100).round(1)
s["record_share"] = (s.records / s.records.sum() * 100).round(1)
s = s.rename(columns={"stateProvince": "name"}).sort_values("records_per_100k", ascending=False)
# label anchor points for the choropleth (ACT and Tas. labels sit offshore with leader lines)
anchor = {"NSW": (146.6, -32.4), "Vic.": (144.0, -36.9), "Qld": (144.6, -23.0), "SA": (135.2, -29.8),
          "WA": (122.4, -26.0), "Tas.": (149.6, -42.4), "NT": (133.4, -19.6), "ACT": (153.6, -36.6)}
s["label_lon"] = s.state.map(lambda k: anchor[k][0]); s["label_lat"] = s.state.map(lambda k: anchor[k][1])
s.to_csv(OUT + "state_summary.csv", index=False)
print(s.to_string())

# ---------- 2. 1-degree grid for the bin map ----------
mainland["gx"] = np.floor(mainland.decimalLongitude).astype(int)
mainland["gy"] = np.floor(mainland.decimalLatitude).astype(int)
g = mainland.groupby(["gx", "gy"]).agg(
    records=("occurrenceID", "size"), recordings=("eventID", "nunique"),
    people=("recordedBy", "nunique"), species=("scientificName", "nunique")).reset_index()
feats = []
for r in g.itertuples():
    x, y = int(r.gx), int(r.gy)
    ring = [[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]
    ring = ring[::-1]  # clockwise exterior ring for d3-geo (spherical winding)
    feats.append({"type": "Feature",
                  "properties": {"cell": f"{abs(y+1)}–{abs(y)}°S, {x}–{x+1}°E", "records": int(r.records),
                                 "recordings": int(r.recordings), "people": int(r.people),
                                 "species": int(r.species)},
                  "geometry": {"type": "Polygon", "coordinates": [ring]}})
json.dump({"type": "FeatureCollection", "features": feats}, open(OUT + "grid_1deg.geojson", "w"),
          separators=(",", ":"))
print("grid cells", len(g), "max records", g.records.max(), "cells >=1", len(g))

# ---------- 3. 2-degree species richness (proportional symbols) ----------
mainland["hx"] = (np.floor(mainland.decimalLongitude / 2) * 2).astype(int)
mainland["hy"] = (np.floor(mainland.decimalLatitude / 2) * 2).astype(int)
def top_species(x):
    vc = x.value_counts()
    return vc.index[0]
h = mainland.groupby(["hx", "hy"]).agg(
    species=("scientificName", "nunique"), records=("occurrenceID", "size"),
    lon=("decimalLongitude", "mean"), lat=("decimalLatitude", "mean"),
    top=("commonName", top_species)).reset_index()
h["species_per_100_records"] = (h.species / h.records * 100).round(1)
h["lon"] = h.lon.round(2); h["lat"] = h.lat.round(2)
h.to_csv(OUT + "richness_2deg.csv", index=False)
print(h.sort_values("species", ascending=False).head(8).to_string())

# ---------- 4. contributors (waffle / unit chart) ----------
per = d.groupby("recordedBy").eventID.nunique()
bins = [0, 1, 5, 20, 100, 10**9]
labels = ["1 recording", "2–5", "6–20", "21–100", "More than 100"]
cls = pd.cut(per, bins=bins, labels=labels)
people = cls.value_counts().reindex(labels)
recs = per.groupby(cls, observed=False).sum().reindex(labels)
def hundred(counts):
    share = counts / counts.sum() * 100
    base = np.floor(share).astype(int)
    rem = (share - base).sort_values(ascending=False)
    for k in rem.index[: 100 - base.sum()]:
        base[k] += 1
    return base
rows = []
for panel, counts in [("Share of people", people), ("Share of recordings", recs)]:
    units = hundred(counts)
    i = 0
    for lab in labels:
        for _ in range(int(units[lab])):
            rows.append({"panel": panel, "unit": i, "col": i % 10, "row": i // 10, "class": lab,
                         "order": labels.index(lab), "count": int(counts[lab]),
                         "pct": round(float(counts[lab] / counts.sum() * 100), 1)})
            i += 1
pd.DataFrame(rows).to_csv(OUT + "contributors_units.csv", index=False)
print(pd.DataFrame({"people": people, "recordings": recs, "pp": (people/people.sum()*100).round(1), "rp": (recs/recs.sum()*100).round(1)}))
top1 = per.sort_values(ascending=False)
k = int(round(len(top1) * 0.01))
print("top 1% people", k, "share recordings", round(top1.head(k).sum() / top1.sum() * 100, 1),
      "max", top1.max(), "median", top1.median())

# ---------- 5. hour of day by season (radial clocks) ----------
season_of = {12: "Summer", 1: "Summer", 2: "Summer", 3: "Autumn", 4: "Autumn", 5: "Autumn",
             6: "Winter", 7: "Winter", 8: "Winter", 9: "Spring", 10: "Spring", 11: "Spring"}
ev = d.drop_duplicates("eventID").copy()
ev["season"] = ev.month.map(season_of)
hs = ev.groupby(["season", "hour"]).size().rename("recordings").reset_index()
hs["share"] = (hs.recordings / hs.groupby("season").recordings.transform("sum") * 100).round(2)
hs.to_csv(OUT + "hour_season.csv", index=False)
night = ev.hour.isin([18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5])
print("share recordings 6pm-6am", round(night.mean() * 100, 1), "7-10pm", round(ev.hour.isin([19,20,21]).mean()*100,1))
print(hs.loc[hs.groupby("season").recordings.idxmax()])

# ---------- 6. daily recordings (calendar heatmap) ----------
dd = ev.groupby("ldate").agg(recordings=("eventID", "size"), people=("recordedBy", "nunique")).reset_index()
recs_day = d.groupby("ldate").size().rename("records")
dd = dd.join(recs_day, on="ldate")
full = pd.DataFrame({"ldate": pd.date_range("2023-01-01", "2023-12-31")})
dd = full.merge(dd, on="ldate", how="left")
dd["date"] = dd.ldate.dt.strftime("%Y-%m-%d")
dd[["date", "recordings", "people", "records"]].to_csv(OUT + "daily.csv", index=False)
print(dd.sort_values("recordings", ascending=False).head(8)[["date", "recordings", "people"]])
ev["dow"] = ev.ldate.dt.dayofweek
print("by weekday", ev.groupby("dow").size().round().tolist())

# ---------- 7. species summary (treemap + dot strip) ----------
sp = d.groupby(["scientificName", "commonName", "group"]).agg(
    records=("occurrenceID", "size"), people=("recordedBy", "nunique"),
    states=("state", lambda x: ", ".join(sorted(set(x))))).reset_index()
sp["share"] = (sp.records / sp.records.sum() * 100).round(2)
sp = sp.sort_values("records", ascending=False)
sp.to_csv(OUT + "species_summary.csv", index=False)
print(sp.head(12).to_string())
print("species with <10 records", (sp.records < 10).sum(), "<=2", (sp.records <= 2).sum(), "single", (sp.records == 1).sum())
print(sp.groupby("group").agg(n=("records", "size"), r=("records", "sum")))

# ---------- 8. ridgeline: monthly profile of the 14 most-recorded native species ----------
top = sp[sp.group != "Cane toad (introduced)"].head(14).scientificName.tolist()
sm = d[d.scientificName.isin(top)].groupby(["scientificName", "commonName", "group", "month"]).size().rename("records").reset_index()
sm = (sm.set_index(["scientificName", "commonName", "group", "month"]).records.unstack("month", fill_value=0)
      .stack(future_stack=True).rename("records").reset_index())
sm["share"] = (sm.records / sm.groupby("scientificName").records.transform("sum") * 100).round(2)
allm = d.groupby("month").size()
all_share = (allm / allm.sum() * 100).round(2)
sm["all_share"] = sm.month.map(all_share)
sm["lift"] = (sm.share / sm.all_share).round(3)          # >1: species is heard more than usual that month
peak = sm.loc[sm.groupby("scientificName").lift.idxmax()].set_index("scientificName").month
sm["peak_month"] = sm.scientificName.map(peak)
codes = {name: i for i, name in enumerate(sorted(top, key=lambda x: (peak[x], x)))}
sm["code"] = sm.scientificName.map(codes)
sm["order"] = sm.code
sm.to_csv(OUT + "species_month.csv", index=False)
print(peak.sort_values())

# ---------- 9. latitude band x month (row-normalised heatmap) ----------
mainland["band"] = (np.floor(mainland.decimalLatitude / 2) * 2).astype(int)
lm = mainland.groupby(["band", "month"]).size().rename("records").reset_index()
lm = (lm.set_index(["band", "month"]).records.unstack("month", fill_value=0).stack(future_stack=True)
      .rename("records").reset_index())
lm["share"] = (lm.records / lm.groupby("band").records.transform("sum") * 100).round(2)
lm["band_total"] = lm.groupby("band").records.transform("sum")
lm["label"] = lm.band.apply(lambda b: f"{abs(b+2)}–{abs(b)}°S")
lm = lm[lm.band_total >= 300]   # drop the two thinly sampled Torres Strait / Cape York tip bands
lm.to_csv(OUT + "lat_month.csv", index=False)
print(lm.pivot(index="label", columns="month", values="share").round(0).to_string())

# ---------- 10. dot map points: top species by 0.1-degree cell and month ----------
pts = mainland[mainland.scientificName.isin(top)].copy()
pts["lon"] = (np.floor(pts.decimalLongitude * 10) / 10 + 0.05).round(2)
pts["lat"] = (np.floor(pts.decimalLatitude * 10) / 10 + 0.05).round(2)
pts["sp"] = pts.scientificName.map(codes)
pp = pts.groupby(["sp", "lon", "lat", "month"]).size().rename("n").reset_index()
pp.to_csv(OUT + "species_points.csv", index=False)
json.dump([{"sp": int(codes[x]), "scientificName": x,
            "commonName": d.loc[d.scientificName == x, "commonName"].iloc[0],
            "group": d.loc[d.scientificName == x, "group"].iloc[0]} for x in sorted(codes, key=codes.get)],
          open(OUT + "species_codes.json", "w"), indent=1, ensure_ascii=False)
print("species point rows", len(pp))

# ---------- 11. cane toad records ----------
ct = mainland[mainland.scientificName == "Rhinella marina"].copy()
ct["lon"] = (np.floor(ct.decimalLongitude * 20) / 20 + 0.025).round(3)
ct["lat"] = (np.floor(ct.decimalLatitude * 20) / 20 + 0.025).round(3)
cc = ct.groupby(["lon", "lat", "state"]).size().rename("n").reset_index()
cc.to_csv(OUT + "canetoad_points.csv", index=False)
print("cane toad", len(ct), ct.state.value_counts().to_dict(), "cells", len(cc),
      "min lat", ct.decimalLatitude.min(), "min lon", ct.decimalLongitude.min())
print("cane toad share of records", round(len(ct) / len(d) * 100, 2), "people", ct.recordedBy.nunique())
# cane toads far from the main range
print(ct[ct.state.isin(["WA", "NSW"])].groupby("state")[["decimalLatitude", "decimalLongitude"]].describe().T)

# headline numbers for the page
head = {"records": int(len(d)), "recordings": int(d.eventID.nunique()), "people": int(d.recordedBy.nunique()),
        "species": int(d.scientificName.nunique()), "first": str(d.ldate.min().date()), "last": str(d.ldate.max().date())}
json.dump(head, open(OUT + "headline.json", "w"), indent=2)
print(head)
