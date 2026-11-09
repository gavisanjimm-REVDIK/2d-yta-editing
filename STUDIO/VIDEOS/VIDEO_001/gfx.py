"""gfx.py - VIDEO_001 overlays: parchment case file (recap) + end card question. Safe area respected."""
import sys
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "PIPELINE" / "twod"))
from kit import W, H, SAFE, rgb, clamp, text, EASE  # noqa: E402

SERIF = "Cinzel-VF.ttf"
INK = "#3A2414"


def _parchment(c, x, y, w, h, alpha):
    p = skia.Path()
    p.moveTo(x, y + 14)
    for k in range(9):  # slightly ragged top/bottom edges
        p.lineTo(x + w * (k + 1) / 9, y + (6 if k % 2 else 18))
    p.lineTo(x + w, y + h - 14)
    for k in range(9):
        p.lineTo(x + w - w * (k + 1) / 9, y + h - (6 if k % 2 else 18))
    p.close()
    sh = skia.Paint(AntiAlias=True, Color=rgb("#000000"))
    sh.setAlphaf(0.35 * alpha)
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
    c.save()
    c.translate(8, 14)
    c.drawPath(p, sh)
    c.restore()
    grad = skia.GradientShader.MakeRadial(skia.Point(x + w / 2, y + h / 2), w * 0.75,
                                          [rgb("#F3E3BF"), rgb("#D9C092")])
    fp = skia.Paint(AntiAlias=True, Shader=grad)
    fp.setAlphaf(alpha)
    c.drawPath(p, fp)
    lp = skia.Paint(AntiAlias=True, Color=rgb(INK), Style=skia.Paint.kStroke_Style, StrokeWidth=5)
    lp.setAlphaf(alpha)
    c.drawPath(p, lp)


def case_file(t_oliver, t_sophie, t_daniel):
    rows = [(t_oliver, "OLIVER", "KITCHEN", "never left"),
            (t_sophie, "SOPHIE", "UPSTAIRS", "heard thunder"),
            (t_daniel, "DANIEL", "BASEMENT", "saw lightning")]

    def draw(c, t, al):
        x, y, w, h = SAFE + 30, 150, W - 2 * SAFE - 60, 600
        c.save()
        k = EASE["back"](clamp(al))
        c.translate(W / 2, y + h / 2)
        c.scale(0.9 + 0.1 * k, 0.9 + 0.1 * k)
        c.rotate(-1.5)
        c.translate(-W / 2, -(y + h / 2))
        _parchment(c, x, y, w, h, al)
        text(c, "CASE FILE", W / 2, y + 105, 78, INK, face=SERIF, shadow=False, alpha=al, max_w=w - 80)
        lp = skia.Paint(AntiAlias=True, Color=rgb(INK), StrokeWidth=4)
        lp.setAlphaf(al)
        c.drawLine(x + 70, y + 140, x + w - 70, y + 140, lp)
        for i, (tr, name, place, note) in enumerate(rows):
            a = clamp((t - tr + 0.1) / 0.25) * al
            if a <= 0:
                continue
            ry = y + 240 + i * 130
            text(c, name, x + 60, ry, 54, "#8A1F1A", face=SERIF, align="left", shadow=False, alpha=a, max_w=300)
            text(c, place, x + w - 60, ry, 54, INK, face=SERIF, align="right", shadow=False, alpha=a, max_w=330)
            text(c, note, x + w - 60, ry + 46, 32, "#6A4A2A", face=SERIF, align="right", shadow=False, alpha=a,
                 max_w=330)
        c.restore()
    return draw


def end_card(t0):
    def draw(c, t, al):
        u = clamp((t - t0) / 0.35)
        s = EASE["back"](u)
        c.save()
        c.translate(W / 2, 300)
        c.scale(0.6 + 0.4 * s, 0.6 + 0.4 * s)
        text(c, "WHO IS LYING?", 0, 0, 150, "#FFFFFF", face="Anton-Regular.ttf", outline=16, alpha=u, clamp_safe=False,
             max_w=W - 2 * SAFE)
        c.restore()
        u2 = clamp((t - t0 - 0.6) / 0.3)
        if u2 > 0:
            c.save()
            c.translate(W / 2, 1640)
            k = 0.85 + 0.15 * EASE["back"](u2)
            c.scale(k, k)
            text(c, "COMMENT YOUR ANSWER!", 0, 0, 92, "#FFD23F", face="Anton-Regular.ttf", outline=12, alpha=u2, clamp_safe=False,
                 max_w=W - 2 * SAFE)
            c.restore()
    return draw
