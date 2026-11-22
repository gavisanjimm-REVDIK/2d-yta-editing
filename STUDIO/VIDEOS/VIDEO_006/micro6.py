"""micro6.py - VIDEO_006 drawings: new organisms + case props. Reuses VIDEO_005's micro.py library.
Same contract: fn(c, x, y, s, t, **kw) -> dict of anchor points."""
from __future__ import annotations

import importlib.util
import math
import random
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("micro5", HERE.parent / "VIDEO_005" / "micro.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

INK = M.INK
P, shape, rect, poly, radial, line_w = M.P, M.shape, M.rect, M.poly, M.radial, M.line_w
smooth_path, oval, wavy, blob = M.smooth_path, M.oval, M.wavy, M.blob


# ================================================================ Archaeplastida
def cyanobacterium(c, x, y, s, t, **kw):
    shape(c, smooth_path([(x - 70 * s, y - 28 * s), (x + 70 * s, y - 28 * s), (x + 82 * s, y), (x + 70 * s, y + 28 * s),
                          (x - 70 * s, y + 28 * s), (x - 82 * s, y)]), "#4AB8A8", shade="#329888", sdx=0, sdy=6 * s)
    for k in range(4):  # thylakoid membranes
        c.drawLine(x - 55 * s, y - 12 * s + k * 8 * s, x + 55 * s, y - 12 * s + k * 8 * s, line_w(2.5, "#1E7A6A"))
    return {"cell": (x, y - 30 * s)}


def glaucophyte(c, x, y, s, t, **kw):
    """Cyanophora paradoxa: bean-shaped cell, 2 flagella, blue-green cyanelles."""
    wavy(c, x - 20 * s, y - 40 * s, -2.6, 220, s, t, amp=14, width=4)
    wavy(c, x - 10 * s, y + 20 * s, 2.8, 260, s, t, amp=12, width=4, phase=2)
    body = smooth_path([(x - 110 * s, y - 20 * s), (x - 60 * s, y - 100 * s), (x + 60 * s, y - 110 * s), (x + 130 * s, y - 30 * s),
                        (x + 110 * s, y + 70 * s), (x + 20 * s, y + 110 * s), (x - 80 * s, y + 70 * s), (x - 60 * s, y + 10 * s)])
    shape(c, body, "#E4F0E8", shade="#C4D8CC", sdx=12 * s)
    shape(c, oval(x + 20 * s, y + 10 * s, 34 * s, 30 * s), "#9A7AC8", ow=3)
    for cx_, cy_ in ((x + 70 * s, y - 50 * s), (x - 10 * s, y - 60 * s), (x + 80 * s, y + 40 * s)):  # cyanelles
        shape(c, oval(cx_, cy_, 30 * s, 26 * s), "#3A9AB0", ow=3)
        for k in range(3):
            c.drawPath(oval(cx_, cy_, (24 - 7 * k) * s, (20 - 6 * k) * s), line_w(2, "#1E6A80", 0.8))
    return {"cyanelles": (x + 70 * s, y - 50 * s), "nucleus": (x + 20 * s, y + 10 * s), "flagella": (x - 220 * s, y + 80 * s)}


def red_alga(c, x, y, s, t, depth=0.0, **kw):
    """Branching filamentous red seaweed; darker with depth (0 shallow pink .. 1 almost black)."""
    def mix(a, b, u):
        a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
        return "#" + "".join(f"{int(a[i] + (b[i] - a[i]) * u):02x}" for i in range(3))
    col = mix("#E86A7A", "#3A0E1A", depth)
    sh = mix("#C84A5A", "#1E0610", depth)

    def branch(x0, y0, ang, L, depth_k, seed):
        if depth_k == 0 or L < 20 * s:
            return
        sway = 0.08 * math.sin(t * 1.3 + seed)
        x1, y1 = x0 + math.cos(ang + sway) * L, y0 + math.sin(ang + sway) * L
        c.drawLine(x0, y0, x1, y1, line_w(depth_k * 5 * s + 5, INK))
        c.drawLine(x0, y0, x1, y1, line_w(depth_k * 5 * s + 1, col))
        branch(x1, y1, ang - 0.5, L * 0.7, depth_k - 1, seed * 2 + 1)
        branch(x1, y1, ang + 0.45, L * 0.68, depth_k - 1, seed * 2 + 2)
    if kw.get("bushy"):
        for k, a in enumerate((-2.1, -1.57, -1.05)):
            branch(x, y + 200 * s, a, 120 * s, 5, k + 3)
    else:
        branch(x, y + 200 * s, -math.pi / 2, 150 * s, 5, 1)
    shape(c, oval(x, y + 205 * s, 40 * s, 16 * s), sh, ow=3)
    return {"cell": (x + 20 * s, y - 100 * s)}


def chlamydomonas(c, x, y, s, t, **kw):
    wavy(c, x - 14 * s, y - 100 * s, -2.0, 200, s, t, amp=16, width=4, speed=10)
    wavy(c, x + 14 * s, y - 100 * s, -1.15, 200, s, t, amp=16, width=4, speed=10, phase=math.pi)
    shape(c, oval(x, y, 90 * s, 105 * s), "#DCF0C8", shade="#BCD8A8", sdx=10 * s)
    cup = smooth_path([(x - 80 * s, y - 30 * s), (x - 70 * s, y + 60 * s), (x, y + 95 * s), (x + 70 * s, y + 60 * s), (x + 80 * s, y - 30 * s),
                       (x + 50 * s, y - 10 * s), (x + 40 * s, y + 50 * s), (x, y + 62 * s), (x - 40 * s, y + 50 * s), (x - 50 * s, y - 10 * s)])
    shape(c, cup, "#4AA83A", ow=3)  # cup-shaped chloroplast
    shape(c, oval(x, y + 70 * s, 18 * s, 14 * s), "#2E7A24", ow=2)  # pyrenoid
    shape(c, oval(x, y - 20 * s, 26 * s, 26 * s), "#9A7AC8", ow=3)
    shape(c, oval(x + 62 * s, y - 40 * s, 11 * s, 9 * s), "#E8382E", ow=2)  # eyespot
    return {"cell": (x + 80 * s, y - 60 * s), "chloro": (x - 60 * s, y + 50 * s), "flagella": (x - 120 * s, y - 260 * s)}


def volvox(c, x, y, s, t, **kw):
    c.save()
    c.translate(x, y)
    c.rotate(t * 12)
    shape(c, oval(0, 0, 220 * s, 220 * s), "#E4F4D0", shade="#C8E0B0", sdx=14 * s)
    r = random.Random(3)
    for k in range(90):
        a, d = r.uniform(0, math.tau), r.uniform(0.85, 0.98) * 215 * s
        c.drawCircle(math.cos(a) * d, math.sin(a) * d, 6 * s, P("#3E9A30"))
    for cx_, cy_, rr in ((-60, -40, 60), (70, 30, 55), (-10, 90, 45)):  # daughter colonies
        shape(c, oval(cx_ * s, cy_ * s, rr * s, rr * s), "#8AC86A", ow=3)
        for k in range(10):
            a = k / 10 * math.tau
            c.drawCircle(cx_ * s + math.cos(a) * rr * 0.8 * s, cy_ * s + math.sin(a) * rr * 0.8 * s, 4 * s, P("#2E7A24"))
    c.restore()
    return {"cell": (x, y - 220 * s)}


def ulva(c, x, y, s, t, **kw):
    pts = []
    for i in range(14):
        a = i / 14 * math.tau
        rr = (1 + 0.15 * math.sin(a * 5 + t * 1.5)) * 170 * s
        pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr * 1.2))
    shape(c, smooth_path(pts), "#6AC84A", shade="#4AA82E", sdx=12 * s)
    for k in range(5):
        a = -1.2 + k * 0.6
        c.drawLine(x, y + 150 * s, x + math.cos(a) * 140 * s, y + 150 * s - abs(math.sin(a)) * 260 * s, line_w(3, "#3A8A24", 0.7))
    return {"cell": (x, y - 200 * s)}


