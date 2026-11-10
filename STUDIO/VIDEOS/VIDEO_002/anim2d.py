"""anim2d.py - VIDEO_002 "Death by Pudding" shots. shot_NAME(c, t), t = global story time.

    python anim2d.py --frames-json '{...}'   (render_needed.py)
    python anim2d.py --stills                (one still per shot -> qc/test_stills/)
"""
import argparse
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[1]
sys.path.insert(0, str(STUDIO / "PIPELINE" / "twod"))
sys.path.insert(0, str(HERE))
import skia  # noqa: E402
from kit import W, H, FPS, key, blink, clamp, smooth_noise, rgb, text  # noqa: E402
from toon import (draw_character, mix_expr, prop_magnifier, prop_notebook, prop_cleaver, prop_papers,  # noqa: E402
                  prop_keys)
from lipsync import load as load_lip, viseme  # noqa: E402
import sets as S  # noqa: E402
import edit_video002 as EDL  # noqa: E402

B = EDL.B
LIP = load_lip("VIDEO_002")
DET = "marcus_detective"


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


def vignette(c, s=0.45):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.62,
                                        [skia.Color(0, 0, 0, 0), skia.Color(0, 0, 0, int(255 * s))], [0.5, 1.0])
    c.save()
    c.resetMatrix()
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    c.restore()


def idle_tilt(t, seed):
    return 2.0 * smooth_noise(t, seed, 0.3)


def expr_track(t, track, blend=0.12):
    cur = mix_expr(track[0][1], track[0][1], 1)
    for i, (tt, e) in enumerate(track):
        if t >= tt:
            prev = track[i - 1][1] if i else e
            cur = mix_expr(prev, e, clamp((t - tt) / blend))
    return cur


def ground(c, x, y, w, alpha=0.32):
    p = skia.Paint(AntiAlias=True, Color=rgb("#1A0E0A"))
    p.setAlphaf(alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.08))
    c.drawOval(skia.Rect(x - w / 2, y - w * 0.07, x + w / 2, y + w * 0.07), p)


def actor(c, name, x, y, h, pose, shadow=True, t=0.0):
    if shadow:
        ground(c, x, y, h * 0.42)
    pose = dict(pose, _t=t)
    return draw_character(c, name, x, y, h, pose)


def idle(t, seed):
    return {"blink": blink(t, seed), "tilt": idle_tilt(t, seed), "bob": 0.012 * math.sin(t * 2.2 + seed),
            "look": (0.45 * smooth_noise(t, seed + 5, 0.2), 0.0)}


def win_snow(c, t, r, n=26, seed=3):
    x, y, w_, h_ = r
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w_, h_))
    S.snowfall(c, t, r, n=n, seed=seed, size=5, speed=90, drift=20)
    c.restore()


def hall_live(c, t):
    win_snow(c, t, S.HALL_WIN, 30)


def dim_layer(c, amount):
    m = [1 - amount, 0, 0, 0, 0, 0, 1 - amount, 0, 0, 0, 0, 0, 1 - amount * 0.9, 0, 0, 0, 0, 0, 1, 0]
    c.saveLayer(None, skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m)))


# suspects: everyone gets one "guilty-looking" habit (red herrings, nobody stands out)
SUS = {
    "gaston": dict(arm_r=(0.55, -0.15), prop_r=prop_cleaver, arm_l="hips", expr="sad", tears=0.6),
    "prim": dict(arm_l="front_high", prop_l=prop_papers, arm_r="relaxed", expr="smug", turn=0.15),
    "cedric": dict(arm_l="hips", arm_r=(0.35, 0.75), prop_r=prop_keys, expr="confident"),
}


def sus_pose(t, n, seed, **kw):
    p = idle(t, seed)
    p.update(SUS[n])
    p["vis"] = vis(t, n)
    p.update(kw)
    return p


# ================================================================ 1. the victim (event on frame 0: spoon drops)
def shot_dining(c, t):
    z = key(t, [(0.0, 1.9), (1.6, 1.0, "io")])
    c.save()
    cam(c, z, 540, key(t, [(0.0, 1080.0), (1.6, 980.0, "io")]))
    bg(c, "dining")
    S.draw_candles(c, S.DINING_CANDLES, t, 1.0, holder=False)
    S.victim(c, 470, 1195, 520, t)
    c.restore()
    if t >= B["poisoned"]:
        overlay(c, "#5A9A3A", 0.18 * clamp(1 - (t - B["poisoned"]) / 0.6))  # sickly green tint on "Poisoned!"
    vignette(c, 0.5)


