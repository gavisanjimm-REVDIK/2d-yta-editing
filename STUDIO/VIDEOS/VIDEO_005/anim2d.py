"""anim2d.py - VIDEO_005 "Protists Part 1" explainer. One job per narration line: s_L01 ... s_L54.

Each job draws plan.PLAN[line] with t = global time; callouts/bullets pop on the spoken word (`at`).
    python anim2d.py --frames-json '{...}'   (render_needed.py)
    python anim2d.py --stills                (one still per line -> qc/test_stills/)
"""
import argparse
import importlib.util
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
from kit import W, H, FPS, key, blink, clamp, smooth_noise, rgb, text, text_width, EASE  # noqa: E402
from toon import draw_character, prop_magnifier, prop_notebook  # noqa: E402
from lipsync import load as load_lip, viseme  # noqa: E402
import micro as M  # noqa: E402
from plan import PLAN, SC  # noqa: E402

_spec = importlib.util.spec_from_file_location("v001_gfx", HERE.parent / "VIDEO_001" / "gfx.py")
GFX = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GFX)

T = json.loads((HERE / "audio" / "timing.json").read_text())
LINES = {l["id"]: l for l in T["lines"]}
IDS = [l["id"] for l in T["lines"]]
LIP = load_lip("VIDEO_005")
INK = "#2A1A12"
SERIF, BOLD, UI = "Cinzel-VF.ttf", "Anton-Regular.ttf", "Oswald-VF.ttf"


# ================================================================ timing helpers
def seg_bounds(lid):
    i = IDS.index(lid)
    t0 = 0.0 if i == 0 else LINES[lid]["start"] - 0.15
    t1 = LINES[IDS[i + 1]]["start"] - 0.15 if i + 1 < len(IDS) else LINES[lid]["end"] + 4.0
    return t0, t1


def word_t(lid, keyw, default=None):
    """Start time of the first word in line `lid` that starts with `keyw` (case-insensitive)."""
    for wd in LINES[lid]["words"]:
        if wd["word"].strip(".,!?:;'\"()").lower().startswith(keyw.lower()):
            return wd["start"]
    return default if default is not None else LINES[lid]["start"] + 0.3


def pop(t, ta, dur=0.28):
    return clamp((t - ta) / dur)


# ================================================================ drawing helpers
def paint(color, alpha=1.0, stroke=None):
    p = skia.Paint(AntiAlias=True, Color=rgb(color))
    p.setAlphaf(clamp(alpha))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    return p


def vgrad(c, r, c0, c1):
    x, y, w, h = r
    sh = skia.GradientShader.MakeLinear([skia.Point(x, y), skia.Point(x, y + h)], [rgb(c0), rgb(c1)])
    c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), skia.Paint(Shader=sh))


def vignette(c, s=0.45):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.62,
                                        [skia.Color(10, 6, 4, 0), skia.Color(10, 6, 4, int(255 * s))], [0.55, 1.0])
    c.drawRect(skia.Rect(0, 0, W, H), skia.Paint(Shader=sh))


def desk_bg(c):
    vgrad(c, (0, 0, W, H), "#4A3424", "#2E2016")
    for k in range(0, W, 90):
        c.drawLine(k, 0, k + 60, H, paint("#22160E", 0.5, 4))


def pill(c, label, x, y, size=40, fg="#FFFFFF", bg="#2A1A12", alpha=1.0, scale=1.0):
    size *= scale
    tw = text_width(label, size, BOLD)
    pw, ph = tw + size * 0.9, size * 1.45
    x = clamp(x, 40 + pw / 2, W - 40 - pw / 2)
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - pw / 2, y - ph / 2, pw, ph), ph / 2, ph / 2), paint(bg, 0.92 * alpha))
    c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - pw / 2, y - ph / 2, pw, ph), ph / 2, ph / 2),
                paint("#FFFFFF", 0.8 * alpha, 3))
    text(c, label, x, y + size * 0.36, size, fg, face=BOLD, shadow=False, alpha=alpha, clamp_safe=False, max_w=W - 120)
    return pw, ph


