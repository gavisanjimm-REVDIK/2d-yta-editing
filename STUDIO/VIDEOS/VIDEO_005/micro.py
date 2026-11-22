"""micro.py - VIDEO_005 protist drawing library (storybook outline style, animated by t).

Every organism: fn(c, x, y, s, t, **kw) draws centred at (x, y); s = scale (1.0 ~ 300 px body).
They return a dict of named anchor points (for callout labels).
"""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("v001_sets", HERE.parent / "VIDEO_001" / "sets.py")
base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(base)

INK = base.INK
P, shape, rect, poly, radial, line_w = base.P, base.shape, base.rect, base.poly, base.radial, base.line_w
smooth_path, oval = base.smooth_path, base.oval


def wavy(c, x0, y0, ang, length, s, t, amp=14, waves=2.0, speed=8.0, width=5, color=INK, phase=0.0):
    """Beating flagellum from (x0, y0) along angle ang (rad)."""
    p = skia.Path()
    n = 24
    ca, sa = math.cos(ang), math.sin(ang)
    for i in range(n + 1):
        u = i / n
        d = u * length * s
        off = math.sin(u * waves * math.tau - t * speed + phase) * amp * s * u
        x, y = x0 + ca * d - sa * off, y0 + sa * d + ca * off
        (p.moveTo if i == 0 else p.lineTo)(x, y)
    c.drawPath(p, line_w(width * s + 2.5, INK))
    if color != INK:
        c.drawPath(p, line_w(width * s, color))
    return p


def blob(cx, cy, rx, ry, t, seed=0, wob=0.06, n=10, rot=0.0):
    pts = []
    for i in range(n):
        a = i / n * math.tau + rot
        k = 1 + wob * math.sin(t * 2.0 + i * 1.7 + seed)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    return smooth_path(pts)


# ================================================================ bacterium (for size comparison)
def bacterium(c, x, y, s, t, **kw):
    wavy(c, x + 60 * s, y, 0.1, 90, s, t, amp=10, width=3)
    shape(c, smooth_path([(x - 60 * s, y - 24 * s), (x + 60 * s, y - 24 * s), (x + 70 * s, y), (x + 60 * s, y + 24 * s),
                          (x - 60 * s, y + 24 * s), (x - 70 * s, y)]), "#8AC86A", shade="#6EA852", sdx=0, sdy=6 * s)
    for k in range(3):
        c.drawCircle(x - 30 * s + k * 30 * s, y, 5 * s, P("#4E8A3A"))
    return {"cell": (x, y - 30 * s)}


# ================================================================ Giardia (diplomonad)
def giardia(c, x, y, s, t, label_nuclei=False, **kw):
    bob = 6 * s * math.sin(t * 3)
    y += bob
    for k, (dx, ang) in enumerate(((-40, 2.3), (40, 0.84), (-60, 1.9), (60, 1.24))):  # 4 pairs of flagella (front/side/back)
        wavy(c, x + dx * s * 0.5, y + 40 * s, ang, 190, s, t, amp=12, width=4, phase=k)
    wavy(c, x - 12 * s, y + 140 * s, 1.7, 160, s, t, amp=10, width=4, phase=1.5)
    wavy(c, x + 12 * s, y + 140 * s, 1.44, 160, s, t, amp=10, width=4, phase=2.5)
    body = smooth_path([(x, y - 150 * s), (x + 110 * s, y - 90 * s), (x + 100 * s, y + 30 * s), (x + 40 * s, y + 130 * s),
                        (x, y + 160 * s), (x - 40 * s, y + 130 * s), (x - 100 * s, y + 30 * s), (x - 110 * s, y - 90 * s)])
    shape(c, body, "#F4B8C8", shade="#E098AC", sdx=14 * s)
    shape(c, oval(x, y - 60 * s, 80 * s, 66 * s), "#F8D0DA", ow=3)  # ventral (sucking) disc
    nuclei = []
    for sx in (-1, 1):  # two identical nuclei: the famous "face"
        nx, ny = x + sx * 38 * s, y - 70 * s
        shape(c, oval(nx, ny, 26 * s, 32 * s), "#7A5AA8", ow=3)
        c.drawCircle(nx + 4 * s, ny - 6 * s, 7 * s, P("#D8C8F0"))
        nuclei.append((nx, ny))
    c.drawLine(x, y - 10 * s, x, y + 120 * s, line_w(4 * s, "#C87890"))  # median bodies / axonemes
    return {"nuclei": nuclei[1], "nucleus_l": nuclei[0], "flagella": (x + 150 * s, y + 10 * s), "body": (x - 100 * s, y + 60 * s),
            "disc": (x, y - 100 * s)}