# ================================================================ 2. three suspects (+ the cat)
TRIO = {"gaston": (250, 1650, 900), "prim": (545, 1650, 860), "cedric": (840, 1650, 940)}


def trio_in_hall(c, t, extra=lambda n, t: {}, cat_smug=1.0):
    bg(c, "hall")
    hall_live(c, t)
    for i, (n, (x, y, h)) in enumerate(TRIO.items()):
        actor(c, n, x, y, h, sus_pose(t, n, 21 + i, **extra(n, t)), t=t)
    S.cat(c, 560, 1830, 170, t, smug=cat_smug)


def shot_trio(c, t):
    c.save()
    cam(c, 1.0, 540, 1000)

    def glance(n, tt):  # side-eye each other on "one killer"
        k = {"gaston": 1, "prim": -1, "cedric": -1}[n]
        return {"look": (k * 0.8 * clamp((tt - B["one_killer"]) / 0.25), 0.0)}
    trio_in_hall(c, t, glance)
    c.restore()
    vignette(c, 0.45)


# ================================================================ 3. exterior: mansion in the blizzard (cars in the drive!)
def shot_ext(c, t):
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "ext")
    S.snowfall(c, t, (-100, -100, W + 200, H + 200), n=170, seed=7, size=7, speed=150, drift=60)
    c.restore()
    vignette(c, 0.5)


# ================================================================ 4. Marcus arrives, covered in snow
def shot_arrive(c, t):
    t0 = B["arrive"]
    snow = key(t, [(t0, 1.0), (t0 + 1.4, 1.0), (t0 + 2.0, 0.25, "out")])  # brushes most of it off
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "hall")
    hall_live(c, t)
    # cold air + flakes blowing in through the open door for a moment
    if t < t0 + 1.0:
        S.snowfall(c, t, (60, 620, 330, 690), n=30, seed=9, size=6, speed=200, drift=40)
    walk_x = key(t, [(t0, 220.0), (t0 + 0.9, 420.0, "out")])
    pose = {"expr": expr_track(t, [(t0, "surprised"), (t0 + 0.9, "neutral"), (B["nobody"] - 0.2, "determined")]),
            "vis": vis(t, "marcus"), "blink": blink(t, 4), "snow": snow,
            "walk": (t * 1.8) % 1 if t < t0 + 0.9 else None,
            "arm_l": "hips" if t > t0 + 2.0 else (0.2, -0.4 + 0.15 * math.sin(t * 18)),  # brushing snow off
            "arm_r": key(t, [(t0, (0.18, 1.28)), (B["nobody"], (0.18, 1.28)), (B["nobody"] + 0.3, (1.1, 0.05), "back")]),
            "hand_r": "point" if t > B["nobody"] else "open",
            "turn": key(t, [(t0, 0.4), (B["nobody"], 0.0)]), "tilt": idle_tilt(t, 1)}
    actor(c, DET, walk_x, 1760, 1150, pose, t=t)
    c.restore()
    vignette(c, 0.45)


# ================================================================ 5. alibis: medium close-ups in the hall (blurred bg)
CU = {"gaston": (440, 900), "prim": (540, 880), "cedric": (640, 860), "marcus": (450, 900)}  # cx in [432, 648] at zoom 1.25 -> no black edges
MCU_H, MCU_Y = 1550, 2200


def cu_bg(c, t, who):
    cx, cy = CU[who]
    c.save()
    cam(c, 1.25, cx, cy)
    bg(c, "hall_blur")
    c.restore()


def shot_cu_gaston(c, t):
    cu_bg(c, t, "gaston")
    cr = B["crying"]
    pose = sus_pose(t, "gaston", 21, expr=expr_track(t, [(B["gaston"], "worried"), (cr - 0.2, "sad")]),
                    tears=key(t, [(B["gaston"], 0.5), (cr - 0.2, 0.5), (cr, 1.0)]), turn=-0.15,
                    arm_r=(0.55, -0.15 + 0.12 * math.sin(t * 7)))  # waves the cleaver while talking
    actor(c, "gaston", 540, MCU_Y, MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.45)


