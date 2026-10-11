# Omi Buses

A very simple iPhone web app (PWA) for Omi (88): three huge buttons
(Falmouth, Treliske Hospital, Portscatho), each showing the next bus from
Truro Bus Station, the rest of today's buses, and a "Buses back to Truro"
button that flips the direction.

## Data
Official timetables from the Bus Open Data Service (BODS) South West GTFS feed,
which downloads freely with no API key. `tools/build_timetable.py` cuts it down to
`data/timetable.json` (~28 KB): every journey plus the service calendars
(weekday / Saturday / Sunday / school-day / bank-holiday exceptions), so the app
works out the right buses for any date, offline.

| Trip | Routes | Truro stop | Other end |
|---|---|---|---|
| Falmouth | 32, 32A | Stand B (arrive G) | The Moor |
| Treliske Hospital | 32A (Stand G), 87 (Stand J) | | Trelawny Entrance |
| Portscatho | 50 | Stand C | Springfield |

The 494 circular also reaches the hospital but leaves from Lemon Quay, not the
bus station, so it is left out to keep things simple.

## Phases
1. **App + built-in timetable.** DONE 2026-10-11: big buttons, next-bus card,
   countdown, arrival times, day-aware, tomorrow's buses after the last one, offline service worker.
2. **Hosting + weekly auto-refresh.** DONE 2026-10-11: live at
   https://tobiashk-git.github.io/omi-buses/ (repo tobiashk-git/omi-buses). GitHub Pages (HTTPS, so it installs to the
   home screen) and a weekly GitHub Action that runs `build_timetable.py` and commits
   `data/timetable.json` if it changed (`.github/workflows/refresh-timetable.yml`, Mondays 05:00 UTC,
   also runnable by hand from the Actions tab). Optional: a plain-words notice for diversions.
3. **Live times (optional).** BODS live bus locations need an API key, so this needs a
   tiny proxy (e.g. a Cloudflare Worker) to keep the key off the phone.

## Commands
    python tools/build_timetable.py            # download feed + rebuild data
    python tools/build_timetable.py feed.zip   # rebuild from a local copy
    python tools/make_icons.py                 # redraw the icons
Bump `VERSION` in `sw.js` and `APP_VERSION` in `index.html` together on every release (shown in the footer).