def callout(c, label, anchor, t, ta, side=None, dy=0, bg="#C8382E"):
    """Pin dot at anchor + line + pill label; pops on word time ta."""
    u = pop(t, ta)
    if u <= 0:
        return
    ax, ay = anchor
    side = side or (1 if ax >= W / 2 else -1)
    lx = ax + side * 190
    ly = ay - 110 + dy
    e = EASE["out"](u)
    c.drawLine(ax, ay, ax + (lx - ax) * e, ay + (ly - ay) * e, paint(INK, 1, 7))
    c.drawLine(ax, ay, ax + (lx - ax) * e, ay + (ly - ay) * e, paint("#FFFFFF", 1, 3))
    c.drawCircle(ax, ay, 12, paint("#FFFFFF"))
    c.drawCircle(ax, ay, 12, paint(INK, 1, 4))
    pill(c, label, lx, ly, 46, bg=bg, alpha=u, scale=0.85 + 0.15 * EASE["back"](u))


def org(c, name, x, y, s, t, **kw):
    return M.ORGANISMS[name](c, x, y, s, t, **kw)


def stamp(c, label, t, ta, y=960, rot=-8):
    u = pop(t, ta, 0.18)
    if u <= 0:
        return
    k = 1.6 - 0.6 * EASE["out"](u)
    c.save()
    c.translate(W / 2, y)
    c.rotate(rot)
    c.scale(k, k)
    tw = min(text_width(label, 84, BOLD), W - 200)
    r = skia.Rect(-tw / 2 - 30, -70, tw / 2 + 30, 40)
    c.drawRRect(skia.RRect.MakeRectXY(r, 14, 14), paint("#FFF4E0", 0.85 * u))
    c.drawRRect(skia.RRect.MakeRectXY(r, 14, 14), paint("#C8382E", u, 9))
    text(c, label, 0, 4, 84, "#C8382E", face=BOLD, shadow=False, alpha=u, clamp_safe=False, max_w=W - 120)
    c.restore()


def parchment(c, x, y, w, h, al=1.0):
    GFX._parchment(c, x, y, w, h, al)


# ================================================================ 1. host (Marcus in his lab)
def lab_bg(c, board):
    vgrad(c, (0, 0, W, 1320), "#6A7A6A", "#56665A")
    for x in range(0, W, 160):
        c.drawLine(x, 0, x, 1320, paint("#4A5A4E", 0.6, 3))
    M.shape(c, M.rect(120, 240, 840, 520, 16), "#3A2418")
    M.shape(c, M.rect(150, 270, 780, 460, 8), "#2E4A3A")  # chalkboard
    text(c, board, 540, 470, 96, "#F4F1EA", face=BOLD, shadow=False, max_w=720)
    r = random.Random(3)
    for k in range(5):  # chalk doodles: little protists
        cx, cy = r.uniform(220, 860), r.uniform(560, 690)
        c.drawPath(M.oval(cx, cy, 30, 18), paint("#E8E4D8", 0.6, 3))
        c.drawLine(cx + 30, cy, cx + 70, cy - 14, paint("#E8E4D8", 0.6, 3))
    M.shape(c, M.poly([(0, 1320), (W, 1320), (W, H), (0, H)]), "#7A5A3A")
    for k in range(0, W + 300, 170):
        c.drawLine(k, 1320, k - 240, H, paint(INK, 0.35, 3))
    M.shape(c, M.rect(560, 1160, 520, 60, 8), "#8A6A4A")  # lab bench with microscope + flask
    M.shape(c, M.rect(600, 1220, 40, 420), "#6A4A2A")
    M.shape(c, M.rect(1000, 1220, 40, 420), "#6A4A2A")
    M.shape(c, M.rect(760, 1120, 160, 40, 8), "#3A3A44")
    M.shape(c, M.poly([(820, 1120), (860, 1120), (880, 940), (850, 930)]), "#4A4A56")
    M.shape(c, M.rect(830, 900, 70, 40, 8), "#2A2A30")
    M.shape(c, M.oval(880, 1100, 70, 14), "#C8DCEE")
    M.shape(c, M.poly([(640, 1160), (700, 1160), (690, 1080), (650, 1080)]), "#BCE0D8")
    M.shape(c, M.rect(655, 1040, 30, 40, 4), "#BCE0D8")


