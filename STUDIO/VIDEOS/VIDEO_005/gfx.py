"""gfx.py - VIDEO_005 overlays: section breadcrumb at the top (where are we in the lesson)."""
import sys
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "PIPELINE" / "twod"))
from kit import W, rgb, clamp, text, text_width, EASE  # noqa: E402


def breadcrumb(sections):
    def draw(c, t, al):
        cur = None
        for i, (t0, name) in enumerate(sections):
            if t >= t0:
                cur = i
        if cur is None:
            return
        t0, name = sections[cur]
        u = EASE["out"](clamp((t - t0) / 0.35))
        size = 38
        tw = text_width(name, size, "Anton-Regular.ttf")
        pw, ph = tw + 70, 64
        x, y = W / 2 - pw / 2, 118 - 20 * (1 - u)
        p = skia.Paint(AntiAlias=True, Color=rgb("#1A120C"))
        p.setAlphaf(0.78 * u)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, pw, ph), 32, 32), p)
        q = skia.Paint(AntiAlias=True, Color=rgb("#FFD27A"), Style=skia.Paint.kStroke_Style, StrokeWidth=3)
        q.setAlphaf(u)
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, pw, ph), 32, 32), q)
        text(c, name, W / 2, y + 46, size, "#FFD27A", face="Anton-Regular.ttf", shadow=False, alpha=u, clamp_safe=False)
        n = len(sections)  # progress dots
        for i in range(n):
            cx = W / 2 - (n - 1) * 14 + i * 28
            d = skia.Paint(AntiAlias=True, Color=rgb("#FFD27A" if i <= cur else "#6A5A4A"))
            d.setAlphaf(u)
            c.drawCircle(cx, y + ph + 26, 7, d)
    return draw