# ================================================================ generic excavate (feeding groove)
def excavate(c, x, y, s, t, highlight=0.0, **kw):
    wavy(c, x - 30 * s, y - 110 * s, -2.0, 160, s, t, amp=10, width=4)
    wavy(c, x - 10 * s, y + 60 * s, 2.6, 180, s, t, amp=10, width=4, phase=2)
    body = smooth_path([(x - 40 * s, y - 130 * s), (x + 70 * s, y - 120 * s), (x + 120 * s, y - 20 * s), (x + 90 * s, y + 110 * s),
                        (x - 10 * s, y + 140 * s), (x - 90 * s, y + 70 * s), (x - 60 * s, y - 20 * s)])
    shape(c, body, "#A8D8C8", shade="#86B8A6", sdx=14 * s)
    groove = smooth_path([(x - 60 * s, y - 60 * s), (x - 10 * s, y - 40 * s), (x + 10 * s, y + 40 * s), (x - 30 * s, y + 90 * s),
                          (x - 70 * s, y + 40 * s)])
    shape(c, groove, "#5A9A86", ow=3)
    if highlight > 0:
        p = line_w(8 * s, "#FFD23F", highlight)
        c.drawPath(groove, p)
    shape(c, oval(x + 50 * s, y - 30 * s, 26 * s, 26 * s), "#5A8A9A", ow=3)
    return {"groove": (x - 40 * s, y + 20 * s), "cell": (x + 80 * s, y - 80 * s)}


# ================================================================ organelles
def mitochondrion(c, x, y, s, t, **kw):
    body = smooth_path([(x - 120 * s, y), (x - 90 * s, y - 55 * s), (x + 90 * s, y - 55 * s), (x + 120 * s, y), (x + 90 * s, y + 55 * s),
                        (x - 90 * s, y + 55 * s)])
    shape(c, body, "#F0A060", shade="#D08040", sdx=0, sdy=10 * s)
    q = skia.Path()  # cristae
    q.moveTo(x - 95 * s, y)
    for k in range(7):
        xx = x - 80 * s + k * 26 * s
        q.lineTo(xx, y + (-34 if k % 2 else 34) * s)
        q.lineTo(xx + 13 * s, y)
    c.drawPath(q, line_w(5 * s, "#A85A28"))
    return {"cell": (x, y - 60 * s)}


def mitosome(c, x, y, s, t, **kw):
    shape(c, oval(x, y, 34 * s, 22 * s), "#F0B080", ow=3)
    return {"cell": (x, y - 26 * s)}


def hydrogenosome(c, x, y, s, t, bubbles=True, **kw):
    shape(c, oval(x, y, 80 * s, 52 * s), "#E8C070", shade="#C8A050", sdx=0, sdy=8 * s)
    c.drawPath(oval(x, y, 56 * s, 32 * s), line_w(3, "#A88030", 0.7))
    if bubbles:
        r = random.Random(3)
        for k in range(7):
            ph = (t * 0.6 + k / 7) % 1
            bx = x + r.uniform(-60, 60) * s + 10 * s * math.sin(t * 2 + k)
            by = y - 60 * s - ph * 260 * s
            c.drawCircle(bx, by, (8 + 6 * r.random()) * s, P("#BFE4FF", 0.9 * (1 - ph)))
            c.drawCircle(bx, by, (8 + 6 * r.random()) * s, line_w(2.5, INK, 0.7 * (1 - ph)))
    return {"cell": (x, y - 56 * s), "gas": (x + 60 * s, y - 220 * s)}