def shot_cu_prim(c, t):
    cu_bg(c, t, "prim")
    pose = sus_pose(t, "prim", 22, expr=expr_track(t, [(B["prim"], "smug"), (B["cat_word"] - 0.4, "suspicious")]))
    actor(c, "prim", 540, MCU_Y - 40, MCU_H * 0.95, pose, shadow=False, t=t)
    # the cat pops up from the bottom on "cat" (gag)
    up = clamp((t - B["cat_word"] + 0.1) / 0.25)
    if up > 0:
        S.cat(c, 860, 1920 + 230 - 360 * (1 - (1 - up) ** 3), 420, t)
    vignette(c, 0.45)


def shot_cu_cedric(c, t):
    cu_bg(c, t, "cedric")
    yr = B["yours"]
    pose = sus_pose(t, "cedric", 23, expr=expr_track(t, [(B["cedric"], "surprised"), (B["cedric"] + 0.8, "confident"),
                                                          (yr - 0.3, "smile")]),
                    arm_r=key(t, [(B["cedric"], (0.35, 0.75)), (yr - 0.4, (0.35, 0.75)), (yr - 0.1, (1.1, 0.1), "back")]),
                    hand_r="point" if t > yr - 0.15 else "open", prop_r=None if t > yr - 0.2 else prop_keys,
                    look=(0.7, 0.0) if t > yr - 0.3 else (0.0, 0.0))
    actor(c, "cedric", 540, MCU_Y, MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.45)


def shot_cu_marcus(c, t):
    cu_bg(c, t, "marcus")
    pose = {"expr": "suspicious", "vis": vis(t, "marcus"), "blink": blink(t, 4), "turn": 0.25, "look": (0.6, -0.1),
            "tilt": idle_tilt(t, 1), "arm_r": "chin", "arm_l": "front_high", "prop_l": prop_notebook}
    actor(c, DET, 540, MCU_Y, MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.45)


# ================================================================ 6. the search: kitchen, library, hall (equal)
def inspect_pose(t, t0, flip=False):
    u = clamp((t - t0) / EDL.ROOM_LEN)
    return {"expr": "suspicious" if u < 0.6 else "determined", "blink": blink(t, 4), "arm_r": "front_high",
            "prop_r": prop_magnifier, "arm_l": "hips", "turn": key(t, [(t0, 0.6), (t0 + 0.6, 0.2)]),
            "look": (0.6, 0.5), "tilt": 6, "lean": 4, "flip": flip}


def room_cam(t, t0):
    u = clamp((t - t0) / EDL.ROOM_LEN)
    return 1.04 + 0.05 * u, 520 + 40 * u


def onions(c, x, y):
    S.shape(c, S.rect(x - 130, y - 18, 260, 22, 6), "#C99668", ow=3)  # cutting board on the counter
    for k, dx in enumerate((-80, -40, 0, 45, 85)):
        S.shape(c, S.oval(x + dx, y - 34, 22, 18), "#E8D6A8" if k % 2 else "#D8C08A", ow=3)


def shot_room_kitchen(c, t):
    t0 = B["room_kitchen"]
    z, cx = room_cam(t, t0)
    c.save()
    cam(c, z, cx, 1050)
    bg(c, "kitchen")
    win_snow(c, t, S.KITCHEN_WIN)
    S.draw_candles(c, S.KITCHEN_CANDLES, t, 0.9)
    onions(c, 260, 1000)
    actor(c, DET, 720, 1800, 950, inspect_pose(t, t0, flip=True), t=t)
    c.restore()
    vignette(c, 0.45)


def shot_room_library(c, t):
    t0 = B["room_library"]
    z, cx = room_cam(t, t0)
    c.save()
    cam(c, z, cx, 1050)
    bg(c, "library")
    win_snow(c, t, (380, 200, 320, 520))
    S.cat(c, 740, 1182, 150, t)  # Mr. Whiskers on the desk, unbothered
    actor(c, DET, 330, 1760, 950, inspect_pose(t, t0), t=t)
    c.restore()
    vignette(c, 0.45)


