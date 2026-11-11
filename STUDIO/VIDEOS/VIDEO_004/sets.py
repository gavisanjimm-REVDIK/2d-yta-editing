"""sets.py - VIDEO_004 "The Day Evil Disappeared". Storybook style, helpers from VIDEO_001.

city_night (midnight, New Year), prison (cell block), office (Marcus's detective office), street (town street,
summer; winter is drawn live on top), park (bench at sunset), desk (newspapers land on it).
"""
from __future__ import annotations

import importlib.util
import math
import random
from functools import lru_cache
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("v001_sets", HERE.parent / "VIDEO_001" / "sets.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

W, H, INK = base.W, base.H, base.INK
P, shape, rect, poly, vgrad, radial, line_w = base.P, base.shape, base.rect, base.poly, base.vgrad, base.radial, base.line_w
smooth_path, oval, snapshot = base.smooth_path, base.oval, base.snapshot


# ================================================================ city at midnight
CLOCK = (540, 640, 110)  # x, y, radius of the clock-tower face


def draw_city(c, w, h):
    vgrad(c, (0, 0, w, h), "#0E1430", "#2A2A55")
    rnd = random.Random(2)
    for _ in range(90):
        c.drawCircle(rnd.uniform(0, w), rnd.uniform(0, 900), rnd.uniform(1.5, 3.5), P("#FFFFFF", rnd.uniform(0.3, 0.9)))
    c.drawCircle(860, 260, 70, P("#F4EED8"))
    c.drawCircle(885, 245, 66, P("#0E1430"))  # crescent moon
    for layer, (col, y0, hmin, hmax) in enumerate((("#2A2E52", 1150, 260, 520), ("#1E2242", 1300, 200, 420))):
        x = -40
        while x < w:
            bw = rnd.randint(120, 200)
            bh = rnd.randint(hmin, hmax)
            shape(c, rect(x, y0 - bh, bw, bh + 900), col, ow=3.5)
            for wy in range(int(y0 - bh + 30), int(y0 + 300), 60):
                for wx in range(x + 18, x + bw - 30, 42):
                    if rnd.random() < 0.35:
                        c.drawRect(skia.Rect.MakeXYWH(wx, wy, 20, 28), P("#FFD27A", 0.85))
            x += bw + rnd.randint(0, 20)
    # clock tower in the middle
    x, y, r = CLOCK
    shape(c, rect(x - 150, y - 160, 300, 1400), "#4A3E5E", shade="#3A3050", sdx=18)
    shape(c, poly([(x - 175, y - 160), (x, y - 420), (x + 175, y - 160)]), "#3A3050")
    shape(c, oval(x, y, r + 22, r + 22), "#C9A24A")
    shape(c, oval(x, y, r, r), "#F4EED8")
    for k in range(12):
        a = k * math.tau / 12
        c.drawLine(x + math.cos(a) * r * 0.8, y + math.sin(a) * r * 0.8, x + math.cos(a) * r * 0.93,
                   y + math.sin(a) * r * 0.93, line_w(6 if k % 3 == 0 else 3))
    # rooftop in the foreground (where we watch from)
    shape(c, poly([(-20, 1650), (w + 20, 1560), (w + 20, h + 20), (-20, h + 20)]), "#3A2E3E", shade="#2E2432", sdy=0)
    c.drawLine(-20, 1650, w + 20, 1560, line_w(8, "#5A4A5E"))


def clock_hands(c, t_midnight, t, scale=1.0):
    """Hands sweep to 12:00 exactly at t_midnight (minute hand ticks the last seconds)."""
    x, y, r = CLOCK
    secs = min(0.0, t - t_midnight)  # <= 0 before midnight
    minute_ang = -math.pi / 2 + (secs / 60.0) * math.tau * 0.5
    hour_ang = -math.pi / 2 + (secs / 3600.0) * math.tau
    c.drawLine(x, y, x + math.cos(hour_ang) * r * 0.5, y + math.sin(hour_ang) * r * 0.5, line_w(12))
    c.drawLine(x, y, x + math.cos(minute_ang) * r * 0.82, y + math.sin(minute_ang) * r * 0.82, line_w(8))
    c.drawCircle(x, y, 12, P(INK))


def firework(c, x, y, t, t0, color, seed):
    u = (t - t0) / 1.6
    if not 0 <= u < 1:
        return
    rnd = random.Random(seed)
    rad = 220 * (1 - (1 - u) ** 3)
    for k in range(22):
        a = k * math.tau / 22 + rnd.uniform(-0.05, 0.05)
        px, py = x + math.cos(a) * rad, y + math.sin(a) * rad + 90 * u * u
        c.drawCircle(px, py, 9 * (1 - u) + 2, P(color, 1 - u))
        c.drawLine(px, py, px - math.cos(a) * 40 * (1 - u), py - math.sin(a) * 40 * (1 - u), line_w(4, color, 0.6 * (1 - u)))
    radial(c, x, y, 380 * (1 - u * 0.5), color, 0.35 * (1 - u), plus=True)


# ================================================================ prison cell block
def draw_prison(c, w, h):
    vgrad(c, (0, 0, w, 1350), "#8A929A", "#6E767E")
    for y in range(0, 1350, 110):
        for x in range(0, w, 220):
            c.drawRect(skia.Rect.MakeXYWH(x + ((y // 110) % 2) * 110, y, 220, 110), line_w(3, INK, 0.3))
    for cx in (60, 600):  # two cells, dark inside
        shape(c, rect(cx, 420, 420, 930), "#3A3E46")
        shape(c, rect(cx + 40, 860, 260, 60, 8), "#6A5A4A")  # bunk
        shape(c, rect(cx - 20, 380, 460, 50, 6), "#5A626A")
    c.drawRect(skia.Rect.MakeXYWH(0, 120, w, 60), P("#5A626A"))
    radial(c, 540, 160, 520, "#F4F0D8", 0.25, plus=True)
    shape(c, poly([(0, 1350), (w, 1350), (w, h), (0, h)]), "#5A6068")
    for k in range(0, w + 300, 180):
        c.drawLine(k, 1350, k - 220, h, line_w(3, INK, 0.35))


def bars(c, x0, open_u):
    """Cell bars: a sliding barred door covering x0..x0+420, slides right by open_u."""
    dx = 380 * open_u
    c.save()
    c.clipRect(skia.Rect(x0 - 20, 380, x0 + 440, 1360))  # bars slide into the wall
    for k in range(9):
        x = x0 + 20 + k * 48 + dx
        c.drawLine(x, 430, x, 1350, line_w(16, INK))
        c.drawLine(x, 430, x, 1350, line_w(10, "#9AA2AA"))
    for y in (600, 1000):
        c.drawLine(x0 + dx, y, x0 + 420 + dx, y, line_w(20, INK))
        c.drawLine(x0 + dx, y, x0 + 420 + dx, y, line_w(12, "#9AA2AA"))
    c.restore()


# ================================================================ Marcus's office
def draw_office(c, w, h):
    vgrad(c, (0, 0, w, 1300), "#5A4636", "#4A3A2C")
    for x in range(0, w, 140):
        c.drawLine(x, 0, x, 1300, line_w(3, INK, 0.25))
    # window with blinds (city day light)
    shape(c, rect(620, 220, 380, 520, 6), "#BCD8EE")
    for k in range(12):
        c.drawLine(620, 240 + k * 42, 1000, 240 + k * 42, line_w(6, "#E8E2D6", 0.8))
    c.drawRect(skia.Rect.MakeXYWH(620, 220, 380, 520), line_w(10, "#3A2A1E"))
    # case board with photos + red string
    shape(c, rect(60, 230, 470, 400, 8), "#B88A5A", shade="#9A6E42", sdx=10)
    pins = [(130, 300), (300, 280), (450, 330), (160, 470), (330, 520), (470, 560)]
    for i, (px, py) in enumerate(pins):
        shape(c, rect(px - 45, py - 30, 90, 70, 4), ["#F4F1EA", "#E8DCC0"][i % 2], ow=3)
        c.drawCircle(px, py - 26, 8, P("#C83A3A"))
    for a, b in ((0, 1), (1, 2), (0, 3), (3, 4), (4, 5), (1, 4)):
        c.drawLine(pins[a][0], pins[a][1] - 26, pins[b][0], pins[b][1] - 26, line_w(3, "#C83A3A"))
    # coat rack (empty hook later), desk with lamp, phone and files
    c.drawLine(560, 820, 560, 1300, line_w(12, "#3A2418"))
    for k in (-1, 1):
        c.drawLine(560, 840, 560 + k * 46, 806, line_w(8, "#3A2418"))
    shape(c, oval(560, 1300, 60, 12), "#3A2418", ow=3)
    shape(c, poly([(0, 1300), (w, 1300), (w, h), (0, h)]), "#6A4A30")
    for k in range(0, w + 300, 170):
        c.drawLine(k, 1300, k - 240, h, line_w(3, INK, 0.4))
    shape(c, rect(80, 1180, 640, 60, 8), "#7A4A2E", shade="#603822", sdy=12, sdx=0)
    shape(c, rect(110, 1240, 60, 330), "#603822")
    shape(c, rect(630, 1240, 60, 330), "#603822")
    shape(c, rect(170, 1110, 170, 70, 6), "#2A2A30", ow=3.5)  # old phone
    shape(c, smooth_path([(170, 1110), (255, 1080), (340, 1110), (300, 1095), (210, 1095)]), "#1A1A20", ow=3)
    for k in range(3):
        shape(c, rect(420 + k * 8, 1152 - k * 14, 200, 30, 4), ["#E8C878", "#D8B868", "#E8D8A0"][k], ow=3)


def box(c, x, y, s=1.0, fill=0.0):
    """Cardboard box (x, y = bottom centre). fill draws the folded coat inside, flaps open."""
    w_, h_ = 300 * s, 210 * s
    shape(c, rect(x - w_ / 2, y - h_, w_, h_, 6), "#C8965A", shade="#A87A42", sdx=14 * s)
    if fill > 0:
        shape(c, rect(x - w_ / 2 + 14 * s, y - h_ - 20 * s * fill, w_ - 28 * s, 40 * s, 10 * s), "#B8894C", ow=3)
    for sx in (-1, 1):  # open flaps
        shape(c, poly([(x + sx * w_ / 2, y - h_), (x + sx * (w_ / 2 + 70 * s), y - h_ - 60 * s),
                       (x + sx * (w_ / 2 - 30 * s), y - h_ - 70 * s), (x, y - h_)]), "#D8A66A", ow=3)
    c.drawLine(x - w_ / 2 + 20 * s, y - h_ * 0.55, x + w_ / 2 - 20 * s, y - h_ * 0.55, line_w(5, "#8A6232", 0.6))


# ================================================================ town street (summer; winter drawn live)
def draw_street(c, w, h):
    vgrad(c, (0, 0, w, 900), "#9ED0EE", "#D8EEF6")
    for cx, cy, r in ((240, 260, 70), (760, 180, 90)):
        for k in range(4):
            c.drawCircle(cx + (k - 1.5) * r * 0.7, cy + (12 if k % 2 else 0), r * 0.6, P("#FFFFFF", 0.9))
    houses = [(-40, 380, "#E8A07A"), (340, 420, "#9AC48A"), (720, 380, "#E8D07A")]
    for i, (x, hh, col) in enumerate(houses):
        y = 1250 - hh
        shape(c, rect(x, y, 380, hh + 10), col, ow=4)
        shape(c, poly([(x - 20, y), (x + 190, y - 170), (x + 400, y)]), "#B5503A")
        # door (wide open: nobody locks anything)
        shape(c, rect(x + 150, 1250 - 230, 100, 230, 4), "#3A2418")
        shape(c, poly([(x + 150, 1250 - 230), (x + 100, 1250 - 250), (x + 100, 1250 + 10), (x + 150, 1250)]), "#7A4A2E")
        for wx in (x + 40, x + 280):
            shape(c, rect(wx, y + 60, 70, 80, 4), "#BCD8EE")
        for k in range(5):  # flower box
            c.drawCircle(x + 50 + k * 14, y + 150, 9, P(["#E8708A", "#F4D24A", "#FFFFFF"][k % 3]))
    shape(c, poly([(0, 1250), (w, 1250), (w, 1420), (0, 1420)]), "#C8C0B0")  # sidewalk
    for k in range(0, w, 120):
        c.drawLine(k, 1250, k, 1420, line_w(3, INK, 0.3))
    shape(c, poly([(0, 1420), (w, 1420), (w, h), (0, h)]), "#8A8A8E")  # road
    for k in range(0, w, 220):
        shape(c, rect(k + 40, 1640, 120, 18, 4), "#F4F1EA", ow=2)
    shape(c, rect(880, 1100, 26, 320), "#3A3A44")  # street lamp
    shape(c, oval(893, 1090, 46, 26), "#F4E6B8")


def snow_cover(c, amount):
    """Winter: snow on roofs, sidewalk and road."""
    if amount <= 0:
        return
    houses = [(-40, 380), (340, 420), (720, 380)]
    for x, hh in houses:
        y = 1250 - hh
        c.drawPath(poly([(x - 24, y + 4), (x + 190, y - 176), (x + 404, y + 4), (x + 380, y + 22), (x + 190, y - 140),
                         (x, y + 22)]), P("#FFFFFF", amount))
    c.drawRect(skia.Rect(0, 1240, W, 1300), P("#FFFFFF", amount))
    c.drawRect(skia.Rect(0, 1420, W, 1480), P("#F4F8FC", amount * 0.9))


# ================================================================ park bench at sunset
def draw_park(c, w, h):
    vgrad(c, (0, 0, w, 1100), "#F4A86A", "#FCE0B0")
    radial(c, 760, 900, 520, "#FFE2A0", 0.55, plus=True)
    c.drawCircle(760, 920, 120, P("#FFE8B8"))
    shape(c, smooth_path([(-40, 1050), (300, 960), (700, 1000), (w + 40, 940), (w + 40, 1200), (-40, 1200)]),
          "#8A9A5A", ow=3.5)
    shape(c, poly([(0, 1150), (w, 1150), (w, h), (0, h)]), "#6E8A44", shade="#5A7438", sdy=0, sdx=0)
    shape(c, smooth_path([(380, h + 20), (520, 1150), (600, 1150), (900, h + 20)]), "#D8C090", ow=3)  # path
    # big tree left
    shape(c, rect(70, 640, 90, 620, 20), "#5A3A22", shade="#46301A", sdx=14)
    for cx, cy, r in ((40, 520, 210), (220, 460, 200), (120, 330, 190), (300, 600, 150)):
        shape(c, oval(cx, cy, r, r * 0.9), "#5E8A3C", shade="#4C7432", sdx=20)
    # lamp post right
    shape(c, rect(930, 760, 22, 520), "#2E2E34")
    shape(c, oval(941, 750, 44, 30), "#F4E6B8")
    # the bench
    for k in range(3):
        shape(c, rect(330, 1180 + k * 34, 460, 26, 6), "#8A5A34", ow=3.5)
    shape(c, rect(330, 1300, 460, 30, 6), "#7A4A2A", ow=3.5)
    for lx in (360, 740):
        shape(c, rect(lx, 1330, 24, 140), "#2E2E34")


BENCH_SEAT_Y = 1310


# ================================================================ desk for the newspaper montage
def draw_desk(c, w, h):
    vgrad(c, (0, 0, w, h), "#5A3A26", "#3A2418")
    for k in range(0, w, 90):
        c.drawLine(k, 0, k + 60, h, line_w(4, "#2E1C12", 0.5))
    shape(c, oval(170, 1640, 120, 120), "#F4F1EA", ow=4)  # coffee cup from above
    shape(c, oval(170, 1640, 90, 90), "#6A3A1E", ow=3)


@lru_cache(maxsize=None)
def img(name):
    fns = {"city": draw_city, "prison": draw_prison, "office": draw_office, "street": draw_street,
           "park": draw_park, "desk": draw_desk}
    if name.endswith("_blur"):
        return snapshot(fns[name[:-5]], blur=16)
    return snapshot(fns[name])