# ================================================================ Trichomonas (parabasalid)
def trichomonas(c, x, y, s, t, **kw):
    for k in range(4):  # 4 anterior flagella
        wavy(c, x - 20 * s + k * 12 * s, y - 120 * s, -1.9 + k * 0.25, 170, s, t, amp=12, width=4, phase=k)
    wavy(c, x, y + 130 * s, 1.6, 120, s, t, amp=6, width=4)  # axostyle tail
    body = smooth_path([(x, y - 130 * s), (x + 90 * s, y - 70 * s), (x + 80 * s, y + 60 * s), (x + 20 * s, y + 130 * s),
                        (x - 30 * s, y + 120 * s), (x - 90 * s, y + 40 * s), (x - 90 * s, y - 70 * s)])
    shape(c, body, "#C8E0F4", shade="#A6C2DC", sdx=14 * s)
    um = skia.Path()  # undulating membrane rippling along the right side
    for i in range(21):
        u = i / 20
        yy = y - 110 * s + u * 210 * s
        xx = x + (88 - 20 * u) * s + math.sin(u * 3 * math.tau - t * 10) * 14 * s
        (um.moveTo if i == 0 else um.lineTo)(xx, yy)
    c.drawPath(um, line_w(9 * s, "#6A9AC8"))
    c.drawPath(um, line_w(3, INK))
    shape(c, oval(x - 20 * s, y - 50 * s, 30 * s, 36 * s), "#5A7AB8", ow=3)
    for k in range(4):  # hydrogenosomes inside
        shape(c, oval(x - 40 * s + k * 26 * s, y + 40 * s + (k % 2) * 24 * s, 12 * s, 8 * s), "#E8C070", ow=2)
    return {"membrane": (x + 100 * s, y), "flagella": (x - 30 * s, y - 230 * s), "hydro": (x - 20 * s, y + 60 * s)}


# ================================================================ Euglena (euglenoid)
def euglena(c, x, y, s, t, light=1.0, ang=0.0, **kw):
    c.save()
    c.translate(x, y)
    c.rotate(math.degrees(ang))
    wavy(c, 0, -150 * s, -1.57, 220, s, t, amp=18, width=5, speed=10)
    body = blob(0, 0, 70 * s, 160 * s, t * 1.5, 3, 0.05)
    shape(c, body, "#C8E8A0" if light > 0.5 else "#D8DCC0", shade="#A8C880", sdx=12 * s)
    k = 0.4 + 0.6 * light  # chloroplasts shrink in the dark
    r = random.Random(1)
    for i in range(9):
        cx, cy = r.uniform(-40, 40) * s, r.uniform(-100, 110) * s
        col = "#3E9A3A" if light > 0.5 else "#7A9A60"
        shape(c, oval(cx, cy, 16 * s * k, 9 * s * k), col, ow=2)
    shape(c, oval(0, 10 * s, 28 * s, 34 * s), "#9A7AC8", ow=3)  # nucleus
    shape(c, oval(18 * s, -118 * s, 12 * s, 10 * s), "#E8382E", ow=2.5)  # eyespot
    c.restore()

    def rot(px, py):
        ca, sa = math.cos(ang), math.sin(ang)
        return x + px * ca - py * sa, y + px * sa + py * ca
    return {"eyespot": rot(18 * s, -118 * s), "flagella": rot(0, -330 * s), "chloro": rot(-40 * s, 60 * s),
            "nucleus": rot(0, 10 * s)}


# ================================================================ Trypanosoma (kinetoplastid)
def trypanosome(c, x, y, s, t, **kw):
    pts_top, pts_bot = [], []
    for i in range(21):
        u = i / 20
        cx = x - 220 * s + u * 440 * s
        cy = y + math.sin(u * 2.2 * math.pi - t * 6) * 40 * s
        w_ = (34 * math.sin(math.pi * min(1, u * 1.1))) * s + 3 * s
        pts_top.append((cx, cy - w_))
        pts_bot.append((cx, cy + w_))
    body = smooth_path(pts_top + pts_bot[::-1])
    shape(c, body, "#E8B0D8", shade="#C890B8", sdx=0, sdy=8 * s)
    fin = skia.Path()  # undulating membrane along the top
    for i, (px, py) in enumerate(pts_top[2:]):
        (fin.moveTo if i == 0 else fin.lineTo)(px, py - 6 * s - 6 * s * math.sin(i * 1.3 - t * 10))
    c.drawPath(fin, line_w(4, INK))
    wavy(c, pts_top[-1][0], (pts_top[-1][1] + pts_bot[-1][1]) / 2, 0.0, 80, s, t, amp=10, width=4)
    mid = pts_top[10]
    shape(c, oval(mid[0], mid[1] + 34 * s, 24 * s, 22 * s), "#8A5AB8", ow=3)  # nucleus
    kp = pts_top[4]
    shape(c, oval(kp[0], kp[1] + 30 * s, 28 * s, 16 * s), "#F0A060", ow=3)  # the one big mitochondrion
    c.drawCircle(kp[0], kp[1] + 30 * s, 9 * s, P("#3A2A8A"))  # kinetoplast (DNA mass)
    return {"kinetoplast": (kp[0], kp[1] + 30 * s), "nucleus": (mid[0], mid[1] + 34 * s), "body": (x + 200 * s, y)}


