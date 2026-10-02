# Chart toolkit — JSON-driven planning charts

Charts are rendered directly with PIL by `bin/gantt.py` and
`bin/stepchart.py`, driven by JSON specs. No matplotlib: full control over
the period look (paper plate, typewriter labels, ink bars, rubber-stamp
accents), and no fighting a plotting library's default aesthetic.

```bash
./bin/gantt.py --spec examples/charts/production-timetable.json \
    --out timetable.png
./bin/stepchart.py --spec examples/charts/power-plan.json \
    --out power.png
```

Shared primitives live in `bin/chartkit.py`: plate baking, font loading,
dashed lines, hatch rects (clipped via mask), milestone diamonds, the
seal/stamp header block, margin footer, and the time-axis helpers. Both
renderers import it; do not duplicate the helpers.

## Gantt spec (`gantt.py`)

```json
{
  "title": "PRODUCTION TIMETABLE", "subtitle": "...", "sub2": "...",
  "footer": "...", "seal": "path-or-null", "stamp": "RESTRICTED",
  "tmax": 120, "tick": 10, "major": 30, "xlabel": "MINUTES",
  "rows": [
    {"name": "REFINERY", "sub": "Tine",
     "bars": [
       {"a": 0, "b": 53, "label": "REFINED MATERIALS ×80 — 53 MIN"},
       {"a": 0, "b": 5, "label": "580 B.M. FIRST", "thin": true},
       {"a": 5, "b": 112, "label": "LIT · ~107 MIN", "hatch": true}
     ],
     "milestones": [{"t": 53, "label": "REFINED DONE", "above": true}]}
  ],
  "vlines": [{"t": 111, "label": "MUSTER"}]
}
```

Bar kinds: solid ink (default), `"thin"` (small bar under the row's main
bar, italic caption), `"hatch"` (hatched — plant-lit). Labels sit inside
wide bars, right of narrow ones. Milestones are red diamonds labeled above
(`"above": false` for below). `vlines` are red dashed terminal lines. The
legend lays itself out dynamically from measured label widths, and the
"plant lit" entry appears only when a hatch bar exists.

## Step-chart spec (`stepchart.py`)

```json
{
  "title": "POWER PLAN", "subtitle": "...", "sub2": "...", "footer": "...",
  "seal": null, "stamp": "RESTRICTED",
  "tmax": 120, "tick": 10, "xlabel": "MINUTES",
  "ymax": 14, "ytick": 2, "ylabel": "MW",
  "capacity": [{"mw": 5, "label": "ONE PLANT — 5 MW"}],
  "steps": [
    {"t0": 0, "t1": 5, "mw": 0},
    {"t0": 5, "t1": 26, "mw": 2, "label": "MATERIALS\nFACTORY"}
  ],
  "annotations": [
    {"t": 52, "mw": 5, "dy": 44, "text": "5 MW ON A 5 MW PLANT — NO MARGIN",
     "color": "red", "italic": true}
  ],
  "callouts": [{"text": "NOTE — NEVER RUN ALL FOUR WORKS AT ONCE ..."}],
  "vlines": [{"t": 111, "label": "MUSTER"}]
}
```

Steps draw as a filled step line with 7px ink risers. A step `"label"`
(`\n` for line breaks) sits above the segment midpoint, or at `"t"` when
given. Annotations pin styled text above/below (`"dy"`) a `(t, mw)` point.
Callouts stack as red bold lines under the axis. Capacity lines are dashed
with right-hand labels.

## Data-grounding rule

Every bar's endpoints come from stated figures in the source order. A
duration the order does not give is **not** a bar — it is a milestone
diamond (an event) or it is omitted. Never invent end times to fill the
chart; a staff officer's chart with a guessed bar is worse than an honest
gap.
