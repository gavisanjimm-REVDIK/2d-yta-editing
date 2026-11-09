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
from toon import draw_character, CAST, mix_expr, prop_flashlight, prop_notebook, prop_magnifier  # noqa: E402
from lipsync import load as load_lip, viseme  # noqa: E402
import sets as S  # noqa: E402
import edit_video001 as EDL  # noqa: E402

B = EDL.B
WORDS = EDL.WORDS


# ================================================================ shared helpers
LIP = load_lip("VIDEO_001")


def vis(t, who):
    return viseme(t, LIP, who)


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


DET = "marcus_detective"


def ground(c, x, y, w, alpha=0.32):
    """Soft contact shadow so characters/props stand ON the floor."""
    p = skia.Paint(AntiAlias=True, Color=rgb("#1A0E0A"))
    p.setAlphaf(alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.08))
    c.drawOval(skia.Rect(x - w / 2, y - w * 0.07, x + w / 2, y + w * 0.07), p)


def actor(c, name, x, y, h, pose, shadow=True):
    if shadow:
        ground(c, x, y, h * 0.42)
    return draw_character(c, name, x, y, h, pose)


def window_flash(c, t, r, rr=6):
    lt = lightning(t)
    x, y, w_, h_ = r
    c.save()
    c.clipPath(S.rect(x, y, w_, h_, rr), doAntiAlias=True)
    rain(c, t, r, n=30, alpha=0.6, seed=int(x), length=45)
    if lt > 0.01:
        c.drawPaint(skia.Paint(Color=skia.Color(235, 240, 255, int(235 * lt))))
    c.restore()
    return lt


def nervous_idle(t, seed):
    return {"blink": blink(t, seed), "tilt": idle_tilt(t, seed), "bob": 0.012 * math.sin(t * 2.2 + seed),
            "look": (0.5 * smooth_noise(t, seed + 5, 0.2), 0.0)}


# ================================================================ HOOK 1: storm exterior (event on frame 0)
def shot_ext(c, t):
    c.save()
    z = key(t, [(0.0, 1.0), (B["hook_lineup"], 1.6, "in")])
    cam(c, z, 540, 1180 + 100 * (z - 1))
    bg(c, "ext")
    lt = lightning(t)
    if lt > 0.05:
        bolt(c, 760, 0, 900, int(t * 2) + 3, lt)
    rain(c, t, (-200, -200, W + 400, H + 400), n=140, alpha=0.45, length=90)
    c.restore()
    overlay(c, "#DCE4FF", 0.7 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.55)


# ================================================================ HOOK 2: three suspects (all equally uneasy)
TRIO = {"oliver": (250, 1640, 940), "daniel": (545, 1660, 910), "sophie": (840, 1640, 820)}
TRIO_POSE = {"oliver": dict(arm_r="neck", arm_l="behind", expr="nervous"),
             "daniel": dict(arm_l="hips", arm_r="neck", expr="worried"),
             "sophie": dict(arm_l="front", arm_r="front", expr="shy", look=(0.0, 0.6))}


def trio(c, t, extra=None, sweat=0.0):
    for i, (n, (x, y, h)) in enumerate(TRIO.items()):
        p = nervous_idle(t, 11 + i)
        p.update(TRIO_POSE[n])
        p["sweat"] = sweat
        p["vis"] = vis(t, n)
        if extra:
            p.update(extra(n, t))
        actor(c, n, x, y, h, p)


def shot_hook_lineup(c, t):
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "foyer")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = window_flash(c, t, (300, 120, 170, 330), 85) + window_flash(c, t, (640, 120, 170, 330), 85)

    def glance(n, tt):  # they glance at each other (everyone is a possible suspect)
        k = {"oliver": 1, "daniel": -1, "sophie": -1}[n]
        return {"look": (k * 0.8 * clamp((tt - B["hook_lineup"] - 0.4) / 0.3), 0.0)}
    trio(c, t, glance)
    c.restore()
    overlay(c, "#DCE4FF", 0.12 * min(lt, 1), skia.BlendMode.kScreen)
    vignette(c, 0.45)