def shot_host(c, t, lid, p):
    lab_bg(c, p["board"])
    poses = {"magnify": dict(arm_r=(0.8, -0.2, "down"), prop_r=prop_magnifier, arm_l="hips"),
             "chin": dict(arm_r="chin", hand_r="fist", arm_l="hips"),
             "point": dict(arm_r=(1.0, -0.6, "down"), hand_r="point", arm_l="hips"),
             "notebook": dict(arm_l="front_high", prop_l=prop_notebook, arm_r="chin", hand_r="fist"),
             "salute": dict(arm_r=(0.38, -1.18, "down"), arm_l="hips")}
    pose = dict(poses[p["pose"]], expr=p["mood"], vis=viseme(t, LIP, "marcus"), blink=blink(t, 4),
                tilt=2 * smooth_noise(t, 1, 0.3), turn=-0.15, look=(-0.3, 0.0), bob=0.012 * math.sin(t * 2))
    c.drawOval(skia.Rect(160, 1700, 560, 1760), paint("#1A0E0A", 0.3))
    draw_character(c, "marcus_detective", 360, 1730, 1150, pose)
    vignette(c, 0.4)


# ================================================================ 2. microscope view
def scope_frame(c, t, draw_inside):
    vgrad(c, (0, 0, W, H), "#16222E", "#0A1016")
    cx, cy, r = 540, SC, 470
    clip = skia.Path()
    clip.addCircle(cx, cy, r)
    c.save()
    c.clipPath(clip, doAntiAlias=True)
    sh = skia.GradientShader.MakeRadial(skia.Point(cx - 80, cy - 100), r * 1.3, [rgb("#F4FBFC"), rgb("#BFDDE6")])
    c.drawRect(skia.Rect(cx - r, cy - r, cx + r, cy + r), skia.Paint(Shader=sh))
    rr = random.Random(7)
    for _ in range(30):  # drifting particles in the water
        px, py = rr.uniform(cx - r, cx + r), rr.uniform(cy - r, cy + r)
        c.drawCircle(px + 10 * math.sin(t * 0.7 + px), py + 8 * math.cos(t * 0.5 + py), rr.uniform(2, 6), paint("#8AB0BC", 0.5))
    anchors = draw_inside(c)
    c.restore()
    c.drawCircle(cx, cy, r + 14, paint("#2A2A30", 1, 30))
    c.drawCircle(cx, cy, r + 14, paint("#6A6A78", 1, 8))
    c.drawCircle(cx, cy, r, paint(INK, 1, 6))
    for k in range(0, 360, 10):  # scale ticks
        a = math.radians(k)
        L = 22 if k % 30 == 0 else 12
        c.drawLine(cx + math.cos(a) * (r + 34), cy + math.sin(a) * (r + 34), cx + math.cos(a) * (r + 34 + L),
                   cy + math.sin(a) * (r + 34 + L), paint("#8A8A98", 1, 3))
    return anchors


def shot_scope(c, t, lid, p):
    t0, t1 = seg_bounds(lid)
    u = clamp((t - t0) / max(t1 - t0, 0.1))

    def inside(c):
        c.save()
        k = 1.0 + 0.06 * u  # slow zoom, like focusing in
        c.translate(540, SC)
        c.scale(k, k)
        c.translate(-540, -SC)
        anchors = []
        if p.get("lamp"):
            M.radial(c, 900, 520, 380, "#FFF2A0", 0.8, plus=True)
            c.drawCircle(900, 520, 40, paint("#FFF4B0"))
        for name, x, y, s, kw in p["orgs"]:
            kw = dict(kw)
            if kw.pop("swim", False):
                x, y = x + 120 * u, y - 150 * u
            if kw.get("enter") is True:
                kw["enter"] = EASE["io"](clamp((t - word_t(lid, "apical")) / 1.6))
            a = org(c, name, x, y, s, t, **kw) or {}
            anchors.append({k_: ((v[0] - 540) * k + 540, (v[1] - SC) * k + SC) for k_, v in a.items()})
        c.restore()
        return anchors
    anchors = scope_frame(c, t, inside)
    for i, (label, akey, at) in enumerate(p.get("labels", [])):
        oi = 0
        for j, a in enumerate(anchors):
            if akey in a:
                oi = j
                if j == i or len(anchors) > 1 and j >= min(i, len(anchors) - 1):
                    break
        if len(anchors) > 1 and len(p["orgs"]) == len(p["labels"]):
            oi = i
        anc = anchors[oi].get(akey) or list(anchors[oi].values())[0]
        callout(c, label, anc, t, word_t(lid, at), dy=-60 * (i % 2))
    if p.get("q"):
        pill(c, p["q"], 540, 400, 52, bg="#2A1A12", alpha=pop(t, seg_bounds(lid)[0] + 0.1))


