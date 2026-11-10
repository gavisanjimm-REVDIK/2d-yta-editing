"""anim2d.py - VIDEO_003 "The Three Doors of Doom" shots. shot_NAME(c, t), t = global story time.

    python anim2d.py --frames-json '{...}'   (render_needed.py)
    python anim2d.py --stills                (one still per shot -> qc/test_stills/)
"""
import argparse
import importlib.util
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
from kit import W, H, FPS, key, blink, clamp, smooth_noise, rgb, text, EASE  # noqa: E402
from toon import draw_character, mix_expr, prop_flashlight, arm_blend  # noqa: E402
from lipsync import load as load_lip, viseme  # noqa: E402
import sets as S  # noqa: E402
import edit_video003 as EDL  # noqa: E402

_spec = importlib.util.spec_from_file_location("v001_gfx", HERE.parent / "VIDEO_001" / "gfx.py")
GFX = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GFX)

B = EDL.B
LIP = load_lip("VIDEO_003")
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


def overlay(c, color, alpha):
    if alpha <= 0.002:
        return
    p = skia.Paint(Color=rgb(color))
    p.setAlphaf(clamp(alpha))
    c.save()
    c.resetMatrix()
    c.drawRect(skia.Rect(0, 0, W, H), p)
    c.restore()


def vignette(c, s=0.5):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.62,
                                        [skia.Color(0, 0, 0, 0), skia.Color(20, 8, 0, int(255 * s))], [0.5, 1.0])
    c.save()
    c.resetMatrix()
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))
    c.restore()


def expr_track(t, track, blend=0.12):
    cur = mix_expr(track[0][1], track[0][1], 1)
    for i, (tt, e) in enumerate(track):
        if t >= tt:
            prev = track[i - 1][1] if i else e
            cur = mix_expr(prev, e, clamp((t - tt) / blend))
    return cur


def ground(c, x, y, w, alpha=0.3):
    p = skia.Paint(AntiAlias=True, Color=rgb("#3A2008"))
    p.setAlphaf(alpha)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, w * 0.08))
    c.drawOval(skia.Rect(x - w / 2, y - w * 0.07, x + w / 2, y + w * 0.07), p)


def actor(c, name, x, y, h, pose, shadow=True, t=0.0):
    if shadow:
        ground(c, x, y, h * 0.42)
    return draw_character(c, name, x, y, h, dict(pose, _t=t))


def tilt(t, seed):
    return 2.0 * smooth_noise(t, seed, 0.3)


def torches(c, t, pts, s):
    for i, (x, y) in enumerate(pts):
        S.torch(c, x, y, t, s, i)


def sign_card(c, n, al, y=150):
    """Parchment strip with the door's carved sign (exact text, the viewer needs it)."""
    if al <= 0:
        return
    x, w_, h_ = 70, W - 140, 250
    GFX._parchment(c, x, y, w_, h_, al)
    text(c, f"DOOR {n}", W / 2, y + 82, 56, "#8A1F1A", face="Cinzel-VF.ttf", shadow=False, alpha=al, max_w=w_ - 80)
    text(c, EDL.SIGNS[n], W / 2, y + 170, 44, "#3A2414", face="Cinzel-VF.ttf", shadow=False, alpha=al, max_w=w_ - 70)


def mummy_pose(t, seed=31, **kw):
    p = {"blink": blink(t, seed, 3.6), "tilt": tilt(t, seed), "vis": vis(t, "mummy"), "bob": 0.015 * math.sin(t * 2.0)}
    p.update(kw)
    return p


def marcus_pose(t, **kw):
    p = {"blink": blink(t, 4), "tilt": tilt(t, 1), "vis": vis(t, "marcus")}
    p.update(kw)
    return p


# ================================================================ 1. the chase down the corridor (event on frame 0)
def depth_y(d):
    """Floor y + scale for corridor depth d (0 = far end, 1 = at camera)."""
    return 1020 + 880 * d ** 1.4, 0.18 + 0.95 * d ** 1.4


