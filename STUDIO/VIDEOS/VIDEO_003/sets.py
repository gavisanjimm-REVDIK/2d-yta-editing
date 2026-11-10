"""sets.py - VIDEO_003 "The Three Doors of Doom" (pyramid). Storybook style, helpers shared with VIDEO_001/002.

HIDDEN CLUES (never pointed at):
  door 1 (fire, "burns for 1,000 years"): cold, cobweb across the handle, no glow under the door -> fire long out
  door 2 (lions): deep claw scratches + feeding hatch -> very much alive (roar later)
  door 3 (flood, "arrives in 3,000 years"): a thin trickle of water + wet stain under the door -> the flood is due now
  (the signs were carved 3,000 years ago - the mummy says so)
"""
from __future__ import annotations

import importlib.util
import math
import random
from functools import lru_cache
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


base = _load("v001_sets", HERE.parent / "VIDEO_001" / "sets.py")
v2 = _load("v002_sets", HERE.parent / "VIDEO_002" / "sets.py")

W, H, INK = base.W, base.H, base.INK
P, shape, rect, poly, vgrad, radial, line_w = base.P, base.shape, base.rect, base.poly, base.vgrad, base.radial, base.line_w
smooth_path, oval, snapshot = base.smooth_path, base.oval, base.snapshot

SAND, SAND_SH, STONE, STONE_SH = "#D9B26A", "#B8904E", "#C99A58", "#A87C42"