# ================================================================ 3. compare (two stacked panels)
def shot_compare(c, t, lid, p):
    desk_bg(c)
    for i, (name, kw, cap) in enumerate(p["panels"]):
        y0 = 320 + i * 640
        ta = seg_bounds(lid)[0] + 0.1 + 0.5 * i
        u = EASE["out"](pop(t, ta, 0.4))
        if u <= 0:
            continue
        c.save()
        c.translate(0, 40 * (1 - u))
        dark = p.get("dark2") and i == 1
        r = skia.Rect.MakeXYWH(70, y0, 940, 520)
        c.drawRRect(skia.RRect.MakeRectXY(r, 30, 30), paint("#1E2A36" if dark else "#EAF4F6", u))
        c.drawRRect(skia.RRect.MakeRectXY(r, 30, 30), paint(INK, u, 6))
        c.save()
        c.clipRect(r)
        kw = dict(kw)
        s = kw.pop("s", 1.0)
        org(c, name, 540, y0 + 215, s, t, **kw)
        c.restore()
        text(c, cap, 540, y0 + 480, 52, "#FFFFFF" if dark else INK, face=BOLD, shadow=False, alpha=u, max_w=880)
        c.restore()
    if p.get("stamp"):
        lab, at = p["stamp"]
        stamp(c, lab, t, word_t(lid, at), y=935, rot=-4)


# ================================================================ 4. parchment card with bullets
def shot_card(c, t, lid, p):
    desk_bg(c)
    t0, _ = seg_bounds(lid)
    u = EASE["out"](pop(t, t0, 0.35))
    x, y, w_, h_ = 70, 330, 940, 1160
    c.save()
    c.translate(0, 60 * (1 - u))
    parchment(c, x, y, w_, h_, u)
    text(c, p["title"], W / 2, y + 140, 70, "#8A1F1A", face=SERIF, shadow=False, alpha=u, max_w=w_ - 100)
    c.drawLine(x + 80, y + 180, x + w_ - 80, y + 180, paint(INK, u, 4))
    top = y + 270
    if p.get("icon"):
        name, s = p["icon"]
        c.save()
        clip = skia.Rect.MakeXYWH(x + 60, y + 200, w_ - 120, 340)
        c.clipRect(clip)
        org(c, name, W / 2, y + 380, s * 1.35, t)
        c.restore()
        top = y + 640
    for i, (b, at) in enumerate(p["bullets"]):
        ta = word_t(lid, at)
        v = pop(t, ta, 0.3)
        if v <= 0:
            continue
        by = top + i * min(165, (y + h_ - 90 - top) / max(len(p["bullets"]) - 1, 1))
        c.drawCircle(x + 100, by - 22, 16 * EASE["back"](v), paint("#C8382E"))
        text(c, b, x + 140, by, 62, INK, face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=w_ - 200)
        if p.get("strike") and i == 0 and len(p["bullets"]) > 1:
            s2 = pop(t, word_t(lid, p["bullets"][1][1]), 0.4)
            if s2 > 0:
                tw = min(text_width(b, 62, BOLD), w_ - 200)
                c.drawLine(x + 130, by - 22, x + 130 + (tw + 20) * s2, by - 22, paint("#C8382E", 1, 9))
    c.restore()


