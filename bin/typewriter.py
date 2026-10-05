#!/usr/bin/env python3
"""Inject vintage-manual-typewriter imperfections into HTML text.

A real typewriter never strikes the same letter twice: typebars bend
(baseline shift), the carriage gear slips (tracking jitter), typebars
hit at an angle (rotation), and finger pressure / ribbon dryness varies
(opacity). This script wraps a seeded-random SUBSET of characters in
spans carrying those micro-imperfections.

Only a fraction of characters are wrapped (default 18%): the untouched
majority keeps line-breaking and OpenType contextual alternates intact,
while the sprinkled defects read as mechanical wear. Same --seed gives
byte-identical output; spans are marked data-tw so re-runs are safe.

With --overstrike, text inside <strong>/<b> (or any element carrying a
`data-os` attribute, for headings/table headers/labels that were
font-weight:700) is double-struck: each glyph is emitted twice, the
second copy overlaid at a micro-rotation and reduced opacity — exactly
how a typist faked bold by hitting the key twice. (TT2020 ships no bold
weight, and WeasyPrint neither synthesizes faux bold nor implements
text-shadow, so overstrike is the honest route.)

Usage:
    typewriter.py [--seed 7] [--rate 0.18] [--overstrike] in.html -o out.html

Skips script/style/pre/textarea and existing data-tw spans. Whitespace
is never wrapped (a shifted space is invisible; a rotated one is a lie).
"""
import argparse
import html
import random
import re
import sys
from html.parser import HTMLParser

SKIP = {"script", "style", "pre", "textarea"}


def jitter_span(rng, ch):
    """Build the style for one imperfect character, or None to leave it."""
    parts = ["display:inline-block"]
    # bent typebar: microscopic baseline shift (0.4–1.2pt either way)
    if rng.random() < 0.55:
        dy = round(rng.uniform(0.4, 1.2) * rng.choice((-1, 1)), 2)
        parts.append(f"position:relative;top:{dy}pt")
    # slipping carriage: fractional tracking nudge
    if rng.random() < 0.45:
        dx = round(rng.uniform(0.2, 0.7) * rng.choice((-1, 1)), 2)
        parts.append(f"margin-left:{dx}pt")
    # typebar striking at an angle (heavy letters suffer most;
    # we can't weigh glyphs here, so sprinkle uniformly)
    if rng.random() < 0.35:
        rot = round(rng.uniform(0.3, 0.8) * rng.choice((-1, 1)), 2)
        parts.append(f"transform:rotate({rot}deg)")
    # light finger strike / dry ribbon patch
    if rng.random() < 0.30:
        parts.append(f"opacity:{round(rng.uniform(0.72, 0.95), 2)}")
    if len(parts) == 1:
        return None
    return ("<span data-tw style=\"" + ";".join(parts) + "\">"
            + html.escape(ch) + "</span>")


class Typer(HTMLParser):
    def __init__(self, seed, rate, overstrike):
        super().__init__(convert_charrefs=False)
        self.rng = random.Random(seed)
        self.rate = rate
        self.overstrike = overstrike
        self.out = []
        self.skip_depth = 0
        self.tw_depth = 0
        self.os_stack = []  # tags currently inside an overstrike context

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip_depth += 1
        if tag in ("strong", "b") or any(k == "data-os" for k, _ in attrs):
            self.os_stack.append(tag)
        if any(k == "data-tw" for k, _ in attrs):
            self.tw_depth += 1
        self.out.append(self.get_starttag_text())

    def handle_endtag(self, tag):
        if tag in SKIP and self.skip_depth:
            self.skip_depth -= 1
        if self.os_stack and self.os_stack[-1] == tag:
            self.os_stack.pop()
        if tag == "span" and self.tw_depth:
            self.tw_depth -= 1
        self.out.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.out.append(self.get_starttag_text())

    def _emit(self, ch):
        """One character, with optional overstrike second hit."""
        if (self.overstrike and self.os_stack and ch.strip()
                and not self.tw_depth):
            rot = round(self.rng.uniform(0.2, 0.6)
                        * self.rng.choice((-1, 1)), 2)
            op = round(self.rng.uniform(0.6, 0.8), 2)
            base = jitter_span(self.rng, ch)
            base = base if base else html.escape(ch)
            return (base + "<span data-tw style=\"display:inline-block;"
                    f"margin-left:-1ch;opacity:{op};"
                    f"transform:rotate({rot}deg)\">"
                    + html.escape(ch) + "</span>")
        if ch.strip() and self.rng.random() < self.rate:
            s = jitter_span(self.rng, ch)
            return s if s else html.escape(ch)
        return html.escape(ch)

    def handle_data(self, data):
        if self.skip_depth or self.tw_depth:
            self.out.append(data)
            return
        # Words are the unit of wrapping: any imperfection span inside a
        # word gets a white-space:nowrap guard, because inline-block spans
        # introduce break opportunities and a typewriter never splits a
        # word mid-line. Clean words stay plain text (leaner HTML, calt
        # context untouched).
        parts = []
        for tok in re.finditer(r"\S+|\s+", data):
            w = tok.group(0)
            if not w.strip():
                parts.append(html.escape(w))
                continue
            inner = "".join(self._emit(ch) for ch in w)
            if inner == html.escape(w):
                parts.append(inner)
            else:
                parts.append('<span data-tw style="white-space:nowrap">'
                             + inner + "</span>")
        self.out.append("".join(parts))

    def handle_entityref(self, name):
        self.out.append(f"&{name};")

    def handle_charref(self, name):
        self.out.append(f"&#{name};")

    def handle_comment(self, data):
        self.out.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.out.append(f"<!{decl}>")

    def handle_pi(self, data):
        self.out.append(f"<?{data}>")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("html_in")
    p.add_argument("-o", "--out", default=None)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--rate", type=float, default=0.18,
                   help="fraction of characters to imperfect (0-1)")
    p.add_argument("--overstrike", action="store_true",
                   help="double-strike <strong>/<b> and [data-os] text like "
                        "a real typewriter faking bold")
    a = p.parse_args()
    if not 0 <= a.rate <= 1:
        p.error("--rate must be between 0 and 1")

    with open(a.html_in, encoding="utf-8") as f:
        src = f.read()
    typer = Typer(a.seed, a.rate, a.overstrike)
    typer.feed(src)
    out = "".join(typer.out)
    n = out.count("data-tw")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(out)
    else:
        sys.stdout.write(out)
    print(f"typed {n} characters (seed {a.seed}, rate {a.rate})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
