# diegetic-docs

Generate **diegetic in-world documents** — military orders, requisition
forms, staff paperwork — and **planning charts** (Gantt timetables, capacity
step-charts) on aged paper with typewriter typography. For LARP props,
tabletop handouts, and anything that should look typed, stamped, and filed.

Proven on: an 11-page Warden requisition order (Form LQ-7, rev. 2) with a
production Gantt and power-plan chart — all figures traced to the source text.

## Quickstart

```bash
cd examples/minimal-order
../../bin/make_plate.py --out assets/paper-plate.png
../../bin/fetch_fonts.py --out assets/fonts
../../bin/check.py --html order.html
python3 -m weasyprint order.html order.pdf
```

## Layout

- `SKILL.md` — the operational skill (purpose, workflow, tooling, rules).
- `bin/` — `make_plate.py` (aged-paper plate), `fetch_fonts.py`
  (fetch + verify fonts), `check.py` (executable gate),
  `war_telemetry.py` (live Foxhole war telemetry for stamped orders).
- `assets/fonts/` — vendored OFL fonts (Courier Prime, Special Elite).
- `references/` — `print-css.md` (WeasyPrint form patterns + the hard-won
  `@page` background rules), `charts.md` (JSON-driven Gantt / step-chart
  renderers + schemas), `war-telemetry.md` (WarAPI endpoints, field mapping,
  rate limits).
- `assets/fonts/` — vendored OFL fonts (Courier Prime, Special Elite).
- `references/` — `print-css.md` (WeasyPrint form patterns + the hard-won
  `@page` background rules), `charts.md` (PIL chart toolkit + recipes).
- `examples/minimal-order/` — minimal end-to-end order; render it to try
  the pipeline.

## The hard-won rules

1. WeasyPrint for styled prose, never takumi-pdf (italic/state corruption).
2. Exactly one `@page` background-image layer; bake everything into the plate
   PNG and offset it by the negative margins.
3. Verify every TTF is real font data — Google Fonts can serve 404 HTML.
4. Rasterize and look; never trust `pdftotext` at style boundaries.
5. Chart bars come from stated figures; unstated durations are milestones,
   not bars.
