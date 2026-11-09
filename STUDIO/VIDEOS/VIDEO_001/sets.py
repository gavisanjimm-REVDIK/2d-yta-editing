"""sets.py - VIDEO_001 storybook backgrounds (built once per process, cached as images).

Style: flat colours, thinner dark outlines than characters, subtle paper grain, warm candle light.
Power is OUT in the story (9 pm) -> candles + lightning only. The basement has NO windows (the riddle's clue):
lightning never lights it.
"""
from __future__ import annotations

import math
import random
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "PIPELINE" / "twod"))
from kit import W, H, rgb, clamp  # noqa: E402
from toon import smooth_path, oval, INK  # noqa: E402

BG_OW = 4.5


def P(color, alpha=1.0):
    p = skia.Paint(AntiAlias=True, Color=rgb(color))
    p.setAlphaf(alpha)
    return p


LINE = skia.Paint(AntiAlias=True, Color=rgb(INK), Style=skia.Paint.kStroke_Style, StrokeWidth=BG_OW,
                  StrokeJoin=skia.Paint.kRound_Join, StrokeCap=skia.Paint.kRound_Cap)


def line_w(w, color=INK, alpha=1.0):
    p = skia.Paint(LINE)
    p.setStrokeWidth(w)
    p.setColor(rgb(color))
    p.setAlphaf(alpha)
    return p


def shape(c, path, color, outline=True, shade=None, sdx=10, sdy=0, ow=BG_OW):
    c.drawPath(path, P(color))
    if shade:
        lit = skia.Path(path)
        lit.offset(-sdx, -sdy)
        d = skia.Op(path, lit, skia.PathOp.kDifference_PathOp)
        if d:
            c.drawPath(d, P(shade))
    if outline:
        c.drawPath(path, line_w(ow))


def rect(x, y, w, h, r=0):
    p = skia.Path()
    if r:
        p.addRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    else:
        p.addRect(skia.Rect.MakeXYWH(x, y, w, h))
    return p


def poly(pts):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    p.close()
    return p


def vgrad(c, r, c0, c1):
    x, y, w, h = r
    sh = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)], [rgb(c0), rgb(c1)])
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=sh))


def radial(c, x, y, r, color, alpha, plus=False):
    col = rgb(color)
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [skia.ColorSetA(col, int(255 * alpha)),
                                                               skia.ColorSetA(col, 0)])
    c.drawCircle(x, y, r, skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus if plus else skia.BlendMode.kSrcOver))


@lru_cache(maxsize=4)
def grain(w, h, seed=3):
    """Paper grain texture image (storybook feel)."""
    r = np.random.default_rng(seed)
    n = r.normal(0, 1, (h // 4 + 1, w // 4 + 1)).astype(np.float32)
    n = np.kron(n, np.ones((4, 4), np.float32))[:h, :w]
    fine = r.normal(0, 1, (h, w)).astype(np.float32)
    v = np.clip(128 + n * 9 + fine * 6, 0, 255).astype(np.uint8)
    rgba = np.dstack([v, v, v, np.full_like(v, 255)])
    return skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType)


def apply_grain(c, w, h, amount=0.16):
    p = skia.Paint(BlendMode=skia.BlendMode.kOverlay)
    p.setAlphaf(amount)
    c.drawImage(grain(w, h), 0, 0, skia.SamplingOptions(), p)


def snapshot(fn, w=W, h=H, blur=0.0):
    s = skia.Surface(w, h)
    c = s.getCanvas()
    fn(c, w, h)
    apply_grain(c, w, h)
    img = s.makeImageSnapshot()
    if blur:
        s2 = skia.Surface(w, h)
        p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(blur, blur))
        s2.getCanvas().drawImage(img, 0, 0, skia.SamplingOptions(), p)
        img = s2.makeImageSnapshot()
    return img