def shot_room_hall(c, t):
    t0 = B["room_hall"]
    z, cx = room_cam(t, t0)
    c.save()
    cam(c, z, cx, 1050)
    bg(c, "hall")
    hall_live(c, t)
    actor(c, DET, 300, 1760, 950, dict(inspect_pose(t, t0), look=(0.6, 0.7)), t=t)  # checks the coat rack / doormat
    c.restore()
    vignette(c, 0.45)


# ================================================================ 7. "Case closed."
def shot_marcus_end(c, t):
    cl = B["closed"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "hall")
    hall_live(c, t)
    pose = {"expr": expr_track(t, [(B["marcus_end"], "neutral"), (cl, "smug")]), "vis": vis(t, "marcus"),
            "blink": blink(t, 4), "arm_l": "hips",
            "arm_r": key(t, [(B["marcus_end"], (0.18, 1.28)), (cl - 0.3, (0.18, 1.28)), (cl, (-0.2, -1.25), "back"),
                             (cl + 0.9, (-0.2, -1.25)), (cl + 1.2, (0.18, 1.28))]),
            "tilt": -5 * clamp((t - cl) / 0.3)}
    actor(c, DET, 470, 1840, 1250, pose, t=t)
    c.restore()
    vignette(c, 0.45)


# ================================================================ 8. recap cards (split screen)
CARD = (190, 652, 700, 616)
CARD_S = 0.64


def panel(c, t, name_t, label, room, cx, cy, people):
    c.drawPaint(skia.Paint(Color=rgb("#241A22")))
    x, y, w_, h_ = CARD
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w_, h_))
    c.translate(x + w_ / 2, y + h_ / 2)
    c.scale(CARD_S, CARD_S)
    c.translate(-cx, -cy)
    bg(c, room)
    people(c, t)
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(x, y, w_, h_), skia.Paint(AntiAlias=True, Color=rgb("#E9DFC4"),
                                                            Style=skia.Paint.kStroke_Style, StrokeWidth=10))
    end = B["final"] - 0.6
    if not (name_t - 0.1 <= t or t >= end):
        overlay(c, "#000000", 0.55)
    text(c, label, x + 24, y + 70, 50, "#FFFFFF", face="Anton-Regular.ttf", align="left", outline=8)


def shot_panel_kitchen(c, t):
    def ppl(c, t):
        win_snow(c, t, S.KITCHEN_WIN)
        onions(c, 260, 1000)
        actor(c, "gaston", 560, 1340, 720, sus_pose(t, "gaston", 21, vis=(0, 0, 0)), t=t)
    panel(c, t, B["n_gaston"], "KITCHEN · GASTON", "kitchen", 540, 960, ppl)


def shot_panel_library(c, t):
    def ppl(c, t):
        win_snow(c, t, (380, 200, 320, 520))
        S.cat(c, 740, 1182, 150, t)
        actor(c, "prim", 330, 1560, 680, sus_pose(t, "prim", 22, vis=(0, 0, 0)), t=t)
    panel(c, t, B["n_prim"], "LIBRARY · MISS PRIM", "library", 540, 1100, ppl)


def shot_panel_hall(c, t):
    def ppl(c, t):
        hall_live(c, t)
        actor(c, "cedric", 470, 1410, 660, sus_pose(t, "cedric", 23, vis=(0, 0, 0)), t=t)
    panel(c, t, B["n_cedric"], "JUST ARRIVED · CEDRIC", "hall", 540, 980, ppl)


# ================================================================ 9. final question: all three equal (+ offended cat)
def shot_final_lineup(c, t):
    z = key(t, [(B["final"], 1.0), (B["freeze"], 1.08, "io")])
    c.save()
    cam(c, z, 540, 1040)

    def nerves(n, tt):
        return {"look": (0.0, 0.0), "sweat": 1.0,
                "expr": {"gaston": "worried", "prim": "nervous", "cedric": "worried"}[n]}
    offended = t > B["not_cat"] - 0.1
    trio_in_hall(c, t, nerves, cat_smug=0.0 if offended else 1.0)
    c.restore()
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
    ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    if a.stills:
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
