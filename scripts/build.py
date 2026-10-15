#!/usr/bin/env python3
"""
Download Paris trees GeoJSON and generate compact public/trees.json.
Used by Netlify and GitHub Actions at deploy time.

Can also be run locally:
  python3 scripts/build.py
  python3 scripts/build.py /path/to/local.geojson   # skip download
"""
import json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL  = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/les-arbres/exports/geojson"
DST  = os.path.join(ROOT, "public", "trees.json")

local_src = sys.argv[1] if len(sys.argv) > 1 else None

if local_src:
    print(f"Reading {local_src}...")
    with open(local_src, encoding="utf-8") as f:
        data = json.load(f)
else:
    print(f"Downloading Paris trees GeoJSON (~100 MB)...")
    try:
        with urllib.request.urlopen(URL, timeout=300) as resp:
            raw = resp.read()
    except Exception as e:
        sys.exit(f"Download failed: {e}")
    print(f"Downloaded {len(raw) / 1_000_000:.0f} MB. Parsing...")
    data = json.loads(raw)

features = data.get("features") or []
print(f"Parsed {len(features)} features")

out = []
skipped = 0
for feat in features:
    props = feat.get("properties") or {}
    geom  = feat.get("geometry") or {}
    if geom.get("type") != "Point":
        skipped += 1
        continue
    coords = geom.get("coordinates") or []
    if len(coords) < 2:
        skipped += 1
        continue
    lon, lat = coords[0], coords[1]
    rv = props.get("remarquable")
    remarkable = 1 if rv in (True, "OUI", "oui", "1", 1) else 0
    try:   h = float(props["hauteurenm"]) if props.get("hauteurenm") else None
    except: h = None
    try:   c = int(props["circonferenceencm"]) if props.get("circonferenceencm") else None
    except: c = None
    out.append([
        round(float(lat), 6), round(float(lon), 6),
        props.get("libellefrancais") or None,
        props.get("genre") or None,
        props.get("espece") or None,
        props.get("adresse") or None,
        h, c, remarkable
    ])

os.makedirs(os.path.dirname(DST), exist_ok=True)
with open(DST, "w", encoding="utf-8") as f:
    json.dump({"t": out}, f, separators=(",", ":"), ensure_ascii=False)

size_mb = os.path.getsize(DST) / 1_000_000
print(f"Written {len(out)} trees ({skipped} skipped) → {DST} ({size_mb:.1f} MB)")
