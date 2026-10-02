#!/usr/bin/env python3
"""Pull live Foxhole war telemetry for stamping diegetic documents.

Queries the community War API (clapfoot/warapi docs) and prints the routing
block fields a telemetry-stamped order needs: war number, war ID, shard,
in-game day (warReport dayOfWar — matches the client's war clock), and the
war start rendered diegetically.

The API does NOT expose the in-game HHMM clock (client-side derived); the
stamp carries the live in-game day and leaves HHMM to the issuer.

Usage:
    war_telemetry.py [--shard live-1|live-2|live-3] [--map DeadLandsHex]
                     [--format stamp|json]

    --format stamp  prints a ready-to-transcribe routing block (default)
    --format json   prints the raw fields as JSON

Single request per endpoint; respect the API's cache headers (see
references/war-telemetry.md) — do not poll in a loop.
"""
import argparse
import datetime
import json
import sys
import urllib.request

SHARDS = {
    "live-1": "https://war-service-live.foxholeservices.com/api",
    "live-2": "https://war-service-live-2.foxholeservices.com/api",
    "live-3": "https://war-service-live-3.foxholeservices.com/api",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "diegetic-docs/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def ordinal(n):
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def telemetry(shard, map_name):
    root = SHARDS[shard]
    war = get(f"{root}/worldconquest/war")
    report = get(f"{root}/worldconquest/warReport/{map_name}")
    start_ms = war["conquestStartTime"]
    start_utc = datetime.datetime.fromtimestamp(start_ms / 1000,
                                               datetime.timezone.utc)
    return {
        "war_number": war["warNumber"],
        "war_id": war["warId"],
        "shard": shard,
        "winner": war["winner"],
        "required_victory_towns": war["requiredVictoryTowns"],
        "war_start_utc": start_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "war_start_hour": start_utc.strftime("%H%M"),
        "ingame_day": report["dayOfWar"],
    }


def stamp(t):
    n, day = t["war_number"], t["ingame_day"]
    lines = [
        f"WAR ................ {n} (Shard: Able / {t['shard']})",
        f"WAR ID ............. {t['war_id']}",
        (f"DATE ............... Day {day} of the {ordinal(n)} War "
         f"(war clock, live telemetry)"),
        f"WAR START .......... Day 1, {t['war_start_hour']} hours",
    ]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--shard", choices=sorted(SHARDS), default="live-1")
    p.add_argument("--map", default="DeadLandsHex")
    p.add_argument("--format", choices=["stamp", "json"], default="stamp")
    a = p.parse_args()
    try:
        t = telemetry(a.shard, a.map)
    except Exception as e:  # noqa: BLE001
        print(f"war telemetry failed: {e}", file=sys.stderr)
        sys.exit(1)
    if a.format == "json":
        print(json.dumps(t, indent=2))
    else:
        print(stamp(t))


if __name__ == "__main__":
    main()
