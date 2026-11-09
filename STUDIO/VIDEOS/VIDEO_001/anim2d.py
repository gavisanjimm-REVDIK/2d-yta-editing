"""anim2d.py - VIDEO_001 shots. shot_NAME(c, t): t = global story time (EDL uses src_t = segment start).

    python anim2d.py --frames-json '{...}'      (render_needed.py)
    python anim2d.py --still cu_daniel 22.0     (test still -> qc/)
    python anim2d.py --stills                   (one still per shot -> qc/test_stills/)
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
from kit import W, H, FPS, key, blink, mouth_open, clamp, smooth_noise, rgb  # noqa: E402
from toon import draw_character, CAST, mix_expr, prop_flashlight, prop_notebook, prop_towel  # noqa: E402
import sets as S  # noqa: E402
import edit_video001 as EDL  # noqa: E402

B = EDL.B
WORDS = EDL.WORDS


# ================================================================ shared helpers
def talk(t, who):
    return mouth_open(t, WORDS, who=who)


def lightning(t):
    """0..1 flash intensity (double flicker per strike)."""
    v = 0.0
    for s in EDL.STRIKES:
        d = t - s
        if 0 <= d < 0.5:
            v = max(v, math.exp(-d / 0.06) + 0.6 * math.exp(-max(d - 0.16, 0) / 0.07) * (d > 0.16))
    return clamp(v)


def cam(c, scale, cx, cy):
    """Camera: bg point (cx, cy) at frame centre, zoomed by scale."""
    c.translate(W / 2, H / 2)
    c.scale(scale, scale)
    c.translate(-cx, -cy)


def bg(c, name, x=0, y=0):
    c.drawImage(S.img(name), x, y, skia.SamplingOptions(skia.FilterMode.kLinear))


def rain(c, t, rect, n=90, alpha=0.5, seed=1, length=70, slant=0.25):
    x0, y0, w, h = rect
    r = random.Random(seed)
    p = skia.Paint(AntiAlias=True, Color=rgb("#BFD0F0"), StrokeWidth=3, StrokeCap=skia.Paint.kRound_Cap)
    p.setAlphaf(alpha)
    for i in range(n):
        sx, sp, ph = r.uniform(0, 1), r.uniform(1800, 2600), r.uniform(0, 1)
        y = y0 + ((ph * h + t * sp) % (h + length)) - length
        x = x0 + (sx * w + (y - y0) * slant) % w
        c.drawLine(x, y, x - length * slant, y - length, p)


def bolt(c, x, y0, y1, seed, alpha):
    r = random.Random(seed)
    p = skia.Path()
    p.moveTo(x, y0)
    y, xx = y0, x
    while y < y1:
        y += r.uniform(40, 90)
        xx += r.uniform(-60, 60)
        p.lineTo(xx, y)
    pa = skia.Paint(AntiAlias=True, Color=rgb("#FFFFFF"), Style=skia.Paint.kStroke_Style, StrokeWidth=9,
                    StrokeJoin=skia.Paint.kRound_Join)
    pa.setAlphaf(alpha)
    glow = skia.Paint(pa)
    glow.setColor(rgb("#B9C8FF"))
    glow.setStrokeWidth(30)
    glow.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14))
    c.drawPath(p, glow)
    c.drawPath(p, pa)


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


def vignette(c, s=0.5):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.62,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, int(255 * s))], [0.5, 1.0])
    c.save()
    c.resetMatrix()
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    c.restore()


def dimmed(c, amount):
    """saveLayer that darkens what is drawn inside (non-speaking characters in the lineup)."""
    m = [1 - amount, 0, 0, 0, 0, 0, 1 - amount, 0, 0, 0, 0, 0, 1 - amount * 0.9, 0, 0, 0, 0, 0, 1, 0]
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))


def beam(c, hand, aim_dev, length=2200, spread=0.3, alpha=0.5, color="#FFE9B0"):
    """Flashlight cone in device space from hand along direction to aim_dev."""
    (hx, hy), _ = hand
    ax, ay = aim_dev
    a = math.atan2(ay - hy, ax - hx)
    p = skia.Path()
    p.moveTo(hx, hy)
    p.lineTo(hx + math.cos(a - spread) * length, hy + math.sin(a - spread) * length)
    p.lineTo(hx + math.cos(a + spread) * length, hy + math.sin(a + spread) * length)
    p.close()
    return p, a


def idle_tilt(t, seed):
    return 2.0 * smooth_noise(t, seed, 0.3)


def expr_track(t, track, blend=0.12):
    """track = [(t, expr_name), ...] -> blended expression dict."""
    cur = track[0][1]
    for i, (tt, e) in enumerate(track):
        if t >= tt:
            prev = track[i - 1][1] if i else e
            u = clamp((t - tt) / blend)
            cur = mix_expr(prev, e, u)
    return cur if isinstance(cur, dict) else mix_expr(cur, cur, 1)


# ================================================================ 1. storm exterior (hook, event on frame 0)
def shot_ext(c, t):
    c.save()
    z = key(t, [(0.0, 1.0), (B["basement_hook"], 1.75, "in")])
    cam(c, z, 540, 1180 + 120 * (z - 1))
    bg(c, "ext")
    lt = lightning(t)
    if lt > 0.05:
        bolt(c, 760, 0, 900, int(t * 2) + 3, lt)
    rain(c, t, (-200, -200, W + 400, H + 400), n=140, alpha=0.45, length=90)
    c.restore()
    overlay(c, "#DCE4FF", 0.75 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.55)


# ================================================================ 2. basement hook: detective, flashlight, solid walls
def _basement_view(c, t, cx, scale, marcus=None, aim_bg=None, base_y=960):
    """Dark basement panorama + flashlight. marcus = dict(x, y, h, pose). aim_bg = point on wall (bg coords)."""
    c.save()
    cam(c, scale, cx, base_y)
    bg(c, "base_dark")
    info = None
    if marcus:
        pose = dict(marcus["pose"])
        pose["prop_r"] = prop_flashlight(1.0)
        info = draw_character(c, "marcus", marcus["x"], marcus["y"], marcus["h"], pose)
    m = c.getTotalMatrix()
    c.restore()
    if info and "r" in info["hands"] and aim_bg is not None:
        hand = info["hands"]["r"]
        aim_dev = m.mapXY(*aim_bg)
        cone, a = beam(c, hand, aim_dev)
        # lit version of the wall inside the cone (the light reveals solid stone everywhere)
        c.save()
        c.clipPath(cone, doAntiAlias=True)
        c.concat(m)
        lit = skia.Paint()
        lit.setAlphaf(0.95)
        c.drawImage(S.img("base_lit"), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), lit)
        c.restore()
        # soft beam glow
        (hx, hy), _ = hand
        sh = skia.GradientShader.MakeRadial(skia.Point(hx, hy), 1500,
                                            [skia.Color(255, 236, 190, 70), skia.Color(255, 236, 190, 0)])
        c.save()
        c.clipPath(cone, doAntiAlias=True)
        c.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))
        c.restore()
        # redraw the detective on top (so the beam does not cover him), with flashlight spill
        c.save()
        c.concat(m)
        pose = dict(marcus["pose"])
        pose["prop_r"] = prop_flashlight(1.0)
        dimmed(c, 0.25)
        draw_character(c, "marcus", marcus["x"], marcus["y"], marcus["h"], pose)
        c.restore()
        c.restore()
        S.radial(c, hx, hy, 70, "#FFF3C8", 0.8, plus=True)
    vignette(c, 0.6)


def shot_basement_hook(c, t):
    t0 = B["basement_hook"]
    td = B["detective"]
    turn = key(t, [(t0, -0.7), (td - 0.15, -0.7), (td + 0.25, 0.1, "back")])
    sweep = key(t, [(t0, 700.0), (td - 0.1, 1900.0, "io"), (td + 0.4, 1500.0, "out")])
    pose = {"expr": expr_track(t, [(t0, "suspicious"), (td + 0.1, "smug")]),
            "turn": turn, "look": (key(t, [(t0, -0.8), (td, -0.8), (td + 0.25, 0.0)]), 0.0),
            "blink": blink(t, 4), "arm_r": "flash", "arm_l": "relaxed", "tilt": idle_tilt(t, 1),
            "talk": 0.0, "bob": 0.02 * math.sin(t * 2)}
    z = key(t, [(t0, 1.0), (B["safe"], 1.12, "lin")])
    _basement_view(c, t, 1330, z, {"x": 1180, "y": 1780, "h": 1150, "pose": pose}, (sweep, 650))


# ================================================================ 3. study: empty safe insert, Harrison
def _study_light(c, t):
    S.draw_candles(c, S.STUDY_CANDLES, t)
    lt = lightning(t)
    c.save()
    c.clipPath(S.rect(620, 160, 360, 640, 170), doAntiAlias=True)
    rain(c, t, (620, 160, 360, 640), n=40, alpha=0.6, seed=4, length=50)
    c.drawPaint(skia.Paint(Color=skia.Color(230, 236, 255, int(230 * lt))))
    c.restore()
    return lt


def shot_study_safe(c, t):
    c.save()
    cam(c, 2.3, 470, 1120)
    bg(c, "study")
    _study_light(c, t)
    c.restore()
    vignette(c, 0.55)


def shot_study(c, t):
    t0 = B["harrison_ms"]
    c.save()
    cam(c, 1.22, 610, 1020)
    bg(c, "study")
    lt = _study_light(c, t)
    pw = B["power"]
    pose = {"expr": expr_track(t, [(t0, "panic"), (pw, "shocked")]),
            "talk": talk(t, "harrison"), "blink": blink(t, 7),
            "arm_l": key(t, [(t0, (0.55, -1.05)), (pw - 0.1, (0.55, -1.05)), (pw + 0.2, (0.4, 0.9))]),
            "arm_r": key(t, [(t0, (0.55, -1.05)), (pw - 0.1, (0.55, -1.05)), (pw + 0.2, (1.2, -0.3))]),
            "hand_r": "point" if t > pw else "open",
            "turn": key(t, [(t0, -0.2), (pw, -0.2), (pw + 0.3, 0.35)]),
            "look": (key(t, [(t0, 0.0), (pw, 0.0), (pw + 0.2, 0.8)]), -0.2),
            "tilt": 3 * math.sin(t * 9) * (t < pw),  # panicked jitter
            "bob": 0.03 * abs(math.sin(t * 6))}
    draw_character(c, "harrison", 560, 1960, 1500, pose)
    c.restore()
    overlay(c, "#DCE4FF", 0.25 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.5)


# ================================================================ 4. foyer: detective + three suspects
def _foyer_light(c, t, windows=True):
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = lightning(t)
    if windows and lt > 0.01:
        for x0 in (300, 640):
            c.save()
            c.clipPath(S.rect(x0, 120, 170, 330, 85), doAntiAlias=True)
            c.drawPaint(skia.Paint(Color=skia.Color(235, 240, 255, int(240 * lt))))
            c.restore()
    return lt


def suspects_pose(t, name, base_expr="nervous"):
    seed = {"oliver": 11, "daniel": 12, "sophie": 13}[name]
    p = {"expr": base_expr, "blink": blink(t, seed), "tilt": idle_tilt(t, seed), "talk": talk(t, name),
         "look": (0.6 * smooth_noise(t, seed + 5, 0.15), 0.0), "bob": 0.015 * math.sin(t * 2.2 + seed)}
    if name == "oliver":
        p.update(arm_r="neck", arm_l="behind", expr="nervous")
    elif name == "daniel":
        p.update(arm_l="hips", arm_r="hips", expr="confident")
    else:
        p.update(arm_l="front", arm_r="front", prop_r=prop_towel, expr="shy", look=(0.0, 0.7))
    return p


def shot_foyer_wide(c, t):
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "foyer")
    lt = _foyer_light(c, t)
    draw_character(c, "oliver", 520, 1690, 980, suspects_pose(t, "oliver"))
    draw_character(c, "daniel", 735, 1710, 940, suspects_pose(t, "daniel"))
    draw_character(c, "sophie", 945, 1690, 830, suspects_pose(t, "sophie"))
    mp = {"expr": "determined", "turn": 0.75, "look": (0.9, 0.0), "talk": talk(t, "marcus"), "blink": blink(t, 4),
          "arm_l": "hips", "arm_r": key(t, [(B["foyer"], (0.18, 1.28)), (B["foyer"] + 0.5, (1.1, 0.05))]),
          "hand_r": "point", "tilt": idle_tilt(t, 1)}
    draw_character(c, "marcus", 70, 2230, 1450, mp)
    c.restore()
    overlay(c, "#DCE4FF", 0.18 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


# ================================================================ 5. close-ups (blurred foyer behind)
CU = {"marcus": (410, 820), "oliver": (670, 900), "daniel": (560, 760), "sophie": (660, 700)}  # cx in [400, 680] so the zoomed bg covers the frame


def _cu_bg(c, t, name, z=1.35):
    cx, cy = CU[name]
    c.save()
    cam(c, z, cx, cy)
    bg(c, "foyer_blur")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = lightning(t)
    c.restore()
    return lt


def shot_cu_marcus(c, t):
    lt = _cu_bg(c, t, "marcus")
    pose = {"expr": expr_track(t, [(B["marcus_q"], "suspicious")]), "talk": talk(t, "marcus"),
            "blink": blink(t, 4), "turn": 0.25, "look": (0.5, 0.0), "tilt": idle_tilt(t, 1),
            "arm_l": "front_high", "prop_l": prop_notebook, "arm_r": "chin"}
    draw_character(c, "marcus", 540, 3020, 2650, pose)
    overlay(c, "#DCE4FF", 0.2 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


def shot_cu_oliver(c, t):
    lt = _cu_bg(c, t, "oliver")
    wig = 0.06 * math.sin(t * 16)
    pose = {"expr": "nervous" if talk(t, "oliver") < 0.05 else "worried", "talk": talk(t, "oliver"),
            "blink": blink(t, 11, 2.0), "turn": -0.25, "look": (-0.5 + 0.4 * math.sin(t * 1.7), 0.0),
            "tilt": idle_tilt(t, 2) - 3, "arm_r": (-0.45, -0.05 + wig), "arm_l": "relaxed", "sweat": 0.6}
    draw_character(c, "oliver", 540, 3080, 2650, pose)
    overlay(c, "#DCE4FF", 0.2 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


def _daniel_pose(t):
    if t >= B["daniel_ecu"] - 0.01 and t < B["lineup"]:  # the moment he realises
        return {"expr": "nervous", "talk": 0.0, "blink": 0.0, "turn": 0.0, "sweat": 1.0,
                "look": (math.sin(t * 9) * 0.7, 0.0), "arm_l": "relaxed", "arm_r": "relaxed"}
    if t >= B["daniel2"] - 0.01:  # "Yes! Clear as day."
        return {"expr": "confident", "talk": talk(t, "daniel"), "blink": blink(t, 12), "turn": 0.15,
                "arm_l": "shrug", "arm_r": "shrug", "tilt": 4 + idle_tilt(t, 3)}
    bw = B["basement_word"]
    return {"expr": expr_track(t, [(B["daniel"], "confident"), (B["lightning_word"], "happy")]),
            "talk": talk(t, "daniel"), "blink": blink(t, 12), "flip": True, "turn": 0.2,
            "arm_r": key(t, [(B["daniel"], (0.18, 1.28)), (bw - 0.3, (0.18, 1.28)), (bw, (1.25, -0.15), "back")]),
            "hand_r": "point" if t > bw - 0.15 else "open", "arm_l": "hips", "tilt": idle_tilt(t, 3),
            "look": (0.6, 0.0)}


def shot_cu_daniel(c, t):
    lt = _cu_bg(c, t, "daniel")
    draw_character(c, "daniel", 540, 3060, 2650, _daniel_pose(t))
    if B["daniel_ecu"] <= t < B["lineup"]:
        overlay(c, "#1A2240", 0.25)
    overlay(c, "#DCE4FF", 0.2 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


def shot_cu_sophie(c, t):
    lt = _cu_bg(c, t, "sophie")
    th = B["thunder_word"]
    pose = {"expr": expr_track(t, [(B["sophie"], "shy"), (th, "worried"), (th + 0.9, "shy")]),
            "talk": talk(t, "sophie"), "blink": blink(t, 13),
            "look": key(t, [(B["sophie"], (0.0, 0.8)), (th - 0.1, (0.0, 0.8)), (th + 0.1, (0.7, -0.8)),
                            (th + 0.9, (0.7, -0.8)), (th + 1.1, (0.0, 0.8))]),
            "turn": key(t, [(B["sophie"], -0.1), (th, -0.1), (th + 0.2, 0.3), (th + 0.9, 0.3), (th + 1.1, -0.1)]),
            "tilt": key(t, [(B["sophie"], 6), (th, 6), (th + 0.2, -3), (th + 0.9, -3), (th + 1.1, 6)]),
            "arm_l": "front", "arm_r": "front", "prop_r": prop_towel}
    draw_character(c, "sophie", 540, 2860, 2450, pose)
    overlay(c, "#DCE4FF", 0.2 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


# ================================================================ 6. detective turns toward the basement door
def shot_marcus_turn(c, t):
    t0, tn = B["turn"], B["daniel_name"]
    c.save()
    cam(c, 1.25, 430, 1060)
    bg(c, "foyer")
    lt = _foyer_light(c, t)
    pose = {"expr": expr_track(t, [(t0, "determined"), (t0 + 0.6, "suspicious")]), "talk": talk(t, "marcus"),
            "blink": blink(t, 4), "arm_l": "front_high", "prop_l": prop_notebook, "arm_r": "chin",
            "turn": key(t, [(t0, 0.4), (t0 + 0.9, -0.85, "io"), (tn - 0.15, -0.85), (tn + 0.3, 0.6, "io")]),
            "look": key(t, [(t0, (0.5, 0.0)), (t0 + 0.9, (-1.0, 0.1)), (tn - 0.15, (-1.0, 0.1)), (tn + 0.3, (0.9, 0.0))]),
            "tilt": idle_tilt(t, 1)}
    draw_character(c, "marcus", 600, 2020, 1450, pose)
    c.restore()
    overlay(c, "#DCE4FF", 0.18 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


# ================================================================ 7. down into the basement: pan across solid walls
def shot_basement_pan(c, t):
    t0, t1 = B["descend"], B["daniel_ecu"]
    cx = key(t, [(t0, 650.0), (t1, 1650.0, "io")])
    walk_x = key(t, [(t0, 420.0), (t0 + 1.0, 980.0, "out")])
    walk_y = key(t, [(t0, 1520.0), (t0 + 1.0, 1760.0, "out")])
    walking = t < t0 + 1.0
    pose = {"expr": expr_track(t, [(t0, "suspicious"), (B["explain"], "determined")]), "talk": talk(t, "marcus"),
            "blink": blink(t, 4), "arm_r": "flash", "arm_l": "relaxed",
            "walk": (t * 1.8) % 1 if walking else None,
            "turn": key(t, [(t0, 0.6), (B["explain"], 0.6), (B["explain"] + 0.5, 0.0)]),
            "look": (key(t, [(t0, 0.9), (B["explain"], 0.9), (B["explain"] + 0.5, 0.0)]), 0.0)}
    aim = (cx + 520 + 120 * math.sin(t * 2.1), 760 + 80 * math.sin(t * 1.3))
    _basement_view(c, t, cx, 1.0, {"x": walk_x, "y": walk_y, "h": 1050, "pose": pose}, aim)


# ================================================================ 8. the three suspects together (recap + question)
LINEUP = {"oliver": (250, 1860, 1080), "daniel": (545, 1880, 1040), "sophie": (840, 1860, 930)}


def shot_lineup(c, t):
    tz, tf = B["zoom"], B["freeze"]
    dx, dy, dh = LINEUP["daniel"]
    dhead_y = dy - dh * 0.72
    z = key(t, [(B["lineup"], 1.0), (tz, 1.04, "lin"), (tf, 2.35, "io")])
    cx = key(t, [(B["lineup"], 540.0), (tz, 540.0), (tf, dx, "io")])
    cy = key(t, [(B["lineup"], 960.0), (tz, 960.0), (tf, dhead_y + 60, "io")])
    c.save()
    cam(c, z, cx, cy)
    bg(c, "foyer")
    lt = _foyer_light(c, t)
    named = {"oliver": B["n_oliver"], "sophie": B["n_sophie"], "daniel": B["n_daniel"]}
    for name in ("oliver", "sophie", "daniel"):
        x, y, h = LINEUP[name]
        pose = suspects_pose(t, name)
        if name == "daniel":
            pose.update(expr=expr_track(t, [(B["lineup"], "confident"), (tz, "nervous")]),
                        sweat=key(t, [(tz, 0.0), (tz + 1.0, 1.0)]), arm_l="relaxed", arm_r="relaxed",
                        look=(0.8 * math.sin(t * 5) if t > tz else 0.2, 0.0))
        # spotlight whoever the narrator names; others dim
        active = None
        for n2, tt in sorted(named.items(), key=lambda kv: kv[1]):
            if B["lineup"] < t and t >= tt - 0.1 and t < B["recap_end"]:
                active = n2
        dim = 0.0 if active in (None, name) else 0.45
        if dim:
            dimmed(c, dim)
        draw_character(c, name, x, y, h, pose)
        if dim:
            c.restore()
    c.restore()
    overlay(c, "#DCE4FF", 0.18 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


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
    ap.add_argument("--still", nargs=2)
    ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    if a.still:
        still(a.still[0], float(a.still[1]), HERE / "qc" / f"still_{a.still[0]}_{float(a.still[1]):.2f}.png")
    elif a.stills:
        for s in EDL.SEGMENTS:
            if s["src"] in SHOTS:
                tm = (s["t0"] + s["t1"]) / 2
                still(s["src"], tm, HERE / "qc" / "test_stills" / f"{tm:05.2f}_{s['src']}.png")
    else:
        todo = [(j, i) for j, fr in json.loads(a.frames_json).items() for i in fr]
        with Pool() as p:
            for k, _ in enumerate(p.imap_unordered(render, todo, chunksize=6)):
                if k % 100 == 0:
                    print(f"  2d {k}/{len(todo)}", flush=True)
        print(f"  2d rendered {len(todo)} frames")
