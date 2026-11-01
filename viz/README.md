# GMAPS runway monitor (viz)

Real KSFO geometry from OpenStreetMap (runways, taxiways, holding positions), fictional traffic, animated on a
dark "tower display" with the radio transcript → parsed record → clearance state → conflict alert pipeline shown live.

```
python3 viz/fetch_airport_osm.py KSFO viz/ksfo.geojson --bbox 37.595,-122.415,37.645,-122.345
python3 viz/build_scenario.py viz/ksfo.geojson viz/scenario_sfo_sim1.json --runway 28L
cd viz && python3 -m http.server 8080      # then open http://localhost:8080/
```
Query params: `?scenario=other.json&geo=other.geojson`. Variants: *unresolved* (RESCUE7 crosses in front of the lander)
and *hold-short issued* (GND issues hold short at t=34 s, conflict clears). The page needs internet once for the
MapLibre script and the label fonts (unpkg / openmaptiles); vendor them into `viz/` for an offline demo.

Attribution: © OpenStreetMap contributors (ODbL). FAA airport diagrams are public domain and were used only to
cross-check runway/taxiway names.
