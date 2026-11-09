"""anim2d.py - VIDEO_000 2D shots (Skia). One draw function per shot: shot_NAME(canvas, t), t = source seconds.

    python anim2d.py --frames-json '{"room": [0,1,2], "face": [10,11]}'   (called by render_needed.py)
    python anim2d.py --still room 3.5                                      (one test still -> qc/)
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[1]
sys.path.insert(0, str(STUDIO / "PIPELINE" / "twod"))
sys.path.insert(0, str(HERE))
import skia  # noqa: E402
from kit import W, H, FPS, key, blink, PerspCam, paint, clamp, smooth_noise  # noqa: E402
from flat import draw_puppet, glow, vignette, linear_grad, rrect  # noqa: E402
import edit_video000 as EDL  # noqa: E402

WORDS = EDL.WORDS
LAMP_ON = EDL.LAMP_ON


def lamp_level(t):
    return clamp((t - LAMP_ON) / 0.08) * (0.85 + 0.15 * (1 if int(t * 30) % 7 else 0.6))


def pose_at(t):
    on = t >= LAMP_ON
    react = clamp((t - LAMP_ON - 0.1) / 0.25)
    return {
        "lids": blink(t, 3),
        "talk": 0.0,  # narrator speaks, not the mascot
        "mouth": "o" if on and t < LAMP_ON + 1.2 else ("flat" if on else "smile"),
        # idle: glances around the quiet room, then snaps to the lamp
        "eyes_x": key(t, [(0, 0.0), (1.6, 0.0), (1.9, -0.6), (3.0, -0.6), (3.3, 0.3), (4.4, 0.3), (4.7, 0.0),
                          (LAMP_ON + 0.05, 0.0), (LAMP_ON + 0.25, 0.9, "out")]),
        "eyes_y": key(t, [(0, 0.0), (3.0, 0.0), (3.3, -0.3), (4.4, -0.3), (4.7, 0.0)]),
        "brow_l": 0.9 * react, "brow_r": 0.9 * react,
        "tilt": key(t, [(0, 0), (LAMP_ON, 0), (LAMP_ON + 0.3, -6, "back")]) + 2.5 * smooth_noise(t, 7, 0.25),
        "turn": key(t, [(0, 0.0), (LAMP_ON + 0.1, 0.0), (LAMP_ON + 0.45, 0.45, "out")]),
        "arm_l": (8, 5),
        "arm_r": key(t, [(0, (8, 5)), (LAMP_ON + 0.1, (8, 5)), (LAMP_ON + 0.35, (25, 70), "back")]),
        "breathe": (t * 0.3) % 1,
        "crouch": key(t, [(0, 0.0), (LAMP_ON, 0.0), (LAMP_ON + 0.12, 0.08, "out"), (LAMP_ON + 0.5, 0.0)]),
    }


def draw_room(c, cam, lamp):
    dim = 1 - 0.0 * lamp
    cam.box_room(c, 6, 3.0, 9, 0.4, {"floor": "#6E5442", "ceil": "#B9B4AC", "left": "#8E9A93",
                                     "right": "#84908A", "back": "#97A39C"})
    # window on back wall (cool daylight)
    win = cam.quad([(-1.2, 1.2, 9.39), (0.2, 1.2, 9.39), (0.2, 2.3, 9.39), (-1.2, 2.3, 9.39)])
    c.drawPath(win, paint("#BFD8EE"))
    c.drawPath(win, paint("#F2EFE8", stroke=10))
    # desk + lamp on the right
    c.drawPath(cam.quad([(1.4, 0.75, 6.0), (2.9, 0.75, 6.0), (2.9, 0.75, 7.2), (1.4, 0.75, 7.2)]), paint("#9C7552"))
    c.drawPath(cam.quad([(1.4, 0.0, 6.0), (2.9, 0.0, 6.0), (2.9, 0.75, 6.0), (1.4, 0.75, 6.0)]), paint("#7E5C40"))
    lx, ly, ls = cam.project(2.3, 1.05, 6.6)
    bx, by, _ = cam.project(2.3, 0.76, 6.6)
    c.drawLine(lx, ly, bx, by, paint("#2C2C2C", stroke=0.03 * ls))
    shade = skia.Path()
    shade.moveTo(lx - 0.16 * ls, ly)
    shade.lineTo(lx + 0.16 * ls, ly)
    shade.lineTo(lx + 0.09 * ls, ly - 0.2 * ls)
    shade.lineTo(lx - 0.09 * ls, ly - 0.2 * ls)
    shade.close()
    c.drawPath(shade, paint("#FFE2A8" if lamp > 0.1 else "#D9CBB0"))
    if lamp > 0:
        glow(c, lx, ly - 0.05 * ls, 3.2 * ls * lamp, "#FFB766", 0.55 * lamp)
        glow(c, lx, ly - 0.1 * ls, 0.35 * ls, "#FFF2D0", 0.5 * lamp)
    # mood: cool dim before, warm after
    c.drawRect(skia.Rect(0, 0, W, H), paint("#0A1830", alpha=0.28 * dim * (1 - 0.6 * lamp)))
    return lx, ly


def shot_room(c, t):
    lamp = lamp_level(t)
    cam = PerspCam(focal=950, cam_y=1.45, horizon=H * 0.40)
    lx, ly = draw_room(c, cam, lamp)
    fx, fy, s = cam.project(0.0, 0.0, 4.2)
    # contact shadow
    c.drawOval(skia.Rect(fx - 0.35 * s, fy - 0.06 * s, fx + 0.35 * s, fy + 0.06 * s), paint("#000000", alpha=0.25))
    look = {"rim": "#FFD9A0"} if lamp > 0.2 else {"rim": "#CFE0FF"}
    sway = 6 * smooth_noise(t, 3, 0.2)  # weight shift
    draw_puppet(c, fx + sway, fy, s / 900 * 1.45, pose_at(t), look)
    vignette(c, 0.5)


def shot_face(c, t):
    lamp = lamp_level(t)
    linear_grad(c, (0, 0, W, H), "#5E6D74", "#2E3438")
    if lamp > 0:
        glow(c, W * 1.05, H * 0.35, 1100 * lamp, "#FFB766", 0.5 * lamp)
    p = pose_at(t)
    look = {"rim": "#FFD9A0" if lamp > 0.2 else None}
    draw_puppet(c, W * 0.5, H * 1.75, 2.6, p, look)
    c.drawRect(skia.Rect(0, 0, W, H), paint("#0A1830", alpha=0.22 * (1 - 0.7 * lamp)))
    vignette(c, 0.55)


SHOTS = {"room": shot_room, "face": shot_face}


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


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-json")
    ap.add_argument("--still", nargs=2)
    a = ap.parse_args()
    if a.still:
        job, t = a.still[0], float(a.still[1])
        surf = skia.Surface(W, H)
        SHOTS[job](surf.getCanvas(), t)
        (HERE / "qc").mkdir(exist_ok=True)
        surf.makeImageSnapshot().save(str(HERE / "qc" / f"still_{job}_{t:.2f}.png"), skia.kPNG)
    else:
        todo = [(j, i) for j, fr in json.loads(a.frames_json).items() for i in fr]
        with Pool() as p:
            for k, _ in enumerate(p.imap_unordered(render, todo, chunksize=8)):
                if k % 50 == 0:
                    print(f"  2d {k}/{len(todo)}", end="\r")
        print(f"  2d rendered {len(todo)} frames")