# ================================================================ exterior: mansion in the storm
def draw_ext(c, w, h):
    vgrad(c, (0, 0, w, h), "#151833", "#3A3460")
    rnd = random.Random(4)
    for i in range(7):  # heavy clouds
        cx, cy = rnd.uniform(-100, w + 100), rnd.uniform(60, 520)
        pts = [(cx + math.cos(a) * rnd.uniform(160, 260) * 1.6, cy + math.sin(a) * rnd.uniform(60, 100))
               for a in np.linspace(0, 2 * math.pi, 9, endpoint=False)]
        c.drawPath(smooth_path(pts), P("#2A2B4A", 0.9))
    # hill
    shape(c, smooth_path([(-50, 1500), (w * 0.3, 1330), (w * 0.7, 1310), (w + 50, 1420), (w + 50, h + 50), (-50, h + 50)]),
          "#1E2B2A", shade="#172221")
    # mansion
    mx, base = w * 0.5, 1360
    body = rect(mx - 420, base - 520, 840, 520)
    shape(c, body, "#3B3550", shade="#2E2942", sdx=20)
    for k, (x0, ww, hh) in enumerate(((mx - 470, 260, 760), (mx + 210, 260, 720))):  # towers
        shape(c, rect(x0, base - hh, ww, hh), "#433C5A", shade="#332D47", sdx=18)
        shape(c, poly([(x0 - 30, base - hh), (x0 + ww / 2, base - hh - 260), (x0 + ww + 30, base - hh)]), "#25223A")
    shape(c, poly([(mx - 300, base - 520), (mx, base - 760), (mx + 300, base - 520)]), "#25223A")
    shape(c, rect(mx - 70, base - 980, 50, 200), "#2E2942")  # chimney
    # windows: mostly dark (power is out) - two faint candle glows
    lit = {(0, 1), (2, 0)}
    for row in range(2):
        for col in range(5):
            x = mx - 330 + col * 150
            y = base - 450 + row * 210
            wcol = "#E8A94E" if (row, col) in lit else "#1D1E33"
            shape(c, rect(x, y, 80, 130, 36), wcol)
            c.drawLine(x + 40, y, x + 40, y + 130, line_w(3.5))
            if (row, col) in lit:
                radial(c, x + 40, y + 65, 140, "#FFB257", 0.35, plus=True)
    for x0 in (mx - 400, mx + 280):  # tower windows
        for y in (base - 620, base - 380):
            shape(c, rect(x0, y, 70, 120, 32), "#1D1E33")
    shape(c, rect(mx - 70, base - 200, 140, 200, 70), "#2A1E1A")  # door
    # dead tree left
    tr = skia.Path()
    tr.moveTo(120, 1520)
    tr.lineTo(150, 1100)
    tr.lineTo(80, 900)
    tr.moveTo(150, 1100)
    tr.lineTo(260, 950)
    tr.lineTo(330, 960)
    tr.moveTo(130, 1000)
    tr.lineTo(40, 960)
    c.drawPath(tr, line_w(26, "#141522"))
    # iron fence foreground
    for i in range(-1, 13):
        x = i * 95
        c.drawLine(x, 1950, x, 1600, line_w(14, "#0E0F18"))
        shape(c, poly([(x - 16, 1605), (x, 1560), (x + 16, 1605)]), "#0E0F18", outline=False)
    c.drawLine(0, 1650, w, 1650, line_w(12, "#0E0F18"))
    c.drawLine(0, 1820, w, 1820, line_w(12, "#0E0F18"))


# ================================================================ basement: stone walls, pipes, NO windows
BASE_W = 2600