# ================================================================ 5. diagrams
def shot_eukarya(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    ue = pop(t, word_t(lid, "eukaryotes"), 0.5)
    text(c, "DOMAIN EUKARYA", 540, 430, 66, "#8A1F1A", face=SERIF, shadow=False, alpha=max(ue, 0.25))
    c.drawCircle(540, 950, 430 * (0.85 + 0.15 * EASE["out"](ue)), paint("#E8D6AE", ue))
    c.drawCircle(540, 950, 430 * (0.85 + 0.15 * EASE["out"](ue)), paint(INK, ue, 6))
    groups = [("PLANTS", "plants", 330, 720, "#5E8A3C"), ("ANIMALS", "animals", 750, 720, "#C8784A"),
              ("FUNGI", "fungi", 540, 1210, "#A87AC8")]
    for name, at, gx, gy, col in groups:
        v = pop(t, word_t(lid, at), 0.3)
        if v <= 0:
            continue
        rr = 120 * EASE["back"](v)
        c.drawCircle(gx, gy, rr, paint(col))
        c.drawCircle(gx, gy, rr, paint(INK, 1, 5))
        text(c, name, gx, gy + 14, 40, "#FFFFFF", face=BOLD, shadow=False, alpha=v)
        pill(c, "NOT", gx, gy - rr - 10, 30, bg="#C8382E", alpha=v)
    vp = pop(t, word_t(lid, "fungi") + 0.4, 0.6)
    if vp > 0:  # everything left over: protists
        r = random.Random(5)
        for k in range(14):
            a, d = r.uniform(0, math.tau), r.uniform(80, 330)
            px, py = 540 + math.cos(a) * d, 950 + math.sin(a) * d
            if min(math.hypot(px - gx, py - gy) for _, _, gx, gy, _ in groups) < 160:
                continue
            org(c, r.choice(["giardia", "euglena", "ciliate", "diatom"]), px, py, 0.16 * vp, t + k)
        pill(c, "PROTISTS = EVERYTHING ELSE", 540, 990, 44, bg="#2A1A12", alpha=vp)


def shot_groups(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "THE OLD WAY: BY LOOKS", 540, 430, 58, "#8A1F1A", face=SERIF, shadow=False)
    cols = [("ANIMAL-LIKE", "protozoa", "rhizarian", "animal"), ("PLANT-LIKE", "protophyta · algae", "golden_alga", "plant"),
            ("FUNGUS-LIKE", "slime & water molds", "slime", "fungus")]
    for i, (head, sub, icon, at) in enumerate(cols):
        y0 = 520 + i * 330
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(120, y0, 840, 290), 24, 24), paint("#F4E8C8"))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(120, y0, 840, 290), 24, 24), paint(INK, 1, 4))
        v = pop(t, word_t(lid, at), 0.3) if p["stage"] == 1 else 0.0
        if v <= 0:
            text(c, "?", 300, y0 + 190, 140, "#B8A07A", face=BOLD, shadow=False)
            continue
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(130, y0 + 10, 330, 270))
        if icon == "slime":
            M.shape(c, M.blob(300, y0 + 150, 120 * v, 70 * v, t, 3, 0.12, 12), "#F4D24A", shade="#D4B22A", sdx=10)
            for k in range(5):
                c.drawCircle(220 + k * 40, y0 + 90 + 10 * math.sin(t * 2 + k), 10 * v, paint("#D4B22A"))
        else:
            org(c, icon, 300, y0 + 150, 0.55 * v, t)
        c.restore()
        text(c, head, 470, y0 + 120, 56, INK, face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=470)
        text(c, sub, 470, y0 + 200, 42, "#6A4A2A", face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=470)


TREE = [("Excavata", "excavata", "excavate", "#A8D8C8"), ("SAR", "sar", "dinoflagellate", "#D88A5A"),
        ("Archaeplastida", "archaeplastida", "golden_alga", "#8AC86A"), ("Unikonta", "unikonta", "rhizarian", "#E8C8A0")]


def shot_tree(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "PROTISTS: 4 SUPERGROUPS", 540, 430, 54, "#8A1F1A", face=SERIF, shadow=False)
    M.shape(c, M.rect(400, 500, 280, 100, 20), "#F4E8C8")
    text(c, "PROTISTS", 540, 568, 50, INK, face=BOLD, shadow=False)
    for i, (name, at, icon, col) in enumerate(TREE):
        if p["reveal"] is None:
            v = 1.0
        else:
            v = pop(t, word_t(lid, at[:6]), 0.35)
        if v <= 0:
            continue
        hi = not p["hi"] or name in p["hi"]
        al = v * (1.0 if hi else 0.3)
        x = 190 + i * 233
        y = 780
        c.drawLine(540, 600, x, y - 40, paint(INK, al, 6))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 105, y - 40, 210, 520), 22, 22), paint(col, al))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 105, y - 40, 210, 520), 22, 22), paint(INK, al, 5))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x - 100, y - 35, 200, 300))
        org(c, icon, x, y + 110, 0.42, t)
        c.restore()
        c.save()
        c.translate(x, y + 360)
        c.rotate(-90)
        text(c, name.upper(), 0, 16, 50, INK, face=BOLD, shadow=False, alpha=al, clamp_safe=False, max_w=300)
        c.restore()
        if p["hi"] and name in p["hi"]:
            pill(c, "THIS LESSON", x, y + 540, 30, bg="#C8382E", alpha=v * pop(t, seg_bounds(lid)[0] + 0.6))


