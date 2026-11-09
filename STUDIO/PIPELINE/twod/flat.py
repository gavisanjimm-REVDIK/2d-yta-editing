"""flat.py - 2D cut-out puppet (Skia vector) + painting helpers.

Puppet look: flat fill + one cel-shadow tone + optional rim light.
draw_puppet(canvas, x, y, scale, pose, look)  -- (x, y) = point between feet, scale 1 = ~900 px tall.

pose keys (all optional):
  eyes_x, eyes_y      pupil offset -1..1
  lids                0 open .. 1 closed (blink)
  brow_l, brow_r      -1 angry .. +1 raised
  mouth               "smile" | "flat" | "open" | "o" | "frown" | "grin"
  talk                0..1 mouth openness from word timing
  tilt                head tilt degrees
  turn                -1..1 fake 3/4 turn (features slide, head squashes)
  arm_l, arm_r        (shoulder_deg, elbow_deg), 0 = hanging down, + = forward/out
  walk                phase 0..1 for front/back stepping walk (bob + leg alternate)
  side                None | "left" | "right" : side view (walk/run cycle with `walk`, `run`=True)
  crouch              0..1
  breathe             0..1 phase (chest bob)
  held_r, held_l      callable(canvas, hand_x, hand_y, scale) to draw a held item
look keys: skin, skin_shadow, hair, shirt, shirt_shadow, pants, shoes, eye, rim (hex or None), hair_style
"""
from __future__ import annotations

import math

import skia

from kit import paint, rgb, W, H

MASCOT = {  # placeholder palette until reference arrives - edit in ASSETS/mascot/mascot_spec.json
    "skin": "#F2C6A0", "skin_shadow": "#D9A47E", "hair": "#3B2A20", "hair_shadow": "#2A1D16",
    "shirt": "#F07A1E", "shirt_shadow": "#C85F12", "pants": "#3A4A63", "pants_shadow": "#2B3850",
    "shoes": "#2B2B2B", "eye": "#2A1F1A", "rim": "#FFE9C8", "hair_style": "messy",
}


# ---------------------------------------------------------------- painting helpers
def linear_grad(canvas, rect, c0, c1, vertical=True):
    x0, y0, x1, y1 = rect
    pts = [skia.Point(x0, y0), skia.Point(x0, y1) if vertical else skia.Point(x1, y0)]
    sh = skia.GradientShader.MakeLinear(pts, [rgb(c0), rgb(c1)])
    canvas.drawRect(skia.Rect(x0, y0, x1, y1), skia.Paint(Shader=sh))


def glow(canvas, x, y, r, color, alpha=0.6):
    """Painted additive glow."""
    c = rgb(color)
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [skia.ColorSetA(c, int(255 * alpha)),
                                                               skia.ColorSetA(c, 0)])
    canvas.drawCircle(x, y, r, skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))


def vignette(canvas, strength=0.55, w=W, h=H):
    sh = skia.GradientShader.MakeRadial(skia.Point(w / 2, h / 2), max(w, h) * 0.75,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, int(255 * strength))],
                                        [0.45, 1.0])
    canvas.drawRect(skia.Rect(0, 0, w, h), skia.Paint(Shader=sh))