def caulerpa(c, x, y, s, t, **kw):
    """One giant cell: a creeping stolon with feather-like fronds."""
    c.drawLine(x - 230 * s, y + 130 * s, x + 230 * s, y + 140 * s, line_w(18 * s + 5, INK))
    c.drawLine(x - 230 * s, y + 130 * s, x + 230 * s, y + 140 * s, line_w(18 * s, "#4AA83A"))
    for k in range(4):
        bx = x - 170 * s + k * 115 * s
        sway = 12 * s * math.sin(t * 1.2 + k)
        c.drawLine(bx, y + 132 * s, bx + sway, y - 150 * s, line_w(12 * s + 4, INK))
        c.drawLine(bx, y + 132 * s, bx + sway, y - 150 * s, line_w(12 * s, "#5AB84A"))
        for j in range(9):
            yy = y + 100 * s - j * 28 * s
            for sd in (-1, 1):
                c.drawLine(bx + sway * (j / 9), yy, bx + sway * (j / 9) + sd * 34 * s, yy - 18 * s, line_w(9 * s, "#6AC85A"))
        for k2 in range(3):  # rhizoids
            c.drawLine(bx, y + 140 * s, bx - 20 * s + k2 * 20 * s, y + 190 * s, line_w(3, "#3A6A2A"))
    return {"cell": (x, y - 160 * s)}


