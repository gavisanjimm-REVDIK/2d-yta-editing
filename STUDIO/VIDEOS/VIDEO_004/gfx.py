"""gfx.py - VIDEO_004 overlays: typewriter date stamps (top), white dip transition, end question card."""
import math
import sys
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "PIPELINE" / "twod"))
from kit import W, H, SAFE, rgb, clamp, text, EASE, typeface  # noqa: E402

TYPE = "SpecialElite-Regular.ttf"
CPS = 26  # typed characters per second


def _typed(s, t, t0):
    n = int(max(0.0, t - t0) * CPS)
    return s[:n], n < len(s)


def date_stamps(stamps):
    """stamps: [(t, big, small|callable|None)]. Each stamp types itself in at the top, the previous one is
    wiped out quickly (time skip). Thin rule + blinking cursor, soft shadow for any background."""
    def draw(c, t, al):
        cur = None
        for i, st in enumerate(stamps):
            if t >= st[0]:
                cur = i
        if cur is None:
            return
        t0, big, small = stamps[cur]
        nxt = stamps[cur + 1][0] if cur + 1 < len(stamps) else 1e9
        out = clamp((t - (nxt - 0.18)) / 0.18)  # wipe before the next stamp
        a = 1 - out
        typed, typing = _typed(big, t, t0)
        y = 175
        # dark soft band so white type reads on bright skies too
        band = skia.Paint(AntiAlias=True, Color=rgb("#000000"))
        band.setAlphaf(0.28 * a)
        band.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
        c.drawRect(skia.Rect(120, y - 90, W - 120, y + 95), band)
        if typed:
            text(c, typed, W / 2, y, 72, "#FFFFFF", face=TYPE, shadow=True, alpha=a, max_w=W - 2 * SAFE)
        if typing and int(t * 3) % 2 == 0:
            fw = skia.Font(typeface(TYPE), 72).measureText(typed)
            c.drawRect(skia.Rect.MakeXYWH(W / 2 + fw / 2 + 6, y - 56, 6, 64), skia.Paint(Color=rgb("#FFFFFF")))
        lw = (W - 2 * 170) * EASE["out"](clamp((t - t0) / 0.6))
        rule = skia.Paint(AntiAlias=True, Color=rgb("#FFFFFF"), StrokeWidth=3)
        rule.setAlphaf(0.75 * a)
        c.drawLine(W / 2 - lw / 2, y + 26, W / 2 + lw / 2, y + 26, rule)
        if small is not None:
            sm = small(t) if callable(small) else small
            t_small = t0 + len(big) / CPS + 0.1
            styped, _ = _typed(sm, t, t_small) if not callable(small) else (sm, False)
            if callable(small) or styped:
                text(c, styped, W / 2, y + 80, 40, "#FFE6A8", face=TYPE, shadow=True, alpha=a * 0.95,
                     max_w=W - 2 * SAFE)
    return draw


def white_dip(t_peak, t_end):
    """Over-exposure to white ('nobody noticed the light') then fade into the next scene."""
    def draw(c, t, al):
        if t < t_peak:
            u = clamp((t - (t_peak - 0.6)) / 0.6) ** 2
        else:
            u = 1 - clamp((t - t_peak) / max(t_end + 0.6 - t_peak, 0.1))
        p = skia.Paint(Color=rgb("#FFF8EC"))
        p.setAlphaf(clamp(u))
        c.drawRect(skia.Rect(0, 0, W, H), p)
    return draw


def end_card(t0):
    def draw(c, t, al):
        u = clamp((t - t0) / 0.6)
        dim = skia.Paint(Color=rgb("#140C08"))
        dim.setAlphaf(0.35 * u)
        c.drawRect(skia.Rect(0, 0, W, H), dim)
        c.save()
        c.translate(W / 2, 700)
        k = 0.9 + 0.1 * EASE["out"](u)
        c.scale(k, k)
        text(c, "WOULD YOU", 0, -70, 110, "#FFFFFF", face="Anton-Regular.ttf", outline=12, alpha=u, clamp_safe=False,
             max_w=W - 2 * SAFE)
        text(c, "ERASE EVIL?", 0, 70, 150, "#FFD27A", face="Anton-Regular.ttf", outline=14, alpha=u, clamp_safe=False,
             max_w=W - 2 * SAFE)
        c.restore()
        u2 = clamp((t - t0 - 0.9) / 0.5)
        if u2 > 0:
            text(c, "tell us in the comments", W / 2, 900, 46, "#FFFFFF", face=TYPE, alpha=u2, max_w=W - 2 * SAFE)
    return draw
