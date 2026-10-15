#!/usr/bin/env python3
"""
Convert Paris trees GeoJSON to compact JSON for the static map app.

Usage:
  python3 scripts/compact-trees.py <input.geojson> [output]

  output defaults to public/trees.json

Output format: {"t": [[lat, lon, common_name, genus, species, address, height_m, circ_cm, remarkable], ...]}
  Index 0: lat (float, 6 dp)
  Index 1: lon (float, 6 dp)
  Index 2: common_name (str or null)
  Index 3: genus (str or null)
  Index 4: species (str or null)
  Index 5: address (str or null)
  Index 6: height_m (float or null)
  Index 7: circumference_cm (int or null)
  Index 8: remarkable (1 or 0)
"""
import json, sys, os

src = sys.argv[1] if len(sys.argv) > 1 else None
dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), '..', 'public', 'trees.json')

if not src:
    print(__doc__)
    sys.exit(1)

print(f"Reading {src}...")
with open(src, encoding='utf-8') as f:
    data = json.load(f)

features = data.get('features') or []
print(f"Parsed {len(features)} features")

out = []
skipped = 0
for feat in features:
    props = feat.get('properties') or {}
    geom  = feat.get('geometry') or {}
    if geom.get('type') != 'Point':
        skipped += 1
        continue
    coords = geom.get('coordinates') or []
    if len(coords) < 2:
        skipped += 1
        continue

    lon, lat = coords[0], coords[1]

    rv = props.get('remarquable')
    remarkable = 1 if rv in (True, 'OUI', 'oui', '1', 1) else 0

    try:   h = float(props['hauteurenm']) if props.get('hauteurenm') else None
    except: h = None

    try:   c = int(props['circonferenceencm']) if props.get('circonferenceencm') else None
    except: c = None

    out.append([
        round(float(lat), 6),
        round(float(lon), 6),
        props.get('libellefrancais') or None,
        props.get('genre') or None,
        props.get('espece') or None,
        props.get('adresse') or None,
        h,
        c,
        remarkable
    ])

dst = os.path.normpath(dst)
with open(dst, 'w', encoding='utf-8') as f:
    json.dump({'t': out}, f, separators=(',', ':'), ensure_ascii=False)

size_mb = os.path.getsize(dst) / 1_000_000
print(f"Written {len(out)} trees ({skipped} skipped) → {dst} ({size_mb:.1f} MB)")