# ================================================================ Unikonta
def amoeba(c, x, y, s, t, glyco=False, filose=False, **kw):
    """Lobose amoeba with broad pseudopods (or filose); optional glycocalyx coat."""
    pts = []
    n = 16
    for i in range(n):
        a = i / n * math.tau
        lobe = 1.0 + 0.45 * max(0.0, math.sin(a * 3 + t * 0.9)) ** 2
        pts.append((x + math.cos(a) * 130 * s * lobe, y + math.sin(a) * 110 * s * lobe))
    body = smooth_path(pts)
    if filose:
        for k in range(12):
            a = k / 12 * math.tau
            c.drawLine(x + math.cos(a) * 110 * s, y + math.sin(a) * 95 * s, x + math.cos(a) * 230 * s, y + math.sin(a) * 200 * s,
                       line_w(3.5, "#7A5A3A"))
        body = M.blob(x, y, 110 * s, 95 * s, t, 3, 0.05)
    if glyco:
        g = skia.Path(body)
        c.drawPath(g, line_w(26 * s, "#B8E0F0", 0.8))
    shape(c, body, "#C8D8B8", shade="#A8BC98", sdx=12 * s)
    shape(c, oval(x - 10 * s, y, 32 * s, 32 * s), "#8A6AB8", ow=3)
    if kw.get("prey"):  # bacterium inside a food vacuole (phagocytosis)
        shape(c, oval(x + 60 * s, y + 30 * s, 44 * s, 34 * s), "#E8F4FF", ow=3)
        cyanobacterium(c, x + 60 * s, y + 30 * s, 0.35 * s, t)
    for k in range(4):
        c.drawCircle(x + (40 - 25 * k) * s, y + (30 if k % 2 else -40) * s, 10 * s, P("#E8F4FF"))
        c.drawCircle(x + (40 - 25 * k) * s, y + (30 if k % 2 else -40) * s, 10 * s, line_w(2, INK, 0.6))
    return {"pseudo": (x + 160 * s, y - 60 * s), "cell": (x, y - 120 * s), "coat": (x - 140 * s, y - 80 * s)}


def cyst(c, x, y, s, t, red=False, **kw):
    fill, sh, ring = ("#E86A7A", "#C84A5A", "#A83A4A") if red else ("#A89A6A", "#887A4A", "#6A5A2A")
    shape(c, oval(x, y, 90 * s, 90 * s), fill, shade=sh, sdx=10 * s)
    c.drawPath(oval(x, y, 74 * s, 74 * s), line_w(4, ring))
    shape(c, oval(x, y, 26 * s, 26 * s), "#8A6AB8", ow=3)
    return {"cell": (x, y - 90 * s)}