def hieroglyphs(c, x0, y0, w, h, seed=1, alpha=0.55):
    """Simple carved glyph rows (eyes, birds, ankhs, waves) - decoration only."""
    rnd = random.Random(seed)
    col = "#7A5A2E"
    p = line_w(4, col, alpha)
    for row in range(int(h // 90)):
        y = y0 + 30 + row * 90
        x = x0 + 20
        while x < x0 + w - 50:
            k = rnd.randint(0, 4)
            if k == 0:  # eye
                c.drawPath(oval(x + 20, y, 20, 10), p)
                c.drawCircle(x + 20, y, 4, P(col, alpha))
            elif k == 1:  # ankh
                c.drawPath(oval(x + 15, y - 12, 9, 12), p)
                c.drawLine(x + 15, y, x + 15, y + 28, p)
                c.drawLine(x + 2, y + 6, x + 28, y + 6, p)
            elif k == 2:  # bird
                q = skia.Path()
                q.moveTo(x, y + 10)
                q.quadTo(x + 18, y - 18, x + 36, y + 6)
                q.lineTo(x + 26, y + 22)
                c.drawPath(q, p)
            elif k == 3:  # waves
                q = skia.Path()
                q.moveTo(x, y)
                for j in range(3):
                    q.quadTo(x + 6 + j * 12, y - 10, x + 12 + j * 12, y)
                c.drawPath(q, p)
            else:  # sun
                c.drawCircle(x + 16, y, 12, p)
            x += rnd.randint(55, 75)
        c.drawLine(x0 + 10, y + 42, x0 + w - 10, y + 42, line_w(2.5, col, alpha * 0.6))


# ================================================================ corridor (the chase)
def draw_corridor(c, w, h):
    vgrad(c, (0, 0, w, h), "#3A2814", "#1E140A")
    vx, vy = w / 2, 860  # vanishing point (dark end of the corridor)
    shape(c, poly([(0, 0), (vx - 120, vy - 160), (vx - 120, vy + 160), (0, h)]), STONE, shade=STONE_SH, sdx=30)
    shape(c, poly([(w, 0), (vx + 120, vy - 160), (vx + 120, vy + 160), (w, h)]), STONE_SH, ow=4.5)
    shape(c, poly([(0, h), (vx - 120, vy + 160), (vx + 120, vy + 160), (w, h)]), SAND, shade=SAND_SH, sdy=20, sdx=0)
    shape(c, poly([(0, 0), (vx - 120, vy - 160), (vx + 120, vy - 160), (w, 0)]), "#5A3E20")
    shape(c, rect(vx - 120, vy - 160, 240, 320), "#120C06")
    for k in range(1, 6):  # stone block seams in perspective
        t = k / 6
        for side in (-1, 1):
            x = vx + side * (120 + (w / 2 - 120) * (1 - t) ** 1.6)
            y0 = vy - 160 - (vy - 160) * (1 - t) ** 1.6
            y1 = vy + 160 + (h - vy - 160) * (1 - t) ** 1.6
            c.drawLine(x, y0, x, y1, line_w(4, INK, 0.5))
    c.save()
    c.clipPath(poly([(0, 0), (vx - 120, vy - 160), (vx - 120, vy + 160), (0, h)]))
    hieroglyphs(c, 0, 300, 380, 900, 3, 0.45)
    c.restore()


CORRIDOR_TORCHES = [(150, 620), (930, 620)]


# ================================================================ the chamber of three doors
DOORS = {1: (70, 560), 2: (415, 560), 3: (760, 560)}  # top-left of each door
DOOR_W, DOOR_H = 250, 620
FLOOR_Y = 1180


def draw_door(c, n, x, y):
    w_, h_ = DOOR_W, DOOR_H
    shape(c, rect(x - 22, y - 30, w_ + 44, h_ + 30, 10), "#8A6234")  # frame
    shape(c, poly([(x - 30, y - 30), (x + w_ / 2, y - 120), (x + w_ + 30, y - 30)]), "#7A5428")  # pediment
    shape(c, rect(x, y, w_, h_, 8), "#6A4A2A", shade="#553A20", sdx=14)
    for k in range(1, 4):
        c.drawLine(x + 10, y + k * h_ / 4, x + w_ - 10, y + k * h_ / 4, line_w(3.5, INK, 0.6))
    shape(c, oval(x + w_ - 50, y + h_ * 0.55, 18, 18), "#C9A24A")  # ring handle
    c.drawPath(oval(x + w_ - 50, y + h_ * 0.55 + 22, 22, 22), line_w(6, "#C9A24A"))
    # number plaque + sign plaque (text drawn by gfx; here a blank carved tablet)
    shape(c, oval(x + w_ / 2, y - 62, 38, 38), "#E8D2A0")
    font = skia.Font(skia.Typeface.MakeFromFile(str(HERE.parents[1] / "ASSETS" / "fonts" / "Anton-Regular.ttf")), 58)
    tw = font.measureText(str(n))
    c.drawTextBlob(skia.TextBlob(str(n), font), x + w_ / 2 - tw / 2, y - 40, P("#5A3A1E"))
    shape(c, rect(x + 30, y + 40, w_ - 60, 120, 8), "#E8D2A0", shade="#CDB27A", sdx=6)
    # icon on the tablet
    ix, iy = x + w_ / 2, y + 100
    if n == 1:
        fl = skia.Path()  # flame
        fl.moveTo(ix, iy - 44)
        fl.cubicTo(ix + 34, iy - 6, ix + 26, iy + 30, ix, iy + 32)
        fl.cubicTo(ix - 26, iy + 30, ix - 34, iy - 6, ix - 10, iy - 26)
        fl.quadTo(ix - 4, iy - 8, ix, iy - 44)
        c.drawPath(fl, P("#E8642E"))
        c.drawPath(fl, line_w(4))
    elif n == 2:
        for dx, dy, r in ((0, 10, 20), (-26, -18, 9), (-9, -30, 9), (9, -30, 9), (26, -18, 9)):
            c.drawCircle(ix + dx, iy + dy, r, P("#7A4A2A"))
    else:
        for k in range(3):
            q = skia.Path()
            q.moveTo(ix - 40, iy - 20 + k * 20)
            for j in range(4):
                q.quadTo(ix - 30 + j * 20, iy - 32 + k * 20, ix - 20 + j * 20, iy - 20 + k * 20)
            c.drawPath(q, line_w(5, "#2E6A9A"))
    # --- the quiet clues
    if n == 1:  # cobweb across the handle, a little dust
        cx_, cy_ = x + w_ - 50, y + h_ * 0.55
        web = skia.Path()
        for a in range(6):
            web.moveTo(cx_, cy_)
            web.lineTo(cx_ + math.cos(a * 1.05) * 70, cy_ + math.sin(a * 1.05) * 70)
        for r in (25, 45, 65):
            web.addCircle(cx_, cy_, r)
        c.drawPath(web, line_w(2, "#F4F1EA", 0.6))
    elif n == 2:  # claw scratches + feeding hatch
        for k in range(4):
            c.drawLine(x + 60 + k * 16, y + 300, x + 90 + k * 16, y + 400, line_w(5, "#2E1E10", 0.8))
        shape(c, rect(x + 95, y + 470, 100, 60, 6), "#4A3018")



def draw_chamber(c, w, h):
    vgrad(c, (0, 0, w, FLOOR_Y), "#B88A4A", "#9A6E36")
    for x in range(0, w, 180):  # stone blocks
        for y in range(0, FLOOR_Y, 120):
            c.drawRect(skia.Rect.MakeXYWH(x + ((y // 120) % 2) * 90, y, 180, 120), line_w(3, INK, 0.35))
    hieroglyphs(c, 0, 120, w, 330, 7, 0.5)
    for n, (x, y) in DOORS.items():
        draw_door(c, n, x, y)
    # floor
    shape(c, poly([(0, FLOOR_Y), (w, FLOOR_Y), (w, h), (0, h)]), SAND, shade=SAND_SH, sdy=0, sdx=0)
    for k in range(0, w + 300, 200):
        c.drawLine(k, FLOOR_Y, k - 220, h, line_w(3, INK, 0.3))
    x, y = DOORS[3]  # thin trickle of water seeping under door 3 + wet stain on the sand
    shape(c, smooth_path([(x + 30, FLOOR_Y + 2), (x + DOOR_W - 30, FLOOR_Y + 2), (x + DOOR_W - 10, FLOOR_Y + 26),
                          (x + DOOR_W / 2 + 20, FLOOR_Y + 40), (x + 20, FLOOR_Y + 22)]), "#8AA6B8", ow=2.5)
    c.drawPath(smooth_path([(x + 60, FLOOR_Y + 8), (x + DOOR_W / 2, FLOOR_Y + 18), (x + DOOR_W - 60, FLOOR_Y + 8)],
                           closed=False), line_w(3, "#FFFFFF", 0.6))
    # sarcophagus (the mummy's bed) left, meat cart right, cat-sized hole low on the right wall
    shape(c, rect(-60, 1240, 300, 520, 60), "#C9A24A", shade="#A8842E", sdx=20)
    shape(c, oval(90, 1360, 70, 80), "#E8B86A")  # golden face mask
    shape(c, poly([(20, 1300), (160, 1300), (190, 1460), (-10, 1460)]), "#2E6A9A", ow=3.5)  # striped headdress
    shape(c, oval(90, 1365, 55, 62), "#E8B86A", ow=3)
    for dx in (-22, 22):
        c.drawPath(oval(90 + dx, 1352, 10, 6), P(INK))
    for k in range(4):
        c.drawLine(10, 1500 + k * 50, 220, 1500 + k * 50, line_w(6, "#2E6A9A"))
    shape(c, rect(830, 1480, 220, 120, 12), "#7A5428")
    for k, col in enumerate(("#B5352E", "#C9503A", "#B5352E")):
        shape(c, oval(880 + k * 55, 1470, 32, 22), col, ow=3)
    for wx in (860, 1020):
        shape(c, oval(wx, 1610, 26, 26), "#3A2418", ow=3)
    shape(c, rect(1000, 1110, 70, 60, 30), "#1A1008")  # where the cat squeezed out


@lru_cache(maxsize=None)
def img(name):
    fns = {"corridor": draw_corridor, "chamber": draw_chamber}
    if name.endswith("_blur"):
        return snapshot(fns[name[:-5]], blur=16)
    return snapshot(fns[name])


def torch(c, x, y, t, s=1.0, i=0):
    """Wall torch: bracket + flickering flame + warm glow."""
    f = 0.85 + 0.15 * math.sin(t * 15 + i) * math.sin(t * 6.1 + 2 * i)
    radial(c, x, y - 40 * s, 520 * s * f, "#FFAA40", 0.28, plus=True)
    shape(c, poly([(x - 18 * s, y), (x + 18 * s, y), (x + 10 * s, y + 90 * s), (x - 10 * s, y + 90 * s)]), "#5A3A1E", ow=3)
    fl = smooth_path([(x, y - 100 * s * f), (x + 30 * s, y - 30 * s), (x + 16 * s, y), (x - 16 * s, y), (x - 30 * s, y - 30 * s)])
    c.drawPath(fl, P("#FF8A2A"))
    c.drawPath(smooth_path([(x, y - 60 * s * f), (x + 14 * s, y - 20 * s), (x, y - 4 * s), (x - 14 * s, y - 20 * s)]), P("#FFE07A"))
    c.drawPath(fl, line_w(3, "#B8501E"))


CHAMBER_TORCHES = [(36, 820), (1046, 820), (372, 420), (717, 420)]


def lion_eyes(c, x, y, s, t, on):
    """Glowing eyes in the feeding hatch."""
    if on <= 0:
        return
    shape(c, rect(x - 50 * s, y - 30 * s, 100 * s, 60 * s, 6), "#0A0604", ow=3)
    for dx in (-22, 22):
        radial(c, x + dx * s, y, 30 * s, "#FFD040", 0.8 * on, plus=True)
        c.drawPath(oval(x + dx * s, y, 12 * s, 9 * s * (0.3 + 0.7 * on)), P("#FFE070", on))
        c.drawPath(oval(x + dx * s, y, 3 * s, 8 * s * on), P(INK, on))


def scarab(c, x, y, s=1.0):
    shape(c, oval(x, y, 22 * s, 16 * s), "#E8B83A", ow=3)
    c.drawLine(x, y - 16 * s, x, y + 16 * s, line_w(2.5))


# ================================================================ Mr. Whiskers, cleaner design (sitting + running)
ORANGE, ORANGE_SH, CREAM, PINK = "#F0A040", "#D4832A", "#FBE7C6", "#F08A9A"


def _cat_face(c, x, hy, k, look=0.0, smug=1.0, blink_=0.0, mouth="w"):
    """Cat head centred at (x, hy), size factor k (1.0 = head radius 80px)."""
    for sx in (-1, 1):  # ears with pink inner
        ear = poly([(x + sx * 72 * k, hy - 30 * k), (x + sx * 64 * k, hy - 112 * k), (x + sx * 18 * k, hy - 66 * k)])
        shape(c, ear, ORANGE, ow=4)
        c.drawPath(poly([(x + sx * 60 * k, hy - 44 * k), (x + sx * 58 * k, hy - 92 * k), (x + sx * 30 * k, hy - 64 * k)]),
                   P(PINK))
    head = smooth_path([(x, hy - 76 * k), (x + 66 * k, hy - 52 * k), (x + 92 * k, hy + 6 * k), (x + 70 * k, hy + 58 * k),
                        (x, hy + 72 * k), (x - 70 * k, hy + 58 * k), (x - 92 * k, hy + 6 * k), (x - 66 * k, hy - 52 * k)])
    shape(c, head, ORANGE, shade=ORANGE_SH, sdx=10 * k, ow=4)
    for dx in (-16, 0, 16):  # forehead stripes
        c.drawLine(x + dx * k, hy - 72 * k, x + dx * 0.8 * k, hy - 48 * k, line_w(6 * k, ORANGE_SH))
    shape(c, smooth_path([(x - 44 * k, hy + 24 * k), (x, hy + 8 * k), (x + 44 * k, hy + 24 * k), (x + 30 * k, hy + 60 * k),
                          (x, hy + 68 * k), (x - 30 * k, hy + 60 * k)]), CREAM, ow=0.01)  # white muzzle
    for sx in (-1, 1):  # almond eyes, slit pupils, smug lids
        ex, ey = x + sx * 34 * k, hy - 6 * k
        eye = smooth_path([(ex - 20 * k, ey), (ex, ey - 15 * k), (ex + 20 * k, ey), (ex, ey + 15 * k)])
        c.drawPath(eye, P("#C8E870"))
        c.save()
        c.clipPath(eye, doAntiAlias=True)
        c.drawPath(oval(ex + look * 7 * k, ey, 4 * k, 12 * k), P(INK))
        lid = max(0.45 * smug, blink_)
        if lid > 0.02:
            c.drawRect(skia.Rect(ex - 22 * k, ey - 16 * k, ex + 22 * k, ey - 16 * k + 32 * k * lid), P(ORANGE))
        c.restore()
        c.drawPath(eye, line_w(3.5))
        if lid > 0.02:
            c.drawLine(ex - 19 * k, ey - 16 * k + 32 * k * lid, ex + 19 * k, ey - 16 * k + 32 * k * lid, line_w(3.5))
    shape(c, poly([(x - 9 * k, hy + 16 * k), (x + 9 * k, hy + 16 * k), (x, hy + 27 * k)]), PINK, ow=2.5)  # nose
    if mouth == "w":
        sm = skia.Path()
        sm.moveTo(x - 18 * k, hy + 34 * k)
        sm.quadTo(x - 8 * k, hy + 44 * k, x, hy + 30 * k)
        sm.quadTo(x + 8 * k, hy + 44 * k, x + 18 * k, hy + 34 * k)
        c.drawPath(sm, line_w(3))
    for sy in (-1, 0, 1):  # whiskers
        for sx in (-1, 1):
            c.drawLine(x + sx * 46 * k, hy + (28 + sy * 7) * k, x + sx * 112 * k, hy + (22 + sy * 16) * k, line_w(2.5))


def cat(c, x, y, s, t, smug=1.0, look=0.0):
    """Mr. Whiskers sitting (x, y = bottom centre), s = height px."""
    k = s / 300
    tail = skia.Path()
    tail.moveTo(x + 70 * k, y - 16 * k)
    tail.cubicTo(x + 170 * k, y - 10 * k, x + 170 * k, y - 120 * k + 16 * k * math.sin(t * 3),
                 x + 125 * k, y - 160 * k)
    c.drawPath(tail, line_w(30 * k, INK))
    c.drawPath(tail, line_w(22 * k, ORANGE))
    body = smooth_path([(x - 92 * k, y), (x - 100 * k, y - 110 * k), (x - 52 * k, y - 178 * k), (x + 52 * k, y - 178 * k),
                        (x + 100 * k, y - 110 * k), (x + 92 * k, y)])
    shape(c, body, ORANGE, shade=ORANGE_SH, sdx=14 * k, ow=4)
    shape(c, smooth_path([(x - 40 * k, y - 10 * k), (x - 46 * k, y - 110 * k), (x, y - 150 * k), (x + 46 * k, y - 110 * k),
                          (x + 40 * k, y - 10 * k)]), CREAM, ow=3)  # belly patch
    for sx in (-1, 1):  # front paws
        shape(c, oval(x + sx * 34 * k, y - 10 * k, 30 * k, 16 * k), CREAM, ow=3.5)
    _cat_face(c, x, y - 232 * k, k, look, smug, blink_=0.0)


def cat_run(c, x, y, s, t, facing=1, scarab_in_mouth=True):
    """Side-view galloping cat (x, y = ground under the body centre), s = body length px, facing +1 = right."""
    k = s / 300
    ph = t * 9.0  # gallop speed
    c.save()
    c.translate(x, y)
    c.scale(facing, 1)
    stretch = 1 + 0.08 * math.sin(ph * 2)
    bob = -12 * k * abs(math.sin(ph))
    # tail streaming behind
    tail = skia.Path()
    tail.moveTo(-120 * k, -120 * k + bob)
    tail.cubicTo(-200 * k, -150 * k + bob, -240 * k, -110 * k + 14 * k * math.sin(ph * 1.5), -280 * k, -150 * k)
    c.drawPath(tail, line_w(26 * k, INK))
    c.drawPath(tail, line_w(18 * k, ORANGE))
    # legs: back pair and front pair, alternating reach (gallop)
    for (bx, phase, far) in ((-90, 0.0, 1), (-70, 0.5, 0), (90, 3.14, 1), (110, 3.64, 0)):
        a = math.sin(ph + phase)
        lx0, ly0 = bx * k * stretch, -70 * k + bob
        lx1, ly1 = lx0 + 46 * k * a, -6 * k - max(0.0, -a) * 30 * k
        col = ORANGE_SH if far else ORANGE
        c.drawLine(lx0, ly0, lx1, ly1, line_w(30 * k, INK))
        c.drawLine(lx0, ly0, lx1, ly1, line_w(22 * k, col))
        shape(c, oval(lx1 + 6 * k, ly1, 18 * k, 11 * k), CREAM, ow=3)
    body = smooth_path([(-140 * k * stretch, -110 * k + bob), (-60 * k, -150 * k + bob), (80 * k, -145 * k + bob),
                        (150 * k * stretch, -110 * k + bob), (120 * k, -60 * k + bob), (-120 * k, -60 * k + bob)])
    shape(c, body, ORANGE, shade=ORANGE_SH, sdx=0, sdy=10 * k, ow=4)
    for dx in (-60, -20, 20):  # back stripes
        c.drawLine(dx * k, -150 * k + bob, (dx + 10) * k, -118 * k + bob, line_w(8 * k, ORANGE_SH))
    # head (3/4 toward the direction of travel) with the golden scarab in its mouth
    hx, hy = 175 * k * stretch, -170 * k + bob
    c.save()
    c.translate(hx, hy)
    c.scale(0.85, 0.85)
    _cat_face(c, 0, 0, k, look=0.8, smug=0.6, mouth="none")
    c.restore()
    if scarab_in_mouth:  # golden scarab held in the teeth, in front of the muzzle
        radial(c, hx + 8 * k, hy + 52 * k, 70 * k, "#FFE070", 0.45, plus=True)
        shape(c, oval(hx + 8 * k, hy + 52 * k, 30 * k, 21 * k), "#E8B83A", ow=3)
        c.drawLine(hx + 8 * k, hy + 32 * k, hx + 8 * k, hy + 72 * k, line_w(3))
    c.restore()


def door_closeup(c, n, t, cx=540):
    """One door, centred, on its own wall section (same framing for all three doors)."""
    vgrad(c, (0, 0, W, H), "#B88A4A", "#9A6E36")
    for x in range(-90, W, 180):
        for y in range(0, 1500, 120):
            c.drawRect(skia.Rect.MakeXYWH(x + ((y // 120) % 2) * 90, y, 180, 120), line_w(3, INK, 0.35))
    hieroglyphs(c, 0, 60, W, 230, 11 + n, 0.5)
    c.save()
    k = 1.6
    c.translate(cx, 1500)
    c.scale(k, k)
    c.translate(-(DOOR_W / 2), -DOOR_H)  # door bottom sits on the floor line
    draw_door(c, n, 0, 0)
    c.restore()
    shape(c, poly([(0, 1500), (W, 1500), (W, H), (0, H)]), SAND, shade=SAND_SH, sdy=0, sdx=0)
    for kx in range(0, W + 300, 200):
        c.drawLine(kx, 1500, kx - 220, H, line_w(3, INK, 0.3))
    if n == 3:  # water seeping under door 3 (scaled with the door)
        x0 = cx - DOOR_W / 2 * k
        shape(c, smooth_path([(x0 + 40, 1502), (x0 + DOOR_W * k - 40, 1502), (x0 + DOOR_W * k - 10, 1540),
                              (cx + 30, 1560), (x0 + 30, 1536)]), "#8AA6B8", ow=2.5)
        c.drawPath(smooth_path([(x0 + 90, 1512), (cx, 1528), (x0 + DOOR_W * k - 90, 1512)], closed=False),
                   line_w(3, "#FFFFFF", 0.6))
    for i, x in enumerate((cx - 330, cx + 330)):
        torch(c, x, 760, t, 1.0, i + n)
