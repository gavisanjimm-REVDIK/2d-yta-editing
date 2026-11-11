"""anim2d.py - VIDEO_004 "The Day Evil Disappeared" shots. shot_NAME(c, t), t = global story time.

    python anim2d.py --frames-json '{...}'   (render_needed.py)
    python anim2d.py --stills                (one still per shot -> qc/test_stills/)
"""
import argparse
import json
import math
import random
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[1]
sys.path.insert(0, str(STUDIO / "PIPELINE" / "twod"))
sys.path.insert(0, str(HERE))
import skia  # noqa: E402
from kit import W, H, FPS, key, blink, clamp, smooth_noise, rgb, text, EASE  # noqa: E402
from toon import draw_character, mix_expr, arm_blend, CAST, draw_fedora  # noqa: E402
from lipsync import load as load_lip, viseme  # noqa: E402
import sets as S  # noqa: E402
import edit_video004 as EDL  # noqa: E402

B = EDL.B
LIP = load_lip("VIDEO_004")
DET = "marcus_detective"
CAST["marcus_nohat"] = dict(CAST["marcus_detective"], extras=("trench",))


# ================================================================ helpers
def vis(t, who):
    return viseme(t, LIP, who)


def cam(c, scale, cx, cy):
    c.translate(W / 2, H / 2)
    c.scale(scale, scale)
    c.translate(-cx, -cy)


def bg(c, name):
    c.drawImage(S.img(name), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear))


def overlay(c, color, alpha, blend=None):
    if alpha <= 0.002:
        return
    p = skia.Paint(Color=rgb(color))
    p.setAlphaf(clamp(alpha))
    if blend:
        p.setBlendMode(blend)
    c.save()
    c.resetMatrix()
    c.drawRect(skia.Rect(0, 0, W, H), p)
    c.restore()


def vignette(c, s=0.5, col=(20, 10, 6)):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.62,
                                        [skia.Color(*col, 0), skia.Color(*col, int(255 * s))], [0.5, 1.0])
    c.save()
    c.resetMatrix()
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    c.restore()


def graded(c, sat=1.0, warm=0.0, bright=1.0):
    """saveLayer with a colour grade (saturation / warmth / brightness). Pair with c.restore()."""
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    s = sat
    m = [lr * (1 - s) + s, lg * (1 - s), lb * (1 - s), 0, 0,
         lr * (1 - s), lg * (1 - s) + s, lb * (1 - s), 0, 0,
         lr * (1 - s), lg * (1 - s), lb * (1 - s) + s, 0, 0,
         0, 0, 0, 1, 0]
    for row, k in ((0, 1 + 0.08 * warm), (1, 1.0), (2, 1 - 0.1 * warm)):
        for col in range(3):
            m[row * 5 + col] *= k * bright
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))


def expr_track(t, track, blend=0.25):
    cur = mix_expr(track[0][1], track[0][1], 1)
    for i, (tt, e) in enumerate(track):
        if t >= tt:
            prev = track[i - 1][1] if i else e
            cur = mix_expr(prev, e, clamp((t - tt) / blend))
    return cur


def ground(c, x, y, w, alpha=0.3):
    p = skia.Paint(AntiAlias=True, Color=rgb("#1A0E0A"))
    p.setAlphaf(alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.08))
    c.drawOval(skia.Rect(x - w / 2, y - w * 0.07, x + w / 2, y + w * 0.07), p)


def actor(c, name, x, y, h, pose, shadow=True, t=0.0):
    if shadow:
        ground(c, x, y, h * 0.42)
    return draw_character(c, name, x, y, h, dict(pose, _t=t))


def breathe(t, seed, amt=0.015):
    return {"blink": blink(t, seed, 4.0), "tilt": 1.5 * smooth_noise(t, seed, 0.2),
            "bob": amt * math.sin(t * 1.6 + seed)}


