#!/usr/bin/env python3
"""Pull an airport's runways, taxiways and holding positions from OpenStreetMap (Overpass) → GeoJSON.

  python viz/fetch_airport_osm.py KSFO viz/ksfo.geojson
  python viz/fetch_airport_osm.py KSFO viz/ksfo.geojson --bbox 37.595,-122.415,37.645,-122.345
  python viz/fetch_airport_osm.py --from-raw viz/ksfo_overpass_raw.json viz/ksfo.geojson   # offline convert

OSM data © OpenStreetMap contributors, ODbL. Keep the attribution in the viewer.
The FAA airport diagram (public domain) is only a cross-reference for runway/taxiway names;
the geometry drawn comes from OSM.
"""
import argparse, json, sys, time, urllib.parse, urllib.request

MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]


def query_area(icao):
    return (f'[out:json][timeout:120];area["icao"="{icao}"]->.a;'
            '(way["aeroway"="runway"](area.a);way["aeroway"="taxiway"](area.a);'
            'node["aeroway"="holding_position"](area.a););out body geom;')


def query_bbox(bbox):
    return (f'[out:json][timeout:120][bbox:{bbox}];'
            '(way["aeroway"="runway"];way["aeroway"="taxiway"];node["aeroway"="holding_position"];);out body geom;')


def fetch(q):
    last = None
    for url in MIRRORS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                             headers={"User-Agent": "gmaps-hackathon/1.0"})
                with urllib.request.urlopen(req, timeout=150) as r:
                    body = r.read().decode("utf-8")
                d = json.loads(body)
                if d.get("elements"):
                    return d
                last = f"{url}: empty result"
            except Exception as e:
                last = f"{url}: {e!r}"
                time.sleep(3)
    sys.exit(f"all Overpass mirrors failed: {last}")


def to_geojson(d):
    feats = []
    for e in d.get("elements", []):
        tags = e.get("tags", {})
        kind = tags.get("aeroway")
        props = {"osm_id": e["id"], "kind": kind, "ref": tags.get("ref"), "name": tags.get("name"),
                 "width": tags.get("width"), "surface": tags.get("surface")}
        if e["type"] == "node":
            feats.append({"type": "Feature", "properties": props,
                          "geometry": {"type": "Point", "coordinates": [e["lon"], e["lat"]]}})
        elif e["type"] == "way" and e.get("geometry"):
            coords = [[p["lon"], p["lat"]] for p in e["geometry"]]
            if len(coords) < 2:
                continue
            feats.append({"type": "Feature", "properties": props,
                          "geometry": {"type": "LineString", "coordinates": coords}})
    return {"type": "FeatureCollection",
            "attribution": "© OpenStreetMap contributors (ODbL)", "features": feats}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("icao", nargs="?", help="ICAO code, e.g. KSFO")
    ap.add_argument("out")
    ap.add_argument("--bbox", help="south,west,north,east — use when the area lookup times out")
    ap.add_argument("--from-raw", help="convert a saved Overpass JSON instead of fetching")
    args = ap.parse_args()

    if args.from_raw:
        d = json.load(open(args.from_raw))
    else:
        if not args.icao:
            sys.exit("give an ICAO code or --from-raw")
        d = fetch(query_bbox(args.bbox) if args.bbox else query_area(args.icao))
    gj = to_geojson(d)
    json.dump(gj, open(args.out, "w"), separators=(",", ":"))
    kinds = {}
    for f in gj["features"]:
        kinds[f["properties"]["kind"]] = kinds.get(f["properties"]["kind"], 0) + 1
    rws = sorted({f["properties"]["ref"] for f in gj["features"] if f["properties"]["kind"] == "runway" and f["properties"]["ref"]})
    print(f"wrote {args.out}: {kinds}  runways: {rws}")


if __name__ == "__main__":
    main()
