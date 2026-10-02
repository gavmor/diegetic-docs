#!/usr/bin/env python3
"""Render a diegetic Gantt timetable from a JSON spec.

Usage:
    gantt.py --spec spec.json --out chart.png [--fonts assets/fonts]
             [--dpi 300] [--seed 56]

Spec schema (see examples/charts/production-timetable.json):
{
  "title": "PRODUCTION TIMETABLE",
  "subtitle": "...", "sub2": "...", "footer": "...",
  "seal": "path-or-null", "stamp": "RESTRICTED" (or null),
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
Bar kinds: default solid ink; "thin": small bar under the row's main bar;
"hatch": hatched bar (plant-lit). Labels sit inside wide bars, right of
narrow ones. Milestones are red diamonds, labeled above (or below).
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

    # layout is designed at 300dpi; --dpi downscales the finished plate
    W, H = K.W, K.H
    base, d, F = K.new_canvas(a.fonts, a.seed)
    K.header(base, d, F, s["title"], s.get("subtitle", ""),
             s.get("sub2", ""), s.get("seal"), s.get("stamp", "RESTRICTED"))
    K.footer(base, d, F, s.get("footer", ""))

    top, bottom = 470, H - 320
    x0, x1 = 780, W - 170
    tmax = s.get("tmax", 120)
    rows = s["rows"]
    n = len(rows)
    rh = (bottom - top) / n

    K.time_axis(d, F, x0, x1, top, bottom, tmax, s.get("tick", 10),
                s.get("major", 30), s.get("xlabel", "MINUTES"))
    K.vlines_draw(d, F, x0, x1, top, bottom, tmax, s.get("vlines"))

    def yc(i):
        return top + rh * i + rh / 2

    has_hatch = False
    for i, row in enumerate(rows):
        y = yc(i)
        d.text((x0 - 24, y - 12), row["name"], font=F.cp_row, fill=K.INK,
               anchor="ra")
        d.text((x0 - 24, y + 22), row.get("sub", ""), font=F.cp_rowsub,
               fill=K.FAINT, anchor="ra")
        if i < n - 1:
            d.line([x0, top + rh * (i + 1), x1, top + rh * (i + 1)],
                   fill=(190, 178, 148), width=2)

        for b in row.get("bars", []):
            xa, xb = K.t2x(x0, x1, b["a"], tmax), K.t2x(x0, x1, b["b"], tmax)
            label = b.get("label", "")
            if b.get("hatch"):
                has_hatch = True
                K.hatch_rect(base, xa, y - 34, xb, y + 34)
                d.text((xa + 14, y), label, font=F.cp_bar_s, fill=K.INK,
                       anchor="lm")
            elif b.get("thin"):
                d.rectangle([xa, y + 42, xb, y + 66], fill=K.INK)
                d.text(((xa + xb) / 2, y + 96), label, font=F.cp_thin,
                       fill=K.FAINT, anchor="ma")
            else:
                d.rectangle([xa, y - 34, xb, y + 34], fill=K.INK)
                if xb - xa > 340:
                    d.text(((xa + xb) / 2, y), label, font=F.cp_bar,
                           fill=K.PAPER_LABEL, anchor="mm")
                elif label:
                    d.text((xb + 14, y), label, font=F.cp_bar_s,
                           fill=K.INK, anchor="lm")

        for m in row.get("milestones", []):
            x = K.t2x(x0, x1, m["t"], tmax)
            K.diamond(d, x, y, 22, K.RED)
            above = m.get("above", True)
            ly = y - 58 if above else y + 58
            d.text((x, ly), m.get("label", ""), font=F.cp_bar_s,
                   fill=K.RED, anchor="ma")

    # legend — dynamic layout, labels never collide
    lx, ly = x0, H - 175
    x = lx
    items = [("rect", "shop work"), ("diamond", "event / milestone")]
    if has_hatch:
        items.append(("hatch", "plant lit"))
    items.append(("dash", "muster"))
    for kind, label in items:
        if kind == "rect":
            d.rectangle([x, ly - 20, x + 90, ly + 20], fill=K.INK)
            x += 90
        elif kind == "diamond":
            K.diamond(d, x + 16, ly, 16, K.RED)
            x += 36
        elif kind == "hatch":
            K.hatch_rect(base, x, ly - 20, x + 90, ly + 20)
            x += 90
        elif kind == "dash":
            K.dashed_line(d, x, ly, x + 80, ly, K.RED, width=4)
            x += 80
        x += 16
        d.text((x, ly), label, font=F.cp_legend, fill=K.INK, anchor="lm")
        x += F.cp_legend.getbbox(label)[2] + 80

    if a.dpi != 300:
        from PIL import Image
        base = base.resize((int(W * a.dpi / 300), int(H * a.dpi / 300)),
                           Image.BICUBIC)
    base.save(a.out)
    print(f"wrote {a.out} ({base.size[0]}x{base.size[1]})")


if __name__ == "__main__":
    main()