# ================================================================ SAR signatures
def hairy_flagellate(c, x, y, s, t, **kw):
    """Stramenopile cell: one long hairy flagellum forward, one smooth trailing."""
    p = wavy(c, x, y - 90 * s, -1.57, 260, s, t, amp=14, width=5, speed=7)
    meas = skia.PathMeasure(p, False)
    L = meas.getLength()
    for k in range(1, 26):  # tripartite hairs (mastigonemes)
        pos, tan = meas.getPosTan(L * k / 27)
        nx, ny = -tan.y(), tan.x()
        for sd in (-1, 1):
            c.drawLine(pos.x(), pos.y(), pos.x() + nx * sd * 22 * s, pos.y() + ny * sd * 22 * s, line_w(2.5, "#3A6A9A"))
    wavy(c, x + 20 * s, y + 70 * s, 1.2, 180, s, t, amp=10, width=4, phase=1)
    shape(c, blob(x, y, 80 * s, 95 * s, t, 5, 0.04), "#F0D070", shade="#D0B050", sdx=12 * s)
    shape(c, oval(x - 10 * s, y + 10 * s, 26 * s, 26 * s), "#8A6AB8", ow=3)
    return {"hairy": (x + 40 * s, y - 250 * s), "smooth": (x + 120 * s, y + 200 * s)}


def alveolate_cell(c, x, y, s, t, **kw):
    shape(c, oval(x, y, 150 * s, 120 * s), "#D8C8F0", shade="#BAA8D8", sdx=14 * s)
    for k in range(18):  # alveoli just under the membrane
        a = k / 18 * math.tau
        shape(c, oval(x + math.cos(a) * 128 * s, y + math.sin(a) * 100 * s, 16 * s, 11 * s), "#F4ECFF", ow=2)
    shape(c, oval(x, y, 34 * s, 34 * s), "#8A6AB8", ow=3)
    return {"alveoli": (x + 128 * s, y - 40 * s)}


def rhizarian(c, x, y, s, t, **kw):
    r = random.Random(4)
    for k in range(14):  # thread-like (filose) pseudopodia
        a = k / 14 * math.tau + 0.1 * math.sin(t + k)
        L = r.uniform(160, 260) * s
        p = skia.Path()
        p.moveTo(x + math.cos(a) * 90 * s, y + math.sin(a) * 90 * s)
        p.quadTo(x + math.cos(a + 0.15) * L * 0.6, y + math.sin(a + 0.15) * L * 0.6, x + math.cos(a) * L, y + math.sin(a) * L)
        c.drawPath(p, line_w(3.5, "#7A5A3A"))
    shape(c, blob(x, y, 100 * s, 92 * s, t, 7, 0.08), "#E8C8A0", shade="#C8A880", sdx=12 * s)
    shape(c, oval(x, y, 30 * s, 30 * s), "#8A6AB8", ow=3)
    return {"pseudo": (x + 200 * s, y - 120 * s)}


# ================================================================ stramenopiles
def diatom(c, x, y, s, t, **kw):
    c.save()
    c.translate(x, y)
    c.rotate(8 * math.sin(t * 0.8))
    shape(c, rect(-150 * s, -60 * s, 300 * s, 120 * s, 40 * s), "#E8D07A", shade="#C8B05A", sdx=0, sdy=10 * s)
    shape(c, rect(-160 * s, -70 * s, 320 * s, 40 * s, 20 * s), "#F4E4A0", ow=3)  # top valve (lid of the glass box)
    for i in range(12):
        for j in range(2):
            c.drawCircle(-130 * s + i * 23 * s, -5 * s + j * 30 * s, 5 * s, P("#B8983A"))
    c.restore()
    return {"cell": (x, y - 70 * s)}