def slime_mold(c, x, y, s, t, grow=1.0, **kw):
    """Plasmodium: branching yellow vein network spreading (grow 0..1)."""
    r = random.Random(11)

    def vein(x0, y0, ang, L, d):
        if d == 0:
            return
        x1, y1 = x0 + math.cos(ang) * L * grow, y0 + math.sin(ang) * L * grow
        pulse = 1 + 0.15 * math.sin(t * 3 - d)
        c.drawLine(x0, y0, x1, y1, line_w((d * 4 + 6) * s * pulse + 4, "#B8901E"))
        c.drawLine(x0, y0, x1, y1, line_w((d * 4 + 6) * s * pulse, "#F4D03A"))
        for k in range(2):
            vein(x1, y1, ang + r.uniform(-0.8, 0.8), L * r.uniform(0.55, 0.8), d - 1)
    for k in range(5):
        vein(x, y, -math.pi / 2 + (k - 2) * 0.6, 120 * s, 4)
    shape(c, M.blob(x, y, 70 * s, 50 * s, t, 9, 0.1), "#F4C83A", shade="#D4A81A", sdx=8 * s)
    return {"cell": (x, y - 250 * s)}


def choanoflagellate(c, x, y, s, t, current=False, **kw):
    """Single choanoflagellate: egg-shaped cell, collar of microvilli, one flagellum pulling food in."""
    shape(c, oval(x, y + 60 * s, 70 * s, 90 * s), "#F0D8B8", shade="#D0B898", sdx=10 * s)
    shape(c, oval(x, y + 70 * s, 22 * s, 22 * s), "#8A6AB8", ow=3)
    c.drawLine(x, y + 150 * s, x, y + 260 * s, line_w(6 * s + 2))  # stalk
    for k in range(-6, 7):  # collar of microvilli
        c.drawLine(x + k * 8 * s, y - 20 * s, x + k * 15 * s, y - 150 * s, line_w(3, "#7A5A3A"))
    wavy(c, x, y - 20 * s, -1.57, 330, s, t, amp=20, width=5, speed=12)
    if current:  # food particles drawn toward the collar
        r = random.Random(2)
        for k in range(12):
            ph = (t * 0.35 + k / 12) % 1
            sx = r.choice((-1, 1))
            px = x + sx * (260 - 170 * ph) * s + 10 * s * math.sin(k)
            py = y - 330 * s + 200 * ph * s
            c.drawCircle(px, py, 8 * s, P("#8A6A3A", 0.8))
            c.drawLine(px - sx * 22 * s, py - 14 * s, px - sx * 6 * s, py - 4 * s, line_w(2, "#4A7AA8", 0.5))
    return {"collar": (x + 90 * s, y - 130 * s), "flagella": (x + 30 * s, y - 330 * s), "cell": (x + 70 * s, y + 60 * s)}


def choano_colony(c, x, y, s, t, **kw):
    for k in range(8):
        a = k / 8 * math.tau + t * 0.2
        cx_, cy_ = x + math.cos(a) * 130 * s, y + math.sin(a) * 130 * s
        c.save()
        c.translate(cx_, cy_)
        c.rotate(math.degrees(a) + 90)
        choanoflagellate(c, 0, -80 * s * 0.45, s * 0.45, t + k)
        c.restore()
    return {"cell": (x, y - 260 * s)}


def nucleariid(c, x, y, s, t, **kw):
    return amoeba(c, x, y, s, t, filose=True)


def choanocyte_sponge(c, x, y, s, t, **kw):
    """A sponge wall lined with choanocytes (collar cells)."""
    shape(c, rect(x - 260 * s, y + 60 * s, 520 * s, 120 * s, 20 * s), "#E8B870", shade="#C8984A", sdy=10 * s, sdx=0)
    for k in range(5):
        cx_ = x - 200 * s + k * 100 * s
        choanoflagellate(c, cx_, y - 40 * s, 0.5 * s, t + k * 0.3)
    return {"cell": (x, y - 230 * s)}