# ================================================================ HOOK 3: the detective
def shot_hook_marcus(c, t):
    td = B["detective"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "foyer")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = window_flash(c, t, (300, 120, 170, 330), 85) + window_flash(c, t, (640, 120, 170, 330), 85)
    pose = {"expr": expr_track(t, [(B["hook_marcus"], "determined"), (td, "smug")]), "blink": blink(t, 4),
            "turn": key(t, [(B["hook_marcus"], 0.5), (td, 0.0)]), "look": (0.0, 0.0),
            "arm_r": key(t, [(B["hook_marcus"], (0.18, 1.28)), (td - 0.1, (0.18, 1.28)), (td + 0.25, (-0.2, -1.25), "back"),
                             (td + 0.9, (-0.2, -1.25)), (td + 1.2, (0.18, 1.28))]),
            "arm_l": "hips", "tilt": idle_tilt(t, 1) - 4 * clamp((t - td) / 0.3)}
    actor(c, DET, 600, 1760, 1150, pose)
    c.restore()
    overlay(c, "#DCE4FF", 0.15 * min(lt, 1), skia.BlendMode.kScreen)
    vignette(c, 0.5)


# ================================================================ Harrison & the empty safe
def _study_light(c, t):
    S.draw_candles(c, S.STUDY_CANDLES, t, 1.0, holder=False)
    return window_flash(c, t, (620, 160, 360, 640), 170)


def shot_study_safe(c, t):
    c.save()
    cam(c, 1.9, 470, 1110)
    bg(c, "study")
    _study_light(c, t)
    c.restore()
    vignette(c, 0.55)


def shot_study(c, t):
    t0, pw = B["harrison_ms"], B["power"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "study")
    lt = _study_light(c, t)
    pose = {"expr": expr_track(t, [(t0, "panic"), (pw, "shocked")]), "vis": vis(t, "harrison"),
            "blink": blink(t, 7),
            "arm_l": key(t, [(t0, (0.55, -1.0)), (pw - 0.1, (0.55, -1.0)), (pw + 0.2, (0.3, 0.9))]),
            "arm_r": key(t, [(t0, (0.55, -1.0)), (pw - 0.1, (0.55, -1.0)), (pw + 0.2, (1.2, -0.35))]),
            "hand_r": "point" if t > pw else "open",
            "turn": key(t, [(t0, -0.2), (pw, -0.2), (pw + 0.3, 0.4)]),
            "look": (key(t, [(t0, 0.0), (pw, 0.0), (pw + 0.2, 0.8)]), -0.3), "tilt": 2 * math.sin(t * 8) * (t < pw)}
    actor(c, "harrison", 400, 1760, 1150, pose)
    c.restore()
    overlay(c, "#DCE4FF", 0.22 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.5)


# ================================================================ "Nobody leaves" (over the shoulder)
def shot_foyer_wide(c, t):
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "foyer")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = window_flash(c, t, (300, 120, 170, 330), 85) + window_flash(c, t, (640, 120, 170, 330), 85)
    sub = {"oliver": (470, 1610, 820), "daniel": (690, 1625, 800), "sophie": (900, 1610, 720)}
    for i, (n, (x, y, h)) in enumerate(sub.items()):
        p = nervous_idle(t, 11 + i)
        p.update(TRIO_POSE[n])
        p["look"] = (-0.7, 0.0)  # all watch the detective
        actor(c, n, x, y, h, p)
    mp = {"expr": "determined", "turn": 0.7, "look": (0.9, 0.0), "vis": vis(t, "marcus"), "blink": blink(t, 4),
          "arm_l": "hips", "arm_r": key(t, [(B["foyer"], (0.18, 1.28)), (B["foyer"] + 0.5, (1.0, 0.1), "back")]),
          "hand_r": "point", "tilt": idle_tilt(t, 1)}
    actor(c, DET, 150, 2060, 1250, mp, shadow=False)
    c.restore()
    overlay(c, "#DCE4FF", 0.12 * min(lt, 1), skia.BlendMode.kScreen)
    vignette(c, 0.45)


# ================================================================ alibis: medium close-ups (smaller, more room)
CU = {"oliver": (640, 880), "daniel": (520, 760), "sophie": (660, 700), "marcus": (430, 820)}
MCU_H, MCU_Y = 1550, 2200


def _cu_bg(c, t, name):
    cx, cy = CU[name]
    c.save()
    cam(c, 1.25, cx, cy)
    bg(c, "foyer_blur")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = window_flash(c, t, (300, 120, 170, 330), 85) + window_flash(c, t, (640, 120, 170, 330), 85)
    c.restore()
    return min(lt, 1)