def draw_basement(c, w, h, lit=False):
    wall, wall_sh, mortar = ("#7E7A86", "#6A6573", "#4C4856") if lit else ("#2C2F44", "#25283A", "#1A1C2B")
    floor = "#5B524D" if lit else "#1F1E28"
    c.drawRect(skia.Rect(0, 0, w, h), P(mortar))
    rnd = random.Random(11)
    # stone blocks across the whole panorama: solid walls, no openings anywhere
    y = 120
    row = 0
    while y < 1450:
        bh = rnd.randint(110, 150)
        x = -rnd.randint(0, 120) if row % 2 else -40
        while x < w:
            bw = rnd.randint(170, 260)
            col = wall if rnd.random() > 0.25 else wall_sh
            shape(c, rect(x + 6, y + 6, bw - 12, bh - 12, 18), col, ow=3.5)
            x += bw
        y += bh
        row += 1
    vgrad(c, (0, 0, w, 220), "#000000" if not lit else "#3A3640", mortar)  # dark ceiling
    for bx in range(80, w, 420):  # ceiling beams
        shape(c, rect(bx, 0, 70, 200), "#3A2A22" if lit else "#18141A", ow=3.5)
    # floor
    shape(c, poly([(0, 1450), (w, 1450), (w, h), (0, h)]), floor)
    for k in range(0, w, 160):
        c.drawLine(k, 1450, k - 200, h, line_w(3, INK, 0.5))
    # pipes along the wall (Daniel's "checking the pipes")
    pc, psh = ("#B8743E", "#94592C") if lit else ("#4A3326", "#3A281E")
    for py, x0, x1 in ((340, 0, w), (420, 300, w - 200)):
        shape(c, rect(x0, py, x1 - x0, 46, 23), pc, shade=psh, sdy=8, sdx=0, ow=4)
        for vx in range(x0 + 180, x1, 520):
            shape(c, rect(vx, py - 12, 36, 70, 8), psh, ow=3.5)
    for vx in (700, 1650):
        shape(c, rect(vx, 340, 46, 1110, 23), pc, shade=psh, sdx=10, ow=4)
        shape(c, oval(vx + 23, 900, 46, 46), "#B5352E" if lit else "#3A1A1A")  # valve wheel
    # water heater, shelves with jars, crates
    shape(c, rect(1900, 820, 300, 630, 120), "#9EA4A8" if lit else "#353A44", shade="#7D8388" if lit else "#2A2F38",
          sdx=30)
    for sy in (800, 1050):
        shape(c, rect(900, sy, 520, 26), "#6B4A32" if lit else "#2A2026")
        for j in range(5):
            jc = ["#C9A24A", "#7FA35A", "#B5552E", "#5A8AB5", "#C9A24A"][j]
            shape(c, rect(930 + j * 95, sy - 110, 70, 110, 14), jc if lit else "#2E2C38", ow=3.5)
    for cx_, cy_, s in ((300, 1260, 230), (480, 1330, 160), (2350, 1250, 240)):
        shape(c, rect(cx_, cy_, s, 1450 - cy_ + 30, 6), "#A87A4A" if lit else "#33281F", shade="#8A6038" if lit else "#2A2019",
              sdx=18)
        c.drawLine(cx_, cy_, cx_ + s, 1450 + 30, line_w(4, INK, 0.7))
    # stairs on the far left going UP to the foyer door (the only way in)
    for k in range(7):
        shape(c, rect(-40 + k * 30, 1450 - k * 140, 260 - k * 30, 34), "#6B4A32" if lit else "#241C22", ow=3.5)
    shape(c, rect(40, 120, 160, 300, 8), "#3A2418" if lit else "#151015")
    # dead bulb hanging (power is out)
    c.drawLine(1300, 0, 1300, 330, line_w(4))
    shape(c, oval(1300, 360, 34, 40), "#D8D4C8" if lit else "#3A3A44", ow=3.5)
    # cobwebs
    for (x, y, s) in ((0, 0, 200), (w, 0, -220)):
        web = skia.Path()
        for a in range(4):
            web.moveTo(x, y)
            web.lineTo(x + s * math.cos(a * 0.4), y + abs(s) * math.sin(a * 0.4 + 0.2))
        c.drawPath(web, line_w(2.5, "#C8C8D8" if lit else "#4A4A5A", 0.8))


