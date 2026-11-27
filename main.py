#!/usr/bin/env python3
"""THE WORLD TODAY -- Thursday 26 November 2026.

A newspaper front-page poster summing up the world's news of
26 November 2026 in one deterministic PNG image.

Pure Python 3 standard library only: no network, no files read at
runtime. Text comes from a small 5x7 bitmap font defined below,
illustrations are drawn from basic shapes, and the PNG bytes are
written by hand with zlib and struct. Running it twice produces
byte-identical output.

Usage:
    python3 main.py            # writes /output/entry.png
    python3 main.py out.png    # or pass an output path
    OUTPUT_PATH=out.png python3 main.py
"""

import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (20, 20, 20)
RED = (176, 32, 32)
BLUE = (31, 58, 110)
DARKBLUE = (16, 38, 74)
SKY = (168, 205, 232)
SEA = (24, 68, 110)
SEALIGHT = (52, 110, 158)
ORANGE = (224, 110, 30)
GOLD = (212, 160, 40)
GREY = (110, 110, 108)
LIGHTGREY = (200, 198, 190)
DARKGREY = (70, 70, 68)
WHITE = (255, 255, 255)
CREAM = (232, 222, 200)
GREEN = (34, 110, 60)
NIGHT = (24, 30, 52)
DUSK = (214, 128, 64)

# ------------------------------------------------------------------- font
# 5x7 bitmap font, one row per string, '1' = ink. Uppercase, digits and
# the punctuation the page needs. Every headline and caption on the page
# is set in this font.
_GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "01100", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
}

# bitmask per row: bit 4 is the leftmost pixel
FONT = {}
for _ch, _rows in _GLYPHS.items():
    _bits = []
    for _r in _rows:
        _v = 0
        for _i, _c in enumerate(_r):
            if _c == "1":
                _v |= 1 << (4 - _i)
        _bits.append(_v)
    FONT[_ch] = tuple(_bits)


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px per char, 1 px gap)."""
    return len(text) * 6 * scale


# ------------------------------------------------------------------ canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, color):
        self.rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.rect(x, y, 1, h, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        """Filled circle."""
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for dy in range(-ry, ry + 1):
            t = 1.0 - (dy * dy) / float(ry * ry)
            dx = int(rx * (t ** 0.5)) if t > 0 else 0
            self.hline(cx - dx, cy + dy, 2 * dx + 1, color)

    def triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Filled triangle via horizontal scanlines."""
        pts = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = pts
        if ay == cy:
            return

        def edge_x(y, p, q):
            if q[1] == p[1]:
                return p[0]
            return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])

        for y in range(ay, cy + 1):
            if y < by:
                xa = edge_x(y, (ax, ay), (bx, by))
                xb = edge_x(y, (ax, ay), (cx, cy))
            else:
                xa = edge_x(y, (bx, by), (cx, cy))
                xb = edge_x(y, (ax, ay), (cx, cy))
            lo, hi = int(min(xa, xb)), int(max(xa, xb))
            self.hline(lo, y, hi - lo + 1, color)

    def text(self, x, y, s, scale, color):
        """Draw uppercase text; unknown chars render as space."""
        cx = x
        for ch in s.upper():
            rows = FONT.get(ch, FONT[" "])
            for r, bits in enumerate(rows):
                for c in range(5):
                    if bits & (1 << (4 - c)):
                        self.rect(cx + c * scale, y + r * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, y, s, scale, color, x0=0, x1=None):
        if x1 is None:
            x1 = self.w
        w = text_width(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, color)

    def wrap(self, text, max_chars):
        """Greedy word wrap, returns a list of lines."""
        words = text.split()
        lines, cur = [], ""
        for wd in words:
            if cur and len(cur) + 1 + len(wd) > max_chars:
                lines.append(cur)
                cur = wd
            else:
                cur = (cur + " " + wd).strip()
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, w, text, scale, color, max_lines=None,
             line_gap=4):
        """Wrapped paragraph; returns the y just below the last line."""
        max_chars = max(1, w // (6 * scale))
        lines = self.wrap(text, max_chars)
        if max_lines is not None:
            lines = lines[:max_lines]
        lh = 7 * scale + line_gap
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, scale, color)
        return y + len(lines) * lh