def shot_title(c, t, lid, p):
    t0, _ = seg_bounds(lid)
    vgrad(c, (0, 0, W, H), "#1E2A36", "#0E141A")
    u = EASE["out"](pop(t, t0, 0.5))
    M.radial(c, 540, 1150, 700, "#4A7A8A", 0.35 * u, plus=True)
    org(c, p["org"], 540, 1180, 1.6 * (0.8 + 0.2 * u), t)
    text(c, p["n"], 540, 470, 60, "#FFD27A", face=BOLD, shadow=False, alpha=u)
    text(c, p["name"], 540, 640, 150 * (0.9 + 0.1 * u), "#FFFFFF", face=BOLD, alpha=u, outline=10, max_w=940)
    if p.get("sar"):  # S / A / R spelled out as each group is named
        for i, (letter, word) in enumerate((("S", "stramenopiles"), ("A", "alveolates"), ("R", "rhizarians"))):
            v = pop(t, word_t(lid, word), 0.3)
            if v > 0:
                pill(c, f"{letter} = {word.upper()}", 540, 790 + i * 95, 44, bg="#C8382E", alpha=v)


def shot_sar3(c, t, lid, p):
    desk_bg(c)
    items = [("S", "STRAMENOPILES", "hairy + smooth flagella", "hairy_flagellate", "hairy", 0.55),
             ("A", "ALVEOLATES", "sacs (alveoli) under membrane", "alveolate_cell", "alveolates", 0.75),
             ("R", "RHIZARIANS", "threadlike pseudopodia", "rhizarian", "rhizarians", 0.6)]
    for i, (letter, name, sub, icon, at, s) in enumerate(items):
        v = EASE["out"](pop(t, word_t(lid, at), 0.35))
        y0 = 300 + i * 420
        if v <= 0:
            continue
        r = skia.Rect.MakeXYWH(60, y0, 960, 380)
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint("#EAF4F6", v))
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint(INK, v, 6))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(70, y0 + 10, 380, 360))
        org(c, icon, 260, y0 + 200, s, t)
        c.restore()
        text(c, letter, 960, y0 + 120, 110, "#C8382E", face=BOLD, align="right", shadow=False, alpha=v, clamp_safe=False)
        text(c, name, 470, y0 + 200, 58, INK, face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=520)
        text(c, sub, 470, y0 + 280, 40, "#4A5A6A", face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=520)


def shot_lifecycle(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "T. BRUCEI LIFE CYCLE", 540, 420, 56, "#8A1F1A", face=SERIF, shadow=False)
    nodes = [("INFECTED HUMAN", (300, 760), "bites"), ("FLY GUT", (780, 760), "gut"),
             ("SALIVARY GLANDS", (780, 1250), "salivary"), ("NEW HOST", (300, 1250), "next")]
    for i, (lab, (x, y), at) in enumerate(nodes):
        v = pop(t, word_t(lid, at), 0.35)
        if v <= 0:
            continue
        c.drawCircle(x, y, 170, paint("#F4E8C8", v))
        c.drawCircle(x, y, 170, paint(INK, v, 5))
        c.save()
        c.clipPath(M.oval(x, y, 165, 165), doAntiAlias=True)
        if i in (0, 3):
            draw_character(c, "daniel" if i == 0 else "sophie", x, y + 260, 520,
                           {"expr": "sad" if i == 0 else "worried", "blink": 0.5 if i == 0 else 0})
        else:
            org(c, "insect", x - 30, y, 0.9, t, kind="tsetse")
            M.radial(c, x - 30 if i == 1 else x + 60, y - 10, 70, "#E8509A", 0.8, plus=True)
        c.restore()
        pill(c, lab, x, y + 215, 42, bg="#2A1A12", alpha=v)
        if i > 0:  # arrow from previous node
            px, py = nodes[i - 1][1]
            e = EASE["out"](v)
            ex, ey = px + (x - px) * e, py + (y - py) * e
            ang = math.atan2(y - py, x - px)
            sx, sy = px + math.cos(ang) * 180, py + math.sin(ang) * 180
            ex, ey = ex - math.cos(ang) * 180 * e, ey - math.sin(ang) * 180 * e
            c.drawLine(sx, sy, ex, ey, paint("#C8382E", 1, 12))
    v = pop(t, word_t(lid, "next") + 0.6, 0.5)
    if v > 0:  # loop back: the new host can be bitten again
        c.drawLine(300, 1080, 300, 940, paint("#C8382E", v, 12))


