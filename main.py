#!/usr/bin/env python3
"""THE WORLD TODAY - Thursday 26 November 2026.

Pure-stdlib program: draws a 1024x1024 newspaper front page summing up
26 November 2026 in one PNG image, written to /output/entry.png.
No network, no files read, deterministic output (same bytes every run).
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024
OUT = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output", "entry.png")

# ---------------------------------------------------------------- palette
PAPER = bytes((247, 242, 230))
INK = bytes((22, 22, 20))
RED = bytes((176, 30, 36))
BLUE = bytes((26, 58, 92))
GREY = bytes((112, 110, 102))
LIGHT = bytes((226, 219, 200))
SKY = bytes((176, 213, 233))
DARK = bytes((16, 20, 30))
WHITE = bytes((255, 255, 255))
YELLOW = bytes((240, 196, 60))
GREEN = bytes((38, 132, 66))
ORANGE = bytes((224, 122, 42))

# ---------------------------------------------------------------- canvas
pix = bytearray(PAPER * (W * H))


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        pix[i:i + 3] = c


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = c * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        pix[i:i + (x1 - x0) * 3] = row


def hline(x, y, w, c, t=1):
    fill_rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    fill_rect(x, y, t, h, c)


def rect_border(x, y, w, h, c, t=1):
    hline(x, y, w, c, t)
    hline(x, y + h - t, w, c, t)
    vline(x, y, h, c, t)
    vline(x + w - t, y, h, c, t)


def line(x0, y0, x1, y1, c):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        set_px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def filled_circle(cx, cy, r, c):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)


def filled_ellipse(cx, cy, rx, ry, c):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        dx = int(rx * math.sqrt(max(0.0, t)))
        fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, c)


def circle_outline(cx, cy, r, c):
    for a in range(360):
        t = math.radians(a)
        set_px(cx + int(r * math.cos(t)), cy + int(r * math.sin(t)), c)


def filled_triangle(x0, y0, x1, y1, x2, y2, c):
    ymin = min(y0, y1, y2)
    ymax = max(y0, y1, y2)
    for y in range(ymin, ymax + 1):
        xs = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2), (x2, y2, x0, y0)):
            if ay == by:
                continue
            if (y >= min(ay, by)) and (y < max(ay, by)):
                xs.append(ax + (bx - ax) * (y - ay) / (by - ay))
        if len(xs) >= 2:
            xa, xb = int(min(xs)), int(max(xs))
            fill_rect(xa, y, xb - xa + 1, 1, c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '1' = ink.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    'q': ("00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10001", "01111"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    '=': ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '~': ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    '^': ("00100", "01010", "10001", "00000", "00000", "00000", "00000"),
    '`': ("01000", "00100", "00000", "00000", "00000", "00000", "00000"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    '\\': ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    '{': ("00110", "01000", "01000", "11100", "01000", "01000", "00110"),
    '}': ("01100", "00010", "00010", "00111", "00010", "00010", "01100"),
    '\u2022': ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
}


def char_w(scale):
    return 6 * scale


def text_w(s, scale):
    return len(s) * char_w(scale) - scale


def draw_glyph(x, y, ch, scale, color, bold=False):
    g = FONT.get(ch)
    if g is None:
        return
    for r in range(7):
        row = g[r]
        for col in range(5):
            if row[col] == '1':
                fill_rect(x + col * scale, y + r * scale, scale, scale, color)
                if bold:
                    fill_rect(x + col * scale + 1, y + r * scale, scale, scale, color)


def draw_text(x, y, s, scale, color, bold=False):
    for ch in s:
        draw_glyph(x, y, ch, scale, color, bold)
        x += char_w(scale)
    return x


def draw_text_centered(cx, y, s, scale, color, bold=False):
    draw_text(cx - text_w(s, scale) // 2, y, s, scale, color, bold)


def wrap(s, scale, max_w):
    lines = []
    cur = ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_w(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(x, y, s, scale, max_w, color, line_h, bold=False):
    lines = wrap(s, scale, max_w)
    for ln in lines:
        draw_text(x, y, ln, scale, color, bold)
        y += line_h
    return y, len(lines)


# ---------------------------------------------------------------- PNG writer
def _chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += pix[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ---------------------------------------------------------------- illustrations
def draw_globe(cx, cy, r):
    filled_circle(cx, cy, r, bytes((120, 170, 205)))
    filled_ellipse(cx - 6, cy - 4, 7, 5, bytes((74, 140, 82)))
    filled_ellipse(cx + 5, cy + 6, 6, 4, bytes((74, 140, 82)))
    filled_ellipse(cx + 7, cy - 8, 4, 3, bytes((74, 140, 82)))
    circle_outline(cx, cy, r, BLUE)
    vline(cx - r // 2, cy - r + 2, 2 * r - 4, bytes((200, 225, 240)))
    vline(cx + r // 2, cy - r + 2, 2 * r - 4, bytes((200, 225, 240)))


def draw_parade(x0, y0, w, h):
    fill_rect(x0, y0, w, h, SKY)
    # sun
    filled_circle(x0 + w - 52, y0 + 26, 15, YELLOW)
    filled_circle(x0 + w - 52, y0 + 26, 10, bytes((248, 220, 110)))
    # clouds
    filled_ellipse(x0 + 120, y0 + 18, 34, 8, WHITE)
    filled_ellipse(x0 + 140, y0 + 14, 24, 7, WHITE)
    filled_ellipse(x0 + 330, y0 + 30, 28, 7, WHITE)
    # skyline
    base = y0 + h - 34
    heights = [58, 84, 66, 96, 72, 88, 60, 78, 92, 64, 70, 80]
    for i, bh in enumerate(heights):
        bx = x0 + 6 + i * 44
        bw = 40
        fill_rect(bx, base - bh, bw, bh, bytes((52, 74, 102)))
        for wy in range(base - bh + 8, base - 6, 14):
            for wx in range(bx + 6, bx + bw - 4, 10):
                fill_rect(wx, wy, 5, 7, bytes((240, 214, 120)))
    # street
    fill_rect(x0, base, w, 18, bytes((96, 96, 92)))
    # balloons with strings
    balloons = [
        (x0 + 92, y0 + 52, 34, 24, RED),
        (x0 + 258, y0 + 38, 30, 22, BLUE),
        (x0 + 424, y0 + 56, 36, 24, ORANGE),
    ]
    for (bx, by, rx, ry, col) in balloons:
        filled_ellipse(bx, by, rx, ry, col)
        filled_ellipse(bx - rx // 3, by - ry // 3, rx // 3, ry // 3,
                       bytes((255, 255, 255)))
        line(bx, by + ry, bx - 6, base, INK)
        line(bx, by + ry, bx + 8, base, INK)
    # turkey head on the orange balloon
    filled_circle(x0 + 424 + 30, y0 + 56 - 14, 7, bytes((190, 90, 30)))
    filled_triangle(x0 + 424 + 36, y0 + 56 - 15, x0 + 424 + 44, y0 + 56 - 12,
                    x0 + 424 + 36, y0 + 56 - 9, YELLOW)
    # confetti (deterministic pattern)
    conf = [RED, YELLOW, BLUE, bytes((46, 160, 90))]
    for i in range(70):
        cx = x0 + 8 + (i * 53) % (w - 16)
        cy = y0 + 6 + (i * 29) % 62
        fill_rect(cx, cy, 3, 3, conf[i % 4])
    # crowd along the street
    for i in range(46):
        cx = x0 + 10 + i * 11
        filled_circle(cx, base + 6, 3, INK)
        fill_rect(cx - 3, base + 9, 6, 7, bytes((40, 40, 44)))
    # caption band
    fill_rect(x0, y0 + h - 16, w, 16, DARK)
    draw_text(x0 + 8, y0 + h - 12, "THE 100TH MACY'S THANKSGIVING DAY PARADE, NEW YORK",
              1, WHITE)


def draw_asteroid(x, y, w, h):
    fill_rect(x, y, w, h, DARK)
    for i in range(26):
        sx = x + 6 + (i * 47) % (w - 12)
        sy = y + 3 + (i * 23) % (h - 6)
        fill_rect(sx, sy, 2, 2, WHITE)
    # asteroid Dimorphos
    ax, ay, ar = x + 62, y + h // 2, 15
    filled_circle(ax, ay, ar, bytes((150, 148, 142)))
    filled_circle(ax - 5, ay - 4, 4, bytes((110, 108, 102)))
    filled_circle(ax + 6, ay + 5, 3, bytes((110, 108, 102)))
    filled_circle(ax + 3, ay - 8, 2, bytes((110, 108, 102)))
    # trajectory
    for i in range(0, 90, 8):
        fill_rect(x + 130 + i, y + h // 2 - 6 - i // 6, 4, 2, YELLOW)
    # Hera spacecraft
    sx, sy = x + 232, y + 8
    fill_rect(sx, sy + 3, 18, 9, WHITE)
    fill_rect(sx - 16, sy + 5, 14, 5, bytes((60, 110, 190)))
    fill_rect(sx + 20, sy + 5, 14, 5, bytes((60, 110, 190)))
    line(sx + 9, sy + 3, sx + 14, sy - 4, WHITE)
    filled_circle(sx + 14, sy - 5, 2, YELLOW)


def draw_football(x, y, w, h):
    fill_rect(x, y, w, h, GREEN)
    for i in range(6):
        if i % 2 == 0:
            fill_rect(x + i * (w // 6), y, w // 6, h, bytes((46, 150, 74)))
    # floodlight beams (narrow, from the top corners)
    filled_triangle(x + 6, y, x + 52, y + h, x + 6, y + h,
                    bytes((240, 230, 160)))
    filled_triangle(x + w - 6, y, x + w - 52, y + h, x + w - 6, y + h,
                    bytes((240, 230, 160)))
    # pitch lines
    hline(x, y + h // 2, w, WHITE)
    circle_outline(x + w // 2, y + h // 2, 12, WHITE)
    rect_border(x + 4, y + 4, w - 8, h - 8, WHITE)
    # ball
    filled_circle(x + w - 46, y + h // 2, 10, WHITE)
    filled_circle(x + w - 46, y + h // 2, 3, INK)
    filled_circle(x + w - 52, y + h // 2 - 5, 2, INK)
    filled_circle(x + w - 40, y + h // 2 + 5, 2, INK)


# ---------------------------------------------------------------- content
# (kicker, headline, summary, illustration or None)
COL1 = [
    ("UKRAINE WAR", "RUSSIA'S WAR DEAD NEAR HALF A MILLION",
     "Leaked Russian mortality data analysed by the BBC put the death toll at 490,334 soldiers in Ukraine.", None),
    ("UKRAINE", "SEVEN KILLED AS RUSSIA STRIKES UKRAINE",
     "Overnight drone strikes hit six regions; Kyiv said it struck three Russian refineries and an airbase.", None),
    ("RUSSIA", "UKRAINE HITS FIVE JETS AT AIRBASE",
     "Kyiv said its forces struck Savasleyka airfield overnight, hitting five Russian aircraft.", None),
    ("POLAND", "POLAND PLANS NO-FLY ZONE ON BORDER",
     "Warsaw plans a no-fly zone on its Ukraine border by early 2027 and seeks a NATO role in interceptions.", None),
    ("CHINA", "SHANGHAI CHIEF FALLS IN GRAFT PROBE",
     "Chen Jining, the Communist Party chief of Shanghai and a Politburo member, is under investigation.", None),
    ("NORTH KOREA", "NORTH KOREA ORDERS SWISS OFFICE SHUT",
     "Pyongyang told Switzerland to close its newly opened diplomatic office in the North Korean capital.", None),
    ("SPACE", "PAKISTAN'S FIRST ASTRONAUT FLIES WITH CHINA",
     "Muhammad Zeeshan Ali will join China's Shenzhou-24 mission to the Tiangong space station.", None),
    ("BANGLADESH", "HASINA SEEKS RETURN TO DHAKA ON DEC 16",
     "Former Bangladesh PM Sheikh Hasina asked Dhaka to arrange her return from India on 16 December.", None),
    ("BANGLADESH", "BANGLADESH RAISES GARMENT PAY BY 36%",
     "Dhaka lifted the minimum monthly wage for entry-level garment workers by more than a third.", None),
    ("SOUTH ASIA", "INDIA GIVES NEPAL RS 15,000 CRORE AID",
     "PM Modi announced a development package for Nepal after talks with PM Balendra Shah in Delhi.", None),
]

COL2 = [
    ("EUROPE", "EU COURT ORDERS CAGE-BAN TIMELINE",
     "The EU court told the Commission to set a date to end caged farming for animals across the bloc.", None),
    ("EUROPE", "3.7 MILLION EUROPEAN JOBS AT RISK",
     "Industry warns millions of jobs are threatened as energy costs and competition squeeze factories.", None),
    ("SPACE", "HERA TO SHOW ASTEROID STRUCK BY NASA",
     "Close-up images of Dimorphos, the asteroid hit to test Earth's defences, are to be revealed today.", "asteroid"),
    ("CULTURE", "DURAN DURAN GUITARIST ANDY TAYLOR DIES",
     "The original guitarist of the 1980s pop band died aged 65 after a long battle with prostate cancer.", None),
    ("UNITED NATIONS", "UN DOUBTS SACKING OF GAZA AID WORKERS",
     "A UN tribunal ruled nine Gaza aid workers were sacked in 2024 on almost entirely unproven claims.", None),
    ("MIDDLE EAST", "ISRAELI STRIKE KILLS HAMAS OFFICIAL",
     "An Israeli strike killed a Hamas official as tensions rise along the Gaza ceasefire line.", None),
    ("SAUDI ARABIA", "INDIA CONDEMNS ATTACK ON RIYADH TOWER",
     "Delhi condemned an attack on a Riyadh tower after two Indians were injured in the incident.", None),
    ("EGYPT", "AT LEAST 30 DEAD IN EGYPT HIGHWAY FIRE",
     "A vehicle carrying petroleum products overturned and caught fire on a ring road in Greater Cairo.", None),
    ("NORWAY", "NORWAY COURT VOIDS DISPUTED OIL LICENCES",
     "The supreme court ruled climate-disputed oil licences invalid in a landmark climate case.", None),
    ("INDIA", "INDIA MARKS CONSTITUTION DAY",
     "India marked Samvidhan Divas; IITs will add 6,000 seats in robotics, AI and space technology.", None),
]

COL3 = [
    ("TRADE", "US READIES NEW TARIFF PLAN",
     "Washington is preparing to unveil a plan for new tariffs on global trading partners, reports say.", None),
    ("USA", "TOP COURT TO RULE ON ASSAULT-WEAPON BANS",
     "The US Supreme Court will hear arguments on 2 Dec on whether states may ban AR-15 style rifles.", None),
    ("MEDIA", "BBC APPEALS AGAINST TRUMP $10BN SUIT",
     "The BBC lodged an urgent appeal against President Trump's $10bn defamation lawsuit.", None),
    ("COLOMBIA", "COLOMBIA FREES 20 SUPERMARKET HOSTAGES",
     "Police stormed a supermarket and freed 20 people held hostage for 17 hours in a Colombian city.", None),
    ("SPORT", "PSG HELD AS BARCA AND LIVERPOOL WIN",
     "Roma ended PSG's perfect Champions League record; Liverpool won 3-0 and Barcelona 4-1.", "football"),
    ("BUSINESS", "FLIPKART CHIEF TO STEP DOWN IN DECEMBER",
     "Flipkart CEO Kalyan Krishnamurthy will leave the post in December, the company said.", None),
    ("AFRICA", "KENYA BEATS EBOLA; DRC TOLL PASSES 5,300",
     "Kenya discharged its last Ebola patient as the death toll in DR Congo rose past 5,300.", None),
    ("GHANA", "GHANA UNVEILS HERITAGE BANKNOTES",
     "Ghana launched a Heritage Series of banknotes honouring Nkrumah, Kofi Annan and Makola traders.", None),
    ("SOUTH AFRICA", "SOUTH AFRICA BARS ANTI-MIGRANT RALLIES",
     "Police barred anti-migrant rallies as protesters gathered outside a court in South Africa.", None),
    ("NIGERIA", "NIGERIA STARTS BUILDING NAVAL SHIPS",
     "Nigeria began building naval ships at home to cut its dependence on foreign suppliers.", None),
]

BRIEFS = [
    "IPL 2027 auction draws 1,220 players",
    "Sooryavanshi smashes 204 off 53 balls vs UAE",
    "Gukesh faces Sindarov in world chess title match",
    "Wolbachia mosquitoes cut Brazil infections 68%",
    "Puigdemont to return to Spain on 12 December",
]

LEAD_HEADLINE = "AMERICA GIVES THANKS: 100TH MACY'S PARADE"
LEAD_SUMMARY = ("The 100th Macy's Thanksgiving Day Parade marched through New York "
                 "as 81.5 million Americans travelled for the holiday. Markets closed; "
                 "the NFL served up its traditional tripleheader.")
LEAD_EXTRA = "Bears-Lions, Eagles-Cowboys, Chiefs-Bills in the NFL tripleheader."


# ---------------------------------------------------------------- layout
def draw_story(x, y, w, kicker, headline, summary, art, bottom):
    if art == "asteroid":
        draw_asteroid(x, y, w, 40)
        y += 46
    elif art == "football":
        draw_football(x, y, w, 40)
        y += 46
    # kicker line: region left, date right
    draw_text(x, y, kicker, 1, RED, bold=True)
    draw_text(x + w - text_w("26 NOV", 1), y, "26 NOV", 1, GREY)
    y += 9
    y, _ = draw_wrapped(x, y, headline, 2, w, INK, 15, bold=True)
    y += 1
    y, _ = draw_wrapped(x, y, summary, 1, w, INK, 8)
    y += 3
    hline(x, y, w, LIGHT)
    return y + 5


def build():
    rect_border(6, 6, W - 12, H - 12, INK, 2)

    # ---- masthead
    draw_globe(56, 30, 20)
    draw_text_centered(W // 2, 10, "THE WORLD TODAY", 5, INK, bold=True)
    hline(24, 52, W - 48, INK)
    draw_text(24, 58, "THURSDAY, 26 NOVEMBER 2026", 2, INK, bold=True)
    right = "36 STORIES FROM AROUND THE WORLD"
    draw_text(W - 24 - text_w(right, 2), 58, right, 2, RED, bold=True)
    hline(24, 78, W - 48, INK, 2)
    hline(24, 82, W - 48, INK)

    # ---- hero: parade illustration + lead story
    draw_parade(24, 88, 532, 152)
    rect_border(24, 88, 532, 152, INK)
    lx = 572
    draw_text(lx, 92, "LEAD STORY - UNITED STATES", 1, RED, bold=True)
    y, _ = draw_wrapped(lx, 106, LEAD_HEADLINE, 3, 428, INK, 22, bold=True)
    y += 4
    y, _ = draw_wrapped(lx, y, LEAD_SUMMARY, 1, 428, INK, 10)
    y += 6
    draw_text(lx, y, LEAD_EXTRA, 1, INK)
    y += 12
    draw_text(lx, y, "NEW YORK - 26 NOVEMBER 2026", 1, GREY, bold=True)

    # ---- story grid
    cols = [COL1, COL2, COL3]
    col_x = [24, 354, 684]
    col_w = 314
    tops = []
    for cx, stories in zip(col_x, cols):
        y = 248
        for (kicker, headline, summary, art) in stories:
            y = draw_story(cx, y, col_w, kicker, headline, summary, art, 948)
        tops.append(y)
    grid_bottom = max(tops)

    # ---- footer: briefs + credit line
    fy = 952
    hline(24, fy, W - 48, INK, 2)
    fy += 8
    briefs = "  \u2022  ".join(BRIEFS)
    fy, nlines = draw_wrapped(24, fy, "IN BRIEF:  " + briefs, 1, W - 48, INK, 10)
    fy += 4
    draw_text_centered(
        W // 2, fy,
        "THE WORLD TODAY - THURSDAY 26 NOVEMBER 2026 - ALL STORIES REPORTED ON 26 NOVEMBER 2026",
        1, GREY)
    return grid_bottom


def main():
    grid_bottom = build()
    size = write_png(OUT)
    print("wrote %s (%d bytes), grid bottom y=%d" % (OUT, size, grid_bottom))


if __name__ == "__main__":
    main()
