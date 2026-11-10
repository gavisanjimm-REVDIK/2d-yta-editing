"""toon.py - storybook 2D cartoon characters (house style for 2D videos).

Look (from ASSETS/mascot/reference/character_sheet.webp): thick dark outlines, big round heads, small bodies,
thin limbs, flat colours + one subtle shadow tone, white eyes with dark pupils, messy hair, simple faces.

    from toon import CAST, draw_character, EXPR
    draw_character(canvas, CAST["marcus"], x, y_feet, height_px, pose)

pose keys (all optional):
  expr        name in EXPR, or a dict (see EXPR entries) - use mix_expr() to blend
  talk        0..1 mouth openness (from kit.mouth_open with who=...)
  look        (x, y) pupil direction -1..1
  blink       0..1 lid closure (kit.blink)
  turn        -1..1 fake 3/4 head turn (+ = toward screen right)
  tilt        head tilt (deg)
  lean        upper-body lean (deg, + = right)
  bob         vertical body offset (units, + = down)
  arm_l/arm_r preset name in ARM or (hx, hy[, bend]) hand target relative to shoulder (units, x = outward)
  hand_l/hand_r  "open" | "fist" | "point"
  prop_l/prop_r  callable(canvas, hand_x, hand_y, unit_px, side) drawn at the hand (units already applied)
  walk        phase 0..1 for a stepping walk (None = standing)
  flip        True = mirror (character faces left)
  sweat       0..1 nervous sweat drop
Units: 1 unit = head radius. y grows downward, feet at 0.
"""
from __future__ import annotations

import math

import skia

from kit import rgb, clamp, lerp

INK = "#2A1A12"


# ================================================================ cast
def _c(**kw):
    base = dict(
        skin="#F2B98A", skin_sh="#D99A6C", hair="#5A3A22", hair_sh="#3F2817",
        shirt="#6B3A22", shirt_sh="#52291A", pants="#252838", pants_sh="#1A1C29", shoes="#3A2A22",
        eye_w=0.27, eye_h=0.31, eye_sep=0.4, eye_y=-0.02, pupil=0.52,
        head_rx=1.0, head_ry=0.96, neck=0.12, torso_h=1.35, shoulder_w=1.08, hip_w=0.86, leg=1.45,
        upper_arm=0.66, fore_arm=0.66, limb_w=0.2, pants_w=0.34, hand_r=0.17,
        sleeves="short", hair_style="messy", belly=0.0, extras=(), brow_w=0.075, ears=True,
    )
    base.update(kw)
    return base


CAST = {
    # the mascot (identity source: ASSETS/mascot/reference). Detective role in VIDEO_001: same design + props.
    "marcus": _c(),
    # Marcus on duty: same mascot (hair, face, brown tee) + trench coat, fedora, magnifying glass
    "marcus_detective": _c(shirt="#B8894C", shirt_sh="#97703B", sleeves="long", extras=("trench", "fedora"),
                           tee="#6B3A22"),
    "harrison": _c(skin="#F0BE96", skin_sh="#D69C76", hair="#D9D4CC", hair_sh="#B5AEA4", hair_style="bald_mustache",
                   shirt="#5B2A4A", shirt_sh="#431D36", pants="#2E2433", pants_sh="#1F1824", shoes="#1E1A1A",
                   sleeves="long", torso_h=1.55, shoulder_w=1.2, hip_w=1.05, belly=0.22, leg=1.4,
                   eye_w=0.2, eye_h=0.23, eye_sep=0.38, extras=("cravat", "watch_chain")),
    "oliver": _c(skin="#E9B48E", skin_sh="#CC946D", hair="#2B2B30", hair_sh="#1A1A1E", hair_style="slick",
                 shirt="#1E1E24", shirt_sh="#121216", pants="#3A3A44", pants_sh="#2A2A32", shoes="#111111",
                 sleeves="long", torso_h=1.7, shoulder_w=1.0, hip_w=0.8, leg=1.85, head_ry=1.04,
                 eye_w=0.19, eye_h=0.22, eye_sep=0.36, extras=("butler",)),
    "daniel": _c(skin="#E8A97E", skin_sh="#C98A5F", hair="#B4532A", hair_sh="#8A3D1D", hair_style="cap_beard",
                 shirt="#C9622F", shirt_sh="#A54D22", pants="#3F6B3A", pants_sh="#2F5229", shoes="#5A3A22",
                 sleeves="rolled", torso_h=1.5, shoulder_w=1.25, hip_w=1.0, leg=1.55,
                 eye_w=0.2, eye_h=0.24, eye_sep=0.39, extras=("overalls",)),
    "sophie": _c(skin="#F5C7A2", skin_sh="#DDA781", hair="#D99A3E", hair_sh="#B37A28", hair_style="bun",
                 shirt="#3F6FA8", shirt_sh="#2F5687", pants="#3F6FA8", pants_sh="#2F5687", shoes="#3A2A30",
                 sleeves="short", torso_h=1.4, shoulder_w=0.95, hip_w=0.85, leg=1.5,
                 eye_w=0.21, eye_h=0.25, eye_sep=0.38, extras=("dress", "apron", "lashes")),
    # VIDEO_002 cast
    "gaston": _c(skin="#EDB088", skin_sh="#D08F66", hair="#1E1A1A", hair_sh="#0F0D0D", hair_style="chef",
                 shirt="#F4F1EA", shirt_sh="#D8D0C2", pants="#3A3A44", pants_sh="#2A2A32", shoes="#1A1A1A",
                 sleeves="long", torso_h=1.55, shoulder_w=1.2, hip_w=1.1, belly=0.28, leg=1.45,
                 eye_w=0.2, eye_h=0.23, eye_sep=0.38, extras=("chef_jacket",)),
    "prim": _c(skin="#F2C6A4", skin_sh="#D9A684", hair="#3A2440", hair_sh="#24152A", hair_style="bob",
               shirt="#8A5A9A", shirt_sh="#6C437A", pants="#5A3A6A", pants_sh="#452C52", shoes="#2A1A2A",
               sleeves="long", torso_h=1.42, shoulder_w=0.95, hip_w=0.85, leg=1.6,
               eye_w=0.2, eye_h=0.24, eye_sep=0.38, extras=("dress", "cardigan", "glasses", "lashes")),
    "cedric": _c(skin="#F4C9A6", skin_sh="#DAA988", hair="#E3BC5E", hair_sh="#C29A3E", hair_style="slick",
                 shirt="#B5302E", shirt_sh="#932422", pants="#C9B48A", pants_sh="#A8936C", shoes="#5A3A22",
                 sleeves="long", torso_h=1.5, shoulder_w=1.05, hip_w=0.85, leg=1.85, head_ry=1.0,
                 eye_w=0.2, eye_h=0.22, eye_sep=0.37, extras=("scarf",), temples=False),
}