def shot_tide(c, t, lid, p):
    t0, t1 = seg_bounds(lid)
    red = EASE["io"](clamp((t - word_t(lid, "red") + 0.2) / 1.8))
    vgrad(c, (0, 0, W, 760), "#9ED0EE", "#E8F4F8")
    c.drawCircle(860, 260, 90, paint("#FFE8A0"))
    M.tide(c, 0, 760, W, 900, t, red)
    M.shape(c, M.smooth_path([(-40, 1560), (400, 1500), (W + 40, 1580), (W + 40, H + 40), (-40, H + 40)]), "#E8D0A0")
    c.save()
    c.clipPath(M.oval(820, 1140, 190, 190), doAntiAlias=True)
    c.drawRect(skia.Rect(600, 920, 1040, 1360), paint("#EAF4F6"))
    org(c, "dinoflagellate", 820, 1140, 0.8, t)
    c.restore()
    c.drawCircle(820, 1140, 190, paint(INK, 1, 8))
    pill(c, "HARMFUL ALGAL BLOOM", 540, 520, 50, bg="#C8382E", alpha=pop(t, word_t(lid, "harmful")))


def shot_trophic(c, t, lid, p):
    desk_bg(c)
    tiles = [("PARASITIC", "parasitic", "sporozoite", {"host": False}, 0.5), ("HETEROTROPHIC", "heterotrophic", "ciliate", {}, 0.5),
             ("AUTOTROPHIC", "autotrophic", "dinoflagellate", {}, 0.6), ("MIXOTROPHIC", "mixotrophic", "euglena", {}, 0.45)]
    for i, (lab, at, icon, kw, s) in enumerate(tiles):
        v = EASE["out"](pop(t, word_t(lid, at), 0.35))
        if v <= 0:
            continue
        x0, y0 = 70 + (i % 2) * 480, 330 + (i // 2) * 600
        r = skia.Rect.MakeXYWH(x0, y0, 460, 560)
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint("#EAF4F6", v))
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint(INK, v, 6))
        c.save()
        c.clipRect(r)
        if icon == "dinoflagellate":
            M.radial(c, x0 + 380, y0 + 80, 160, "#FFE070", 0.8, plus=True)
        org(c, icon, x0 + 230, y0 + 250, s, t, **kw)
        c.restore()
        text(c, lab, x0 + 230, y0 + 520, 44, INK, face=BOLD, shadow=False, alpha=v, clamp_safe=False, max_w=420)
    v = pop(t, word_t(lid, "stolen"), 0.3)
    if v > 0:
        pill(c, "kleptoplasty: stolen chloroplasts", 540, 1560, 38, bg="#3E7A3A", alpha=v)


def shot_endosym(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "PHOTOSYNTHESIS BY ENGULFING", 540, 420, 48, "#8A1F1A", face=SERIF, shadow=False, max_w=880)
    rows = [("chlorarachniophytes", "green alga", "#6AB84A", "CHLORARACHNIOPHYTE"), ("paulinella", "cyanobacterium", "#3AA8A0", "PAULINELLA")]
    for i, (at, prey, col, name) in enumerate(rows):
        y = 760 + i * 480
        ta = word_t(lid, at)
        v = pop(t, ta - 0.3, 0.3)
        if v <= 0:
            continue
        e = EASE["io"](clamp((t - ta) / 1.4))
        M.shape(c, M.blob(330, y, 170, 150, t, i, 0.06), "#E8C8A0", shade="#C8A880", sdx=10)
        px = 800 - 470 * e
        M.shape(c, M.oval(px, y, 60, 40), col, ow=4)
        text(c, prey, 800, y + 110, 36, "#3A2A1A", face=BOLD, shadow=False, alpha=v * (1 - e))
        if e > 0.95:
            M.shape(c, M.oval(330, y + 10, 60, 40), col, ow=4)
        pill(c, name, 540, y + 220, 38, bg="#2A1A12", alpha=pop(t, ta + 1.2))
        c.drawLine(560, y, 720 - 300 * e, y, paint("#C8382E", v * (1 - e), 8))


def shot_pie(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "PROTISTS IN SOME SOILS", 540, 420, 52, "#8A1F1A", face=SERIF, shadow=False)
    v = pop(t, word_t(lid, "cercozoans"), 0.4)
    cx, cy, r = 540, 900, 300
    c.drawCircle(cx, cy, r, paint("#E8D6AE"))
    c.drawCircle(cx, cy, r, paint(INK, 1, 6))
    if v > 0:  # 30-60% band: solid 30%, hatched up to 60%
        sweep_lo, sweep_hi = 360 * 0.30 * EASE["out"](v), 360 * 0.60 * EASE["out"](v)
        c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), -90, sweep_hi, True, paint("#E8A070"))
        c.drawArc(skia.Rect(cx - r, cy - r, cx + r, cy + r), -90, sweep_lo, True, paint("#C8582E"))
        c.drawCircle(cx, cy, r, paint(INK, 1, 6))
    vt = pop(t, word_t(lid, "thirty"), 0.3)
    text(c, "30 – 60%", cx, cy + 30, 110, "#FFFFFF", face=BOLD, outline=10, alpha=vt)
    text(c, "are CERCOZOANS", cx, 1320, 54, INK, face=BOLD, shadow=False, alpha=v)
    vs = pop(t, word_t(lid, "freshwater"), 0.3)
    pill(c, "freshwater + soil", 540, 1430, 38, bg="#3E7A3A", alpha=vs)