def golden_alga(c, x, y, s, t, **kw):
    wavy(c, x - 20 * s, y - 70 * s, -1.9, 150, s, t, amp=12, width=4)
    wavy(c, x + 20 * s, y - 70 * s, -1.2, 110, s, t, amp=8, width=4, phase=2)
    shape(c, oval(x, y, 80 * s, 90 * s), "#F4C040", shade="#D4A020", sdx=10 * s)
    for sx in (-1, 1):
        shape(c, oval(x + sx * 30 * s, y + 10 * s, 18 * s, 34 * s), "#C88A20", ow=2)
    return {"cell": (x, y - 90 * s)}


def kelp(c, x, y, s, t, **kw):
    """Brown alga: holdfast, stipe and wavy leaf blades swaying."""
    sway = math.sin(t * 1.1)
    c.drawLine(x, y + 230 * s, x + 20 * s * sway, y - 160 * s, line_w(18 * s + 4, INK))
    c.drawLine(x, y + 230 * s, x + 20 * s * sway, y - 160 * s, line_w(18 * s, "#7A5A20"))
    for k, (by, side, L) in enumerate(((140, -1, 170), (60, 1, 190), (-30, -1, 180), (-110, 1, 160), (-170, -1, 120))):
        bx = x + 20 * s * sway * (1 - (by + 230) / 460)
        tipx = bx + side * L * s + 25 * s * math.sin(t * 1.4 + k)
        tipy = y + by * s - 70 * s
        blade = smooth_path([(bx, y + by * s), (bx + side * L * 0.5 * s, y + by * s - 60 * s), (tipx, tipy),
                             (bx + side * L * 0.55 * s, y + by * s - 5 * s)])
        shape(c, blade, "#9A7A32" if k % 2 else "#8A6A28", shade="#6A5020", sdx=6 * s)
        c.drawLine(bx, y + by * s, (bx + tipx) / 2, (y + by * s + tipy) / 2 - 10 * s, line_w(2.5, "#5A4214", 0.7))
    shape(c, smooth_path([(x - 50 * s, y + 250 * s), (x - 20 * s, y + 215 * s), (x + 20 * s, y + 215 * s), (x + 50 * s, y + 250 * s)]),
          "#5A4214", ow=3)
    return {"cell": (x, y - 200 * s)}


# ================================================================ alveolates
def dinoflagellate(c, x, y, s, t, spin=1.0, **kw):
    ang = t * 2.4 * spin
    sq = 0.75 + 0.25 * math.cos(ang)
    c.save()
    c.translate(x, y)
    shape(c, smooth_path([(0, -150 * s), (80 * s * sq, -60 * s), (90 * s * sq, 50 * s), (30 * s * sq, 150 * s), (-20 * s * sq, 170 * s),
                          (-90 * s * sq, 50 * s), (-80 * s * sq, -60 * s)]), "#D88A5A", shade="#B86A3A", sdx=12 * s)
    for k in range(-2, 3):  # cellulose plates, sliding as it turns
        xx = (k * 34 + 34 * (ang % 1)) * s * sq
        c.drawLine(xx, -130 * s, xx * 1.1, -20 * s, line_w(3, INK, 0.6))
        c.drawLine(xx, 30 * s, xx * 0.9, 140 * s, line_w(3, INK, 0.6))
    c.drawPath(oval(0, 0, 92 * s * sq, 18 * s), line_w(10 * s, "#8A4A2A"))  # transverse groove (girdle)
    c.drawLine(0, 0, -10 * s, 150 * s, line_w(8 * s, "#8A4A2A"))  # longitudinal groove (sulcus)
    p = skia.Path()  # transverse flagellum wrapping the girdle
    for i in range(41):
        a = i / 40 * math.tau
        rr = 1 + 0.12 * math.sin(a * 8 - t * 14)
        (p.moveTo if i == 0 else p.lineTo)(math.cos(a) * 92 * s * sq * rr, math.sin(a) * 18 * s * rr)
    c.drawPath(p, line_w(4, "#3A2A1A"))
    c.restore()
    wavy(c, x - 10 * s, y + 150 * s, 1.7, 180, s, t, amp=12, width=4)  # trailing flagellum
    return {"plates": (x + 70 * s, y - 100 * s), "groove": (x + 95 * s, y), "flagella": (x - 20 * s, y + 300 * s)}