# ================================================================ expressions
# brows: raise (-1 low .. 1 high), angle (+ = inner end down = angry, - = inner up = worried)
EXPR = {
    "neutral":    dict(bl=0.0, al=0.0, br=0.0, ar=0.0, lids=0.12, mouth="smile", pupil=1.0),
    "smile":      dict(bl=0.2, al=-0.1, br=0.2, ar=-0.1, lids=0.15, mouth="smile", pupil=1.0),
    "happy":      dict(bl=0.4, al=-0.2, br=0.4, ar=-0.2, lids=0.0, mouth="grin", pupil=1.0),
    "smug":       dict(bl=-0.3, al=0.7, br=-0.3, ar=0.7, lids=0.25, mouth="smirk", pupil=1.0),
    "determined": dict(bl=-0.3, al=0.6, br=-0.3, ar=0.6, lids=0.15, mouth="flat", pupil=1.0),
    "suspicious": dict(bl=-0.5, al=0.6, br=0.6, ar=-0.1, lids=0.35, mouth="flat", pupil=0.9),
    "surprised":  dict(bl=0.9, al=-0.2, br=0.9, ar=-0.2, lids=0.0, mouth="o", pupil=0.8),
    "shocked":    dict(bl=1.0, al=-0.4, br=1.0, ar=-0.4, lids=0.0, mouth="open", pupil=0.6),
    "panic":      dict(bl=0.9, al=-0.7, br=0.9, ar=-0.7, lids=0.0, mouth="open", pupil=0.7),
    "worried":    dict(bl=0.5, al=-0.7, br=0.5, ar=-0.7, lids=0.15, mouth="wavy", pupil=0.9),
    "nervous":    dict(bl=0.4, al=-0.8, br=0.4, ar=-0.8, lids=0.05, mouth="grit", pupil=0.75),
    "angry":      dict(bl=-0.6, al=1.0, br=-0.6, ar=1.0, lids=0.2, mouth="frown", pupil=1.0),
    "confident":  dict(bl=0.3, al=0.1, br=0.5, ar=-0.1, lids=0.1, mouth="grin", pupil=1.0),
    "sad":        dict(bl=0.3, al=-0.9, br=0.3, ar=-0.9, lids=0.35, mouth="frown", pupil=1.0),
    "shy":        dict(bl=0.3, al=-0.6, br=0.3, ar=-0.6, lids=0.45, mouth="wavy", pupil=1.0),
}


def mix_expr(a, b, u):
    a = EXPR[a] if isinstance(a, str) else a
    b = EXPR[b] if isinstance(b, str) else b
    out = {k: lerp(a[k], b[k], u) for k in a if k != "mouth"}
    out["mouth"] = b["mouth"] if u > 0.5 else a["mouth"]
    return out


# ================================================================ arm presets (hand target rel. to shoulder; x outward)
ARM = {
    "down": (0.18, 1.28, "out"),
    "relaxed": (0.1, 1.25, "out"),
    "hips": (0.02, 0.98, "out"),
    "point": (1.25, -0.1, "out"),
    "point_up": (0.9, -0.85, "out"),
    "up": (0.55, -1.05, "out"),
    "chin": (-0.55, -0.2, "down"),
    "neck": (-0.45, -0.05, "down"),
    "front": (-0.3, 0.75, "out"),
    "front_high": (-0.25, 0.45, "out"),
    "flash": (0.85, 0.5, "out"),
    "shrug": (0.75, 0.35, "down"),
    "behind": (0.05, 1.0, "out"),
}


# ================================================================ drawing helpers
class Pen:
    def __init__(self, canvas, unit):
        self.c = canvas
        self.u = unit
        self.ow = clamp(4.0 + unit * 0.03, 4.0, 16.0) / unit  # outline width in units
        self.fill = {}
        self.line = skia.Paint(AntiAlias=True, Color=rgb(INK), Style=skia.Paint.kStroke_Style,
                               StrokeWidth=self.ow, StrokeCap=skia.Paint.kRound_Cap,
                               StrokeJoin=skia.Paint.kRound_Join)

    def p(self, color, alpha=1.0):
        key = (color, alpha)
        if key not in self.fill:
            pp = skia.Paint(AntiAlias=True, Color=rgb(color))
            pp.setAlphaf(alpha)
            self.fill[key] = pp
        return self.fill[key]

    def shape(self, path, color, shadow=None, outline=True, shade_dx=0.12, shade_dy=0.06):
        self.c.drawPath(path, self.p(color))
        if shadow:  # cel shadow on the right/bottom side (light from upper left)
            lit = skia.Path(path)
            lit.offset(-shade_dx, -shade_dy)
            sh = skia.Op(path, lit, skia.PathOp.kDifference_PathOp)
            if sh:
                self.c.drawPath(sh, self.p(shadow))
        if outline:
            self.c.drawPath(path, self.line)

    def stroke(self, path, width=None, color=INK):
        p = skia.Paint(self.line)
        if width is not None:
            p.setStrokeWidth(width)
        if color != INK:
            p.setColor(rgb(color))
        self.c.drawPath(path, p)

    def capsule(self, x0, y0, x1, y1, w, color, shadow=None):
        path = capsule_path(x0, y0, x1, y1, w)
        self.shape(path, color, shadow, shade_dx=w * 0.3, shade_dy=0)
        return path


def capsule_path(x0, y0, x1, y1, w):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-6
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    p = skia.Path()
    p.moveTo(x0 + nx, y0 + ny)
    p.lineTo(x1 + nx, y1 + ny)
    p.arcTo(skia.Rect(x1 - w / 2, y1 - w / 2, x1 + w / 2, y1 + w / 2), math.degrees(math.atan2(ny, nx)), -180, False)
    p.lineTo(x0 - nx, y0 - ny)
    p.arcTo(skia.Rect(x0 - w / 2, y0 - w / 2, x0 + w / 2, y0 + w / 2), math.degrees(math.atan2(-ny, -nx)), -180, False)
    p.close()
    return p


