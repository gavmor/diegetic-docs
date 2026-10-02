#!/usr/bin/env python3
"""Render a diegetic capacity step-chart from a JSON spec.

Usage:
    stepchart.py --spec spec.json --out chart.png [--fonts assets/fonts]
                 [--dpi 300] [--seed 56]

Spec schema (see examples/charts/power-plan.json):
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
    {"t": 52, "mw": 5, "text": "5 MW ON A 5 MW PLANT — NO MARGIN",
     "color": "red", "italic": true}
  ],
  "callouts": [{"text": "NOTE — NEVER RUN ALL FOUR WORKS AT ONCE ..."}],
  "vlines": [{"t": 111, "label": "MUSTER"}]
}
Steps draw as a filled step line; "label" (\\n for lines) sits above the
segment (at its midpoint unless "t" is given). Annotations pin text above a
(t, mw) point. Callouts stack as red bold lines under the axis.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chartkit as K  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spec", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--fonts", default=K.default_fonts_dir())
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--seed", type=int, default=56)
    a = p.parse_args()

    with open(a.spec, encoding="utf-8") as f:
        s = json.load(f)

    W, H = K.W, K.H
    base, d, F = K.new_canvas(a.fonts, a.seed)
    K.header(base, d, F, s["title"], s.get("subtitle", ""),
             s.get("sub2", ""), s.get("seal"), s.get("stamp", "RESTRICTED"))
    K.footer(base, d, F, s.get("footer", ""))

    top, bottom = 520, H - 420
    x0, x1 = 420, W - 420
    tmax, ymax = s.get("tmax", 120), s.get("ymax", 14)

    def y_of(mw):
        return bottom - (bottom - top) * mw / ymax

    # horizontal MW grid
    for mw in range(0, ymax + 1, s.get("ytick", 2)):
        y = y_of(mw)
        major = mw % (s.get("ytick", 2) * 2) == 0
        d.line([x0, y, x1, y],
               fill=K.RULE if major else (170, 158, 130),
               width=3 if major else 2)
        d.text((x0 - 24, y), f"{mw}", font=F.cp_axis, fill=K.INK, anchor="rm")
    d.text((x0 - 24, top - 46), s.get("ylabel", "MW"), font=F.cp_row,
           fill=K.INK, anchor="rm")

    # time grid + labels
    for t in range(0, tmax + 1, s.get("tick", 10)):
        x = K.t2x(x0, x1, t, tmax)
        d.line([x, top, x, bottom], fill=(190, 178, 148), width=2)
        d.text((x, bottom + 26), f"T+{t}", font=F.cp_axis, fill=K.INK,
               anchor="ma")
    d.text(((x0 + x1) / 2, bottom + 78), s.get("xlabel", "MINUTES"),
           font=F.cp_axis_b, fill=K.FAINT, anchor="ma")

    # capacity lines
    for c in s.get("capacity", []):
        y = y_of(c["mw"])
        K.dashed_line(d, x0, y, x1, y, K.FAINT, width=3, dash=20, gap=12)
        d.text((x1 + 16, y), c["label"], font=F.cp_row, fill=K.FAINT,
               anchor="lm")

    # step line + fill
    steps = s["steps"]
    pts = [(x0, bottom)]
    for st in steps:
        pts.append((K.t2x(x0, x1, st["t0"], tmax), y_of(st["mw"])))
        pts.append((K.t2x(x0, x1, st["t1"], tmax), y_of(st["mw"])))
    pts.append((x1, bottom))
    d.polygon(pts, fill=(38, 34, 28, 40))
    prev = None
    for st in steps:
        p0 = (K.t2x(x0, x1, st["t0"], tmax), y_of(st["mw"]))
        p1 = (K.t2x(x0, x1, st["t1"], tmax), y_of(st["mw"]))
        if prev and prev[1] != p0[1]:
            d.line([p0[0], prev[1], p0[0], p0[1]], fill=K.INK, width=7)
        d.line([p0, p1], fill=K.INK, width=7)
        prev = p1
        if st.get("label"):
            tx = K.t2x(x0, x1, st.get("t", (st["t0"] + st["t1"]) / 2), tmax)
            lines = st["label"].split("\n")
            for k, ln in enumerate(lines):
                d.text((tx, y_of(st["mw"]) - 40 - (len(lines) - 1 - k) * 34),
                       ln, font=F.cp_note_b, fill=K.INK, anchor="mb")

    # annotations pinned above (t, mw)
    for an in s.get("annotations", []):
        color = K.RED if an.get("color") == "red" else K.INK
        font = F.cp_note_i if an.get("italic") else F.cp_note_b
        x, y = K.t2x(x0, x1, an["t"], tmax), y_of(an["mw"])
        lines = an["text"].split("\n")
        for k, ln in enumerate(lines):
            d.text((x, y + an.get("dy", 44) + k * 34), ln, font=font,
                   fill=color, anchor="ma")

    # red callout lines under the axis
    cy = H - 280
    for c in s.get("callouts", []):
        d.text((x0 + 40, cy), c["text"], font=F.cp_note_b2, fill=K.RED,
               anchor="la")
        cy += 40

    K.vlines_draw(d, F, x0, x1, top, bottom, tmax, s.get("vlines"))

    if a.dpi != 300:
        from PIL import Image
        base = base.resize((int(W * a.dpi / 300), int(H * a.dpi / 300)),
                           Image.BICUBIC)
    base.save(a.out)
    print(f"wrote {a.out} ({base.size[0]}x{base.size[1]})")


if __name__ == "__main__":
    main()