def _finish(c, lt):
    overlay(c, "#DCE4FF", 0.15 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


def shot_cu_oliver(c, t):
    lt = _cu_bg(c, t, "oliver")
    dk = B["o_dark"]
    pose = {"expr": expr_track(t, [(B["oliver"], "neutral"), (dk - 0.2, "worried")]), "vis": vis(t, "oliver"),
            "blink": blink(t, 11), "turn": -0.2, "look": key(t, [(B["oliver"], (0.0, 0.0)), (dk - 0.8, (0.6, -0.5))]),
            "tilt": idle_tilt(t, 2), "arm_r": (-0.45, -0.05 + 0.05 * math.sin(t * 14)), "arm_l": "behind"}
    actor(c, "oliver", 540, MCU_Y, MCU_H, pose, shadow=False)
    _finish(c, lt)


def shot_cu_daniel(c, t):
    lt = _cu_bg(c, t, "daniel")
    pp = B["d_pipe"]
    pose = {"expr": expr_track(t, [(B["daniel"], "neutral"), (pp, "smile"), (pp + 1.2, "worried")]),
            "vis": vis(t, "daniel"), "blink": blink(t, 12), "turn": 0.15, "tilt": idle_tilt(t, 3),
            # scratches his neck while talking - the same nervous habit as Oliver's tie: nobody stands out
            "arm_r": (-0.45, -0.05) if B["daniel"] + 0.3 < t < pp else "relaxed",
            "arm_l": "hips", "look": (0.3 * smooth_noise(t, 9, 0.3), 0.0)}
    actor(c, "daniel", 540, MCU_Y, MCU_H, pose, shadow=False)
    _finish(c, lt)


def shot_cu_sophie(c, t):
    lt = _cu_bg(c, t, "sophie")
    rt, dr = B["s_rattled"], B["s_dropped"]
    pose = {"expr": expr_track(t, [(B["sophie"], "shy"), (rt - 0.1, "surprised"), (dr + 0.4, "worried")]),
            "vis": vis(t, "sophie"), "blink": blink(t, 13),
            "look": key(t, [(B["sophie"], (0.0, 0.5)), (rt - 0.2, (0.0, 0.5)), (rt, (0.6, -0.8)), (dr + 0.4, (0.0, 0.6))]),
            "turn": key(t, [(B["sophie"], -0.1), (rt - 0.2, -0.1), (rt, 0.25), (dr + 0.4, -0.1)]),
            "arm_l": "front", "arm_r": (0.45, -0.5) if rt < t < dr + 0.6 else "front",  # hand flies up at the thunder
            "tilt": idle_tilt(t, 4) + 4}
    actor(c, "sophie", 540, MCU_Y - 60, MCU_H * 0.92, pose, shadow=False)
    _finish(c, lt)


def shot_cu_marcus(c, t):
    lt = _cu_bg(c, t, "marcus")
    pose = {"expr": "suspicious", "vis": vis(t, "marcus"), "blink": blink(t, 4), "turn": 0.25,
            "look": (0.6, -0.1), "tilt": idle_tilt(t, 1), "arm_r": "chin", "arm_l": "front_high",
            "prop_l": prop_notebook}
    actor(c, DET, 540, MCU_Y, MCU_H, pose, shadow=False)
    _finish(c, lt)


# ================================================================ the investigation: 3 rooms, equal treatment
def _room_cam(t, t0):
    u = clamp((t - t0) / EDL.ROOM_LEN)
    return 1.04 + 0.05 * u, 520 + 40 * u


def _inspect_pose(t, t0, look_up_at):
    up = look_up_at is not None and t > look_up_at
    return {"expr": "surprised" if up and t < look_up_at + 0.5 else "suspicious", "blink": blink(t, 4),
            "arm_r": "front_high", "prop_r": prop_magnifier, "arm_l": "hips",
            "turn": key(t, [(t0, 0.6), (t0 + 0.6, 0.2)]),
            "look": (0.6, -0.9) if up else (0.6, 0.6), "tilt": -6 if up else 6, "lean": 4 if not up else 0}


def shot_room_laundry(c, t):
    t0 = B["room_laundry"]
    z, cx = _room_cam(t, t0)
    c.save()
    cam(c, z, cx, 1050)
    bg(c, "laundry")
    lt = window_flash(c, t, S.LAUNDRY_WIN)
    actor(c, DET, 330, 1800, 950, _inspect_pose(t, t0, t0 + 0.9))
    c.restore()
    overlay(c, "#DCE4FF", 0.2 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


def shot_room_kitchen(c, t):
    t0 = B["room_kitchen"]
    z, cx = _room_cam(t, t0)
    c.save()
    cam(c, z, cx, 1050)
    bg(c, "kitchen")
    S.draw_candles(c, S.KITCHEN_CANDLES, t, 0.9)
    lt = window_flash(c, t, S.KITCHEN_WIN)
    actor(c, DET, 760, 1820, 950, dict(_inspect_pose(t, t0, t0 + 0.9), flip=True))
    c.restore()
    overlay(c, "#DCE4FF", 0.2 * lt, skia.BlendMode.kScreen)
    vignette(c, 0.45)


def shot_room_basement(c, t):
    """Same framing and length as the other rooms. Dark (power out), flashlight sweeps the walls.
    Thunder is heard during this shot, but nothing lights up down here."""
    t0 = B["room_basement"]
    u = clamp((t - t0) / EDL.ROOM_LEN)
    cx = 1250 + 60 * u
    pose = {"expr": "suspicious", "blink": blink(t, 4), "arm_r": "flash", "arm_l": "hips",
            "turn": key(t, [(t0, 0.6), (t0 + 0.6, 0.3)]), "look": (0.8, -0.4), "tilt": 4}
    aim = (cx - 500 + 1100 * u, 700 + 120 * math.sin(t * 2.0))
    _basement_view(c, t, cx, 1.04 + 0.05 * u, {"x": 1150, "y": 1790, "h": 950, "pose": pose}, aim)


def _basement_view(c, t, cx, scale, marcus, aim_bg):
    c.save()
    cam(c, scale, cx, 1000)
    bg(c, "base_dark")
    pose = dict(marcus["pose"], prop_r=prop_flashlight(1.0))
    info = actor(c, DET, marcus["x"], marcus["y"], marcus["h"], pose)
    m = c.getTotalMatrix()
    c.restore()
    hand = info["hands"]["r"]
    cone, _ = beam(c, hand, m.mapXY(*aim_bg))
    c.save()
    c.clipPath(cone, doAntiAlias=True)
    c.concat(m)
    lit = skia.Paint()
    lit.setAlphaf(0.95)
    c.drawImage(S.img("base_lit"), 0, 0, skia.SamplingOptions(skia.FilterMode.kLinear), lit)
    c.restore()
    (hx, hy), _ = hand
    sh = skia.GradientShader.MakeRadial(skia.Point(hx, hy), 1500, [skia.Color(255, 236, 190, 70), skia.Color(255, 236, 190, 0)])
    c.save()
    c.clipPath(cone, doAntiAlias=True)
    c.drawPaint(skia.Paint(Shader=sh, BlendMode=skia.BlendMode.kPlus))
    c.restore()
    c.save()
    c.concat(m)
    dimmed(c, 0.22)
    actor(c, DET, marcus["x"], marcus["y"], marcus["h"], pose)
    c.restore()
    c.restore()
    S.radial(c, hx, hy, 60, "#FFF3C8", 0.8, plus=True)
    vignette(c, 0.55)


# ================================================================ "I know exactly who is lying."
def shot_marcus_end(c, t):
    ly = B["lying"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "foyer")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    window_flash(c, t, (300, 120, 170, 330), 85)
    window_flash(c, t, (640, 120, 170, 330), 85)
    pose = {"expr": expr_track(t, [(B["marcus_end"], "neutral"), (ly - 0.3, "smug")]), "vis": vis(t, "marcus"),
            "blink": blink(t, 4), "turn": 0.0, "look": (0.0, 0.0), "arm_l": "hips",
            "arm_r": key(t, [(B["marcus_end"], (0.18, 1.28)), (ly - 0.4, (0.18, 1.28)), (ly - 0.1, (-0.2, -1.25), "back"),
                             (ly + 0.8, (-0.2, -1.25)), (ly + 1.1, (0.18, 1.28))]),
            "tilt": -5 * clamp((t - ly + 0.3) / 0.3)}
    actor(c, DET, 540, 1840, 1250, pose)
    c.restore()
    vignette(c, 0.45)


# ================================================================ recap panels (split screen, each 1080 x ~633)
PANEL_CY = 960  # the split screen shows the middle band (y 643..1276) of each panel shot
CARD = (190, 652, 700, 616)  # framed "photo" of the room inside the band
CARD_S = 0.64


def _panel(c, t, name_t, label, room_bg, cx, cy, draw_people):
    c.drawPaint(skia.Paint(Color=rgb("#241A22")))
    x, y, w_, h_ = CARD
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w_, h_))
    c.translate(x + w_ / 2, y + h_ / 2)
    c.scale(CARD_S, CARD_S)
    c.translate(-cx, -cy)
    bg(c, room_bg)
    draw_people(c, t)
    c.restore()
    fr = skia.Paint(AntiAlias=True, Color=rgb("#E9DFC4"), Style=skia.Paint.kStroke_Style, StrokeWidth=10)
    c.drawRect(skia.Rect.MakeXYWH(x, y, w_, h_), fr)
    active = name_t - 0.1 <= t < B["n_fit"] - 0.1 or t >= B["n_fit"] - 0.1
    if not active:
        overlay(c, "#000000", 0.55)
    from kit import text
    text(c, label, x + 24, y + 70, 50, "#FFFFFF", face="Anton-Regular.ttf", align="left", outline=8)


