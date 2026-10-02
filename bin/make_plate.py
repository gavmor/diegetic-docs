#!/usr/bin/env python3
"""Bake an aged-paper @page plate PNG (single background-image layer).

The plate carries everything the page background needs — tonal patches,
grain, stains, vignette, crease — because WeasyPrint silently drops
multiple background layers on @page. See references/print-css.md.

Usage:
    make_plate.py [--format portrait|landscape] [--dpi 200] [--seed 7]
                  [--stains 6] [--no-crease] [--out paper-plate.png]
"""
import argparse
import math
import random
from PIL import Image, ImageDraw, ImageFilter

BASE = (233, 222, 198)
PATCH = (228, 214, 186)
DARK = (150, 120, 80)
STAIN = (120, 84, 40)
CREASE = (110, 88, 55)


def make_plate(w, h, seed, stains, crease):
    random.seed(seed)
    base = Image.new("RGB", (w, h), BASE)

    # large soft tonal patches
    patch = Image.new("L", (w // 4, h // 4))
    dpx = patch.load()
    for y in range(patch.size[1]):
        for x in range(patch.size[0]):
            dpx[x, y] = 128 + int(
                28 * math.sin(x * 0.11 + y * 0.05) * math.cos(y * 0.09 - x * 0.03))
    patch = patch.resize((w, h), Image.BILINEAR)
    base = Image.composite(Image.new("RGB", (w, h), PATCH),
                           base, patch.point(lambda v: (v - 100) * 4))

    # fine grain
    noise = Image.effect_noise((w, h), 14).convert("L")
    base = Image.blend(base, Image.merge("RGB", (noise, noise, noise)), 0.05)

    # coffee-ring stains
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rd = ImageDraw.Draw(layer)
    for _ in range(stains):
        cx, cy = random.randint(0, w), random.randint(0, h)
        r = random.randint(90, 260)
        for rr, a in ((r, 10), (r - 6, 14), (r - 12, 8)):
            rd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                       outline=STAIN + (a,), width=random.randint(4, 10))
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    base = Image.alpha_composite(base.convert("RGBA"), layer).convert("RGB")

    # edge vignette
    vig = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vig)
    for inset, alpha in ((0, 60), (18, 34), (40, 18)):
        vd.rectangle([inset, inset, w - inset, h - inset],
                     outline=alpha, width=22)
    vig = vig.filter(ImageFilter.GaussianBlur(30))
    base = Image.composite(Image.new("RGB", (w, h), DARK),
                           base, vig.point(lambda v: v * 2))

    # handling crease
    if crease:
        d = ImageDraw.Draw(base, "RGBA")
        if w >= h:  # landscape: vertical crease
            fx = int(w * 0.62)
            for off, a in ((-2, 26), (0, 40), (3, 18)):
                d.line([fx + off, 0, fx + off, h],
                       fill=CREASE + (a,), width=2)
        else:       # portrait: horizontal crease, upper third
            fy = int(h * 0.36)
            for off, a in ((-2, 26), (0, 40), (3, 18)):
                d.line([0, fy + off, w, fy + off],
                       fill=CREASE + (a,), width=2)
    return base


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--format", choices=["portrait", "landscape"],
                   default="portrait")
    p.add_argument("--dpi", type=int, default=200)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--stains", type=int, default=6)
    p.add_argument("--no-crease", action="store_true")
    p.add_argument("--out", default=None)
    a = p.parse_args()

    if a.format == "portrait":
        w, h = int(8.5 * a.dpi), int(11 * a.dpi)
    else:
        w, h = int(11 * a.dpi), int(8.5 * a.dpi)
    out = a.out or f"paper-plate-{a.format}.png"
    import os as _os
    _os.makedirs(_os.path.dirname(_os.path.abspath(out)), exist_ok=True)
    make_plate(w, h, a.seed, a.stains, not a.no_crease).save(out)
    print(f"wrote {out} ({w}x{h})")


if __name__ == "__main__":
    main()
