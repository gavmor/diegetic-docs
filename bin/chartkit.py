"""Shared drawing kit for diegetic planning charts.

Plates, fonts, and primitives (dashed lines, hatch rects, milestone
diamonds, seal/stamp header, footer). Imported by bin/gantt.py and
bin/stepchart.py — not run directly.
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_plate  # noqa: E402

INK = (38, 34, 28)
FAINT = (122, 108, 84)
RULE = (90, 80, 62)
RED = (140, 28, 28)
PAPER_LABEL = (240, 232, 210)
HATCH_FILL = (214, 202, 172)
HATCH_LINE = (120, 105, 78)

DPI = 300
W, H = 11 * DPI, int(8.5 * DPI)  # 3300 x 2550 landscape


def default_fonts_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    cand = os.path.join(here, "..", "examples", "minimal-order",
                        "assets", "fonts")
    return os.path.normpath(cand)


class Fonts:
    def __init__(self, fonts_dir):
        def f(name, size):
            return ImageFont.truetype(os.path.join(fonts_dir, name), size)
        self.se_title = f("special-elite.ttf", 66)
        self.cp_title = f("courier-prime-regular.ttf", 40)
        self.cp_sub = f("courier-prime-bold.ttf", 34)
        self.cp_sub2 = f("courier-prime-regular.ttf", 30)
        self.cp_row = f("courier-prime-bold.ttf", 34)
        self.cp_rowsub = f("courier-prime-regular.ttf", 30)
        self.cp_axis = f("courier-prime-regular.ttf", 30)
        self.cp_axis_b = f("courier-prime-bold.ttf", 28)
        self.cp_bar = f("courier-prime-bold.ttf", 30)
        self.cp_bar_s = f("courier-prime-regular.ttf", 28)
        self.cp_thin = f("courier-prime-italic.ttf", 26)
        self.cp_legend = f("courier-prime-regular.ttf", 30)
        self.cp_mile = f("courier-prime-bold.ttf", 40)
        self.cp_note = f("courier-prime-regular.ttf", 28)
        self.cp_note_b = f("courier-prime-bold.ttf", 28)
        self.cp_note_b2 = f("courier-prime-bold.ttf", 30)
        self.cp_note_i = f("courier-prime-italic.ttf", 28)
        self.cp_foot = f("courier-prime-regular.ttf", 28)
        self.cp_stamp = f("courier-prime-bold.ttf", 62)


def new_canvas(fonts_dir, seed=56):
    base = make_plate.make_plate(W, H, seed, 6, True)
    return base, ImageDraw.Draw(base, "RGBA"), Fonts(fonts_dir)


def dashed_line(d, x0, y0, x1, y1, fill, width=3, dash=18, gap=12):
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    s = 0
    while s < length:
        e = min(s + dash, length)
        d.line([x0 + ux * s, y0 + uy * s, x0 + ux * e, y0 + uy * e],
               fill=fill, width=width)
        s += dash + gap


def hatch_rect(base, x0, y0, x1, y1, fill=HATCH_FILL, hatch=HATCH_LINE,
               border=INK):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([x0, y0, x1, y1], fill=fill + (255,))
    step = 26
    x = x0 - (y1 - y0)
    while x < x1:
        ld.line([x, y1, x + (y1 - y0), y0], fill=hatch + (255,), width=5)
        x += step
    mask = Image.new("L", base.size, 0)
    ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], fill=255)
    base.paste(Image.alpha_composite(Image.new("RGBA", base.size, (0, 0, 0, 0)),
                                     layer), (0, 0), mask)
    ImageDraw.Draw(base).rectangle([x0, y0, x1, y1], outline=border, width=4)


def diamond(d, cx, cy, r, fill):
    d.polygon([cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy], fill=fill)


def t2x(x0, x1, t, tmax):
    return x0 + (x1 - x0) * t / tmax


def header(base, d, F, title, subtitle, sub2, seal_path=None,
           stamp="RESTRICTED"):
    if seal_path and os.path.isfile(seal_path):
        seal = Image.open(seal_path).convert("RGBA").resize((200, 200))
        base.paste(seal, (150, 120), seal)
    d.line([130, 360, W - 130, 360], fill=INK, width=6)
    d.line([130, 372, W - 130, 372], fill=INK, width=2)
    d.text((W / 2, 150), "WARDEN ARMY OF CAOIVA · TINE LOGISTICS DEPOT",
           font=F.cp_title, fill=INK, anchor="ma")
    d.text((W / 2, 205), title, font=F.se_title, fill=INK, anchor="ma")
    d.text((W / 2, 285), subtitle, font=F.cp_sub, fill=INK, anchor="ma")
    d.text((W / 2, 330), sub2, font=F.cp_sub2, fill=FAINT, anchor="ma")
    if stamp:
        st = Image.new("RGBA", (560, 150), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rectangle([6, 6, 554, 144], outline=RED + (200,), width=8)
        sd.rectangle([22, 22, 538, 128], outline=RED + (200,), width=3)
        sd.text((280, 75), stamp, font=F.cp_stamp, fill=RED + (200,),
                anchor="mm")
        st = st.rotate(-9, expand=True, resample=Image.BICUBIC)
        base.paste(st, (W - 130 - st.size[0], 96), st)


def footer(base, d, F, text):
    d.text((130, H - 110), text, font=F.cp_foot, fill=FAINT, anchor="la")


def time_axis(d, F, x0, x1, top, bottom, tmax, tick, major, xlabel):
    for t in range(0, tmax + 1, tick):
        x = t2x(x0, x1, t, tmax)
        is_major = t % major == 0
        d.line([x, top, x, bottom],
               fill=RULE if is_major else (170, 158, 130),
               width=3 if is_major else 2)
        d.text((x, bottom + 26), f"T+{t}", font=F.cp_axis, fill=INK,
               anchor="ma")
    d.text(((x0 + x1) / 2, bottom + 78), xlabel, font=F.cp_axis_b,
           fill=FAINT, anchor="ma")


def vlines_draw(d, F, x0, x1, top, bottom, tmax, vlines):
    for v in vlines or []:
        x = t2x(x0, x1, v["t"], tmax)
        dashed_line(d, x, top - 10, x, bottom, RED, width=4, dash=22, gap=14)
        d.text((x, top - 44), v.get("label", ""), font=F.cp_mile,
               fill=RED, anchor="mb")