def dust(c, t, alpha=0.5, seed=1, n=40):
    """Floating dust motes in light (slow, emotional)."""
    r = random.Random(seed)
    for _ in range(n):
        x0, y0, sp = r.uniform(0, W), r.uniform(0, H), r.uniform(8, 25)
        x = (x0 + math.sin(t * 0.5 + x0) * 30) % W
        y = (y0 - t * sp) % H
        c.drawCircle(x, y, r.uniform(2, 5), skia.Paint(AntiAlias=True, Color=skia.Color(255, 240, 200, int(255 * alpha * r.random()))))


# ================================================================ 1. midnight, the city (the clock strikes 12)
def shot_city(c, t):
    m = B["midnight"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "city")
    S.clock_hands(c, m, t)
    for i, (dt, x, y, col) in enumerate(((0.05, 260, 520, "#FF6A7A"), (0.35, 820, 420, "#FFD27A"),
                                         (0.75, 420, 340, "#8AD0FF"), (1.2, 760, 660, "#B48AFF"),
                                         (1.6, 200, 300, "#FFD27A"))):
        S.firework(c, x, y, t, m + dt, col, i)
    # the golden wave: evil disappears - a soft ring of light expands from the clock across the city
    u = (t - m) / 2.2
    if 0 <= u < 1:
        x, y, _ = S.CLOCK
        rr = 60 + 1500 * EASE["out"](u)
        p = skia.Paint(AntiAlias=True, Color=rgb("#FFE6A0"), Style=skia.Paint.kStroke_Style, StrokeWidth=60 * (1 - u) + 6)
        p.setAlphaf(0.7 * (1 - u))
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 18))
        c.drawCircle(x, y, rr, p)
        S.radial(c, x, y, rr * 0.9, "#FFE6A0", 0.18 * (1 - u), plus=True)
    c.restore()
    vignette(c, 0.55, (6, 6, 20))


# ================================================================ 2. the prison opens
def shot_prison(c, t):
    g = B["gone"]
    op = EASE["io"](clamp((t - g + 0.6) / 1.2))
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "prison")
    # prisoner steps out of the left cell, the guard (right) lowers his guard; they meet with open arms
    step = EASE["io"](clamp((t - g) / 1.2))
    px = 270 + 150 * step
    actor(c, "prisoner", px, 1560 + 60 * step, 900 + 100 * step, dict(breathe(t, 3), expr=expr_track(t, [(B["prison"], "worried"), (g - 0.2, "surprised"), (g + 0.6, "happy")]),
                                             walk=(t * 1.4) % 1 if 0 < t - g < 1.2 else None, turn=0.4,
                                             arm_l=arm_blend("prisoner", t, [(g, "relaxed"), (g + 1.0, (0.75, 0.35, "out"))], 0.5),
                                             arm_r=arm_blend("prisoner", t, [(g, "relaxed"), (g + 1.0, (0.75, 0.35, "out"))], 0.5)), t=t)
    S.bars(c, 60, op)  # bars in front of the prisoner (he is inside the cell until they slide open)
    actor(c, "guard", 820, 1660, 1040, dict(breathe(t, 5), expr=expr_track(t, [(B["prison"], "determined"), (g, "surprised"), (g + 0.9, "smile")]),
                                           turn=-0.45, look=(-0.7, 0),
                                           arm_l=arm_blend("guard", t, [(g, "hips"), (g + 1.1, (0.75, 0.35, "out"))], 0.5),
                                           arm_r=arm_blend("guard", t, [(g, "relaxed"), (g + 1.1, (0.75, 0.35, "out"))], 0.5)), t=t)
    c.restore()
    vignette(c, 0.5)


# ================================================================ 3. newspapers land on the desk
HEADLINES = [("p1", "ALL PRISONS EMPTY", -9, (540, 820)), ("p2", "WARS END OVERNIGHT", 7, (520, 1180)),
             ("p3", "NOBODY REMEMBERS WHY", -4, (560, 1500))]


