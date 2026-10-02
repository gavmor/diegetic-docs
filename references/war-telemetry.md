# War telemetry for live-stamped documents

`bin/war_telemetry.py` queries the Foxhole War API (documented at
[clapfoot/warapi](https://github.com/clapfoot/warapi)) and prints the routing
block fields for a telemetry-stamped order. Proven on requisition order
141/TINE/0003.

## Endpoints used

Shard roots (`--shard live-1|live-2|live-3`, default `live-1`):

| Shard  | Root                                              |
|--------|---------------------------------------------------|
| live-1 | `https://war-service-live.foxholeservices.com/api`   |
| live-2 | `https://war-service-live-2.foxholeservices.com/api` |
| live-3 | `https://war-service-live-3.foxholeservices.com/api` |

- `GET /worldconquest/war` → `warNumber`, `warId`, `conquestStartTime`
  (unix ms, UTC), `requiredVictoryTowns`, `winner`. Refreshes ~every 60s.
- `GET /worldconquest/warReport/<map>` → `dayOfWar`. This is the **in-game
  day** and matches the client's war clock ("Day 27, 0627 Hours"). Any live
  map name works (`DeadLandsHex` is the default).

## Field mapping

| Stamp line | Source |
|---|---|
| `WAR` | `warNumber` + shard label |
| `WAR ID` | `warId` verbatim |
| `DATE` | `Day {dayOfWar} of the {N}th War (war clock, live telemetry)` |
| `WAR START` | `Day 1, {HHMM} hours` from `conquestStartTime` (UTC hour) |

## What the API does not give

- **In-game HHMM time-of-day** ("0627 Hours") is not exposed by any
  documented endpoint — the client derives it. The stamp carries the live
  in-game *day*; take HHMM from the issuer's client or omit it.
- Historical wars: the API serves the **current** war only.

## Rate limits

Respect the API's cache headers; the war endpoint refreshes every ~60s and
supports ETags (`If-None-Match` → `304 Not Modified`). One request per stamp
is plenty — never poll in a loop. The script makes exactly two requests.

## Diegetic-dates rule

Telemetry-stamped documents still use in-world dating. The war number, war
ID, and in-game day are already diegetic; render `conquestStartTime` as
"Day 1, HHMM hours", never as a Gregorian calendar date.