def sporozoite(c, x, y, s, t, enter=0.0, host=True, **kw):
    if host:  # host cell
        shape(c, oval(x + 160 * s, y, 170 * s, 150 * s), "#F4C8B0", shade="#D8A890", sdx=12 * s)
        shape(c, oval(x + 200 * s, y + 10 * s, 44 * s, 40 * s), "#B87A9A", ow=3)
    dx = -260 * s + 230 * s * enter
    c.save()
    c.translate(x + dx, y)
    c.rotate(-8)
    body = smooth_path([(-130 * s, 10 * s), (-60 * s, -30 * s), (60 * s, -34 * s), (140 * s, -8 * s), (150 * s, 6 * s),
                        (60 * s, 20 * s), (-60 * s, 26 * s)])
    shape(c, body, "#A8C870", shade="#88A850", sdx=0, sdy=8 * s)
    shape(c, poly([(120 * s, -14 * s), (156 * s, 0), (120 * s, 12 * s)]), "#FFD23F", ow=3)  # apical complex
    for k in range(3):
        c.drawLine(100 * s, -6 * s + k * 6 * s, 140 * s, -2 * s + k * 2 * s, line_w(2, INK))
    shape(c, oval(-20 * s, 0, 20 * s, 14 * s), "#6A5AA8", ow=2)
    c.restore()
    return {"apical": (x + dx + 150 * s, y - 20 * s), "host": (x + 220 * s, y - 150 * s)}


def ciliate(c, x, y, s, t, **kw):
    pts = []
    for i in range(36):
        a = i / 36 * math.tau
        pts.append((x + math.cos(a) * 110 * s * (1 + 0.15 * math.cos(2 * a)), y + math.sin(a) * 190 * s))
    body = smooth_path(pts)
    for i, (px, py) in enumerate(pts):  # cilia beat in a metachronal wave
        a = i / 36 * math.tau
        wave = math.sin(i * 0.55 - t * 9)
        L = 34 * s
        ex = px + math.cos(a + 0.6 * wave) * L
        ey = py + math.sin(a + 0.6 * wave) * L
        c.drawLine(px, py, ex, ey, line_w(3.5, INK))
    shape(c, body, "#B8E0E8", shade="#98C0CA", sdx=12 * s)
    shape(c, smooth_path([(x - 40 * s, y - 40 * s), (x + 10 * s, y - 20 * s), (x - 10 * s, y + 40 * s), (x - 50 * s, y + 10 * s)]),
          "#88B8C4", ow=3)  # oral groove
    shape(c, oval(x + 30 * s, y + 40 * s, 40 * s, 56 * s), "#8A6AB8", ow=3)  # macronucleus
    for k in range(2):
        shape(c, oval(x - 30 * s, y - 120 * s + k * 230 * s, 22 * s, 22 * s), "#E8F8FF", ow=2.5)  # contractile vacuoles
    return {"cilia": (x + 140 * s, y - 120 * s), "cell": (x, y - 220 * s)}


# ================================================================ rhizarians
def foram(c, x, y, s, t, **kw):
    r = random.Random(9)
    for k in range(22):  # branching, joining reticulopodia net
        a = k / 22 * math.tau
        L = r.uniform(180, 330) * s
        p = skia.Path()
        p.moveTo(x + math.cos(a) * 100 * s, y + math.sin(a) * 100 * s)
        p.lineTo(x + math.cos(a + 0.05 * math.sin(t + k)) * L, y + math.sin(a) * L)
        c.drawPath(p, line_w(2.5, "#A87A4A", 0.9))
        if k % 2 == 0:
            b = a + 0.28
            c.drawLine(x + math.cos(a) * L * 0.7, y + math.sin(a) * L * 0.7, x + math.cos(b) * L * 0.75, y + math.sin(b) * L * 0.75,
                       line_w(2, "#A87A4A", 0.8))
    for k in range(7, 0, -1):  # spiral chambered shell
        a = k * 0.9
        rr = 18 * s + k * 12 * s
        shape(c, oval(x + math.cos(a) * k * 8 * s, y + math.sin(a) * k * 8 * s, rr, rr * 0.9), "#F0E2C0", shade="#D4C29C",
              sdx=4 * s, ow=3)
    return {"net": (x + 260 * s, y - 150 * s), "shell": (x, y - 110 * s)}