def newspaper(c, x, y, rot, scale, headline):
    c.save()
    c.translate(x, y)
    c.rotate(rot)
    c.scale(scale, scale)
    sh = skia.Paint(AntiAlias=True, Color=rgb("#000000"))
    sh.setAlphaf(0.35)
    sh.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 20))
    c.drawRect(skia.Rect(-400 + 14, -280 + 20, 400 + 14, 280 + 20), sh)
    S.shape(c, S.rect(-400, -280, 800, 560, 4), "#F2ECDC", ow=4)
    text(c, "THE DAILY WORLD", 0, -200, 54, "#2A1A12", face="Cinzel-VF.ttf", shadow=False, clamp_safe=False, max_w=720)
    c.drawLine(-370, -175, 370, -175, S.line_w(4))
    c.drawLine(-370, -165, 370, -165, S.line_w(2))
    text(c, headline, 0, -70, 78, "#1A1A1A", face="Anton-Regular.ttf", shadow=False, clamp_safe=False, max_w=740)
    S.shape(c, S.rect(-370, -30, 330, 250, 2), "#C8C0B0", ow=3)  # photo
    S.radial(c, -205, 95, 120, "#FFE6A0", 0.6)
    for k in range(9):
        c.drawLine(10, -20 + k * 26, 370, -20 + k * 26, S.line_w(5, "#8A8478", 0.8))
    c.restore()


def shot_news(c, t):
    u0 = clamp((t - B["news"]) / (B["office"] - B["news"]))
    c.save()
    cam(c, 1.0 + 0.08 * u0, 540 + 20 * math.sin(t * 0.7), 960 + 60 * u0)  # slow drift, stays inside the desk
    bg(c, "desk")
    for k in range(3):  # coffee steam
        q = skia.Path()
        x0 = 150 + k * 22
        q.moveTo(x0, 1600)
        for j in range(1, 6):
            q.lineTo(x0 + 16 * math.sin(t * 2 + j + k), 1600 - j * 34)
        c.drawPath(q, S.line_w(6, "#FFFFFF", 0.25))
    for key_, head, rot, (x, y) in HEADLINES:
        t0 = B[key_] - 0.35
        u = clamp((t - t0) / 0.45)
        if u <= 0:
            continue
        e = EASE["out"](u)
        settle = 0.6 * math.sin(t * 0.9 + x) * e  # papers keep a tiny drift after landing
        newspaper(c, x, y, rot + settle + 540 * (1 - e), 0.15 + 0.95 * e - 0.1 * (EASE["back"](u) - e), head)
    c.restore()
    vignette(c, 0.55)


# ================================================================ 4. Marcus packs his detective life into a box
def shot_office(c, t):
    graded(c, sat=0.85, warm=0.6)  # colour grade wraps everything drawn below
    t0 = B["office"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "office")
    S.box(c, 470, 1180, 0.85, fill=1.0)  # on the desk, coat already folded inside
    actor(c, "marcus_nohat", 780, 1700, 1080,
          dict(breathe(t, 4), expr=expr_track(t, [(t0, "sad")]), turn=-0.4, look=(-0.6, 0.6), tilt=6,
               arm_l=(-0.2, 0.85, "out"), arm_r=(-0.2, 0.85, "out"),
               prop_r=hat_prop), t=t)
    dust(c, t, 0.5, 3)
    c.restore()
    c.restore()  # end grade layer
    vignette(c, 0.55)


def hat_prop(pen, x, y, ang, side):
    """His fedora, held in both hands in front of him."""
    draw_fedora(pen, 0.0, y + 0.62, 0.62, 0.62, 0.0)  # centred between both hands, crown up