def _p_kitchen(c, t):
    S.draw_candles(c, S.KITCHEN_CANDLES, t, 0.9)
    window_flash(c, t, S.KITCHEN_WIN)
    actor(c, "oliver", 560, 1330, 700, dict(nervous_idle(t, 11), arm_r="neck", arm_l="behind", expr="neutral"))


def _p_basement(c, t):
    overlay(c, "#0A1020", 0.3)
    actor(c, "daniel", 1350, 1460, 640, dict(nervous_idle(t, 12), arm_l="hips", arm_r="relaxed", expr="neutral"))


def _p_laundry(c, t):
    window_flash(c, t, S.LAUNDRY_WIN)
    actor(c, "sophie", 330, 1560, 660, dict(nervous_idle(t, 13), arm_l="front", arm_r="front", expr="neutral"))


def shot_panel_kitchen(c, t):
    _panel(c, t, B["n_kitchen"], "KITCHEN · OLIVER", "kitchen", 540, 940, _p_kitchen)


def shot_panel_basement(c, t):
    _panel(c, t, B["n_basement"], "BASEMENT · DANIEL", "base_lit", 1330, 1060, _p_basement)


def shot_panel_laundry(c, t):
    _panel(c, t, B["n_laundry"], "LAUNDRY ROOM · SOPHIE", "laundry", 540, 1110, _p_laundry)


