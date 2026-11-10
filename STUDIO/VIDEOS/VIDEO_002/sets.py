"""sets.py - VIDEO_002 "Death by Pudding" backgrounds (storybook style, shared helpers from VIDEO_001).

THE HIDDEN CLUE lives in the hall window (draw_drive): Marcus's blue car (he really just arrived) has a thin
layer of snow, Cedric's red car is buried under a deep mound (parked for hours). The doormat shows ONE set of
wet footprints (Marcus's). Never zoomed on, never mentioned.
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
smooth_path, oval, snapshot, draw_candles = base.smooth_path, base.oval, base.snapshot, base.draw_candles
draw_kitchen, KITCHEN_WIN, KITCHEN_CANDLES = base.draw_kitchen, base.KITCHEN_WIN, base.KITCHEN_CANDLES


# ================================================================ cars + snow
def car(c, x, y, w, color, snow):
    """Little storybook car, wheels on y. snow 0..1: 0.15 = light dusting, 1 = buried mound."""
    h = w * 0.42
    body = smooth_path([(x - w / 2, y - h * 0.25), (x - w * 0.46, y - h * 0.55), (x - w * 0.25, y - h * 0.62),
                        (x - w * 0.15, y - h), (x + w * 0.2, y - h), (x + w * 0.32, y - h * 0.62),
                        (x + w * 0.48, y - h * 0.55), (x + w / 2, y - h * 0.25), (x + w * 0.4, y - h * 0.12),
                        (x - w * 0.4, y - h * 0.12)])
    shape(c, body, color, ow=3.5)
    shape(c, poly([(x - w * 0.12, y - h * 0.93), (x + w * 0.17, y - h * 0.93), (x + w * 0.26, y - h * 0.62),
                   (x - w * 0.2, y - h * 0.62)]), "#2A3550", ow=3)
    for wx in (-0.3, 0.3):
        shape(c, oval(x + wx * w, y - h * 0.15, w * 0.11, w * 0.11), "#1A1A1E", ow=3)
    shape(c, oval(x - w * 0.47, y - h * 0.4, w * 0.035, w * 0.03), "#FFB04A", ow=2)  # tail light
    if snow < 0.5:  # thin dusting on roof, hood, boot
        th = 6 + 18 * snow
        for pts in ([(x - w * 0.16, y - h - th * 0.3), (x + w * 0.21, y - h - th * 0.3), (x + w * 0.19, y - h + 4),
                     (x - w * 0.14, y - h + 4)],
                    [(x + w * 0.32, y - h * 0.62 - th * 0.3), (x + w * 0.49, y - h * 0.56 - th * 0.3), (x + w * 0.48, y - h * 0.5),
                     (x + w * 0.33, y - h * 0.57)],
                    [(x - w * 0.47, y - h * 0.56 - th * 0.3), (x - w * 0.25, y - h * 0.63 - th * 0.3),
                     (x - w * 0.26, y - h * 0.56), (x - w * 0.46, y - h * 0.5)]):
            shape(c, smooth_path(pts), "#FFFFFF", ow=2.5)
    else:  # buried: big soft mound, only a tail light and a mirror peek out
        mound = smooth_path([(x - w * 0.62, y + 2), (x - w * 0.55, y - h * 0.8), (x - w * 0.2, y - h * 1.35),
                             (x + w * 0.25, y - h * 1.3), (x + w * 0.6, y - h * 0.75), (x + w * 0.64, y + 2)])
        shape(c, mound, "#F4F7FC", shade="#D8E2EE", sdx=14, ow=3.5)
        shape(c, oval(x - w * 0.56, y - h * 0.38, w * 0.03, w * 0.025), color, ow=2)
        shape(c, oval(x + w * 0.4, y - h * 0.86, w * 0.05, w * 0.03), color, ow=2)


def snowfall(c, t, r, n=60, seed=2, size=6, speed=110, drift=30, alpha=0.9):
    x0, y0, w, h = r
    rnd = random.Random(seed)
    p = P("#FFFFFF", alpha)
    for _ in range(n):
        sx, ph, sp = rnd.uniform(0, 1), rnd.uniform(0, 1), rnd.uniform(0.6, 1.4)
        y = y0 + ((ph * h + t * speed * sp) % h)
        x = x0 + (sx * w + math.sin(t * 1.3 + ph * 9) * drift) % w
        c.drawCircle(x, y, size * sp * 0.7, p)


# ================================================================ exterior: mansion in a blizzard
def draw_ext(c, w, h):
    vgrad(c, (0, 0, w, h), "#1A2140", "#3A4A72")
    shape(c, smooth_path([(-50, 1450), (w * 0.35, 1330), (w * 0.7, 1340), (w + 50, 1420), (w + 50, h + 50), (-50, h + 50)]),
          "#E8EEF6", shade="#CBD6E4")
    mx, bse = w * 0.5, 1360
    shape(c, rect(mx - 400, bse - 500, 800, 500), "#6A4A52", shade="#553A42", sdx=18)
    shape(c, poly([(mx - 450, bse - 500), (mx, bse - 780), (mx + 450, bse - 500)]), "#3A2E3A")
    shape(c, smooth_path([(mx - 440, bse - 505), (mx, bse - 772), (mx + 440, bse - 505), (mx + 380, bse - 480),
                          (mx, bse - 730), (mx - 380, bse - 480)]), "#FFFFFF", ow=3)  # snow on the roof
    for row in range(2):
        for col in range(5):
            x, y = mx - 330 + col * 150, bse - 430 + row * 200
            shape(c, rect(x, y, 80, 120, 36), "#F2C26A")
            radial(c, x + 40, y + 60, 130, "#FFC870", 0.3, plus=True)
            shape(c, rect(x - 6, y + 112, 92, 16, 6), "#FFFFFF", ow=2.5)  # snow on sills
    shape(c, rect(mx - 70, bse - 190, 140, 190, 70), "#3A2418")
    # the drive: both cars are here (tiny at this distance)
    car(c, 250, 1520, 170, "#3F6FA8", 0.15)
    car(c, 820, 1530, 190, "#C0392B", 1.0)
    for x in (120, 960):  # snowy pines
        for k in range(3):
            shape(c, poly([(x - 110 + k * 25, 1600 - k * 120), (x, 1420 - k * 120), (x + 110 - k * 25, 1600 - k * 120)]),
                  "#2E5A48", ow=3.5)
            shape(c, poly([(x - 60 + k * 15, 1480 - k * 120), (x, 1420 - k * 120), (x + 60 - k * 15, 1480 - k * 120)]),
                  "#FFFFFF", ow=2.5)


# ================================================================ entrance hall (window onto the drive)
HALL_WIN = (640, 330, 380, 520)
DOOR = (60, 620, 330, 690)


def draw_drive(c, r):
    """What is visible through the hall window: snowy night drive, porch lamp, the two cars."""
    x, y, w, h = r
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    vgrad(c, (x, y, w, h), "#1A2448", "#3A4C78")
    shape(c, rect(x - 10, y + h * 0.66, w + 20, h * 0.4), "#EEF3FA", ow=3)
    radial(c, x + w * 0.12, y + h * 0.3, 240, "#FFD38A", 0.35, plus=True)
    car(c, x + w * 0.3, y + h * 0.9, 150, "#3F6FA8", 0.15)   # Marcus: just arrived, thin dusting
    car(c, x + w * 0.74, y + h * 0.92, 165, "#C0392B", 1.0)  # Cedric: buried for hours
    c.restore()


def draw_hall(c, w, h):
    vgrad(c, (0, 0, w, 1300), "#3E5A4A", "#334C3E")
    for x in range(40, w, 110):
        for y in range(60, 1260, 130):
            c.drawPath(oval(x + (55 if (y // 130) % 2 else 0), y, 9, 13), P("#4A6A58"))
    shape(c, rect(0, 1040, w, 260), "#6A3E2A", shade="#56301F", sdx=0, sdy=0)  # wainscot
    for x in range(0, w, 180):
        shape(c, rect(x + 14, 1060, 152, 220, 8), "#734430", ow=3)
    # front door (left)
    x, y, ww, hh = DOOR
    shape(c, rect(x - 24, y - 24, ww + 48, hh + 24, 14), "#3A2418")
    shape(c, rect(x, y, ww, hh, 10), "#7A4A2E", shade="#603822", sdx=14)
    c.drawLine(x + ww / 2, y, x + ww / 2, y + hh, line_w(4))
    for dx in (ww / 2 - 30, ww / 2 + 30):
        shape(c, oval(x + dx, y + hh * 0.55, 12, 12), "#C9A24A", ow=3)
    # window onto the drive (right)
    x, y, ww, hh = HALL_WIN
    shape(c, rect(x - 26, y - 26, ww + 52, hh + 52, 10), "#F2EFE8")
    draw_drive(c, HALL_WIN)
    c.drawLine(x + ww / 2, y, x + ww / 2, y + hh, line_w(10, "#E8E2D6"))
    c.drawLine(x, y + hh * 0.45, x + ww, y + hh * 0.45, line_w(10, "#E8E2D6"))
    c.drawRect(skia.Rect.MakeXYWH(x, y, ww, hh), line_w(4.5))
    shape(c, rect(x - 40, y + hh + 20, ww + 80, 26, 4), "#F2EFE8")
    # grandfather clock + coat rack
    shape(c, rect(470, 560, 130, 740, 12), "#5A3424", shade="#46281A", sdx=12)
    shape(c, oval(535, 680, 50, 50), "#F4F1EA")
    c.drawLine(535, 680, 535, 645, line_w(5))
    c.drawLine(535, 680, 562, 690, line_w(5))
    c.drawLine(440, 700, 440, 1300, line_w(10, "#3A2418"))
    for k in (-1, 1):
        c.drawLine(440, 720, 440 + k * 50, 690, line_w(8, "#3A2418"))
    shape(c, oval(440, 1300, 60, 12), "#3A2418", ow=3)
    # floor + doormat with ONE set of wet footprints (Marcus's)
    shape(c, poly([(0, 1300), (w, 1300), (w, h), (0, h)]), "#9A6A44")
    for k in range(0, w + 400, 150):
        c.drawLine(k, 1300, k - 260, h, line_w(3, INK, 0.45))
    shape(c, rect(70, 1330, 320, 120, 14), "#8A2A2A", shade="#6E1F1F", sdx=10)
    for i, (fx, fy) in enumerate(((180, 1370), (260, 1410), (330, 1480), (420, 1520), (500, 1580))):
        c.drawPath(oval(fx, fy, 22, 13), P("#5A7A9A", 0.5))
    # chandelier on (warm light)
    c.drawLine(w / 2, 0, w / 2, 120, line_w(5))
    shape(c, smooth_path([(w / 2 - 130, 130), (w / 2 + 130, 130), (w / 2 + 70, 200), (w / 2 - 70, 200)]), "#C9A24A")
    radial(c, w / 2, 180, 520, "#FFD38A", 0.22, plus=True)


# ================================================================ dining room (the victim)
def draw_dining(c, w, h):
    vgrad(c, (0, 0, w, 1300), "#6A2E36", "#58242C")
    for x in range(0, w, 120):
        c.drawRect(skia.Rect.MakeXYWH(x + 50, 0, 20, 1300), P("#74343E"))
    # portrait of Lord Pumpernickel
    shape(c, rect(340, 220, 400, 470, 12), "#C9A24A")
    shape(c, rect(370, 250, 340, 410, 6), "#2E3A4A")
    shape(c, oval(540, 450, 120, 130), "#F0BE96")
    shape(c, smooth_path([(470, 490), (520, 470), (540, 480), (560, 470), (610, 490), (560, 500), (520, 500)]), "#D9D4CC")
    for sx in (-1, 1):
        shape(c, oval(540 + sx * 40, 425, 14, 16), "#FFFFFF", ow=3)
    shape(c, poly([(420, 660), (540, 570), (660, 660)]), "#5B2A4A")
    shape(c, rect(330, 660, 420, 40, 6), "#B08A3A")
    # long table
    shape(c, rect(-40, 1180, w + 80, 70, 10), "#F4F1EA", shade="#DCD5C8", sdy=14, sdx=0)
    shape(c, rect(-40, 1250, w + 80, 200), "#E8E2D6", shade="#D0C8BA", sdx=0)
    shape(c, poly([(0, 1450), (w, 1450), (w, h), (0, h)]), "#4A2A1E")
    for k in range(0, w, 150):
        c.drawLine(k, 1450, k - 200, h, line_w(3, INK, 0.45))
    # candelabra
    shape(c, oval(880, 1182, 70, 12), "#B08A3A", ow=3)
    shape(c, rect(872, 1070, 16, 112, 4), "#C9A24A", ow=3)
    arm = skia.Path()
    arm.moveTo(820, 1052)
    arm.quadTo(880, 1130, 940, 1052)
    c.drawPath(arm, line_w(12, "#C9A24A"))
    c.drawPath(arm, line_w(3))


DINING_CANDLES = [(820, 1055), (880, 1075), (940, 1055)]


# ================================================================ library (typewriter + the cat)
def draw_library(c, w, h):
    c.drawRect(skia.Rect(0, 0, w, h), P("#4A2C20"))
    rnd = random.Random(9)
    for x0 in (0, 700):
        shape(c, rect(x0 - 20, 120, 400, 1180), "#3A2016")
        for sy in (200, 420, 640, 860, 1080):
            x = x0 + 10
            while x < x0 + 360:
                bw = rnd.randint(28, 48)
                bh = rnd.randint(130, 190)
                shape(c, rect(x, sy + 200 - bh, bw, bh, 4),
                      rnd.choice(["#8A2A2A", "#2A4A6A", "#C9A24A", "#3E6B3A", "#6A4A8A"]), ow=3)
                x += bw + 2
            shape(c, rect(x0 - 20, sy + 200, 400, 24), "#2E1A12", ow=3.5)
    shape(c, rect(380, 200, 320, 520, 150), "#1C2448")  # tall window (snow drawn live)
    c.drawLine(540, 200, 540, 720, line_w(8, "#2E1A12"))
    # desk + lamp + typewriter
    shape(c, rect(250, 1180, 580, 60, 8), "#7A4A2E", shade="#603822", sdy=12, sdx=0)
    shape(c, rect(280, 1240, 60, 300), "#603822")
    shape(c, rect(740, 1240, 60, 300), "#603822")
    shape(c, oval(330, 1176, 50, 10), "#2E5A3A", ow=3)
    shape(c, rect(322, 1060, 16, 116, 4), "#C9A24A", ow=3)
    shape(c, poly([(270, 1070), (390, 1070), (360, 990), (300, 990)]), "#2E8A5A")
    radial(c, 330, 1100, 380, "#FFE2A0", 0.25, plus=True)
    shape(c, rect(470, 1080, 220, 100, 18), "#2A2A30", shade="#1C1C20", sdx=10)  # typewriter
    for k in range(3):
        for j in range(7):
            shape(c, oval(495 + j * 28, 1115 + k * 20, 9, 7), "#D8D4C8", ow=2)
    shape(c, rect(500, 940, 160, 150, 4), "#FFFFFF", ow=3)  # the will
    for k in range(5):
        c.drawLine(515, 965 + k * 20, 640 - (40 if k == 4 else 0), 965 + k * 20, line_w(3, "#6A6A80"))
    shape(c, poly([(0, 1540), (w, 1540), (w, h), (0, h)]), "#3A2218")
    shape(c, smooth_path([(120, 1700), (960, 1660), (1000, 1860), (80, 1890)]), "#2E4A6A", shade="#243A54", sdx=18)


@lru_cache(maxsize=None)
def img(name):
    fns = {"ext": draw_ext, "hall": draw_hall, "dining": draw_dining, "library": draw_library, "kitchen": draw_kitchen}  # *_blur too
    if name.endswith("_blur"):
        return snapshot(fns[name[:-5]], blur=16)
    return snapshot(fns[name])


# ================================================================ live-drawn characters/props that are not people
def cat(c, x, y, s, t, smug=1.0):
    """Mr. Whiskers: fat orange cat sitting (x, y = bottom). s = height px."""
    k = s / 300
    tail = skia.Path()
    tail.moveTo(x + 80 * k, y - 20 * k)
    tail.cubicTo(x + 170 * k, y - 20 * k, x + 160 * k, y - 140 * k + 20 * k * math.sin(t * 3), x + 120 * k, y - 170 * k)
    c.drawPath(tail, line_w(26 * k, "#E8892E"))
    c.drawPath(tail, line_w(4))
    body = smooth_path([(x - 100 * k, y), (x - 110 * k, y - 120 * k), (x - 60 * k, y - 190 * k), (x + 60 * k, y - 190 * k),
                        (x + 110 * k, y - 120 * k), (x + 100 * k, y)])
    shape(c, body, "#F0A040", shade="#D88A2E", sdx=14 * k, ow=4)
    hy = y - 230 * k
    for sx in (-1, 1):
        shape(c, poly([(x + sx * 75 * k, hy - 30 * k), (x + sx * 70 * k, hy - 110 * k), (x + sx * 20 * k, hy - 60 * k)]),
              "#F0A040", ow=4)
    shape(c, oval(x, hy, 90 * k, 75 * k), "#F0A040", shade="#D88A2E", sdx=10 * k, ow=4)
    for sx in (-1, 1):  # half-closed smug eyes
        shape(c, oval(x + sx * 35 * k, hy - 8 * k, 18 * k, 14 * k), "#FFFFFF", ow=3)
        c.drawRect(skia.Rect(x + sx * 35 * k - 20 * k, hy - 24 * k, x + sx * 35 * k + 20 * k, hy - 24 * k + 18 * k * smug),
                   P("#F0A040"))
        c.drawCircle(x + sx * 35 * k, hy - 4 * k, 6 * k, P(INK))
        c.drawLine(x + sx * 18 * k, hy - 24 * k + 16 * k * smug, x + sx * 52 * k, hy - 24 * k + 16 * k * smug, line_w(3))
    shape(c, poly([(x - 8 * k, hy + 14 * k), (x + 8 * k, hy + 14 * k), (x, hy + 24 * k)]), "#E86A7A", ow=2.5)
    sm = skia.Path()
    sm.moveTo(x - 20 * k, hy + 32 * k)
    sm.quadTo(x - 8 * k, hy + 44 * k, x, hy + 30 * k)
    sm.quadTo(x + 8 * k, hy + 44 * k, x + 20 * k, hy + 32 * k)
    c.drawPath(sm, line_w(3))
    for sy in (-1, 1):
        for sx in (-1, 1):
            c.drawLine(x + sx * 40 * k, hy + (24 + sy * 6) * k, x + sx * 110 * k, hy + (20 + sy * 16) * k, line_w(2.5))


def victim(c, x, y, s, t):
    """Lord Pumpernickel slumped face-down in a giant pudding (cartoon, no gore). x, y = bowl bottom on table."""
    k = s / 400
    shape(c, rect(x - 160 * k, y - 330 * k, 320 * k, 340 * k, 30 * k), "#7A3A22", ow=4)  # chair back
    shape(c, smooth_path([(x - 150 * k, y - 10 * k), (x - 170 * k, y - 160 * k), (x - 80 * k, y - 230 * k), (x + 80 * k, y - 230 * k),
                          (x + 170 * k, y - 160 * k), (x + 150 * k, y - 10 * k)]), "#5B2A4A", shade="#431D36", sdx=16 * k, ow=4)
    for sx in (-1, 1):  # arms flopped on the table
        sl = skia.Path()
        sl.addRoundRect(skia.Rect(x + sx * 150 * k - 70 * k, y - 40 * k, x + sx * 150 * k + 70 * k, y + 5 * k), 20 * k, 20 * k)
        shape(c, sl, "#5B2A4A", ow=4)
        shape(c, oval(x + sx * 225 * k, y - 18 * k, 26 * k, 22 * k), "#F0BE96", ow=3.5)
    shape(c, oval(x, y - 150 * k, 105 * k, 95 * k), "#F0BE96", shade="#D69C76", sdx=10 * k, ow=4)  # bald head, top view
    c.drawPath(oval(x - 30 * k, y - 190 * k, 30 * k, 12 * k), P("#FFFFFF", 0.5))
    for sx in (-1, 1):
        shape(c, smooth_path([(x + sx * 95 * k, y - 170 * k), (x + sx * 115 * k, y - 130 * k), (x + sx * 92 * k, y - 110 * k)]),
              "#D9D4CC", ow=3)
    # the pudding bowl in front (face is in it)
    shape(c, smooth_path([(x - 150 * k, y - 80 * k), (x + 150 * k, y - 80 * k), (x + 110 * k, y), (x - 110 * k, y)]),
          "#F4F1EA", shade="#DCD5C8", sdx=12 * k, ow=4)
    shape(c, smooth_path([(x - 140 * k, y - 80 * k), (x - 100 * k, y - 110 * k), (x, y - 100 * k), (x + 100 * k, y - 112 * k),
                          (x + 140 * k, y - 80 * k)]), "#7A4A2A", ow=3.5)
    for dx in (-90, -20, 60, 110):
        shape(c, smooth_path([(x + (dx - 14) * k, y - 82 * k), (x + dx * k, y - 60 * k + 6 * k * math.sin(t * 2 + dx)),
                              (x + (dx + 14) * k, y - 82 * k)]), "#7A4A2A", ow=3)
    c.drawLine(x + 170 * k, y - 10 * k, x + 260 * k, y + 20 * k, line_w(10 * k, "#C8CED4"))  # dropped spoon
    shape(c, oval(x + 268 * k, y + 24 * k, 20 * k, 13 * k), "#C8CED4", ow=3)
