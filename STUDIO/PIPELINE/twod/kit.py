"""kit.py - timing, text and camera helpers for 2D (Skia) shots.

- key(t, [(t0, v0, ease), (t1, v1, ease), ...])  eased keyframes (numbers or tuples)
- blink(t, seed)                                  0..1 lid closure
- mouth_open(t, words)                            0..1 from word timing (timing.json)
- text(canvas, s, x, y, ...)                      drawing with shrink-to-fit inside safe area
- flicker(t, seed)                                light flicker 0..1
- PerspCam                                        one-point perspective camera for rooms/corridors
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import skia

STUDIO = Path(__file__).resolve().parents[2]
FONTS = STUDIO / "ASSETS" / "fonts"
W, H, FPS = 1080, 1920, 30
SAFE = 36


# ---------------------------------------------------------------- easing / keys
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def lerp(a, b, u):
    if isinstance(a, (tuple, list)):
        return type(a)(lerp(x, y, u) for x, y in zip(a, b))
    return a + (b - a) * u


EASE = {
    "lin": lambda u: u,
    "in": lambda u: u * u * u,
    "out": lambda u: 1 - (1 - u) ** 3,
    "io": lambda u: 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2,
    "back": lambda u: 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
    "elastic": lambda u: 1 if u >= 1 else (0 if u <= 0 else
                                          2 ** (-10 * u) * math.sin((u * 10 - .75) * 2 * math.pi / 3) + 1),
    "step": lambda u: 0.0 if u < 1 else 1.0,
}


def key(t, keys, default_ease="io"):
    """keys: list of (time, value[, ease]). Ease applies on the segment ending at that key."""
    if t <= keys[0][0]:
        return keys[0][1]
    for i in range(1, len(keys)):
        k0, k1 = keys[i - 1], keys[i]
        if t <= k1[0]:
            e = EASE[k1[2] if len(k1) > 2 else default_ease]
            u = (t - k0[0]) / max(k1[0] - k0[0], 1e-9)
            return lerp(k0[1], k1[1], e(clamp(u)))
    return keys[-1][1]


def smooth_noise(t, seed=0, freq=1.0):
    """Cheap smooth 1D noise in -1..1 (sum of sines with seeded phases)."""
    r = np.random.default_rng(seed)
    ph, fr = r.uniform(0, 6.28, 3), r.uniform(0.7, 1.3, 3)
    return float(sum(math.sin(t * freq * f * 2 * math.pi + p) for f, p in zip(fr, ph)) / 3)


def blink(t, seed=0, every=3.2, dur=0.14):
    r = np.random.default_rng(seed)
    offs = r.uniform(0, every)
    period = every * (0.8 + 0.4 * ((int((t + offs) / every) * 7919 + seed) % 10) / 10)
    ph = (t + offs) % period
    if ph < dur:
        return math.sin(ph / dur * math.pi)
    return 0.0


def mouth_open(t, words, who=None, lead=0.03):
    """Viseme-ish openness from word timing; vowels approximated by a syllable wobble."""
    for w in words:
        if who and w.get("who") != who:
            continue
        s, e = w["start"] - lead, w["end"]
        if s <= t <= e:
            syl = max(1, len([c for c in w["word"].lower() if c in "aeiouy"]))
            u = (t - s) / max(e - s, 1e-3)
            return 0.35 + 0.65 * abs(math.sin(u * syl * math.pi))
    return 0.0


def flicker(t, seed=0, amount=0.3):
    v = smooth_noise(t, seed, 6) * 0.5 + 0.5
    drop = 1.0 if (int(t * 30) * 1103515245 + seed) % 97 > 3 else 0.2
    return clamp(1 - amount + amount * v) * drop


# ---------------------------------------------------------------- colour / paint
def rgb(h, a=255):
    h = h.lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def paint(color, aa=True, stroke=None, alpha=None, blend=None):
    p = skia.Paint(AntiAlias=aa, Color=rgb(color) if isinstance(color, str) else color)
    if alpha is not None:
        p.setAlphaf(alpha)
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
        p.setStrokeJoin(skia.Paint.kRound_Join)
    if blend:
        p.setBlendMode(blend)
    return p


# ---------------------------------------------------------------- text
@lru_cache(maxsize=32)
def typeface(name="Anton-Regular.ttf"):
    p = FONTS / name
    if p.exists():
        return skia.Typeface.MakeFromFile(str(p))
    return skia.Typeface("DejaVu Sans", skia.FontStyle.Bold())


def text_width(s, size, face="Anton-Regular.ttf"):
    return skia.Font(typeface(face), size).measureText(s)


def text(canvas, s, x, y, size=72, color="#FFFFFF", face="Anton-Regular.ttf", align="center",
         outline=0, outline_color="#000000", shadow=True, max_w=None, alpha=1.0, clamp_safe=True):
    """Draw single-line text; shrinks to fit max_w (default: safe width). Returns final size."""
    max_w = max_w or (W - 2 * SAFE)
    while size > 10 and text_width(s, size, face) > max_w:
        size *= 0.95
    font = skia.Font(typeface(face), size)
    w = font.measureText(s)
    x0 = {"center": x - w / 2, "left": x, "right": x - w}[align]
    if clamp_safe:  # only valid without a canvas transform
        x0 = clamp(x0, SAFE, W - SAFE - w)
    blob = skia.TextBlob(s, font)
    if shadow:
        sp = paint("#000000", alpha=0.45 * alpha)
        sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.06))
        canvas.drawTextBlob(blob, x0 + size * 0.03, y + size * 0.05, sp)
    if outline:
        canvas.drawTextBlob(blob, x0, y, paint(outline_color, stroke=outline, alpha=alpha))
    canvas.drawTextBlob(blob, x0, y, paint(color, alpha=alpha))
    return size


# ---------------------------------------------------------------- perspective camera
class PerspCam:
    """One-point perspective. World: x right, y up (height), z depth (away from camera).

    project(x, y, z) -> (sx, sy, scale). Characters: draw at scale returned for their feet depth.
    """

    def __init__(self, focal=900, cam_x=0.0, cam_y=1.6, cam_z=0.0, horizon=None, cx=W / 2):
        self.f, self.cx = focal, cx
        self.x, self.y, self.z = cam_x, cam_y, cam_z
        self.hy = horizon if horizon is not None else H * 0.42

    def project(self, x, y, z):
        d = max(z - self.z, 0.05)
        s = self.f / d
        return self.cx + (x - self.x) * s, self.hy - (y - self.y) * s, s

    def quad(self, pts):
        path = skia.Path()
        for i, p in enumerate(pts):
            sx, sy, _ = self.project(*p)
            (path.moveTo if i == 0 else path.lineTo)(sx, sy)
        path.close()
        return path

    def box_room(self, canvas, width=6, height=3, depth=10, z0=0.5, colors=None):
        """Draw floor/ceiling/walls/back of a simple room. colors: dict floor/ceil/left/right/back."""
        c = {"floor": "#8a6a52", "ceil": "#d8d2c8", "left": "#c9bfae", "right": "#bdb3a2", "back": "#d2c8b6",
             **(colors or {})}
        hw = width / 2
        z1 = z0 + depth
        faces = {
            "floor": [(-hw, 0, z0), (hw, 0, z0), (hw, 0, z1), (-hw, 0, z1)],
            "ceil": [(-hw, height, z0), (hw, height, z0), (hw, height, z1), (-hw, height, z1)],
            "left": [(-hw, 0, z0), (-hw, height, z0), (-hw, height, z1), (-hw, 0, z1)],
            "right": [(hw, 0, z0), (hw, height, z0), (hw, height, z1), (hw, 0, z1)],
            "back": [(-hw, 0, z1), (hw, 0, z1), (hw, height, z1), (-hw, height, z1)],
        }
        for k in ("back", "ceil", "floor", "left", "right"):
            canvas.drawPath(self.quad(faces[k]), paint(c[k]))
        return faces