def speed_lines(c, t, amount):
    """Streaks rushing out of the vanishing point (we are running with Marcus)."""
    if amount <= 0:
        return
    import random
    r = random.Random(5)
    for i in range(26):
        a = r.uniform(0, math.tau)
        ph = (t * 2.2 + r.random()) % 1
        r0, r1 = 120 + 900 * ph, 120 + 900 * ph + 160
        p = S.line_w(5, "#FFF4D8", 0.35 * amount * (1 - ph))
        c.drawLine(540 + math.cos(a) * r0, 860 + math.sin(a) * r0, 540 + math.cos(a) * r1, 860 + math.sin(a) * r1, p)


def shot_corridor(c, t):
    sl = B["slam"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "corridor")
    torches(c, t, S.CORRIDOR_TORCHES, 1.0)
    speed_lines(c, t, 1.0 - clamp((t - sl + 0.3) / 0.3))
    # the stone slab slams down at the far end, behind Marcus: trapped
    drop = EASE["in"](clamp((t - sl + 0.05) / 0.18))
    if t > sl - 0.3:
        c.save()
        c.clipRect(skia.Rect(420, 700, 660, 1020))  # slides down out of the doorway's top edge
        S.shape(c, S.rect(420, 380 + 320 * drop, 240, 320), "#8A6A3A", shade="#6E5228", sdx=18)
        c.restore()
    if t > sl + 0.1:
        u = clamp((t - sl - 0.1) / 1.0)
        S.radial(c, 540, 1010, 260 * (0.4 + u), "#E8C890", 0.5 * (1 - u))
    # Marcus sprints toward the camera (proper run cycle), then skids to a stop when the slab drops
    run_until = sl - 0.15
    dm = EASE["out"](clamp(t / (run_until + 0.4)))
    y, s = depth_y(0.08 + 0.6 * dm)
    running = t < run_until
    ph = (t * 2.5) % 1
    if running:  # little dust puff on every footfall
        for k in range(2):
            f = (ph + k * 0.5) % 1
            if f < 0.35:
                S.radial(c, 540 - 230 * dm + (60 if k else -60) * s, y + 6, 120 * s * (0.5 + f), "#E8C890",
                         0.45 * (1 - f / 0.35))
    skid = clamp((t - run_until) / 0.3)
    pose = marcus_pose(t, expr="angry" if t < sl else "shocked",
                       turn=-0.65 * EASE["out"](clamp((t - sl) / 0.3)), look=(0, 0) if t < sl else (-0.9, -0.3),
                       tilt=(5 * math.sin(ph * math.tau) if running else -4 * skid))
    if running:
        pose.update(run=ph)
        if t < 2.3:  # shouting + pointing after the thief while running
            pose.update(arm_r=(1.0, -0.15, "down"), hand_r="point")
    else:
        pose.update(arm_l=arm_blend(DET, t, [(run_until, "relaxed"), (sl + 0.25, "up")], 0.2),
                    arm_r=arm_blend(DET, t, [(run_until, "relaxed"), (sl + 0.25, "up")], 0.2))
    mx = 540 - 230 * dm  # veers left so the far doorway (and the slab) stays visible
    actor(c, DET, mx, y, 1150 * s, pose, t=t)
    # the cat burglar gallops across the foreground first, scarab in its mouth
    u = clamp(t / 1.35)
    if u < 1:
        S.cat_run(c, -260 + 1600 * u, 1880, 520, t)
    c.restore()
    vignette(c, 0.6)


# ================================================================ 2. the chamber, the mummy pops out of his sarcophagus
def chamber_live(c, t):
    torches(c, t, S.CHAMBER_TORCHES, 0.75)