# ================================================================ case props
def sushi(c, x, y, s, t, **kw):
    for k in range(3):
        cx_ = x - 150 * s + k * 150 * s
        shape(c, oval(cx_, y, 66 * s, 66 * s), "#1E2A1E", ow=4)  # nori wrap
        shape(c, oval(cx_, y, 52 * s, 52 * s), "#F4F1EA", ow=3)
        shape(c, oval(cx_, y, 20 * s, 20 * s), ["#E8704A", "#6AB84A", "#F4D03A"][k], ow=2.5)
    return {"cell": (x - 150 * s, y - 70 * s)}


def oyster(c, x, y, s, t, open_=True, **kw):
    shape(c, smooth_path([(x - 90 * s, y), (x - 40 * s, y - 50 * s), (x + 70 * s, y - 40 * s), (x + 100 * s, y + 10 * s), (x + 40 * s, y + 50 * s),
                          (x - 60 * s, y + 40 * s)]), "#B8B0A0", shade="#988E7C", sdx=8 * s)
    if open_:
        shape(c, oval(x, y, 60 * s, 34 * s), "#E8E2D6", ow=3)
    for k in range(3):
        c.drawPath(oval(x, y, (80 - 18 * k) * s, (44 - 10 * k) * s), line_w(2, INK, 0.4))
    return {"cell": (x, y - 50 * s)}


def puso(c, x, y, s, t, **kw):
    """Hanging rice in a woven coconut-leaf pouch."""
    shape(c, poly([(x, y - 80 * s), (x + 60 * s, y), (x, y + 80 * s), (x - 60 * s, y)]), "#C8D86A", shade="#A8B84A", sdx=8 * s)
    for k in range(-2, 3):
        c.drawLine(x - 50 * s + abs(k) * 10 * s, y + k * 26 * s, x + 50 * s - abs(k) * 10 * s, y + k * 26 * s, line_w(2.5, "#7A8A2A"))
    c.drawLine(x, y - 80 * s, x, y - 140 * s, line_w(4, "#7A8A2A"))
    return {"cell": (x, y - 140 * s)}


def isaw(c, x, y, s, t, **kw):
    c.drawLine(x - 120 * s, y + 20 * s, x + 120 * s, y - 20 * s, line_w(6 * s + 2, "#B89A6A"))  # skewer
    for k in range(5):
        cx_ = x - 80 * s + k * 40 * s
        shape(c, oval(cx_, y + 14 * s - k * 7 * s, 22 * s, 16 * s), "#8A4A2A", shade="#6A3A1A", sdx=4 * s, ow=3)
    return {"cell": (x, y - 40 * s)}


def pitcher(c, x, y, s, t, **kw):
    shape(c, smooth_path([(x - 60 * s, y - 120 * s), (x + 50 * s, y - 120 * s), (x + 70 * s, y + 100 * s), (x - 70 * s, y + 100 * s)]),
          "#D8EEF8", shade="#B8D8E8", sdx=10 * s)
    c.drawRect(skia.Rect(x - 62 * s, y - 40 * s, x + 62 * s, y + 96 * s), P("#A8D8F0", 0.5))
    c.drawPath(oval(x + 90 * s, y - 20 * s, 36 * s, 56 * s), line_w(10 * s, INK))
    return {"cell": (x, y - 120 * s)}


def banga(c, x, y, s, t, smell=1.0, **kw):
    """Earthen jar with a wavy smell line (rotten-egg odour)."""
    shape(c, smooth_path([(x - 60 * s, y - 130 * s), (x + 60 * s, y - 130 * s), (x + 120 * s, y), (x + 80 * s, y + 120 * s),
                          (x - 80 * s, y + 120 * s), (x - 120 * s, y)]), "#B86A3A", shade="#964A22", sdx=12 * s)
    shape(c, rect(x - 70 * s, y - 150 * s, 140 * s, 30 * s, 10 * s), "#A85A2A", ow=3)
    for k in range(3):
        p = skia.Path()
        x0 = x - 40 * s + k * 40 * s
        p.moveTo(x0, y - 170 * s)
        for j in range(1, 7):
            p.lineTo(x0 + 14 * s * math.sin(t * 3 + j + k), y - 170 * s - j * 30 * s)
        c.drawPath(p, line_w(5, "#9AB83A", 0.8 * smell))
    return {"cell": (x, y - 200 * s)}