# ================================================================ final question: all three, equal, slow push to the group
def shot_final_lineup(c, t):
    z = key(t, [(B["final"], 1.0), (B["freeze"], 1.1, "io")])
    c.save()
    cam(c, z, 540, 1020)
    bg(c, "foyer")
    S.draw_candles(c, S.FOYER_CANDLES, t, 0.8)
    lt = window_flash(c, t, (300, 120, 170, 330), 85) + window_flash(c, t, (640, 120, 170, 330), 85)

    def look_cam(n, tt):
        return {"look": (0.0, 0.0), "expr": {"oliver": "nervous", "daniel": "worried", "sophie": "worried"}[n]}
    trio(c, t, look_cam, sweat=1.0)
    c.restore()
    overlay(c, "#DCE4FF", 0.12 * min(lt, 1), skia.BlendMode.kScreen)
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
        import shutil
        shutil.rmtree(HERE / "qc" / "test_stills", ignore_errors=True)
        for s in EDL.SEGMENTS:
            for sub in (s["split"] if s["src"] == "split" else [s]):
                if sub["src"] in SHOTS:
                    tm = (s["t0"] + s["t1"]) / 2
                    still(sub["src"], tm, HERE / "qc" / "test_stills" / f"{tm:05.2f}_{sub['src']}.png")
    else:
        todo = [(j, i) for j, fr in json.loads(a.frames_json).items() for i in fr]
        with Pool() as p:
            for k, _ in enumerate(p.imap_unordered(render, todo, chunksize=6)):
                if k % 200 == 0:
                    print(f"  2d {k}/{len(todo)}", flush=True)
        print(f"  2d rendered {len(todo)} frames")
