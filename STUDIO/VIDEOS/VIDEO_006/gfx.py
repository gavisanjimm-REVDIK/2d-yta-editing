"""gfx.py - VIDEO_006 overlays: section breadcrumb (hidden while a case stamp or the end card is up),
typed case-file stamps for the crime case, and the end card."""
import importlib.util
import sys
from pathlib import Path

import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "PIPELINE" / "twod"))
from kit import W, SAFE, rgb, clamp, text, EASE, typeface  # noqa: E402

_spec = importlib.util.spec_from_file_location("v005_gfx", HERE.parent / "VIDEO_005" / "gfx.py")
G5 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G5)
_spec = importlib.util.spec_from_file_location("v001_gfx", HERE.parent / "VIDEO_001" / "gfx.py")
G1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G1)

TYPE = "SpecialElite-Regular.ttf"
CPS = 26


def breadcrumb(sections, hide):
    inner = G5.breadcrumb(sections)

    def draw(c, t, al):
        if any(a <= t < b for a, b in hide):
            return
        inner(c, t, al)
    return draw


def case_stamps(stamps):
    """stamps: [(t0, t1, big, small)] typed at the top like a case file (time/place of the crime)."""
    def draw(c, t, al):
        for t0, t1, big, small in stamps:
            if not (t0 <= t < t1):
                continue
            a = clamp((t - t0) / 0.2) * (1 - clamp((t - (t1 - 0.25)) / 0.25))
            y = 175
            band = skia.Paint(AntiAlias=True, Color=rgb("#000000"))
            band.setAlphaf(0.35 * a)
            band.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 40))
            c.drawRect(skia.Rect(100, y - 90, W - 100, y + 105), band)
            n = int((t - t0) * CPS)
            typed = big[:n]
            if typed:
                text(c, typed, W / 2, y, 66, "#FFFFFF", face=TYPE, shadow=True, alpha=a, max_w=W - 2 * SAFE)
            if n < len(big) and int(t * 3) % 2 == 0:
                fw = skia.Font(typeface(TYPE), 66).measureText(typed)
                c.drawRect(skia.Rect.MakeXYWH(W / 2 + fw / 2 + 6, y - 52, 6, 60), skia.Paint(Color=rgb("#FFFFFF")))
            lw = (W - 2 * 170) * EASE["out"](clamp((t - t0) / 0.6))
            rule = skia.Paint(AntiAlias=True, Color=rgb("#FFFFFF"), StrokeWidth=3)
            rule.setAlphaf(0.75 * a)
            c.drawLine(W / 2 - lw / 2, y + 26, W / 2 + lw / 2, y + 26, rule)
            ns = int((t - t0 - len(big) / CPS - 0.1) * CPS)
            if small and ns > 0:
                text(c, small[:ns], W / 2, y + 80, 40, "#FFE6A8", face=TYPE, shadow=True, alpha=a * 0.95, max_w=W - 2 * SAFE)
    return draw


def end_card(t0):
    return G1.end_card(t0, "WHO DID IT?", "COMMENT YOUR SUSPECT!")