def blister(c, x, y, s, t, **kw):
    shape(c, rect(x - 110 * s, y - 60 * s, 220 * s, 120 * s, 12 * s), "#D8DCE0", shade="#B8BCC0", sdx=6 * s)
    for i in range(4):
        for j in range(2):
            c.drawPath(oval(x - 75 * s + i * 50 * s, y - 25 * s + j * 50 * s, 18 * s, 18 * s), line_w(3, "#8A8E92"))
    return {"cell": (x, y - 60 * s)}


def house_sea(c, x, y, s, t, **kw):
    """Small house on the shore facing the sea at night (Biliran)."""
    c.drawRect(skia.Rect(x - 520 * s, y - 520 * s, x + 520 * s, y + 80 * s), P("#1A2448"))
    c.drawCircle(x + 330 * s, y - 380 * s, 50 * s, P("#F4EED8"))
    c.drawRect(skia.Rect(x - 520 * s, y + 40 * s, x + 520 * s, y + 300 * s), P("#2E4A78"))
    for k in range(5):
        c.drawLine(x - 500 * s, y + 80 * s + k * 40 * s, x + 500 * s, y + 80 * s + k * 40 * s,
                   line_w(3, "#FFFFFF", 0.2 + 0.1 * math.sin(t * 2 + k)))
    shape(c, rect(x - 260 * s, y - 220 * s, 420 * s, 260 * s, 6 * s), "#C8A87A", shade="#A8885A", sdx=12 * s)
    shape(c, poly([(x - 300 * s, y - 220 * s), (x - 50 * s, y - 380 * s), (x + 200 * s, y - 220 * s)]), "#6A4A2E")
    for wx in (-200, 40):
        shape(c, rect(x + wx * s, y - 160 * s, 90 * s, 80 * s, 4 * s), "#F2C26A")
        radial(c, x + wx * s + 45 * s, y - 120 * s, 120 * s, "#FFC870", 0.35, plus=True)
    shape(c, rect(x - 80 * s, y - 120 * s, 70 * s, 160 * s, 4 * s), "#3A2418")
    for k in range(4):  # stilts
        c.drawLine(x - 240 * s + k * 130 * s, y + 40 * s, x - 240 * s + k * 130 * s, y + 120 * s, line_w(8 * s, "#5A3A22"))
    return {"cell": (x, y - 380 * s)}


def hospital(c, x, y, s, t, **kw):
    """Two hospital beds, patients asleep (stable, unconscious) with a heart monitor."""
    for k, (bx, col) in enumerate(((x - 220 * s, "#6A3A1E"), (x + 220 * s, "#2A1A12"))):
        shape(c, rect(bx - 170 * s, y, 340 * s, 70 * s, 10 * s), "#E8EEF2", ow=4)
        shape(c, rect(bx - 180 * s, y - 120 * s, 30 * s, 260 * s, 6 * s), "#9AA2AA")
        shape(c, oval(bx - 100 * s, y - 20 * s, 60 * s, 30 * s), "#FFFFFF", ow=3)  # pillow
        shape(c, oval(bx - 100 * s, y - 50 * s, 44 * s, 44 * s), "#F0BE96", ow=3)  # head
        c.drawPath(oval(bx - 100 * s, y - 70 * s, 46 * s, 28 * s), P(col))
        for sx in (-1, 1):  # closed eyes
            q = skia.Path()
            q.moveTo(bx - 100 * s + sx * 18 * s - 8 * s, y - 50 * s)
            q.quadTo(bx - 100 * s + sx * 18 * s, y - 44 * s, bx - 100 * s + sx * 18 * s + 8 * s, y - 50 * s)
            c.drawPath(q, line_w(3))
        shape(c, rect(bx - 60 * s, y - 40 * s, 220 * s, 50 * s, 16 * s), "#8AC0E8", ow=3)  # blanket
    shape(c, rect(x - 70 * s, y - 330 * s, 140 * s, 100 * s, 10 * s), "#1E2A2E", ow=4)  # monitor
    p = skia.Path()
    for i in range(41):
        u = i / 40
        ph = (u * 3 - t * 0.8) % 1
        yy = y - 280 * s - (40 * s if 0.45 < ph < 0.5 else (-15 * s if 0.5 < ph < 0.55 else 0))
        (p.moveTo if i == 0 else p.lineTo)(x - 60 * s + u * 120 * s, yy)
    c.drawPath(p, line_w(3, "#4AE86A"))
    return {"cell": (x, y - 330 * s)}