def radiolarian(c, x, y, s, t, **kw):
    c.save()
    c.translate(x, y)
    c.rotate(t * 6)
    for k in range(16):
        a = k / 16 * math.tau
        c.drawLine(math.cos(a) * 80 * s, math.sin(a) * 80 * s, math.cos(a) * 230 * s, math.sin(a) * 230 * s, line_w(5, "#7AA8C8"))
        c.drawLine(math.cos(a) * 80 * s, math.sin(a) * 80 * s, math.cos(a) * 230 * s, math.sin(a) * 230 * s, line_w(2, "#E8F4FF"))
    shape(c, oval(0, 0, 100 * s, 100 * s), "#D8ECF8", shade="#B8D0E0", sdx=10 * s)
    for k in range(10):
        a = k / 10 * math.tau
        c.drawPath(oval(math.cos(a) * 60 * s, math.sin(a) * 60 * s, 16 * s, 16 * s), line_w(3, "#7AA8C8"))
    c.restore()
    return {"cell": (x, y - 230 * s)}


# ================================================================ insects + people icons (life cycles)
def insect(c, x, y, s, t, kind="tsetse", **kw):
    flap = math.sin(t * 30)
    body_col = "#8A6A4A" if kind == "tsetse" else "#5A5A6A"
    for sd in (-1, 1):
        shape(c, oval(x - 10 * s, y - 40 * s - 10 * s * flap, 70 * s, 26 * s), "#DDEEFF", ow=3)
    shape(c, oval(x + 10 * s, y, 90 * s, 30 * s), body_col, shade="#5A4228", sdx=0, sdy=6 * s)
    for k in range(4 if kind == "tsetse" else 6):
        c.drawLine(x - 40 * s + k * 24 * s, y + 20 * s, x - 50 * s + k * 26 * s, y + 70 * s, line_w(3))
    shape(c, oval(x + 100 * s, y - 4 * s, 30 * s, 26 * s), body_col, ow=3)
    shape(c, oval(x + 108 * s, y - 12 * s, 14 * s, 14 * s), "#C83A3A", ow=2)
    c.drawLine(x + 125 * s, y + 6 * s, x + 175 * s, y + 20 * s, line_w(4))  # proboscis
    if kind == "tsetse":
        for k in range(3):
            c.drawLine(x - 30 * s + k * 30 * s, y - 25 * s, x - 30 * s + k * 30 * s, y + 25 * s, line_w(3, "#3A2A1A", 0.6))
    return {"gut": (x, y), "glands": (x + 100 * s, y - 20 * s)}


def tide(c, x0, y0, w, h, t, red=0.0):
    """Sea patch that turns red (harmful algal bloom)."""
    col = (int(46 + (180 - 46) * red), int(106 - 60 * red), int(154 - 110 * red))
    c.drawRect(skia.Rect.MakeXYWH(x0, y0, w, h), skia.Paint(Color=skia.Color(*col)))
    for k in range(6):
        p = skia.Path()
        yy = y0 + 40 + k * h / 6
        p.moveTo(x0, yy)
        for i in range(1, 13):
            p.quadTo(x0 + (i - 0.5) * w / 12, yy - 14 + 6 * math.sin(t * 2 + k), x0 + i * w / 12, yy)
        c.drawPath(p, line_w(4, "#FFFFFF", 0.4))
    r = random.Random(2)
    for k in range(int(70 * red)):
        cx, cy = x0 + r.uniform(0, w), y0 + r.uniform(0, h)
        c.drawCircle(cx + 6 * math.sin(t + k), cy, r.uniform(4, 9), P("#E8503A", 0.8))


ORGANISMS = {k: v for k, v in globals().items() if callable(v) and not k.startswith("_") and k not in
             ("wavy", "blob", "tide", "smooth_path", "oval", "P", "shape", "rect", "poly", "radial", "line_w")}