# ================================================================ study: open safe, candles, rainy window
def draw_study(c, w, h):
    c.drawRect(skia.Rect(0, 0, w, h), P("#5A3424"))
    for x in range(0, w, 180):  # wood panels
        shape(c, rect(x + 14, 900, 152, 520, 10), "#6A3E2A", shade="#56301F", sdx=8, ow=3.5)
    vgrad(c, (0, 0, w, 900), "#4A5A4A", "#3E4C3E")  # green wallpaper
    for x in range(40, w, 120):
        for y in range(60, 860, 120):
            c.drawPath(oval(x + (60 if (y // 120) % 2 else 0), y, 10, 14), P("#56685A"))
    c.drawLine(0, 900, w, 900, line_w(8, "#2E1A12"))
    # tall window (rain + lightning are drawn live on top)
    shape(c, rect(620, 160, 360, 640, 170), "#1C2140")
    shape(c, rect(600, 790, 400, 40, 6), "#6A3E2A")
    c.drawLine(800, 160, 800, 790, line_w(10, "#3A2418"))
    c.drawLine(620, 470, 980, 470, line_w(10, "#3A2418"))
    c.drawLine(540, 130, 1060, 130, line_w(12, "#3A2418"))  # curtain rod
    for x0, d in ((540, 1), (1060, -1)):  # curtains gathered with a tie-back
        cur = skia.Path()
        cur.moveTo(x0, 120)
        cur.lineTo(x0 + d * 120, 120)
        cur.quadTo(x0 + d * 70, 420, x0 + d * 40, 560)
        cur.quadTo(x0 + d * 90, 720, x0 + d * 110, 880)
        cur.lineTo(x0, 880)
        cur.close()
        shape(c, cur, "#8A2A2A", shade="#6E1F1F", sdx=d * 14)
        for k in range(1, 3):
            c.drawLine(x0 + d * 30 * k, 140, x0 + d * 25 * k, 860, line_w(3, INK, 0.5))
        shape(c, rect(x0 + (0 if d > 0 else -70), 545, 70, 24, 10), "#C9A24A", ow=3)
    # bookshelf left
    shape(c, rect(-20, 200, 380, 1220), "#4A2A1C")
    rnd = random.Random(7)
    for sy in (330, 560, 790, 1020):
        x = 10
        while x < 330:
            bw = rnd.randint(28, 50)
            bh = rnd.randint(130, 190)
            shape(c, rect(x, sy - bh + 210 - 20, bw, bh, 4),
                  rnd.choice(["#8A2A2A", "#2A4A6A", "#C9A24A", "#3E6B3A", "#6A4A8A"]), ow=3)
            x += bw + 2
        shape(c, rect(-20, sy + 190, 380, 24), "#3A2016", ow=3.5)
    # wall safe: OPEN and EMPTY (necklace stand bare)
    sx, sy = 470, 980
    shape(c, rect(sx - 10, sy - 10, 300, 300, 18), "#3A3A44")
    shape(c, rect(sx + 20, sy + 20, 240, 240, 10), "#15151C")
    shape(c, poly([(sx + 120, sy + 230), (sx + 150, sy + 120), (sx + 180, sy + 230)]), "#5A1A2A")  # velvet stand
    c.drawPath(oval(sx + 150, sy + 118, 40, 14), line_w(4, "#C9A24A"))
    shape(c, poly([(sx - 10, sy - 10), (sx - 150, sy + 30), (sx - 150, sy + 330), (sx - 10, sy + 290)]), "#5A5A66",
          shade="#46464F", sdx=20)  # swung-open door
    shape(c, oval(sx - 80, sy + 160, 40, 46), "#A8A8B4")
    c.drawLine(sx - 80, sy + 120, sx - 80, sy + 200, line_w(5))
    # desk + candelabra (candles live-animated)
    shape(c, rect(700, 1250, 520, 60, 8), "#6A3E2A", shade="#56301F", sdy=12, sdx=0)
    shape(c, rect(730, 1310, 60, 300), "#56301F")
    shape(c, rect(1120, 1310, 60, 300), "#56301F")
    # floor + rug
    shape(c, poly([(0, 1420), (w, 1420), (w, h), (0, h)]), "#3A2218")
    shape(c, smooth_path([(120, 1640), (980, 1600), (1040, 1840), (60, 1880)]), "#7A2A2A", shade="#5E2020", sdx=20)


STUDY_CANDLES = [(840, 1180), (900, 1150), (960, 1180)]


def draw_candles(c, pts, t, scale=1.0, base_col="#E8DCC0"):
    for i, (x, y) in enumerate(pts):
        f = 0.85 + 0.15 * math.sin(t * 13 + i * 2.1) * math.sin(t * 7.3 + i)
        radial(c, x, y - 40 * scale, 420 * scale * f, "#FFB45A", 0.22, plus=True)
        shape(c, rect(x - 14 * scale, y - 30 * scale, 28 * scale, 110 * scale, 4), base_col, ow=3)
        fl = smooth_path([(x, y - 80 * scale * f), (x + 12 * scale, y - 45 * scale), (x, y - 30 * scale),
                          (x - 12 * scale, y - 45 * scale)])
        c.drawPath(fl, P("#FFD36A"))
        c.drawPath(fl, line_w(2.5, "#C9601E"))


# ================================================================ foyer: staircase, basement door, candles
def draw_foyer(c, w, h):
    vgrad(c, (0, 0, w, 1300), "#5A3E50", "#4A3242")
    for x in range(0, w, 240):  # pilasters
        shape(c, rect(x + 100, 300, 40, 1000), "#64485C", ow=3)
    # arched windows high up (lightning shows here)
    for x0 in (300, 640):
        shape(c, rect(x0, 120, 170, 330, 85), "#1C2140")
        c.drawLine(x0 + 85, 120, x0 + 85, 450, line_w(7, "#2E1F2A"))
    # grand staircase right
    for k in range(9):
        shape(c, rect(560 + k * 40, 1300 - k * 95, 600, 40), "#7A4A30", shade="#603822", sdy=10, sdx=0, ow=3.5)
    c.drawLine(560, 1300, 920, 445, line_w(14, "#3A2016"))
    for k in range(9):
        c.drawLine(590 + k * 40, 1290 - k * 95, 590 + k * 40, 1180 - k * 95, line_w(7, "#3A2016"))
    # basement door left: heavy wooden door, iron hinges, steps-down lamp hook
    shape(c, rect(80, 760, 290, 560, 24), "#5A3A26", shade="#46301E", sdx=16)
    for k in range(3):
        c.drawLine(105 + k * 85, 790, 105 + k * 85, 1300, line_w(3.5, INK, 0.7))
    for hy in (860, 1180):
        shape(c, rect(90, hy, 120, 26, 6), "#2A2A30", ow=3)
    shape(c, oval(330, 1050, 18, 18), "#C9A24A", ow=3)
    shape(c, rect(70, 740, 310, 30, 6), "#3A2418")
    # portraits
    shape(c, rect(420, 560, 130, 170, 6), "#C9A24A")
    shape(c, rect(436, 576, 98, 138, 4), "#3E4C5A")
    c.drawPath(oval(485, 630, 26, 30), P("#E0B898"))
    # floor checkered
    shape(c, poly([(0, 1300), (w, 1300), (w, h), (0, h)]), "#D8CCB4")
    for i in range(-6, 14):
        for j in range(7):
            if (i + j) % 2:
                y0, y1 = 1300 + j * 95, 1300 + (j + 1) * 95
                k0, k1 = 1 + j * 0.25, 1 + (j + 1) * 0.25
                x0 = w / 2 + (i * 110 - w / 2) * k0
                x1 = w / 2 + ((i + 1) * 110 - w / 2) * k0
                x3 = w / 2 + (i * 110 - w / 2) * k1
                x2 = w / 2 + ((i + 1) * 110 - w / 2) * k1
                c.drawPath(poly([(x0, y0), (x1, y0), (x2, y1), (x3, y1)]), P("#3A3036"))
    c.drawLine(0, 1300, w, 1300, line_w(6))
    # side tables with candles
    for tx in (440, 980):
        shape(c, rect(tx - 70, 1180, 140, 26, 6), "#6A3E2A")
        shape(c, rect(tx - 12, 1206, 24, 110), "#56301F")
    # dark chandelier (power out)
    c.drawLine(w / 2, 0, w / 2, 140, line_w(5))
    shape(c, smooth_path([(w / 2 - 150, 150), (w / 2 + 150, 150), (w / 2 + 80, 230), (w / 2 - 80, 230)]), "#6A5A3A")


FOYER_CANDLES = [(425, 1150), (455, 1140), (965, 1150), (995, 1140)]


@lru_cache(maxsize=None)
def img(name):
    if name == "ext":
        return snapshot(draw_ext)
    if name == "base_dark":
        return snapshot(draw_basement, BASE_W, H)
    if name == "base_lit":
        return snapshot(lambda c, w, h: draw_basement(c, w, h, True), BASE_W, H)
    if name == "study":
        return snapshot(draw_study)
    if name == "study_blur":
        return snapshot(draw_study, blur=14)
    if name == "foyer":
        return snapshot(draw_foyer)
    if name == "foyer_blur":
        return snapshot(draw_foyer, blur=16)
    raise KeyError(name)