# ---------------------------------------------------------------- png out
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ------------------------------------------------------------------ scenes
def _bands(cv, x, y, w, h, colors):
    """Horizontal sky bands, top colour first."""
    n = len(colors)
    for i, col in enumerate(colors):
        y0 = y + i * h // n
        y1 = y + (i + 1) * h // n
        cv.rect(x, y0, w, y1 - y0, col)


def _smoke(cv, x, y, r, color, light):
    """A little cluster of smoke puffs rising from (x, y)."""
    cv.disc(x, y, r, color)
    cv.disc(x - r, y + r // 2, r * 3 // 4, color)
    cv.disc(x + r, y + r // 2, r * 3 // 4, color)
    cv.disc(x - r // 2, y - r, r * 2 // 3, light)
    cv.disc(x + r // 2, y - r * 5 // 4, r // 2, light)


def _burst(cv, cx, cy, r, core, mid, outer):
    """Explosion burst: spiked star with a hot core."""
    cv.disc(cx, cy, r, outer)
    for k in range(8):
        ang = k * 3.14159 / 4.0
        import math
        dx = int(math.cos(ang) * r * 13 // 10)
        dy = int(math.sin(ang) * r * 13 // 10)
        cv.triangle(cx, cy, cx + dx, cy + dy,
                    cx + int(math.cos(ang + 0.35) * r * 3 // 5),
                    cy + int(math.sin(ang + 0.35) * r * 3 // 5), mid)
    cv.disc(cx, cy, r * 2 // 3, mid)
    cv.disc(cx, cy, r // 3, core)


def scene_hormuz(cv, x, y, w, h):
    """Lead scene: oil tankers on fire in the Strait of Hormuz."""
    _bands(cv, x, y, w, h * 42 // 100,
           [(250, 214, 150), (238, 186, 120), SKY])
    cv.disc(x + w * 82 // 100, y + h * 16 // 100, h * 9 // 100, GOLD)
    sea_y = y + h * 42 // 100
    cv.rect(x, sea_y, w, h - h * 42 // 100, SEA)
    cv.rect(x, sea_y, w, 3, SEALIGHT)
    # waves
    for i in range(6):
        wx = x + (i * w) // 6 + w // 24
        wy = sea_y + h * (58 + (i % 3) * 12) // 100
        cv.hline(wx, wy, w // 12, SEALIGHT)
        cv.hline(wx + w // 24, wy + 4, w // 18, SEALIGHT)
    # sea mine, floating, spiked
    mx, my, mr = x + w * 12 // 100, sea_y + h * 22 // 100, h * 7 // 100
    cv.disc(mx, my, mr, INK)
    for k in range(8):
        import math
        ang = k * 3.14159 / 4.0
        cv.line(mx, my, mx + int(math.cos(ang) * mr * 14 // 10),
                my + int(math.sin(ang) * mr * 14 // 10), INK)
    cv.disc(mx, my, mr, (40, 40, 40))
    # tanker hull, left
    hx, hy = x + w * 8 // 100, sea_y + h * 30 // 100
    hw, hh = w * 52 // 100, h * 16 // 100
    cv.rect(hx, hy, hw, hh, (18, 18, 18))
    cv.rect(hx, hy, hw, hh // 4, (150, 40, 36))
    cv.rect(hx + hw * 78 // 100, hy - hh * 9 // 10, hw * 12 // 100,
            hh * 9 // 10, (30, 30, 30))
    cv.rect(hx + hw * 80 // 100, hy - hh * 11 // 10, hw * 8 // 100,
            hh // 5, (150, 40, 36))
    # containers on deck
    for i, col in enumerate(((176, 90, 40), (60, 110, 70), (40, 80, 140))):
        cv.rect(hx + hw * (8 + i * 20) // 100, hy - hh // 2,
                hw * 16 // 100, hh // 2, col)
    # second tanker, right, burning
    hx2 = x + w * 62 // 100
    cv.rect(hx2, hy, w * 32 // 100, hh, (18, 18, 18))
    cv.rect(hx2, hy, w * 32 // 100, hh // 4, (150, 40, 36))
    cv.rect(hx2 + w * 24 // 100, hy - hh, w * 6 // 100, hh, (30, 30, 30))
    bx, by = hx2 + w * 10 // 100, hy - hh * 6 // 10
    _burst(cv, bx, by, h * 13 // 100, (255, 226, 120), ORANGE, RED)
    _smoke(cv, bx + w * 4 // 100, by - h * 16 // 100, h * 8 // 100,
           DARKGREY, GREY)
    _smoke(cv, bx - w * 2 // 100, by - h * 24 // 100, h * 6 // 100,
           DARKGREY, GREY)
    # wake
    cv.hline(hx + 6, hy + hh + 6, hw - 12, WHITE)


def scene_kyiv(cv, x, y, w, h):
    """Kyiv at dusk: skyline, missile streak, smoke over the city."""
    _bands(cv, x, y, w, h,
           [(44, 34, 64), (96, 58, 88), DUSK, (232, 164, 96)])
    cv.disc(x + w * 86 // 100, y + h * 18 // 100, h * 8 // 100,
            (250, 220, 160))
    # missile streak
    mx0, my0 = x + w * 12 // 100, y + h * 8 // 100
    mx1, my1 = x + w * 48 // 100, y + h * 52 // 100
    cv.line(mx0, my0, mx1, my1, (255, 240, 200))
    cv.line(mx0 + 2, my0, mx1 + 2, my1, ORANGE)
    cv.disc(mx1, my1, h * 5 // 100, (255, 220, 140))
    # skyline
    base = y + h
    heights = (46, 30, 58, 38, 66, 34, 52, 42, 60, 28)
    bw = w // 10
    for i, hp in enumerate(heights):
        bh = h * hp // 100
        cv.rect(x + i * bw, base - bh, bw - 2, bh, (22, 20, 34))
        # lit windows
        for wy in range(base - bh + 6, base - 6, 12):
            if (i * 7 + wy) % 3 == 0:
                cv.rect(x + i * bw + 3, wy, 3, 4, GOLD)
    # fire glow + smoke at the strike
    fx = x + w * 48 // 100
    cv.disc(fx, base - h * 8 // 100, h * 10 // 100, ORANGE)
    cv.disc(fx, base - h * 6 // 100, h * 6 // 100, (255, 220, 120))
    _smoke(cv, fx + w * 3 // 100, base - h * 30 // 100, h * 9 // 100,
           DARKGREY, GREY)


def scene_cairo(cv, x, y, w, h):
    """Night highway fire outside Cairo: tanker ablaze on the ring road."""
    _bands(cv, x, y, w, h * 52 // 100, [NIGHT, (52, 52, 92), (96, 72, 110)])
    cv.disc(x + w * 84 // 100, y + h * 14 // 100, h * 6 // 100,
            (235, 230, 210))
    # road
    ry = y + h * 52 // 100
    cv.rect(x, ry, w, h - h * 52 // 100, (38, 38, 42))
    cv.rect(x, ry, w, 2, LIGHTGREY)
    for i in range(6):
        cv.rect(x + i * w // 6 + w // 24, ry + h * 24 // 100,
                w // 14, 3, (220, 200, 90))
    # tanker truck, centre
    tx, ty = x + w * 30 // 100, ry + h * 12 // 100
    tw, th = w * 44 // 100, h * 14 // 100
    cv.ellipse(tx + tw // 2, ty + th // 2, tw // 2, th // 2, (150, 150, 155))
    cv.rect(tx + tw, ty, tw // 4, th, (40, 40, 44))
    cv.disc(tx + tw // 5, ty + th + 4, 5, INK)
    cv.disc(tx + tw * 4 // 5, ty + th + 4, 5, INK)
    cv.disc(tx + tw + tw // 8, ty + th + 4, 5, INK)
    # flames above the tanker
    _burst(cv, tx + tw // 2, ty - h * 10 // 100, h * 18 // 100,
           (255, 226, 120), ORANGE, RED)
    _burst(cv, tx + tw // 5, ty - h * 3 // 100, h * 12 // 100,
           (255, 226, 120), ORANGE, RED)
    _smoke(cv, tx + tw // 2, ty - h * 26 // 100, h * 8 // 100,
           DARKGREY, GREY)
    _smoke(cv, tx + tw * 3 // 4, ty - h * 34 // 100, h * 6 // 100,
           DARKGREY, GREY)
    # small cars fleeing
    for i, cx in enumerate((w * 6 // 100, w * 82 // 100)):
        cv.rect(x + cx, ry + h * 30 // 100, w * 10 // 100, h * 7 // 100,
                (200, 60, 50) if i == 0 else (60, 90, 160))
        cv.disc(x + cx + w * 2 // 100, ry + h * 38 // 100, 3, INK)
        cv.disc(x + cx + w * 8 // 100, ry + h * 38 // 100, 3, INK)


def scene_parade(cv, x, y, w, h):
    """Thanksgiving storm: a parade balloon fights grey wind and rain."""
    _bands(cv, x, y, w, h, [(88, 96, 110), (120, 128, 140),
                            (150, 156, 164), (178, 182, 186)])
    # lightning
    lx = x + w * 78 // 100
    cv.line(lx, y + h * 4 // 100, lx - w * 4 // 100, y + h * 22 // 100,
            (255, 240, 150))
    cv.line(lx - w * 4 // 100, y + h * 22 // 100, lx + w * 2 // 100,
            y + h * 24 // 100, (255, 240, 150))
    cv.line(lx + w * 2 // 100, y + h * 24 // 100, lx - w * 3 // 100,
            y + h * 42 // 100, (255, 240, 150))
    # rain
    for i in range(14):
        rx = x + (i * w) // 14 + (i % 3) * 4
        ry = y + (i * 37) % (h * 70 // 100)
        cv.line(rx, ry, rx - 4, ry + 10, (220, 226, 232))
    # big balloon
    bx, by = x + w * 38 // 100, y + h * 38 // 100
    cv.ellipse(bx, by, w * 26 // 100, h * 22 // 100, RED)
    cv.ellipse(bx, by, w * 26 // 100, h * 22 // 100, RED)
    cv.rect(bx - w * 26 // 100, by - 2, w * 52 // 100, 4, (140, 20, 20))
    cv.disc(bx - w * 10 // 100, by - h * 8 // 100, 3, INK)
    cv.disc(bx + w * 10 // 100, by - h * 8 // 100, 3, INK)
    cv.ellipse(bx, by + h * 30 // 100, w * 8 // 100, h * 6 // 100,
               (120, 90, 60))
    cv.line(bx - w * 6 // 100, by + h * 20 // 100, bx - w * 6 // 100,
            by + h * 26 // 100, INK)
    cv.line(bx + w * 6 // 100, by + h * 20 // 100, bx + w * 6 // 100,
            by + h * 26 // 100, INK)
    # street + umbrellas
    sy = y + h * 82 // 100
    cv.rect(x, sy, w, h - h * 82 // 100, (90, 92, 96))
    for i, col in enumerate((BLUE, GOLD, GREEN, RED)):
        ux = x + w * (10 + i * 22) // 100
        cv.ellipse(ux, sy + 4, w * 9 // 100, h * 6 // 100, col)
        cv.line(ux, sy + 4, ux, sy + h * 10 // 100, INK)


# ------------------------------------------------------------------ stories
# Every story below was first reported on Thursday 26 November 2026.
LEAD_HEADLINE = ("TWO TANKERS HIT BY MINES", "IN THE STRAIT OF HORMUZ")
LEAD_DECK = (
    "TWO OIL TANKERS CAUGHT FIRE AFTER STRIKING SEA MINES NORTH OF "
    "OMAN'S KHASAB PORT, IRAN'S REVOLUTIONARY GUARDS SAID. A THIRD "
    "BLAST WAS REPORTED NEAR A TANKER WEST OF DUBAI, AND OIL PRICES "
    "JUMPED AS THE WORLD'S BUSIEST OIL LANE FACED ITS SHARPEST "
    "SCARE IN YEARS."
)
LEAD_ALSO = (
    "HOUTHIS HIT SAUDI REFINERY AT JAZAN",
    "ISRAELI STRIKES KILL NINE IN GAZA",
    "SPAIN HEADS FOR SNAP VOTE ON SUNDAY",
)

FEATURED = (
    ("UKRAINE", scene_kyiv,
     "MISSILES HIT KYIV MALL AS 113 DRONES FLY IN",
     "SEVEN WOUNDED IN THE DESNIANSKYI DISTRICT; AT LEAST THREE "
     "KILLED ACROSS UKRAINE."),
    ("EGYPT", scene_cairo,
     "FUEL TANKER FIRE KILLS 31 ON CAIRO RING ROAD",
     "BLAZE CHARS 27 VEHICLES IN GIZA; THE DRIVER WAS HELD FOR "
     "SPEEDING."),
    ("UNITED STATES", scene_parade,
     "STORM POSTPONES MACY'S PARADE FOR FIRST TIME",
     "THE 100-YEAR PARADE MOVES TO SATURDAY AS A STORM BATTERS "
     "THE EAST."),
)

GRID = (
    ("EUROPE", "SPAIN TO VOTE ON SUNDAY AS SANCHEZ CALLS SNAP ELECTION"),
    ("EUROPE", "DE COS CHOSEN AS NEXT PRESIDENT OF THE ECB"),
    ("EUROPE", "NATO SENDS AWACS TO WATCH POLISH SKIES AFTER MISSILE CRASH"),
    ("EUROPE", "GERMANY ARRESTS TWO OVER PLOT TO ATTACK SYNAGOGUES"),
    ("EUROPE", "UK NET MIGRATION FALLS TO 77,000, LOWEST SINCE 1997"),
    ("EUROPE", "FIVE NATIONS ORDER 430 CV90 FIGHTING VEHICLES"),
    ("EUROPE", "EU PLANS 50 BILLION EURO FUND FOR QUANTUM RACE"),
    ("MIDDLE EAST", "HOUTHIS HIT SAUDI JAZAN REFINERY, ONE WORKER KILLED"),
    ("MIDDLE EAST", "ISRAELI STRIKES KILL NINE IN GAZA ON THIRD NIGHT"),
    ("MIDDLE EAST", "QATAR AND EGYPT LEADERS TALK GAZA CEASEFIRE IN CAIRO"),
    ("MIDDLE EAST", "KUWAIT: TWO KILLED BY IRANIAN DRONE SHRAPNEL"),
    ("MIDDLE EAST", "ISRAEL THREATENS TO DISPLACE A MILLION IN GAZA"),
    ("ASIA", "INDONESIA MINE FLOOD: 13 DEAD, 13 TRAPPED IN BOGOR"),
    ("ASIA", "HUAWEI GUILTY IN US COURT OVER IRAN SANCTIONS"),
    ("ASIA", "KIM VOWS IRREVERSIBLE NUCLEAR BUILDUP"),
    ("ASIA", "BANK OF KOREA LIFTS RATES TO 3.25 PERCENT"),
    ("ASIA", "BANGKOK REFINERY BLAST INJURES NINE"),
    ("ASIA", "HONG KONG WARNS ON ANNIVERSARY OF FIRE THAT KILLED 168"),
    ("ASIA", "INDIA URGES US TO SETTLE TARIFF DISPUTE"),
    ("AMERICAS", "US UNVEILS NEW TARIFFS ON 14 ECONOMIES, CHINA AT 20 PERCENT"),
    ("AMERICAS", "TRUMP DISPUTES GDP REVISED UP TO 4.3 PERCENT"),
    ("AMERICAS", "FCC CLEARS SPACEX PLAN FOR A MILLION SATELLITES"),
    ("AMERICAS", "BEARS BEAT LIONS 39-35; EAGLES RALLY PAST COWBOYS 39-38"),
    ("AMERICAS", "ABREGO GARCIA LANDS IN SPAIN AFTER US CASE DROPPED"),
    ("AMERICAS", "STORM LEAVES 900,000 WITHOUT POWER IN THE US"),
    ("AFRICA", "GUINEA-BISSAU JUNTA DELAYS ELECTIONS TO 2028"),
    ("WORLD", "UKRAINE DRONE STRIKE KILLS FIVE IN ZAPORIZHIA"),
    ("WORLD", "KURDISH PROTESTS AS IRAQ TAKES OIL AND BORDERS"),
)

TICKER = (
    "OIL JUMPS AFTER HORMUZ MINE BLASTS  *  SPAIN VOTES SUNDAY  *  "
    "KYIV MALL HIT, SEVEN WOUNDED",
    "ECB PICKS DE COS  *  THANKSGIVING STORM: 900,000 WITHOUT POWER  *  "
    "MUMBAI REMEMBERS 26/11, 18 YEARS ON",
)

STORY_COUNT = 1 + len(FEATURED) + len(GRID) + 6


# -------------------------------------------------------------------- build
def build():
    cv = Canvas(W, H, PAPER)
    # page frame
    cv.rect(6, 6, W - 12, 2, INK)
    cv.rect(6, H - 8, W - 12, 2, INK)
    cv.rect(6, 6, 2, H - 12, INK)
    cv.rect(W - 8, 6, 2, H - 12, INK)

    # ---- masthead
    cv.text_center(20, "THE WORLD TODAY", 6, INK)
    cv.text_center(70, "THURSDAY 26 NOVEMBER 2026", 2, RED)
    cv.text_center(92,
                   "ONE DAY IN THE WORLD  -  38 STORIES  -  9 REGIONS  -  "
                   "FIRST REPORTED 26 NOV 2026",
                   1, INK)
    cv.rect(24, 108, W - 48, 3, INK)
    cv.rect(24, 113, W - 48, 1, INK)

    # ---- lead headline
    y = 124
    for ln in LEAD_HEADLINE:
        cv.text(24, y, ln, 4, INK)
        y += 34
    cv.rect(24, 196, W - 48, 1, INK)

    # ---- lead scene + caption strip
    sx, sy, sw, sh = 24, 204, 470, 198
    scene_hormuz(cv, sx, sy, sw, sh)
    cv.rect(sx, sy + sh - 20, sw, 20, CREAM)
    cv.rect(sx, sy + sh - 20, sw, 1, INK)
    cv.text(sx + 6, sy + sh - 15,
            "TWO TANKERS BURN AFTER MINE BLASTS IN THE STRAIT OF HORMUZ.",
            1, INK)
    cv.rect(sx, sy, sw, 2, INK)
    cv.rect(sx, sy + sh, sw, 2, INK)
    cv.rect(sx, sy, 2, sh, INK)
    cv.rect(sx + sw - 2, sy, 2, sh, INK)

    # ---- lead deck
    dx = 510
    cv.text(dx, 204, "MIDDLE EAST  -  LEAD STORY", 1, RED)
    cv.para(dx, 218, 490, LEAD_DECK, 2, INK, max_lines=8)
    ay = 366
    cv.text(dx, ay, "ALSO TODAY:", 1, RED)
    for item in LEAD_ALSO:
        ay += 12
        cv.text(dx, ay, "* " + item, 1, INK)

    # ---- featured row: three pictured stories
    cv.rect(24, 414, W - 48, 1, INK)
    cols = 3
    cw = (W - 48 - (cols - 1) * 16) // cols
    for i, (kick, scene, head, deck) in enumerate(FEATURED):
        fx = 24 + i * (cw + 16)
        scene(cv, fx, 422, cw, 92)
        cv.rect(fx, 422, cw, 2, INK)
        cv.rect(fx, 512, cw, 2, INK)
        cv.text(fx, 520, kick, 1, RED)
        cv.para(fx, 532, cw, head, 2, INK, max_lines=2, line_gap=2)
        cv.para(fx, 570, cw, deck, 1, INK, max_lines=2, line_gap=2)

    # ---- grid header
    cv.rect(24, 596, W - 48, 3, INK)
    cv.text(24, 606, "AROUND THE WORLD  -  26 NOVEMBER 2026", 2, INK)
    cv.rect(24, 624, W - 48, 1, INK)

    # ---- grid: 4 columns x 7 rows = 28 stories
    gcols, grows = 4, 7
    gw = (W - 48 - (gcols - 1) * 16) // gcols
    gh = (946 - 630) // grows
    for idx, (region, head) in enumerate(GRID):
        r, c = divmod(idx, gcols)
        gx = 24 + c * (gw + 16)
        gy = 630 + r * gh
        cv.text(gx, gy, region, 1, RED)
        cv.para(gx, gy + 10, gw, head, 1, INK, max_lines=3, line_gap=2)
        if r < grows - 1:
            cv.hline(gx, gy + gh - 6, gw, LIGHTGREY)

    # ---- ticker
    cv.rect(24, 952, W - 48, 50, INK)
    cv.text_center(960, TICKER[0], 1, WHITE)
    cv.text_center(976, TICKER[1], 1, WHITE)

    # ---- footer
    cv.text_center(1010,
                   "THE WORLD TODAY  -  EVERY STORY FIRST REPORTED ON "
                   "26 NOVEMBER 2026",
                   1, GREY)
    return cv


def main():
    if len(sys.argv) > 1:
        out = sys.argv[1]
    elif os.environ.get("OUTPUT_PATH"):
        out = os.environ["OUTPUT_PATH"]
    elif os.environ.get("MAKEFUN_OUTPUT_DIR"):
        out = os.path.join(os.environ["MAKEFUN_OUTPUT_DIR"], "entry.png")
    else:
        out = "/output/entry.png"
    cv = build()
    size = write_png(cv, out)
    print("wrote %s (%d bytes, %d stories)" % (out, size, STORY_COUNT))


if __name__ == "__main__":
    main()