def shot_chamber_wide(c, t):
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "chamber")
    chamber_live(c, t)
    # the cat squeezes out through the little hole (gets away)
    u = clamp((t - B["chamber"]) / 0.6)
    if u < 1:
        c.save()
        c.clipRect(skia.Rect(0, 0, 1000 + 70 * (1 - u), 1920))
        S.cat_run(c, 820 + 300 * u, 1172, 150, t)
        c.restore()
    # Marcus at the right, the mummy rises from the sarcophagus (left)
    actor(c, DET, 760, 1720, 960, marcus_pose(t, expr=expr_track(t, [(B["chamber"], "angry"), (B["mummy_up"], "shocked")]),
                                             arm_l="hips", arm_r="relaxed", turn=-0.5,
                                             look=(-0.9, 0) if t > B["mummy_up"] else (0.7, 0.3)), t=t)
    rise = EASE["back"](clamp((t - B["mummy_up"]) / 0.45))
    if rise > 0:
        c.save()
        c.clipRect(skia.Rect(-100, 0, 1080, 1520))
        actor(c, "mummy", 150, 1520 + 700 * (1 - rise), 900,
              mummy_pose(t, expr="happy", arm_l=arm_blend("mummy", t, [(B["mummy_up"], "relaxed"), (B["mummy_up"] + 0.5, "up")]),
                         arm_r=arm_blend("mummy", t, [(B["mummy_up"], "relaxed"), (B["mummy_up"] + 0.6, (0.9, -0.7, "down")),
                                                      (B["mummy_up"] + 2.4, (0.9, -0.7, "down")), (B["mummy_up"] + 3.0, "hips")]),
                         turn=0.4), shadow=False, t=t)
        c.restore()
    c.restore()
    vignette(c, 0.5)


# ================================================================ 3. close-ups (blurred chamber behind)
MCU_H, MCU_Y = 1550, 2200


def cu_bg(c, t, cx):
    c.save()
    cam(c, 1.25, cx, 900)
    bg(c, "chamber_blur")
    c.restore()


def shot_cu_mummy(c, t):
    cu_bg(c, t, 470)
    pose = mummy_pose(t, expr=expr_track(t, [(B["cu_mummy"], "happy"), (B["cu_mummy"] + 1.6, "smug")]),
                      arm_l="hips", arm_r=arm_blend("mummy", t, [(B["cu_mummy"], (0.6, -0.4, "down")),
                                                                 (B["cu_mummy"] + 1.9, "relaxed")], 0.35),
                      hand_r="point" if t < B["cu_mummy"] + 1.7 else "open", turn=0.15)
    actor(c, "mummy", 540, MCU_Y, MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.45)


def shot_cu_mummy2(c, t):
    cu_bg(c, t, 600)
    wag = 0.08 * math.sin(t * 10)
    pose = mummy_pose(t, expr=expr_track(t, [(B["mummy2"], "smug"), (B["carved"], "happy"), (B["years_ago"], "smug")]),
                      arm_r=(0.45 + wag, -0.75, "down"), hand_r="point", arm_l="hips", turn=-0.1, tilt=6)
    actor(c, "mummy", 540, MCU_Y, MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.45)


def shot_cu_marcus(c, t):
    cu_bg(c, t, 640)
    pk = B["pick"]
    pose = marcus_pose(t, expr=expr_track(t, [(B["marcus"], "confident"), (pk - 0.2, "smug")]), arm_l="hips",
                       arm_r=arm_blend(DET, t, [(B["marcus"], "chin"), (pk, (1.1, -0.1, "down"))], 0.3),
                       hand_r="point" if t > pk - 0.15 else "fist", turn=0.2, look=(0.6, 0))
    actor(c, DET, 540, MCU_Y, MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.45)


def shot_cu_gulp(c, t):
    cu_bg(c, t, 640)
    pose = marcus_pose(t, expr="nervous", sweat=1.0, arm_l="relaxed", arm_r="relaxed",
                       look=(0.8 * math.sin(t * 6), 0.0), tilt=-3)
    actor(c, DET, 540, MCU_Y + 20 * math.sin(t * 9) * (t < B["gulp"] + 0.6), MCU_H, pose, shadow=False, t=t)
    vignette(c, 0.5)


# ================================================================ 4. the three doors (same framing each, sign card on top)
def door_shot(c, t, n, t0):
    """Same framing for all three doors: the door centred on its wall, sign card above it."""
    u = clamp((t - t0) / 3.6)
    c.save()
    c.translate(W / 2, 1100)
    c.scale(1.0 + 0.05 * u, 1.0 + 0.05 * u)  # gentle push-in
    c.translate(-W / 2, -1100)
    S.door_closeup(c, n, t)
    c.restore()
    vignette(c, 0.45)
    sign_card(c, n, clamp((t - t0 - 0.15) / 0.25))


def shot_door1(c, t):
    door_shot(c, t, 1, B["door1"])


def shot_door2(c, t):
    door_shot(c, t, 2, B["door2"])


def shot_door3(c, t):
    door_shot(c, t, 3, B["door3"])