def blob(points, closed=True):
    """Smooth closed shape through points (Catmull-Rom -> cubic)."""
    p = skia.Path()
    n = len(points)
    if n < 3:
        return p
    p.moveTo(*points[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0, p1 = points[(i - 1) % n], points[i]
        p2, p3 = points[(i + 1) % n], points[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def rrect(canvas, x, y, w, h, r, color, **kw):
    canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r), paint(color, **kw))


def capsule(canvas, x0, y0, x1, y1, width, color):
    canvas.drawLine(x0, y0, x1, y1, paint(color, stroke=width))


def _shadowed(canvas, path, base, shadow, light_dir=(-1, -1), shift=0.12, size=100):
    """Fill path with base, then cel shadow = path minus path shifted toward light."""
    canvas.drawPath(path, paint(base))
    lit = skia.Path(path)
    lit.offset(light_dir[0] * size * shift, light_dir[1] * size * shift)
    sh = skia.Op(path, lit, skia.PathOp.kDifference_PathOp)
    if sh:
        canvas.drawPath(sh, paint(shadow))


def _rim(canvas, path, color, size, light_dir=(1, -0.3)):
    if not color:
        return
    off = skia.Path(path)
    off.offset(-light_dir[0] * size * 0.012, -light_dir[1] * size * 0.012)
    edge = skia.Op(path, off, skia.PathOp.kDifference_PathOp)
    if edge:
        canvas.drawPath(edge, paint(color, alpha=0.7))


# ---------------------------------------------------------------- puppet
def _limb(canvas, sx, sy, a_sh, a_el, l1, l2, w, color, shadow):
    a1 = math.radians(a_sh)
    ex, ey = sx + math.sin(a1) * l1, sy + math.cos(a1) * l1
    a2 = a1 + math.radians(a_el)
    hx, hy = ex + math.sin(a2) * l2, ey + math.cos(a2) * l2
    capsule(canvas, sx, sy, ex, ey, w, shadow)
    capsule(canvas, sx, sy, ex, ey, w * 0.8, color)
    capsule(canvas, ex, ey, hx, hy, w * 0.75, color)
    return hx, hy


def draw_puppet(canvas, x, y, scale=1.0, pose=None, look=None):
    p = pose or {}
    L = {**MASCOT, **(look or {})}
    s = 900 * scale
    canvas.save()
    canvas.translate(x, y)
    crouch = p.get("crouch", 0.0)
    walk = p.get("walk")
    bob = 0.0
    if walk is not None:
        bob = abs(math.sin(walk * 2 * math.pi)) * 0.015 * s
    breathe = math.sin(p.get("breathe", 0.0) * 2 * math.pi) * 0.004 * s
    hip_y = -0.42 * s * (1 - 0.35 * crouch) - bob
    side = p.get("side")

    # legs
    leg_len = 0.42 * s * (1 - 0.35 * crouch)
    lw = 0.075 * s
    for i, sgn in enumerate((-1, 1)):
        if walk is not None and side:
            ph = walk * 2 * math.pi + i * math.pi
            amp = 35 if p.get("run") else 22
            ang = math.sin(ph) * amp
            knee = max(0, -math.cos(ph)) * (60 if p.get("run") else 30)
            lx = 0
        else:
            ang, knee = 0, 0
            lx = sgn * 0.055 * s
        a = math.radians(ang)
        kx = lx + math.sin(a) * leg_len * 0.5
        ky = hip_y + math.cos(a) * leg_len * 0.5
        a2 = a - math.radians(knee)
        fx = kx + math.sin(a2) * leg_len * 0.5
        fy = ky + math.cos(a2) * leg_len * 0.5
        if walk is not None and not side:
            fy -= max(0, math.sin(walk * 2 * math.pi + i * math.pi)) * 0.03 * s
        capsule(canvas, lx, hip_y, kx, ky, lw, L["pants"])
        capsule(canvas, kx, ky, fx, fy, lw * 0.95, L["pants"])
        rrect(canvas, fx - lw * 0.7 + (lw * 0.4 if side == "right" else -lw * 0.4 if side == "left" else 0),
              fy - lw * 0.15, lw * 1.4, lw * 0.6, lw * 0.3, L["shoes"])

    # torso (shirt)
    tw, th = 0.30 * s, 0.36 * s
    ty = hip_y - th + breathe
    torso = blob([(-tw / 2, ty + th * 0.15), (0, ty - th * 0.02), (tw / 2, ty + th * 0.15),
                  (tw * 0.52, ty + th * 0.7), (tw * 0.45, ty + th * 1.03), (-tw * 0.45, ty + th * 1.03),
                  (-tw * 0.52, ty + th * 0.7)])
    _shadowed(canvas, torso, L["shirt"], L["shirt_shadow"], (-1, -0.6), 0.1, tw)
    _rim(canvas, torso, L.get("rim"), s)

    # arms
    sh_y = ty + th * 0.12
    hands = {}
    for side_k, sgn in (("arm_l", -1), ("arm_r", 1)):
        a_sh, a_el = p.get(side_k, (8, 5))
        hx, hy = _limb(canvas, sgn * tw * 0.47, sh_y, sgn * a_sh, sgn * a_el, 0.17 * s, 0.16 * s,
                       0.07 * s, L["shirt"], L["shirt_shadow"])
        canvas.drawCircle(hx, hy, 0.035 * s, paint(L["skin"]))
        hands[side_k] = (hx, hy)
    for k, hk in (("held_r", "arm_r"), ("held_l", "arm_l")):
        if callable(p.get(k)):
            p[k](canvas, *hands[hk], scale)

    # neck + head
    hy0 = ty - 0.02 * s
    capsule(canvas, 0, ty + 0.02 * s, 0, hy0, 0.06 * s, L["skin_shadow"])
    canvas.save()
    canvas.translate(0, hy0)
    canvas.rotate(p.get("tilt", 0.0))
    turn = max(-1.0, min(1.0, p.get("turn", 0.0)))
    hw, hh = 0.25 * s * (1 - 0.12 * abs(turn)), 0.27 * s
    head = blob([(0, -hh), (hw * 0.5, -hh * 0.93), (hw * 0.5, -hh * 0.45), (hw * 0.46, -hh * 0.2),
                 (hw * 0.3, -hh * 0.02), (0, 0), (-hw * 0.3, -hh * 0.02), (-hw * 0.46, -hh * 0.2),
                 (-hw * 0.5, -hh * 0.45), (-hw * 0.5, -hh * 0.93)])
    _shadowed(canvas, head, L["skin"], L["skin_shadow"], (-1, -0.5), 0.08, hw)
    # ears
    for sgn in (-1, 1):
        if sgn * turn > 0.5:
            continue
        canvas.drawOval(skia.Rect.MakeXYWH(sgn * hw * 0.5 - 0.03 * s, -hh * 0.5, 0.06 * s, 0.08 * s),
                        paint(L["skin_shadow"]))
    # hair (messy cap)
    fx_off = turn * hw * 0.22
    hair_pts = [(-hw * 0.56, -hh * 0.5), (-hw * 0.58, -hh * 0.9), (-hw * 0.3, -hh * 1.12),
                (hw * 0.1, -hh * 1.16), (hw * 0.45, -hh * 1.05), (hw * 0.6, -hh * 0.8), (hw * 0.55, -hh * 0.55),
                (hw * 0.35, -hh * 0.72), (fx_off + hw * 0.1, -hh * 0.66), (fx_off - hw * 0.15, -hh * 0.76),
                (-hw * 0.35, -hh * 0.68)]
    hair = blob(hair_pts)
    _shadowed(canvas, hair, L["hair"], L["hair_shadow"], (-1, -1), 0.06, hw)
    _rim(canvas, hair, L.get("rim"), s)

    # face
    ex = 0.11 * s
    ey = -hh * 0.48
    er = 0.045 * s
    lids = max(p.get("lids", 0.0), 0.0)
    for i, sgn in enumerate((-1, 1)):
        cx = sgn * ex * (1 - 0.25 * abs(turn) * (1 if sgn * turn < 0 else 0.4)) + fx_off
        canvas.drawOval(skia.Rect.MakeXYWH(cx - er, ey - er * 1.2, er * 2, er * 2.4), paint("#FFFFFF"))
        px = cx + p.get("eyes_x", 0) * er * 0.45
        py = ey + p.get("eyes_y", 0) * er * 0.5
        canvas.drawCircle(px, py, er * 0.62, paint(L["eye"]))
        canvas.drawCircle(px - er * 0.2, py - er * 0.25, er * 0.18, paint("#FFFFFF"))
        if lids > 0.01:  # lid clipped to the eye shape, with a dark lash line on its edge
            canvas.save()
            canvas.clipRRect(skia.RRect.MakeOval(skia.Rect.MakeXYWH(cx - er * 1.02, ey - er * 1.22,
                                                                     er * 2.04, er * 2.44)), doAntiAlias=True)
            lid_y = ey - er * 1.25 + er * 2.5 * lids
            canvas.drawRect(skia.Rect(cx - er * 1.1, ey - er * 1.3, cx + er * 1.1, lid_y), paint(L["skin_shadow"]))
            canvas.drawLine(cx - er * 1.1, lid_y, cx + er * 1.1, lid_y, paint(L["eye"], stroke=er * 0.18))
            canvas.restore()
        brow = p.get("brow_l" if sgn < 0 else "brow_r", 0.0)
        by = ey - er * 1.6 - brow * er * 0.5
        tilt = (-brow * 0.3 if brow < 0 else brow * 0.15) * sgn
        canvas.drawLine(cx - er, by + tilt * er * 2, cx + er, by - tilt * er * 2,
                        paint(L["hair"], stroke=0.018 * s))

    # mouth
    my = -hh * 0.2
    mx = fx_off * 1.1
    mw = 0.07 * s
    talk = p.get("talk", 0.0)
    shape = p.get("mouth", "smile")
    if talk > 0.05 or shape in ("open", "o"):
        op = max(talk, 0.6 if shape in ("open", "o") else 0)
        ww = mw * (0.6 if shape == "o" else 1.0)
        rect = skia.Rect(mx - ww, my - op * mw * 0.3, mx + ww, my + op * mw * 0.9)
        canvas.drawOval(rect, paint("#5A2320"))
        canvas.drawOval(skia.Rect(mx - ww * 0.6, rect.bottom() - op * mw * 0.35, mx + ww * 0.6, rect.bottom()),
                        paint("#E07A7A"))
    else:
        curve = {"smile": 0.35, "grin": 0.5, "flat": 0.0, "frown": -0.35}.get(shape, 0.3)
        path = skia.Path()
        path.moveTo(mx - mw, my)
        path.quadTo(mx, my + curve * mw * 1.4, mx + mw, my)
        canvas.drawPath(path, paint("#5A2320", stroke=0.016 * s))
    canvas.restore()
    canvas.restore()
    return hands