def shot_cu_marcus(c, t):
    graded(c, sat=0.85, warm=0.6)  # colour grade wraps everything drawn below
    t0, hd = B["cu_marcus"], B["hat_drop"]
    c.save()
    cam(c, 1.3, 600, 900)
    bg(c, "office_blur")
    c.restore()
    lower = EASE["io"](clamp((t - hd) / 1.0))
    # the hat sinks into the box at the bottom of the frame
    pose = dict(breathe(t, 4, 0.01), expr=expr_track(t, [(t0, "sad"), (hd - 0.2, "shy")], 0.5),
                vis=vis(t, "marcus"), turn=0.1, look=(0.0, 0.4 + 0.4 * lower), tilt=5 + 4 * lower,
                arm_l=(-0.2, 0.85 + 0.35 * lower, "out"), arm_r=(-0.2, 0.85 + 0.35 * lower, "out"), prop_r=hat_prop)
    actor(c, "marcus_nohat", 540, 2250, 1650, pose, shadow=False, t=t)
    c.restore()  # end grade layer
    vignette(c, 0.6)


# ================================================================ 5. the perfect world... slowly fading
def shot_street(c, t):
    fade = EASE["io"](clamp((t - B["fade"]) / (B["winter"] + 1.5 - B["fade"])))
    snow = clamp((t - B["winter"] + 0.4) / 1.2)
    graded(c, sat=1.15 - 0.9 * fade, warm=0.3 - 0.9 * fade, bright=1.0 - 0.05 * fade)
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "street")
    S.snow_cover(c, snow)
    summer = t < B["winter"]
    if summer:  # strangers sharing: Gaston hands bread to Sophie, Oliver waves from an open door
        g0 = B["summer"] + 1.4
        give = EASE["io"](clamp((t - g0) / 0.8))
        actor(c, "oliver", 150, 1330, 560, dict(breathe(t, 11), expr="happy", turn=0.3,
                                               arm_r=(0.75, -0.75 + 0.15 * math.sin(t * 7), "down")), t=t)
        actor(c, "gaston", 420, 1580, 800, dict(breathe(t, 12), expr="happy", turn=0.45, look=(0.8, 0),
                                               arm_r=arm_blend("gaston", t, [(g0, "relaxed"), (g0 + 0.8, (1.3, 0.3, "out"))], 0.6),
                                               prop_r=bread if give > 0.5 else None), t=t)
        actor(c, "sophie", 830, 1580, 700, dict(breathe(t, 13), expr="happy", turn=-0.45, look=(-0.8, 0),
                                               arm_l=arm_blend("sophie", t, [(g0, "front"), (g0 + 0.8, (1.2, 0.35, "out"))], 0.6),
                                               prop_l=bread if give <= 0.5 else None), t=t)
    else:  # winter: Daniel gives his scarf to Prim... and nobody even notices it was kind
        c0 = B["coat"] - 0.4
        hand = EASE["io"](clamp((t - c0) / 1.0))
        walk_off = clamp((t - c0 - 1.8) / 2.0)
        actor(c, "daniel", 430, 1560, 800, dict(breathe(t, 21), expr="neutral", turn=0.4, look=(0.7, 0),
                                               arm_r=arm_blend("daniel", t, [(c0, "relaxed"), (c0 + 1.0, (0.95, 0.4, "out")),
                                                                           (c0 + 2.0, "relaxed")], 0.6)), t=t)
        actor(c, "prim", 760 + 300 * walk_off, 1560, 760, dict(breathe(t, 22), expr="neutral", turn=-0.4 + 0.8 * walk_off,
                                                             look=(-0.6 + 1.2 * walk_off, 0), walk=(t * 1.4) % 1 if walk_off > 0 else None,
                                                             arm_l=arm_blend("prim", t, [(c0 + 0.5, "relaxed"), (c0 + 1.2, (0.4, 0.6, "down"))], 0.5)), t=t)
        if hand > 0.6:  # the scarf now around her neck
            S.shape(c, S.rect(760 + 300 * walk_off - 70, 1560 - 760 * 0.52, 140, 46, 18), "#2E5A8A", ow=3)
        # the street lamp switches on in broad daylight; nobody looks up
        lt = clamp((t - B["light"] - 0.4) / 0.4)
        if lt > 0:
            S.radial(c, 893, 1090, 160 * lt, "#FFF2C8", 0.9 * lt, plus=True)
    c.restore()
    if not summer:
        r = random.Random(4)
        for _ in range(80):  # snowfall
            x0, y0, sp = r.uniform(0, W), r.uniform(0, H), r.uniform(60, 140)
            c.drawCircle((x0 + math.sin(t + x0) * 20) % W, (y0 + t * sp) % H, r.uniform(3, 7), S.P("#FFFFFF", 0.85 * snow))
    c.restore()
    vignette(c, 0.4 + 0.2 * fade)