def shot_recap(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "CASE FILE: PART 1", 540, 420, 56, "#8A1F1A", face=SERIF, shadow=False)
    cols = [("EXCAVATA", "excavata", [("diplomonads", "diplomonads", "giardia"), ("parabasalids", "parabasalids", "trichomonas"),
                                       ("euglenozoans", "euglenozoans", "euglena")]),
            ("SAR CLADE", "sar", [("stramenopiles", "stramenopiles", "hairy_flagellate"), ("alveolates", "alveolates", "alveolate_cell"),
                                  ("rhizarians", "rhizarians", "rhizarian")])]
    for ci, (head, hat, items) in enumerate(cols):
        x = 300 + ci * 480
        hv = pop(t, word_t(lid, hat), 0.3)
        text(c, head, x, 540, 52, "#C8382E", face=BOLD, shadow=False, alpha=hv)
        for i, (name, at, icon) in enumerate(items):
            v = pop(t, word_t(lid, at), 0.3)
            if v <= 0:
                continue
            y = 640 + i * 290
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(x - 200, y, 400, 220))
            org(c, icon, x, y + 110, 0.33, t)
            c.restore()
            text(c, name, x, y + 260, 42, INK, face=BOLD, shadow=False, alpha=v, clamp_safe=False, max_w=420)


def shot_montage(c, t, lid, p):
    desk_bg(c)
    tiles = [("GIARDIASIS", "giardiasis", "giardia", {}, 0.5), ("MALARIA", "malaria", "insect", {"kind": "mosquito"}, 0.9),
             ("RED TIDES", "red", "tide", {}, 0), ("HEALTHY SOIL", "soil", "foram", {}, 0.45)]
    for i, (lab, at, icon, kw, s) in enumerate(tiles):
        v = EASE["out"](pop(t, word_t(lid, at), 0.35))
        if v <= 0:
            continue
        x0, y0 = 70 + (i % 2) * 480, 330 + (i // 2) * 600
        r = skia.Rect.MakeXYWH(x0, y0, 460, 560)
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint("#EAF4F6", v))
        c.save()
        c.clipRect(r)
        if icon == "tide":
            M.tide(c, x0, y0, 460, 560, t, 0.9)
        else:
            org(c, icon, x0 + 230, y0 + 250, s, t, **kw)
        c.restore()
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint(INK, v, 6))
        pill(c, lab, x0 + 230, y0 + 500, 40, bg="#2A1A12", alpha=v)


SHOT_FNS = {k[5:]: v for k, v in globals().items() if k.startswith("shot_")}


def draw_job(c, job, t):
    lid = job[2:]
    typ, params = PLAN[lid]
    SHOT_FNS[typ](c, t, lid, params)


def render(job_frame):
    job, i = job_frame
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    draw_job(c, job, i / FPS)
    out = HERE / "frames" / job / f"f_{i:05d}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    surf.makeImageSnapshot().save(str(out), skia.kPNG)
    return out


def still(job, t, out):
    surf = skia.Surface(W, H)
    draw_job(surf.getCanvas(), job, t)
    out.parent.mkdir(parents=True, exist_ok=True)
    surf.makeImageSnapshot().save(str(out), skia.kPNG)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-json")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    if a.stills:
        for lid in (a.only or IDS):
            t0, t1 = seg_bounds(lid)
            still("s_" + lid, t1 - 0.2, HERE / "qc" / "test_stills" / f"{lid}.png")
    else:
        todo = [(j, i) for j, fr in json.loads(a.frames_json).items() for i in fr]
        with Pool() as p:
            for k, _ in enumerate(p.imap_unordered(render, todo, chunksize=6)):
                if k % 500 == 0:
                    print(f"  2d {k}/{len(todo)}", flush=True)
        print(f"  2d rendered {len(todo)} frames")
