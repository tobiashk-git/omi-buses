"""Build data/timetable.json for Omi Buses from the official BODS GTFS feed.

Usage:
    python tools/build_timetable.py [path-to-south_west-gtfs.zip]

With no argument it downloads the South West feed (about 230 MB) from the
Bus Open Data Service. No API key is needed. Only the handful of Go Cornwall
routes and stops below end up in the output, which is a few KB.
"""
import csv, io, json, os, sys, tempfile, urllib.request, zipfile
from datetime import datetime, timezone

FEED_URL = "https://data.bus-data.dft.gov.uk/timetable/download/gtfs-file/south_west/"
AGENCY_NOC = "TFCN"  # Go Cornwall Bus

# Stops that count as each place, with the label shown in the app.
TRURO = {  # Truro Bus Station stands
    "0800COA15345": "Stand B",
    "0800COA15346": "Stand C",
    "0800COA15350": "Stand G",
    "0800COA15352": "Stand J",
}
PLACES = {
    "falmouth": {
        "name": "Falmouth",
        "lines": ["32", "32A"],
        "stops": {"0800COC30662": "The Moor", "0800COZ06299": "The Moor"},
    },
    "hospital": {
        "name": "Treliske Hospital",
        "lines": ["32A", "87"],
        "stops": {"0800COC04351": "Trelawny Entrance"},
    },
    "portscatho": {
        "name": "Portscatho",
        "lines": ["50"],
        "stops": {"0800COC30859": "Springfield"},
    },
}


def hhmm(t):
    h, m, _ = t.split(":")
    return f"{int(h) % 24:02d}:{m}"


def rows(z, name):
    with z.open(name) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig", newline=""))


def journeys(stops, origin, dest):
    """(dep_index, arr_index) for the shortest origin->dest hop within one trip."""
    best = None
    last_origin = None
    for i, r in enumerate(stops):
        if r["stop_id"] in origin and r.get("pickup_type", "0") != "1":
            last_origin = i
        elif r["stop_id"] in dest and last_origin is not None and r.get("drop_off_type", "0") != "1":
            if best is None or i - last_origin < best[1] - best[0]:
                best = (last_origin, i)
            last_origin = None
    return best


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        path = os.path.join(tempfile.gettempdir(), "omi_buses_south_west.zip")
        print("Downloading", FEED_URL)
        urllib.request.urlretrieve(FEED_URL, path)
    z = zipfile.ZipFile(path)

    agency = next(a["agency_id"] for a in rows(z, "agency.txt") if a["agency_noc"] == AGENCY_NOC)
    wanted = {l for p in PLACES.values() for l in p["lines"]}
    routes = {r["route_id"]: r["route_short_name"] for r in rows(z, "routes.txt")
              if r["agency_id"] == agency and r["route_short_name"] in wanted}
    trips = {t["trip_id"]: t for t in rows(z, "trips.txt") if t["route_id"] in routes}
    stop_times = {}
    for r in rows(z, "stop_times.txt"):
        if r["trip_id"] in trips:
            stop_times.setdefault(r["trip_id"], []).append(r)

    out = {}
    used_services = set()
    for key, place in PLACES.items():
        legs = {"there": set(), "back": set()}
        for tid, t in trips.items():
            line = routes[t["route_id"]]
            if line not in place["lines"]:
                continue
            seq = sorted(stop_times.get(tid, []), key=lambda r: int(r["stop_sequence"]))
            for leg, (a, b) in (("there", (TRURO, place["stops"])), ("back", (place["stops"], TRURO))):
                hop = journeys(seq, a, b)
                if not hop:
                    continue
                dep, arr = seq[hop[0]], seq[hop[1]]
                at = (TRURO if leg == "there" else place["stops"])[dep["stop_id"]]
                legs[leg].add((hhmm(dep["departure_time"]), hhmm(arr["arrival_time"]), line, at, t["service_id"]))
                used_services.add(t["service_id"])
        out[key] = {
            "name": place["name"],
            **{leg: [dict(d=d, a=a, l=l, at=at, s=s) for d, a, l, at, s in sorted(v)] for leg, v in legs.items()},
        }

    services = {}
    for c in rows(z, "calendar.txt"):
        if c["service_id"] in used_services:
            days = "".join(c[d] for d in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"))
            services[c["service_id"]] = dict(days=days, start=c["start_date"], end=c["end_date"], add=[], remove=[])
    for c in rows(z, "calendar_dates.txt"):
        if c["service_id"] in used_services:
            s = services.setdefault(c["service_id"], dict(days="0000000", start="", end="", add=[], remove=[]))
            s["add" if c["exception_type"] == "1" else "remove"].append(c["date"])
    for s in services.values():
        s["add"].sort(); s["remove"].sort()

    feed = next(rows(z, "feed_info.txt"))
    data = dict(
        built=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        feed_version=feed["feed_version"],
        valid_until=feed["feed_end_date"],
        places=out,
        services=services,
    )
    dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "timetable.json")
    try:
        with open(dst, encoding="utf-8") as f:
            old = json.load(f)
        if old.get("places") == out and old.get("services") == services:
            print("Timetable unchanged since", old.get("built"), "- leaving", os.path.normpath(dst), "alone")
            return
    except (OSError, ValueError):
        pass
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    for k, p in out.items():
        print(f"{k:11} there {len(p['there']):3}  back {len(p['back']):3}")
    print("services", len(services), "->", os.path.normpath(dst), os.path.getsize(dst), "bytes")


if __name__ == "__main__":
    main()