def bread(pen, x, y, ang, side):
    pen.shape(S.base.oval(x + 0.15 * side, y - 0.1, 0.42, 0.2), "#D89A4A", "#B87A32")
    for k in (-0.15, 0.0, 0.15):
        q = skia.Path()
        q.moveTo(x + 0.15 * side + k - 0.05, y - 0.22)
        q.lineTo(x + 0.15 * side + k + 0.05, y + 0.0)
        pen.stroke(q, pen.ow * 0.6)


# ================================================================ 6. ten years later: the park bench
def badge(c, x, y, s, glint=0.0):
    """Marcus's old detective badge (shield)."""
    pts = [(x, y - 60 * s), (x + 48 * s, y - 40 * s), (x + 44 * s, y + 20 * s), (x, y + 60 * s), (x - 44 * s, y + 20 * s),
           (x - 48 * s, y - 40 * s)]
    S.shape(c, S.smooth_path(pts), "#E0B84A", shade="#C09A32", sdx=8 * s, ow=4)
    S.shape(c, S.oval(x, y - 2 * s, 20 * s, 20 * s), "#F4D878", ow=3)
    if glint > 0:
        S.radial(c, x - 18 * s, y - 30 * s, 80 * s, "#FFFFFF", 0.8 * glint, plus=True)


def badge_prop(s=1.0):
    def draw(pen, x, y, ang, side):
        pts = [(x, y - 0.42), (x + 0.32, y - 0.28), (x + 0.3, y + 0.12), (x, y + 0.38), (x - 0.3, y + 0.12),
               (x - 0.32, y - 0.28)]
        pen.shape(S.smooth_path(pts), "#E0B84A", "#C09A32")
        pen.shape(S.base.oval(x, y - 0.02, 0.13, 0.13), "#F4D878")
    return draw


def park_scene(c, t, marcus_pose, lily_pose, lily_x=330):
    bg(c, "park")
    S.box(c, 860, 1500, 0.7, fill=1.0)  # the old box, brought along, sitting on the grass
    actor(c, "lily", lily_x, 1520, 560, lily_pose, t=t)
    actor(c, "marcus_cardigan", 610, 1470, 880, marcus_pose, shadow=False, t=t)
    dust(c, t, 0.45, 7, 30)


def lily_base(t):
    return dict(breathe(t, 31), vis=vis(t, "lily"), turn=0.35, look=(0.7, -0.6))


def marcus_base(t):
    return dict(breathe(t, 32, 0.008), sit=True, vis=vis(t, "marcus"), arm_l="front", arm_r="front", hand_l="fist")


def shot_park_wide(c, t):
    graded(c, sat=0.95, warm=0.8)  # colour grade wraps everything drawn below
    c.save()
    cam(c, 1.0, 540, 960)
    park_scene(c, t, dict(marcus_base(t), expr="smile", look=(-0.6, 0.3), turn=-0.2),
               dict(lily_base(t), expr="happy", arm_r=(0.3, -0.25, "down"), prop_r=badge_prop()))
    c.restore()
    c.restore()  # end grade layer
    vignette(c, 0.45)