# ================================================================ 5. "Lunch time, kitties!" -> ROAR
def shot_lunch(c, t):
    t0, rr = B["lunch"], B["roar"]
    c.save()
    cam(c, 1.0, 540, 960)
    bg(c, "chamber")
    chamber_live(c, t)
    dx, dy = S.DOORS[2]
    hatch = clamp((t - rr + 0.35) / 0.2)
    S.lion_eyes(c, dx + 125, dy + 500, 1.6, t, hatch)
    # mummy strolls to door two and knocks: "my kitties are mummies too"
    mx = key(t, [(t0, 200.0), (t0 + 1.6, 330.0, "out")])
    knock = (rr - 1.2 < t < rr - 0.4) and (int(t * 6) % 2 == 0)
    actor(c, "mummy", mx, 1700, 900, mummy_pose(t, expr="happy" if t < rr else "surprised",
                                                arm_r=arm_blend("mummy", t, [(t0, "relaxed"),
                                                                             (rr - 1.2, (1.0 if knock else 0.9, -0.2, "down")),
                                                                             (rr - 0.2, "hips")], 0.25),
                                                hand_r="fist", arm_l="hips", turn=0.5,
                                                walk=(t * 1.6) % 1 if t < t0 + 1.6 else None), t=t)
    jump = clamp((t - rr) / 0.12) * (1 - clamp((t - rr - 0.5) / 0.3))
    actor(c, DET, 905, 1780 - 140 * jump, 780,
          marcus_pose(t, expr="suspicious" if t < rr else "panic", turn=-0.5,
                      arm_l=arm_blend(DET, t, [(t0, "hips"), (rr + 0.12, "up")], 0.12),
                      arm_r=arm_blend(DET, t, [(t0, "relaxed"), (rr + 0.12, "up")], 0.12),
                      look=(-0.9, 0.0)), t=t)
    c.restore()
    vignette(c, 0.5)


# ================================================================ 6. recap: the three doors side by side (split screen)
CARD = (200, 652, 680, 520)  # leaves a strip under each card for the caption
CARD_S = 0.95


def panel(c, t, n, name_t):
    c.drawPaint(skia.Paint(Color=rgb("#2A1A0A")))
    x, y, w_, h_ = CARD
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(x, y, w_, h_))
    c.translate(x + w_ / 2, y + h_ / 2)
    c.scale(0.44, 0.44)  # whole door: number, sign tablet, handle clue, floor
    c.translate(-540, -1040)
    S.door_closeup(c, n, t)
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(x, y, w_, h_), skia.Paint(AntiAlias=True, Color=rgb("#E9DFC4"),
                                                            Style=skia.Paint.kStroke_Style, StrokeWidth=10))
    if not (t >= name_t - 0.1):
        overlay(c, "#000000", 0.55)
    bar = skia.Rect.MakeXYWH(x + 10, y + h_ - 110, w_ - 20, 100)
    p = skia.Paint(Color=rgb("#1A1008"))
    p.setAlphaf(0.7)
    c.drawRect(bar, p)
    text(c, f"{n} · {EDL.SIGNS[n]}", W / 2, y + h_ - 45, 40, "#FFF4D8", face="Anton-Regular.ttf", outline=6,
         max_w=w_ - 40)


def shot_panel_1(c, t):
    panel(c, t, 1, B["n_fire"])


def shot_panel_2(c, t):
    panel(c, t, 2, B["n_lions"])


def shot_panel_3(c, t):
    panel(c, t, 3, B["n_flood"])


# ================================================================ 7. final: Marcus between the doors, which one?
def shot_final(c, t):
    z = key(t, [(B["final"], 1.0), (B["freeze"], 1.06, "io")])
    c.save()
    cam(c, z, 540, 960)
    bg(c, "chamber")
    chamber_live(c, t)
    actor(c, "mummy", 150, 1700, 860, mummy_pose(t, expr="smug", arm_l="hips", arm_r="hips", turn=0.4), t=t)
    actor(c, DET, 560, 1780, 980, marcus_pose(t, expr="suspicious", arm_r="chin", hand_r="fist", arm_l="hips",
                                             turn=0.0, look=(0.9 * math.sin(t * 1.6), -0.6)), t=t)
    c.restore()
    vignette(c, 0.5)


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