def spirogyra(c, x, y, s, t, **kw):
    """Filamentous green alga: a chain of cells with spiral chloroplasts."""
    c.save()
    c.translate(x, y)
    c.rotate(-20 + 4 * math.sin(t * 0.8))
    for k in range(5):
        cx_ = (-200 + k * 100) * s
        shape(c, rect(cx_ - 48 * s, -34 * s, 96 * s, 68 * s, 10 * s), "#DCF0C8", ow=3)
        q = skia.Path()
        for i in range(25):
            u = i / 24
            (q.moveTo if i == 0 else q.lineTo)(cx_ - 44 * s + 88 * s * u, 26 * s * math.sin(u * math.tau * 1.5))
        c.drawPath(q, line_w(7 * s, "#3E9A30"))
    c.restore()
    return {"cell": (x, y - 60 * s)}


def fish(c, x, y, s, t, **kw):
    sw = 0.15 * math.sin(t * 4)
    shape(c, poly([(x + 90 * s, y), (x + 160 * s, y - 50 * s * (1 + sw)), (x + 160 * s, y + 50 * s * (1 - sw))]), "#E89A3A")
    shape(c, oval(x, y, 110 * s, 60 * s), "#F4B04A", shade="#D4903A", sdx=0, sdy=10 * s)
    c.drawCircle(x - 60 * s, y - 14 * s, 12 * s, P("#FFFFFF"))
    c.drawCircle(x - 62 * s, y - 14 * s, 6 * s, P(INK))
    return {"cell": (x, y - 60 * s)}


def mushroom(c, x, y, s, t, **kw):
    shape(c, rect(x - 30 * s, y - 40 * s, 60 * s, 150 * s, 20 * s), "#F4ECD8", shade="#D8CCB0", sdx=8 * s)
    shape(c, smooth_path([(x - 150 * s, y - 20 * s), (x - 110 * s, y - 120 * s), (x, y - 160 * s), (x + 110 * s, y - 120 * s),
                          (x + 150 * s, y - 20 * s)]), "#C8483A", shade="#A8302A", sdx=10 * s)
    for dx, dy, rr in ((-70, -80, 18), (30, -120, 14), (80, -60, 16), (-10, -60, 10)):
        c.drawCircle(x + dx * s, y + dy * s, rr * s, P("#FFF4E8"))
    return {"cell": (x, y - 160 * s)}


def sprout(c, x, y, s, t, **kw):
    """A tiny early land plant on wet soil."""
    shape(c, oval(x, y + 90 * s, 170 * s, 40 * s), "#7A5A3A", ow=3)
    c.drawLine(x, y + 90 * s, x + 6 * s * math.sin(t), y - 60 * s, line_w(10 * s + 4, INK))
    c.drawLine(x, y + 90 * s, x + 6 * s * math.sin(t), y - 60 * s, line_w(10 * s, "#5AB84A"))
    for sd in (-1, 1):
        shape(c, smooth_path([(x, y - 20 * s), (x + sd * 60 * s, y - 70 * s), (x + sd * 110 * s, y - 40 * s), (x + sd * 60 * s, y)]),
              "#6AC85A", ow=3)
    return {"cell": (x, y - 80 * s)}


ORGANISMS = dict(M.ORGANISMS)
ORGANISMS.update({k: v for k, v in globals().items() if callable(v) and not k.startswith("_") and k not in
                  ("P", "shape", "rect", "poly", "radial", "line_w", "smooth_path", "oval", "wavy", "blob")})