def shot_cu_lily(c, t):
    graded(c, sat=0.95, warm=0.8)  # colour grade wraps everything drawn below
    c.save()
    cam(c, 1.3, 520, 900)
    bg(c, "park_blur")
    c.restore()
    actor(c, "lily", 540, 2150, 1500, dict(lily_base(t), expr=expr_track(t, [(B["cu_lily"], "happy"), (B["cu_lily"] + 0.9, "surprised")]),
                                         arm_r=(0.3, -0.25, "down"), prop_r=badge_prop(), look=(0.5, -0.6)), shadow=False, t=t)
    c.restore()  # end grade layer
    vignette(c, 0.5)


def shot_cu_marcus2(c, t):
    graded(c, sat=0.9, warm=0.8)  # colour grade wraps everything drawn below
    t0 = B["cu_marcus2"]
    c.save()
    cam(c, 1.3, 600, 900)
    bg(c, "park_blur")
    c.restore()
    pose = dict(marcus_base(t), sit=False, expr=expr_track(t, [(t0, "sad"), (t0 + 1.4, "smile"), (B["two_shot"] - 0.8, "sad")], 0.6),
                look=(-0.6, 0.4), tilt=-4, turn=-0.2)
    actor(c, "marcus_cardigan", 540, 2300, 1650, pose, shadow=False, t=t)
    c.restore()  # end grade layer
    vignette(c, 0.55)


def shot_two_shot(c, t):
    graded(c, sat=0.9, warm=0.8)  # colour grade wraps everything drawn below
    t0 = B["two_shot"]
    c.save()
    cam(c, 1.25, 500, 1220)
    park_scene(c, t, dict(marcus_base(t), expr=expr_track(t, [(t0, "sad"), (t0 + 1.6, "worried")], 0.6),
                          look=key(t, [(t0, (-0.7, 0.4)), (t0 + 1.6, (-0.7, 0.4)), (t0 + 2.4, (0.3, -0.8))])),
               dict(lily_base(t), expr="worried", arm_r=(0.3, -0.25, "down"), prop_r=badge_prop(), tilt=8))
    c.restore()
    c.restore()  # end grade layer
    vignette(c, 0.5)


def shot_final(c, t):
    graded(c, sat=0.85, warm=0.9)  # colour grade wraps everything drawn below
    c.save()
    cam(c, 1.0, 540, 960)
    sink = clamp((t - B["final"]) / 8.0)
    park_scene(c, t, dict(marcus_base(t), expr="sad", look=(0.2, -0.7), turn=-0.1),
               dict(lily_base(t), expr="shy", arm_r=(0.3, -0.25, "down"), prop_r=badge_prop(), look=(0.0, -0.8)))
    c.restore()
    overlay(c, "#3A1A2A", 0.12 + 0.3 * sink)  # dusk falls
    c.restore()  # end grade layer
    vignette(c, 0.6)


SHOTS = {k[5:]: v for k, v in globals().items() if k.startswith("shot_")}


def render(job_frame):
    job, i = job_frame
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    SHOTS[job](c, i / FPS)
    out = HERE / "frames" / job / f"f_{i:05d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    surf.makeImageSnapshot().save(str(out), skia.kPNG)
    return out


def still(job, t, out):
    surf = skia.Surface(W, H)
    SHOTS[job](surf.getCanvas(), t)
    out.parent.mkdir(parents=True, exist_ok=True)
    surf.makeImageSnapshot().save(str(out), skia.kPNG)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-json")
    ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    if a.stills:
        import shutil
        shutil.rmtree(HERE / "qc" / "test_stills", ignore_errors=True)
        for s in EDL.SEGMENTS:
            if s["src"] in SHOTS:
                tm = (s["t0"] + s["t1"]) / 2
                still(s["src"], tm, HERE / "qc" / "test_stills" / f"{tm:05.2f}_{s['src']}.png")
    else:
        todo = [(j, i) for j, fr in json.loads(a.frames_json).items() for i in fr]
        with Pool() as p:
            for k, _ in enumerate(p.imap_unordered(render, todo, chunksize=6)):
                if k % 200 == 0:
                    print(f"  2d {k}/{len(todo)}", flush=True)
        print(f"  2d rendered {len(todo)} frames")