def smooth_path(pts, closed=True):
    """Catmull-Rom through points."""
    p = skia.Path()
    n = len(pts)
    p.moveTo(*pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1 = pts[(i - 1) % n] if (closed or i > 0) else pts[0], pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def oval(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def spiky(cx, cy, angles, r_base, r_tip, sx=1.0, sy=1.0, bend=0.25):
    """Spiky hair silhouette: tips at angles (deg, 0 = right, -90 = up), bases between them."""
    pts = []
    for i, a in enumerate(angles):
        ra = math.radians(a)
        nb = angles[i + 1] if i + 1 < len(angles) else a + 25
        rb = math.radians((a + nb) / 2)
        rt = r_tip[i] if isinstance(r_tip, (list, tuple)) else r_tip
        pts.append(((cx + math.cos(ra + bend * 0.3) * rt * sx, cy + math.sin(ra + bend * 0.3) * rt * sy), "tip"))
        pts.append(((cx + math.cos(rb) * r_base * sx, cy + math.sin(rb) * r_base * sy), "base"))
    p = skia.Path()
    p.moveTo(cx + math.cos(math.radians(angles[0] - 12)) * r_base * sx,
             cy + math.sin(math.radians(angles[0] - 12)) * r_base * sy)
    prev = None
    for (x, y), kind in pts:
        if kind == "tip":
            p.lineTo(x, y)
        else:
            p.quadTo((x + (prev[0] if prev else x)) / 2 * 0.5 + x * 0.5, (y + (prev[1] if prev else y)) / 2 * 0.5 + y * 0.5, x, y)
        prev = (x, y)
    p.close()
    return p


def clumps(cx, cy, lobes, r_base, sx=1.0, sy=1.0, sweep=8.0):
    """Rounded hair clumps with soft points. lobes = [(a0, a1, r_tip)] in deg (-90 = up)."""
    def pt(a, r):
        return cx + math.cos(math.radians(a)) * r * sx, cy + math.sin(math.radians(a)) * r * sy
    p = skia.Path()
    p.moveTo(*pt(lobes[0][0], r_base * 0.9))
    for a0, a1, rt in lobes:
        am = (a0 + a1) / 2 + sweep
        tip = pt(am, rt)
        c1 = pt(a0 + (a1 - a0) * 0.05, (r_base + rt) * 0.55)
        c2 = pt(am - (a1 - a0) * 0.35, rt * 1.02)
        p.cubicTo(*c1, *c2, *tip)
        p.quadTo(*pt(am + (a1 - a0) * 0.15, rt * 0.92), *pt(a1, r_base))
    p.close()
    return p


# ================================================================ hair
def hair_back(pen, C, hx, hy, rx, ry, turn):
    st = C["hair_style"]
    if st == "messy":
        # fluffy chunky clumps swept to the right (reference sheet)
        lobes = [(-205, -182, 1.3), (-182, -158, 1.42), (-158, -132, 1.5), (-132, -106, 1.52), (-106, -80, 1.55),
                 (-80, -55, 1.5), (-55, -30, 1.45), (-30, -8, 1.36), (-8, 14, 1.26)]
        path = clumps(hx - turn * 0.08, hy - 0.04, lobes, 1.08, rx, ry, sweep=9)
        pen.shape(path, C["hair"], C["hair_sh"], shade_dx=0.15, shade_dy=0.1)
    elif st == "bun":
        pen.shape(oval(hx - turn * 0.1, hy - ry * 1.12, 0.42, 0.36), C["hair"], C["hair_sh"])
        pen.shape(oval(hx, hy - 0.08, rx * 1.1, ry * 1.06), C["hair"], C["hair_sh"])
    elif st == "slick":
        pen.shape(oval(hx, hy - 0.1, rx * 1.05, ry * 1.02), C["hair"], C["hair_sh"])
    elif st == "chef":
        pen.shape(oval(hx, hy - 0.05, rx * 1.04, ry * 1.0), C["hair"], C["hair_sh"])
    elif st == "bob":
        bob = smooth_path([(hx - rx * 1.2, hy + ry * 0.55), (hx - rx * 1.22, hy - ry * 0.3), (hx - rx * 0.8, hy - ry * 1.08),
                           (hx, hy - ry * 1.18), (hx + rx * 0.8, hy - ry * 1.08), (hx + rx * 1.22, hy - ry * 0.3),
                           (hx + rx * 1.2, hy + ry * 0.55), (hx, hy + ry * 0.5)])
        pen.shape(bob, C["hair"], C["hair_sh"])
    elif st == "cap_beard":
        tufts = spiky(hx, hy + 0.1, [-200, -185, -170, -10, 5, 20], 1.02, 1.18, rx, ry)
        pen.shape(tufts, C["hair"], C["hair_sh"])


def hair_front(pen, C, hx, hy, rx, ry, turn):
    st = C["hair_style"]
    fx = turn * 0.32 * rx
    if st == "messy":
        # bangs: spikes falling over the forehead (reference: covers top of forehead)
        p = skia.Path()
        # top edge follows the skull (slightly outside it) so no skin shows through: no bald spot
        p.moveTo(hx - rx * 0.98, hy - ry * 0.32)
        p.arcTo(skia.Rect(hx - rx * 1.06, hy - ry * 1.1, hx + rx * 1.06, hy + ry * 1.1), 196, 148, False)
        p.lineTo(hx + rx * 0.98, hy - ry * 0.35)
        tips = [(0.86, -0.22), (0.58, -0.4), (0.3, -0.28), (0.02, -0.46), (-0.3, -0.34), (-0.6, -0.48), (-0.9, -0.22)]
        last = (hx + rx * 0.98, hy - ry * 0.35)
        for i, (tx, ty) in enumerate(tips):
            tip = (hx + tx * rx + fx, hy + ty * ry)
            base = (hx + (tx - 0.16) * rx + fx, hy - ry * (0.7 + 0.05 * (i % 2)))
            p.cubicTo(last[0] - 0.02, last[1] + 0.15, tip[0] + 0.1, tip[1] - 0.12, *tip)
            p.quadTo(tip[0] - 0.04, (tip[1] + base[1]) / 2, *base)
            last = base
        p.close()
        pen.shape(p, C["hair"], C["hair_sh"], shade_dx=0.08, shade_dy=0.08)
    elif st == "bald_mustache":
        for s in (-1, 1):  # side tufts
            if s * turn > 0.6:
                continue
            pen.shape(smooth_path([(hx + s * rx * 0.86, hy - 0.35), (hx + s * rx * 1.08, hy - 0.2),
                                   (hx + s * rx * 1.06, hy + 0.15), (hx + s * rx * 0.9, hy + 0.05)]),
                      C["hair"], C["hair_sh"])
        # shine on the bald top
        pen.c.drawPath(oval(hx - 0.3 * rx + fx * 0.5, hy - ry * 0.68, 0.18, 0.08), pen.p("#FFFFFF", 0.45))
    elif st == "slick":
        p = skia.Path()
        p.moveTo(hx - rx * 1.02, hy - 0.05)
        p.quadTo(hx - rx * 1.0, hy - ry * 1.08, hx + 0.1, hy - ry * 1.04)
        p.quadTo(hx + rx * 1.05, hy - ry * 0.95, hx + rx * 1.02, hy - 0.1)
        p.quadTo(hx + rx * 0.7, hy - ry * 0.7, hx - 0.25 * rx + fx, hy - ry * 0.62)
        p.quadTo(hx - rx * 0.75, hy - ry * 0.55, hx - rx * 1.02, hy - 0.05)
        p.close()
        pen.shape(p, C["hair"], C["hair_sh"])
        q = skia.Path()  # side part line
        q.moveTo(hx - 0.25 * rx + fx, hy - ry * 0.64)
        q.quadTo(hx - 0.35 * rx, hy - ry * 0.9, hx - 0.2 * rx, hy - ry * 1.02)
        pen.stroke(q, pen.ow * 0.6)
        for s in ((-1, 1) if C.get("temples", True) else ()):  # grey temples
            if s * turn > 0.6:
                continue
            pen.c.drawPath(oval(hx + s * rx * 0.97, hy - 0.12, 0.08, 0.2), pen.p("#8C8C94"))
    elif st == "bun":
        p = skia.Path()  # side-swept bangs
        p.moveTo(hx - rx * 1.05, hy - 0.05)
        p.quadTo(hx - rx * 1.05, hy - ry * 1.08, hx, hy - ry * 1.06)
        p.quadTo(hx + rx * 1.05, hy - ry * 1.02, hx + rx * 1.05, hy - 0.05)
        p.quadTo(hx + rx * 0.6, hy - ry * 0.5, hx + 0.1 + fx, hy - ry * 0.6)
        p.quadTo(hx - rx * 0.5, hy - ry * 0.5, hx - rx * 0.85, hy - ry * 0.3)
        p.close()
        pen.shape(p, C["hair"], C["hair_sh"])
    elif st == "chef":
        # tall puffy toque
        hat = smooth_path([(hx - rx * 0.78, hy - ry * 0.62), (hx - rx * 1.05, hy - ry * 1.45), (hx - rx * 0.6, hy - ry * 2.05),
                           (hx, hy - ry * 2.25), (hx + rx * 0.6, hy - ry * 2.05), (hx + rx * 1.05, hy - ry * 1.45),
                           (hx + rx * 0.78, hy - ry * 0.62)])
        pen.shape(hat, "#FFFFFF", "#DAD6CE", shade_dx=0.18)
        band = skia.Path()
        band.addRoundRect(skia.Rect(hx - rx * 0.86, hy - ry * 0.95, hx + rx * 0.86, hy - ry * 0.58), 0.08, 0.08)
        pen.shape(band, "#F4F1EA", "#DAD6CE")
        for k in (-0.3, 0.3):
            q = skia.Path()
            q.moveTo(hx + k * rx, hy - ry * 1.0)
            q.quadTo(hx + k * rx * 1.4, hy - ry * 1.5, hx + k * rx * 0.8, hy - ry * 1.9)
            pen.stroke(q, pen.ow * 0.6)
        for side in (-1, 1):  # black sideburns
            if side * turn > 0.6:
                continue
            pen.shape(smooth_path([(hx + side * rx * 0.85, hy - ry * 0.6), (hx + side * rx * 1.03, hy - ry * 0.4),
                                   (hx + side * rx * 1.0, hy + ry * 0.05), (hx + side * rx * 0.88, hy - 0.05)]),
                      C["hair"], C["hair_sh"])
    elif st == "bob":
        fringe = skia.Path()
        fringe.moveTo(hx - rx * 1.0, hy - ry * 0.2)
        fringe.arcTo(skia.Rect(hx - rx * 1.08, hy - ry * 1.12, hx + rx * 1.08, hy + ry * 1.12), 190, 160, False)
        fringe.lineTo(hx + rx * 1.0, hy - ry * 0.2)
        fringe.quadTo(hx + rx * 0.5 + fx, hy - ry * 0.45, hx + fx, hy - ry * 0.42)
        fringe.quadTo(hx - rx * 0.5 + fx, hy - ry * 0.45, hx - rx * 1.0, hy - ry * 0.2)
        fringe.close()
        pen.shape(fringe, C["hair"], C["hair_sh"])
    elif st == "cap_beard":
        # beard
        b = smooth_path([(hx - rx * 0.92, hy + 0.05), (hx - rx * 0.7, hy + ry * 0.75), (hx + fx, hy + ry * 1.12),
                         (hx + rx * 0.7, hy + ry * 0.75), (hx + rx * 0.92, hy + 0.05), (hx + rx * 0.55, hy + ry * 0.45),
                         (hx + fx, hy + ry * 0.62), (hx - rx * 0.55, hy + ry * 0.45)])
        pen.shape(b, C["hair"], C["hair_sh"])
        # flat cap
        cap = skia.Path()
        cap.moveTo(hx - rx * 1.06, hy - ry * 0.32)
        cap.quadTo(hx - rx * 1.05, hy - ry * 1.25, hx + 0.05, hy - ry * 1.22)
        cap.quadTo(hx + rx * 1.1, hy - ry * 1.15, hx + rx * 1.06, hy - ry * 0.32)
        cap.close()
        pen.shape(cap, "#6B5A3C", "#524429")
        brim = smooth_path([(hx - rx * 0.95 + fx, hy - ry * 0.42), (hx + fx * 1.3, hy - ry * 0.24),
                            (hx + rx * 0.98 + fx, hy - ry * 0.42), (hx + fx, hy - ry * 0.5)])
        pen.shape(brim, "#5A4A30")


# ================================================================ face
def draw_face(pen, C, hx, hy, rx, ry, E, pose):
    turn = pose.get("turn", 0.0)
    fx = turn * 0.32 * rx
    lx, ly = pose.get("look", (0.0, 0.0))
    blinkv = max(pose.get("blink", 0.0), E["lids"])
    ew, eh, sep = C["eye_w"], C["eye_h"], C["eye_sep"]
    ey = hy + C["eye_y"] * ry
    for side in (-1, 1):
        far = side * turn < 0
        sq = 1 - 0.35 * abs(turn) if far else 1 + 0.05 * abs(turn)
        cx = hx + side * sep * rx * (1 - 0.18 * abs(turn) * (1 if far else -0.3)) + fx
        w = ew * sq
        eye = oval(cx, ey, w, eh)
        pen.c.drawPath(eye, pen.p("#FFFFFF"))
        pr = ew * C["pupil"] * E["pupil"]
        px = cx + lx * (w - pr) * 0.75 + turn * w * 0.25
        py = ey + ly * (eh - pr) * 0.7
        pen.c.save()
        pen.c.clipPath(eye, doAntiAlias=True)
        pen.c.drawPath(oval(px, py, pr * sq, pr), pen.p(INK))
        pen.c.drawPath(oval(px - pr * 0.35, py - pr * 0.4, pr * 0.28, pr * 0.28), pen.p("#FFFFFF"))
        if blinkv > 0.02:  # upper lid
            pen.c.drawRect(skia.Rect(cx - w * 1.2, ey - eh * 1.2, cx + w * 1.2, ey - eh + 2 * eh * blinkv),
                           pen.p(C["skin"]))
        pen.c.restore()
        if blinkv > 0.95:  # closed: curved line
            q = skia.Path()
            q.moveTo(cx - w * 0.9, ey)
            q.quadTo(cx, ey + eh * 0.35, cx + w * 0.9, ey)
            pen.stroke(q)
        else:
            pen.stroke(eye)
            if blinkv > 0.02:
                lid_y = ey - eh + 2 * eh * blinkv
                half = w * math.sqrt(max(0.0, 1 - ((lid_y - ey) / eh) ** 2))
                q = skia.Path()
                q.moveTo(cx - half, lid_y)
                q.lineTo(cx + half, lid_y)
                pen.stroke(q)
        if "lashes" in C["extras"]:
            q = skia.Path()
            q.moveTo(cx + side * w * 0.75, ey - eh * 0.75)
            q.lineTo(cx + side * w * 1.2, ey - eh * 1.05)
            pen.stroke(q, pen.ow * 0.8)
    # nose: small hook line (reference)
    nx = hx + fx * 1.25 + turn * 0.05
    ny = hy + ry * 0.24
    q = skia.Path()
    q.moveTo(nx - 0.04 + turn * 0.06, ny - 0.12)
    q.quadTo(nx + 0.1 + turn * 0.08, ny - 0.02, nx + 0.0, ny + 0.05)
    pen.stroke(q, pen.ow * 0.8)
    if C["hair_style"] == "chef":  # big curly black mustache
        m = smooth_path([(nx - 0.62, ny + 0.02), (nx - 0.5, ny + 0.2), (nx - 0.25, ny + 0.12), (nx, ny + 0.16),
                         (nx + 0.25, ny + 0.12), (nx + 0.5, ny + 0.2), (nx + 0.62, ny + 0.02), (nx + 0.42, ny + 0.28),
                         (nx, ny + 0.24), (nx - 0.42, ny + 0.28)])
        draw_mouth(pen, C, nx, hy + ry * 0.6, E, pose)
        pen.shape(m, C["hair"], C["hair_sh"])
        return
    if C["hair_style"] == "bald_mustache":  # handlebar mustache
        m = smooth_path([(nx - 0.45, ny + 0.2), (nx - 0.25, ny + 0.06), (nx, ny + 0.1), (nx + 0.25, ny + 0.06),
                         (nx + 0.45, ny + 0.2), (nx + 0.22, ny + 0.2), (nx, ny + 0.18), (nx - 0.22, ny + 0.2)])
        draw_mouth(pen, C, nx, hy + ry * 0.58, E, pose)
        pen.shape(m, C["hair"], C["hair_sh"])
        return
    draw_mouth(pen, C, hx + fx * 1.15, hy + ry * 0.55, E, pose)
    if pose.get("sweat", 0) > 0.05:
        s = pose["sweat"]
        dx, dy = hx + rx * 0.78, hy - ry * 0.35 + s * 0.15
        d = skia.Path()
        d.moveTo(dx, dy - 0.2)
        d.quadTo(dx + 0.12, dy, dx, dy + 0.06)
        d.quadTo(dx - 0.12, dy, dx, dy - 0.2)
        d.close()
        pen.shape(d, "#8FD3F5")


def draw_brows(pen, C, hx, hy, rx, ry, E, pose):
    turn = pose.get("turn", 0.0)
    fx = turn * 0.32 * rx
    ew, eh, sep = C["eye_w"], C["eye_h"], C["eye_sep"]
    ey = hy + C["eye_y"] * ry
    for side in (-1, 1):
        far = side * turn < 0
        sq = 1 - 0.35 * abs(turn) if far else 1 + 0.05 * abs(turn)
        cx = hx + side * sep * rx * (1 - 0.18 * abs(turn) * (1 if far else -0.3)) + fx
        w = ew * sq
        raise_ = E["bl"] if side < 0 else E["br"]
        ang = E["al"] if side < 0 else E["ar"]
        by = ey - eh - 0.16 - raise_ * 0.12
        inner = (cx - side * w * 0.95, by + ang * 0.13)
        outer = (cx + side * w * 1.05, by - ang * 0.05 - 0.02)
        q = skia.Path()
        q.moveTo(*inner)
        q.quadTo((inner[0] + outer[0]) / 2, by - 0.07, *outer)
        pen.stroke(q, C["brow_w"] * (1.25 if C["hair_style"] == "messy" else 1.0), C["hair_sh"] if C["hair_style"] != "bald_mustache" else "#8C857C")


def draw_mouth(pen, C, mx, my, E, pose):
    """Closed shape from the expression; when speaking, a viseme mouth:
    pose["vis"] = (open 0..1, wide 0..1, round 0..1) from lipsync.json (voice loudness + letters).
    Legacy pose["talk"] (0..1) still works (treated as open)."""
    vis = pose.get("vis")
    if vis is None and pose.get("talk", 0) > 0:
        vis = (pose["talk"], 0.3, 0.2)
    shape = E["mouth"]
    mw = 0.32
    op = vis[0] if vis else 0.0
    fixed = {"open": 0.8, "grin": 0.5, "o": 0.55}.get(shape, 0.0)
    if op > 0.05 or fixed:
        wide = vis[1] if vis and op > 0.05 else (0.6 if shape == "grin" else 0.3)
        rnd = vis[2] if vis and op > 0.05 else (1.0 if shape == "o" else 0.0)
        op = max(op, fixed * (0.6 if op > 0.05 else 1.0))
        w = mw * (0.8 + 0.4 * wide - 0.42 * rnd)
        h = 0.05 + 0.34 * op * (1 + 0.25 * rnd)
        smile = 0.05 if shape in ("grin", "smile", "smirk", "confident", "happy") else (
            -0.04 if shape in ("frown", "wavy", "grit") else 0.0)
        p = skia.Path()
        if rnd > 0.55:
            p.addOval(skia.Rect(mx - w, my - h * 0.35, mx + w, my + h * 0.75))
        else:
            p.moveTo(mx - w, my - smile)
            p.cubicTo(mx - w * 0.5, my - h * 0.32, mx + w * 0.5, my - h * 0.32, mx + w, my - smile)
            p.cubicTo(mx + w * 0.95, my + h * 0.9, mx - w * 0.95, my + h * 0.9, mx - w, my - smile)
            p.close()
        pen.c.drawPath(p, pen.p("#6E231D"))
        pen.c.save()
        pen.c.clipPath(p, doAntiAlias=True)
        if wide > 0.45 and rnd < 0.5:  # upper teeth on wide sounds (E / grin)
            pen.c.drawRect(skia.Rect(mx - w, my - h, mx + w, my - h * 0.05 + 0.06), pen.p("#FFFFFF"))
        pen.c.drawPath(oval(mx, my + h * 0.72, w * 0.62, h * 0.38), pen.p("#E0706A"))
        pen.c.restore()
        pen.stroke(p)
        return
    q = skia.Path()
    if shape == "smile":
        q.moveTo(mx - mw * 0.9, my - 0.03)
        q.quadTo(mx, my + 0.14, mx + mw * 0.9, my - 0.03)
    elif shape == "smirk":
        q.moveTo(mx - mw * 0.9, my + 0.02)
        q.quadTo(mx + 0.05, my + 0.12, mx + mw * 1.0, my - 0.1)
    elif shape == "frown":
        q.moveTo(mx - mw * 0.7, my + 0.08)
        q.quadTo(mx, my - 0.08, mx + mw * 0.7, my + 0.08)
    elif shape == "wavy":
        q.moveTo(mx - mw * 0.8, my)
        q.cubicTo(mx - mw * 0.4, my - 0.08, mx - mw * 0.1, my + 0.08, mx + mw * 0.2, my)
        q.quadTo(mx + mw * 0.5, my - 0.07, mx + mw * 0.8, my + 0.02)
    elif shape == "grit":
        r = skia.Rect(mx - mw * 0.85, my - 0.08, mx + mw * 0.85, my + 0.1)
        pen.c.drawRoundRect(r, 0.06, 0.06, pen.p("#FFFFFF"))
        q.addRoundRect(r, 0.06, 0.06)
        q.moveTo(mx - mw * 0.85, my + 0.01)
        q.lineTo(mx + mw * 0.85, my + 0.01)
        for k in (-0.4, 0.0, 0.4):
            q.moveTo(mx + k * mw, my - 0.08)
            q.lineTo(mx + k * mw, my + 0.1)
    else:  # flat
        q.moveTo(mx - mw * 0.6, my)
        q.lineTo(mx + mw * 0.6, my)
    pen.stroke(q)


# ================================================================ body
def _ik(sx, sy, hx, hy, l1, l2, bend_sign):
    dx, dy = hx - sx, hy - sy
    d = clamp(math.hypot(dx, dy), 1e-3, l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    cos_b = clamp((l1 * l1 + d * d - l2 * l2) / (2 * l1 * d), -1, 1)
    b = math.acos(cos_b) * bend_sign
    ex, ey = sx + math.cos(a + b) * l1, sy + math.sin(a + b) * l1
    k = d / math.hypot(dx, dy) if math.hypot(dx, dy) > 1e-6 else 1
    return (ex, ey), (sx + dx * k, sy + dy * k)


def _hand(pen, C, x, y, kind, ang, side):
    r = C["hand_r"]
    if kind == "point":
        fx, fy = x + math.cos(ang) * r * 2.0, y + math.sin(ang) * r * 2.0
        pen.capsule(x, y, fx, fy, r * 0.62, C["skin"])
    pen.shape(oval(x, y, r, r), C["skin"], C["skin_sh"], shade_dx=r * 0.4, shade_dy=r * 0.2)
    if kind == "open":  # thumb bump
        tx, ty = x + math.cos(ang - side * 1.2) * r * 0.85, y + math.sin(ang - side * 1.2) * r * 0.85
        pen.shape(oval(tx, ty, r * 0.38, r * 0.38), C["skin"])


def draw_character(canvas, C, x, y_feet, height_px, pose=None):
    pose = pose or {}
    if isinstance(C, str):
        C = CAST[C]
    rx, ry = C["head_rx"], C["head_ry"]
    total = C["leg"] + C["torso_h"] + C["neck"] + 2 * ry + 0.35
    u = height_px / total
    pen = Pen(canvas, u)
    E = pose.get("expr", "neutral")
    E = EXPR[E] if isinstance(E, str) else E
    canvas.save()
    canvas.translate(x, y_feet)
    canvas.scale(-u if pose.get("flip") else u, u)
    turn = pose.get("turn", 0.0) * (-1 if pose.get("flip") else 1)
    pose = dict(pose, turn=turn, _hands={})

    # ---- legs
    walk = pose.get("walk")
    hip_y = -C["leg"] + pose.get("bob", 0.0)
    for side in (-1, 1):
        lift = 0.0
        swing = 0.0
        if walk is not None:
            ph = walk * 2 * math.pi + (0 if side < 0 else math.pi)
            lift = max(0.0, math.sin(ph)) * 0.22
            swing = math.cos(ph) * 0.08
        lx = side * C["hip_w"] * 0.27
        fy = -lift
        fx = lx + swing + side * 0.04
        if "dress" in C["extras"]:
            pen.capsule(lx, hip_y + 0.2, fx, fy - 0.12, C["limb_w"], C["skin"], C["skin_sh"])
        else:
            pen.capsule(lx, hip_y, fx, fy - 0.12, C["pants_w"], C["pants"], C["pants_sh"])
        shoe = smooth_path([(fx - 0.2, fy - 0.02), (fx - 0.15, fy - 0.2), (fx + 0.12, fy - 0.2),
                            (fx + 0.3 * side + 0.05 * side, fy - 0.08), (fx + 0.3 * side, fy + 0.02)])
        shoe = skia.Path()
        shoe.addRoundRect(skia.Rect(fx - 0.22, fy - 0.2, fx + 0.22, fy + 0.03), 0.12, 0.12)
        pen.shape(shoe, C["shoes"])
        sole = skia.Path()
        sole.moveTo(fx - 0.2, fy - 0.02)
        sole.lineTo(fx + 0.2, fy - 0.02)
        pen.stroke(sole, pen.ow * 0.6, "#E8E0D8")

    # ---- upper body (lean pivots at hips)
    canvas.save()
    canvas.rotate(pose.get("lean", 0.0) * (-1 if pose.get("flip") else 1), 0, hip_y)
    th, sw, hw = C["torso_h"], C["shoulder_w"], C["hip_w"]
    top = hip_y - th
    bel = C["belly"]
    torso = smooth_path([(-sw / 2, top + 0.12), (-sw / 2 + 0.12, top), (sw / 2 - 0.12, top), (sw / 2, top + 0.12),
                         (hw / 2 + bel, top + th * 0.65), (hw / 2, hip_y + 0.08), (-hw / 2, hip_y + 0.08),
                         (-hw / 2 - bel, top + th * 0.65)])
    if "dress" in C["extras"]:
        torso = smooth_path([(-sw / 2, top + 0.12), (-sw / 2 + 0.12, top), (sw / 2 - 0.12, top), (sw / 2, top + 0.12),
                             (hw / 2 + 0.05, top + th * 0.55), (hw * 0.85, hip_y + 0.5), (-hw * 0.85, hip_y + 0.5),
                             (-hw / 2 - 0.05, top + th * 0.55)])
    # arms behind torso when hands are "behind"
    arms = []
    for side, key_ in ((-1, "arm_l"), (1, "arm_r")):
        a = pose.get(key_, "down")
        hx_, hy_, bend = ARM[a] if isinstance(a, str) else (a + ("out",))[:3]
        sx_ = side * (sw / 2 - 0.1)
        sy_ = top + 0.16
        hand = (sx_ + side * hx_, sy_ + hy_)
        bend_sign = (1 if side > 0 else -1) * (1 if bend == "out" else -1)
        elbow, hpos = _ik(sx_, sy_, *hand, C["upper_arm"], C["fore_arm"], -bend_sign)
        arms.append((side, key_, (sx_, sy_), elbow, hpos, a))
    for arm in arms:
        if arm[5] == "behind":
            _draw_arm(pen, C, pose, *arm)
    pen.shape(torso, C["shirt"], C["shirt_sh"], shade_dx=0.16, shade_dy=0.0)
    _torso_details(pen, C, top, hip_y, sw, hw, th)
    for arm in arms:
        if arm[5] != "behind":
            _draw_arm(pen, C, pose, *arm)

    if pose.get("snow", 0) > 0.02:
        for side in (-1, 1):
            pen.shape(oval(side * (sw / 2 - 0.15), top + 0.0, 0.3 * pose["snow"] + 0.05, 0.1 * pose["snow"] + 0.03),
                      "#FFFFFF", "#DDE6F2")
    # ---- neck + head
    hy = top - C["neck"] - ry * 0.92
    canvas.save()
    canvas.rotate(pose.get("tilt", 0.0) * (-1 if pose.get("flip") else 1), 0, top)
    pen.capsule(0, top + 0.05, 0, top - C["neck"] - 0.25, 0.32, C["skin_sh"])
    hair_back(pen, C, 0, hy, rx, ry, turn)
    if C["ears"]:
        for side in (-1, 1):
            if side * turn < -0.55:
                continue
            ex = side * rx * (0.97 - 0.1 * turn * side) + turn * 0.12
            pen.shape(oval(ex, hy + 0.12, 0.26, 0.3), C["skin"], C["skin_sh"])
            q = skia.Path()
            q.moveTo(ex + side * 0.06, hy + 0.0)
            q.quadTo(ex - side * 0.08, hy + 0.12, ex + side * 0.04, hy + 0.25)
            pen.stroke(q, pen.ow * 0.6)
    head = smooth_path([(0, hy - ry), (rx * 0.75, hy - ry * 0.85), (rx, hy - ry * 0.15), (rx * 0.9, hy + ry * 0.45),
                        (rx * 0.55, hy + ry * 0.88), (0, hy + ry), (-rx * 0.55, hy + ry * 0.88),
                        (-rx * 0.9, hy + ry * 0.45), (-rx, hy - ry * 0.15), (-rx * 0.75, hy - ry * 0.85)])
    pen.shape(head, C["skin"], C["skin_sh"], shade_dx=0.14, shade_dy=0.05)
    draw_face(pen, C, 0, hy, rx, ry, E, pose)
    hair_front(pen, C, 0, hy, rx, ry, turn)
    if C["hair_style"] == "cap_beard":  # mouth sits on top of the beard so speech stays visible
        draw_mouth(pen, C, turn * 0.32 * rx * 1.15, hy + ry * 0.55, E, pose)
    draw_brows(pen, C, 0, hy, rx, ry, E, pose)
    if "glasses" in C["extras"]:
        draw_glasses(pen, C, 0, hy, rx, ry, turn)
    if pose.get("tears", 0) > 0.02:
        draw_tears(pen, C, 0, hy, rx, ry, turn, pose["tears"], pose.get("_t", 0.0))
    if "fedora" in C["extras"]:
        draw_fedora(pen, 0, hy, rx, ry, turn, pose.get("snow", 0.0))
    canvas.restore()
    canvas.restore()
    canvas.restore()
    return {"head": (x, y_feet + hy * u), "unit": u, "hands": pose.get("_hands", {})}


def draw_fedora(pen, hx, hy, rx, ry, turn, snow=0.0):
    """Brown fedora sitting on the messy hair, slightly tilted; hair still pokes out at the sides."""
    c = pen.c
    c.save()
    c.rotate(-6 + turn * 5, hx, hy - ry)
    by = hy - ry * 0.92  # brim height
    fx = turn * 0.12
    brim = smooth_path([(hx - rx * 1.38 + fx, by + 0.02), (hx + fx, by - 0.16), (hx + rx * 1.38 + fx, by - 0.02),
                        (hx + rx * 1.2 + fx, by + 0.16), (hx + fx, by + 0.2), (hx - rx * 1.2 + fx, by + 0.18)])
    crown = skia.Path()
    crown.moveTo(hx - rx * 0.8 + fx, by + 0.05)
    crown.cubicTo(hx - rx * 0.86 + fx, by - 0.55, hx - rx * 0.6 + fx, by - 0.86, hx - 0.12 + fx, by - 0.78)
    crown.quadTo(hx + fx, by - 0.68, hx + 0.12 + fx, by - 0.8)
    crown.cubicTo(hx + rx * 0.62 + fx, by - 0.88, hx + rx * 0.86 + fx, by - 0.55, hx + rx * 0.8 + fx, by + 0.05)
    crown.close()
    pen.shape(crown, "#5A3E2A", "#46301F", shade_dx=0.18, shade_dy=0)
    band = skia.Path()
    band.moveTo(hx - rx * 0.82 + fx, by - 0.04)
    band.quadTo(hx + fx, by - 0.12, hx + rx * 0.82 + fx, by - 0.04)
    band.lineTo(hx + rx * 0.8 + fx, by - 0.24)
    band.quadTo(hx + fx, by - 0.32, hx - rx * 0.82 + fx, by - 0.24)
    band.close()
    pen.shape(band, "#2A1E18")
    pen.shape(brim, "#5A3E2A", "#46301F", shade_dx=0.0, shade_dy=0.06)
    if snow > 0.02:  # snow piled on the hat (fresh from the blizzard)
        cap = smooth_path([(hx - rx * 0.7 + fx, by - 0.62), (hx - 0.1 + fx, by - 0.78 - 0.12 * snow), (hx + rx * 0.68 + fx, by - 0.66),
                           (hx + rx * 0.5 + fx, by - 0.56), (hx + fx, by - 0.62), (hx - rx * 0.5 + fx, by - 0.54)])
        pen.shape(cap, "#FFFFFF", "#DDE6F2")
        for k in (-1.0, 0.6):
            pen.shape(oval(hx + k * rx + fx, by - 0.06, 0.3 * snow + 0.05, 0.1 * snow + 0.03), "#FFFFFF", outline=False)
    c.restore()


def draw_glasses(pen, C, hx, hy, rx, ry, turn):
    fx = turn * 0.32 * rx
    ey = hy + C["eye_y"] * ry
    rr = C["eye_w"] * 1.45
    for side in (-1, 1):
        cx = hx + side * C["eye_sep"] * rx * (1 - 0.15 * abs(turn)) + fx
        pen.c.drawPath(oval(cx, ey, rr, rr), pen.p("#DDEEFF", 0.25))
        pen.stroke(oval(cx, ey, rr, rr), pen.ow * 0.9)
    q = skia.Path()
    q.moveTo(hx - C["eye_sep"] * rx + rr + fx, ey - 0.03)
    q.quadTo(hx + fx, ey - 0.1, hx + C["eye_sep"] * rx - rr + fx, ey - 0.03)
    pen.stroke(q, pen.ow * 0.8)


def draw_tears(pen, C, hx, hy, rx, ry, turn, amount, t):
    fx = turn * 0.32 * rx
    ey = hy + C["eye_y"] * ry + C["eye_h"] * 0.8
    for side in (-1, 1):
        cx = hx + side * C["eye_sep"] * rx + fx
        L = 0.25 + 0.45 * amount
        st = skia.Path()
        st.moveTo(cx - 0.05, ey)
        st.quadTo(cx - 0.07, ey + L * 0.6, cx, ey + L)
        st.quadTo(cx + 0.07, ey + L * 0.6, cx + 0.05, ey)
        st.close()
        pen.c.drawPath(st, pen.p("#8FD3F5", 0.85))
        ph = (t * 2.2 + (0.5 if side > 0 else 0)) % 1  # falling drop
        dy = ey + L + ph * 0.5
        d = skia.Path()
        d.moveTo(cx, dy - 0.1)
        d.quadTo(cx + 0.07, dy + 0.02, cx, dy + 0.05)
        d.quadTo(cx - 0.07, dy + 0.02, cx, dy - 0.1)
        d.close()
        pen.c.drawPath(d, pen.p("#8FD3F5", 1 - ph))


def prop_magnifier(pen, x, y, ang, side):
    """Magnifying glass held at the hand, lens pointing along the forearm."""
    ex, ey = x + math.cos(ang) * 0.55, y + math.sin(ang) * 0.55
    pen.capsule(x - math.cos(ang) * 0.1, y - math.sin(ang) * 0.1, ex, ey, 0.14, "#5A3A22")
    lx, ly = x + math.cos(ang) * 0.9, y + math.sin(ang) * 0.9
    lens = oval(lx, ly, 0.36, 0.36)
    pen.c.drawPath(lens, pen.p("#CFE6F5", 0.55))
    pen.c.drawPath(oval(lx - 0.1, ly - 0.12, 0.09, 0.05), pen.p("#FFFFFF", 0.8))
    rim = skia.Paint(pen.line)
    rim.setStrokeWidth(0.12)
    rim.setColor(rgb("#C9A24A"))
    pen.c.drawPath(lens, rim)
    pen.stroke(oval(lx, ly, 0.42, 0.42))


def _torso_details(pen, C, top, hip_y, sw, hw, th):
    ex = C["extras"]
    # neckline
    q = skia.Path()
    q.moveTo(-0.22, top + 0.02)
    q.quadTo(0, top + 0.22, 0.22, top + 0.02)
    if "trench" in ex:
        coat_l = hip_y + 0.62  # coat hangs to the knees, drawn over the legs
        skirt = smooth_path([(-hw / 2 - 0.02, hip_y - 0.2), (hw / 2 + 0.02, hip_y - 0.2), (hw / 2 + 0.16, coat_l),
                             (0.02, coat_l + 0.04), (-hw / 2 - 0.16, coat_l)])
        pen.shape(skirt, C["shirt"], C["shirt_sh"], shade_dx=0.12)
        q2 = skia.Path()
        q2.moveTo(0.02, hip_y - 0.1)
        q2.lineTo(0.02, coat_l + 0.02)
        pen.stroke(q2, pen.ow * 0.8)
        tee = smooth_path([(-0.2, top + 0.01), (0.2, top + 0.01), (0.08, top + th * 0.62), (-0.08, top + th * 0.62)])
        pen.shape(tee, C.get("tee", "#6B3A22"))
        for s_ in (-1, 1):  # lapels + collar up
            lap = skia.Path()
            lap.moveTo(s_ * 0.2, top - 0.06)
            lap.lineTo(s_ * 0.42, top + 0.05)
            lap.lineTo(s_ * 0.3, top + th * 0.3)
            lap.lineTo(s_ * 0.1, top + th * 0.64)
            lap.close()
            pen.shape(lap, "#A87A40")
        belt = skia.Path()
        belt.addRoundRect(skia.Rect(-hw / 2 - 0.04, hip_y - 0.3, hw / 2 + 0.04, hip_y - 0.14), 0.04, 0.04)
        pen.shape(belt, "#8A6232")
        bk = skia.Path()
        bk.addRect(skia.Rect(-0.1, hip_y - 0.32, 0.1, hip_y - 0.12))
        pen.stroke(bk, pen.ow * 0.8, "#E0C070")
        for yy in (0.72, 0.86):
            for s_ in (-1, 1):
                pen.shape(oval(s_ * 0.2, top + th * yy - 0.05, 0.045, 0.045), "#4A3420", outline=False)
    elif "butler" in ex:
        v = skia.Path()  # white shirt front + lapels
        v.moveTo(-0.28, top + 0.02)
        v.lineTo(0.28, top + 0.02)
        v.lineTo(0.0, top + th * 0.62)
        v.close()
        pen.shape(v, "#F4F1EA")
        bow = skia.Path()
        bow.moveTo(0, top + 0.12)
        bow.lineTo(-0.2, top + 0.02)
        bow.lineTo(-0.2, top + 0.24)
        bow.close()
        bow.moveTo(0, top + 0.12)
        bow.lineTo(0.2, top + 0.02)
        bow.lineTo(0.2, top + 0.24)
        bow.close()
        pen.shape(bow, "#111111")
        for k in (0.35, 0.55):
            pen.shape(oval(0.0, top + th * k + 0.15, 0.04, 0.04), "#C9A54A", outline=False)
    elif "chef_jacket" in ex:
        for s_ in (-1, 1):
            for k in (0.25, 0.45, 0.65):
                pen.shape(oval(s_ * 0.18, top + th * k, 0.05, 0.05), "#2A2A30", outline=False)
        pen.shape(smooth_path([(-0.28, top + 0.02), (0.28, top + 0.02), (0.12, top + 0.22), (0, top + 0.3), (-0.12, top + 0.22)]),
                  "#C8322E")
    elif "cardigan" in ex:
        pen.shape(smooth_path([(-0.22, top + 0.02), (0.22, top + 0.02), (0.0, top + 0.3)]), "#F4F1EA")
        q2 = skia.Path()
        q2.moveTo(0, top + 0.3)
        q2.lineTo(0, hip_y)
        pen.stroke(q2, pen.ow * 0.7)
        for k in (0.4, 0.6, 0.8):
            pen.shape(oval(0.08, top + th * k, 0.04, 0.04), "#E0C070", outline=False)
    elif "scarf" in ex:
        wrap = smooth_path([(-0.36, top - 0.06), (0.36, top - 0.06), (0.3, top + 0.16), (-0.3, top + 0.16)])
        pen.shape(wrap, "#2E5A8A", "#244870")
        tail = skia.Path()
        tail.addRoundRect(skia.Rect(0.1, top + 0.08, 0.34, top + th * 0.75), 0.06, 0.06)
        pen.shape(tail, "#2E5A8A", "#244870")
        for k in (0.35, 0.55):
            q2 = skia.Path()
            q2.moveTo(0.1, top + th * k)
            q2.lineTo(0.34, top + th * k)
            pen.stroke(q2, 0.06, "#F4F1EA")
    elif "overalls" in ex:
        bib = skia.Path()
        bib.addRoundRect(skia.Rect(-hw * 0.42, top + th * 0.38, hw * 0.42, hip_y + 0.08), 0.06, 0.06)
        pen.shape(bib, C["pants"], C["pants_sh"])
        for s in (-1, 1):
            st = skia.Path()
            st.moveTo(s * hw * 0.32, top + th * 0.4)
            st.lineTo(s * sw * 0.32, top + 0.02)
            pen.stroke(st, 0.12, C["pants_sh"])
            pen.shape(oval(s * hw * 0.3, top + th * 0.43, 0.05, 0.05), "#D8C27A")
        pk = skia.Path()
        pk.addRect(skia.Rect(-0.18, top + th * 0.52, 0.18, top + th * 0.68))
        pen.stroke(pk, pen.ow * 0.6)
    elif "cravat" in ex:
        v = skia.Path()
        v.moveTo(-0.24, top + 0.02)
        v.lineTo(0.24, top + 0.02)
        v.lineTo(0, top + th * 0.45)
        v.close()
        pen.shape(v, "#F4F1EA")
        pen.shape(smooth_path([(0, top + 0.08), (0.14, top + 0.2), (0.0, top + 0.42), (-0.14, top + 0.2)]), "#B8322E")
        if "watch_chain" in ex:
            ch = skia.Path()
            ch.moveTo(-hw * 0.4, top + th * 0.62)
            ch.quadTo(0, top + th * 0.78, hw * 0.42, top + th * 0.6)
            pen.stroke(ch, pen.ow * 0.7, "#E0B84A")
    else:
        pen.stroke(q)
    if "apron" in ex:
        ap = smooth_path([(-hw * 0.38, top + th * 0.45), (hw * 0.38, top + th * 0.45), (hw * 0.55, hip_y + 0.42),
                          (0, hip_y + 0.47), (-hw * 0.55, hip_y + 0.42)])
        pen.shape(ap, "#F6F2EA", "#DCD5C8")
        tie = skia.Path()
        tie.moveTo(-hw * 0.45, top + th * 0.5)
        tie.lineTo(hw * 0.45, top + th * 0.5)
        pen.stroke(tie, 0.08, "#DCD5C8")


def _draw_arm(pen, C, pose, side, key_, sh, elbow, hand, preset):
    l = C["limb_w"]
    sleeve_col, sleeve_sh = C["shirt"], C["shirt_sh"]
    if C["sleeves"] == "long":
        pen.capsule(*sh, *elbow, l * 1.55, sleeve_col, sleeve_sh)
        pen.capsule(*elbow, *hand, l * 1.45, sleeve_col, sleeve_sh)
        cuff = "#F4F1EA" if "butler" in C["extras"] or "cravat" in C["extras"] else sleeve_col
        hx_, hy_ = hand
        ex_, ey_ = elbow
        d = math.hypot(hx_ - ex_, hy_ - ey_) or 1
        cx_, cy_ = hx_ - (hx_ - ex_) / d * 0.12, hy_ - (hy_ - ey_) / d * 0.12
        pen.capsule(cx_, cy_, hx_ - (hx_ - ex_) / d * 0.03, hy_ - (hy_ - ey_) / d * 0.03, l * 1.5, cuff)
    else:
        pen.capsule(*sh, *elbow, l, C["skin"], C["skin_sh"])
        pen.capsule(*elbow, *hand, l * 0.95, C["skin"], C["skin_sh"])
        k = 0.62 if C["sleeves"] == "short" else 0.95
        mid = (sh[0] + (elbow[0] - sh[0]) * k, sh[1] + (elbow[1] - sh[1]) * k)
        pen.capsule(sh[0], sh[1] - 0.02, *mid, l * 1.75, sleeve_col, sleeve_sh)
    ang = math.atan2(hand[1] - elbow[1], hand[0] - elbow[0])
    kind = pose.get("hand_l" if side < 0 else "hand_r", "point" if preset in ("point", "point_up") else "open")
    _hand(pen, C, *hand, kind, ang, side)
    m = pen.c.getTotalMatrix()  # device-space hand + aim (for beams, props drawn by the shot)
    tip = (hand[0] + math.cos(ang) * 0.6, hand[1] + math.sin(ang) * 0.6)
    pose.setdefault("_hands", {})["l" if side < 0 else "r"] = (tuple(m.mapXY(*hand)), tuple(m.mapXY(*tip)))
    prop = pose.get("prop_l" if side < 0 else "prop_r")
    if callable(prop):
        prop(pen, hand[0], hand[1], ang, side)


# ================================================================ props (drawn in character units)
def prop_flashlight(on=1.0, length=4.5, color="#FFE7A8"):
    def draw(pen, x, y, ang, side):
        L = 0.55
        bx, by = x + math.cos(ang) * L * 0.2, y + math.sin(ang) * L * 0.2
        tx, ty = x + math.cos(ang) * L, y + math.sin(ang) * L
        pen.capsule(x - math.cos(ang) * 0.15, y - math.sin(ang) * 0.15, tx, ty, 0.2, "#3A3A40")
        pen.shape(oval(tx, ty, 0.14, 0.14), "#FFF3C8" if on > 0.1 else "#888888")
    return draw


def prop_notebook(pen, x, y, ang, side):
    r = skia.Path()
    r.addRoundRect(skia.Rect(x - 0.28, y - 0.4, x + 0.12, y + 0.12), 0.04, 0.04)
    pen.shape(r, "#E9DFC4")
    for k in range(3):
        q = skia.Path()
        q.moveTo(x - 0.22, y - 0.28 + k * 0.1)
        q.lineTo(x + 0.06, y - 0.28 + k * 0.1)
        pen.stroke(q, pen.ow * 0.4, "#8A7A5A")


def prop_towel(pen, x, y, ang, side):
    r = skia.Path()
    r.addRoundRect(skia.Rect(-0.45 if side > 0 else x - 0.1, y - 0.15, 0.45 if side > 0 else x + 0.8, y + 0.2), 0.06, 0.06)
    pen.shape(r, "#F4F1EA", "#D8D0C2")


def prop_cleaver(pen, x, y, ang, side):
    """Big kitchen cleaver (red herring), blade up."""
    pen.capsule(x, y + 0.05, x, y + 0.35, 0.13, "#5A3A22")
    blade = skia.Path()
    blade.addRoundRect(skia.Rect(x - 0.08, y - 0.62, x + 0.42, y - 0.02), 0.05, 0.05)
    pen.shape(blade, "#C8CED4", "#A8B0B8")
    pen.c.drawPath(oval(x + 0.3, y - 0.48, 0.05, 0.05), pen.p(INK))


def prop_papers(pen, x, y, ang, side):
    for k, dx in enumerate((0.0, 0.06)):
        r = skia.Path()
        r.addRoundRect(skia.Rect(x - 0.32 + dx, y - 0.5 + dx, x + 0.18 + dx, y + 0.12 + dx), 0.03, 0.03)
        pen.shape(r, "#FFFFFF" if k else "#F2EEE4")
    for k in range(4):
        q = skia.Path()
        q.moveTo(x - 0.22, y - 0.36 + k * 0.1)
        q.lineTo(x + 0.12, y - 0.36 + k * 0.1)
        pen.stroke(q, pen.ow * 0.4, "#6A6A80")


def prop_keys(pen, x, y, ang, side):
    """Car keys dangling from the fingers."""
    pen.stroke(oval(x, y + 0.2, 0.1, 0.1), pen.ow * 0.7, "#C9A24A")
    k = skia.Path()
    k.addRoundRect(skia.Rect(x - 0.06, y + 0.28, x + 0.06, y + 0.58), 0.03, 0.03)
    pen.shape(k, "#B8BEC4")
    pen.shape(oval(x + 0.05, y + 0.62, 0.1, 0.08), "#2A2A30")
