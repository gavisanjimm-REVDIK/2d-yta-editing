"""Profile picture of the mascot (1080x1080, safe for Instagram's circle crop).
python STUDIO/ASSETS/branding/make_pfp.py -> STUDIO/ASSETS/branding/pfp_detective.png, pfp_classic.png"""
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "PIPELINE" / "twod"))
import skia  # noqa: E402
from kit import rgb  # noqa: E402
from toon import draw_character, prop_magnifier  # noqa: E402

S = 1080


def background(c, c0, c1, ray):
    sh = skia.GradientShader.MakeRadial(skia.Point(S / 2, S * 0.45), S * 0.75, [rgb(c0), rgb(c1)])
    c.drawPaint(skia.Paint(Shader=sh))
    p = skia.Paint(AntiAlias=True, Color=rgb(ray))
    p.setAlphaf(0.35)
    for k in range(16):  # comic sunburst rays
        a0, a1 = k * math.tau / 16, (k + 0.5) * math.tau / 16
        path = skia.Path()
        path.moveTo(S / 2, S * 0.45)
        path.lineTo(S / 2 + math.cos(a0) * S, S * 0.45 + math.sin(a0) * S)
        path.lineTo(S / 2 + math.cos(a1) * S, S * 0.45 + math.sin(a1) * S)
        path.close()
        c.drawPath(path, p)


def question_marks(c):
    f = skia.Font(skia.Typeface.MakeFromFile(str(HERE.parent / "fonts" / "Anton-Regular.ttf")), 120)
    for x, y, r, a in ((175, 330, -18, 0.9), (880, 300, 15, 0.9), (150, 640, -8, 0.55), (915, 660, 10, 0.55)):
        c.save()
        c.translate(x, y)
        c.rotate(r)
        blob = skia.TextBlob("?", f)
        ol = skia.Paint(AntiAlias=True, Color=rgb("#2A1A12"), Style=skia.Paint.kStroke_Style, StrokeWidth=12,
                        StrokeJoin=skia.Paint.kRound_Join)
        ol.setAlphaf(a)
        fill = skia.Paint(AntiAlias=True, Color=rgb("#FFF4D8"))
        fill.setAlphaf(a)
        c.drawTextBlob(blob, -30, 40, ol)
        c.drawTextBlob(blob, -30, 40, fill)
        c.restore()


def render(name, who, pose, bg):
    surf = skia.Surface(S, S)
    c = surf.getCanvas()
    background(c, *bg)
    question_marks(c)
    draw_character(c, who, S / 2 - 20, 1760, 1420, pose)
    # soft inner vignette so the circle crop feels framed
    sh = skia.GradientShader.MakeRadial(skia.Point(S / 2, S / 2), S * 0.5,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, 70)], [0.82, 1.0])
    c.drawPaint(skia.Paint(Shader=sh))
    out = HERE / f"{name}.png"
    surf.makeImageSnapshot().save(str(out), skia.kPNG)
    return out


if __name__ == "__main__":
    print(render("pfp_detective", "marcus_detective",
                 {"expr": "smug", "arm_r": (0.55, -0.35, "down"), "prop_r": prop_magnifier, "arm_l": "hips", "turn": 0.15, "look": (0.4, -0.1),
                  "tilt": -4}, ("#FFD77A", "#E8823A", "#FFE9A8")))
    print(render("pfp_classic", "marcus",
                 {"expr": "happy", "arm_r": (0.95, -0.8, "down"), "arm_l": "hips", "turn": 0.15, "look": (0.4, 0.0), "tilt": -4},
                 ("#9ED8F0", "#3F7FBF", "#C8ECFA")))
