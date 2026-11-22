"""anim2d.py - VIDEO_006 "Protists Part 2" explainer. One job per narration line: s_L01 ... s_L50.

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
import micro6 as M  # noqa: E402
from plan import PLAN, SC  # noqa: E402

_spec = importlib.util.spec_from_file_location("v001_gfx", HERE.parent / "VIDEO_001" / "gfx.py")
GFX = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GFX)

T = json.loads((HERE / "audio" / "timing.json").read_text())
LINES = {l["id"]: l for l in T["lines"]}
IDS = [l["id"] for l in T["lines"]]
LIP = load_lip("VIDEO_006")
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
        if p.get("bubbles"):  # oxygen bubbles rising from the algae
            rb = random.Random(4)
            for kb in range(26):
                bx = rb.uniform(160, 920)
                ph = (t * rb.uniform(0.08, 0.16) + rb.random()) % 1
                c.drawCircle(bx + 8 * math.sin(t * 2 + kb), SC + 460 - ph * 920, rb.uniform(6, 14), paint("#FFFFFF", 0.75, 3))
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
    for i, lab in enumerate(p.get("labels", [])):
        label, akey, at = lab[:3]
        opt = lab[3] if len(lab) > 3 else {}
        oi = 0
        for j, a in enumerate(anchors):
            if akey in a:
                oi = j
                if j == i or len(anchors) > 1 and j >= min(i, len(anchors) - 1):
                    break
        if len(anchors) > 1 and len(p["orgs"]) == len(p["labels"]):
            oi = i
        anc = anchors[oi].get(akey) or list(anchors[oi].values())[0]
        callout(c, label, anc, t, word_t(lid, at), side=opt.get("side"), dy=opt.get("dy", -60 * (i % 2)))
    if p.get("q"):
        pill(c, p["q"], 540, 400, 52, bg="#2A1A12", alpha=pop(t, seg_bounds(lid)[0] + 0.1))



# ================================================================ 3. compare / steps (two stacked panels)
def ghost(c, r, t, rad=28):
    """Faint placeholder slot so a shot never starts as an empty desk; it breathes slightly."""
    a = 0.22 + 0.06 * math.sin(t * 3)
    c.drawRRect(skia.RRect.MakeRectXY(r, rad, rad), paint("#F4E8C8", a * 0.5))
    c.drawRRect(skia.RRect.MakeRectXY(r, rad, rad), paint("#F4E8C8", a, 4))
    text(c, "?", r.centerX(), r.centerY() + 40, 120, "#F4E8C8", face=BOLD, shadow=False, alpha=a, clamp_safe=False)


def shot_compare(c, t, lid, p):
    desk_bg(c)
    for i, panel in enumerate(p["panels"]):
        name, kw, cap = panel[:3]
        y0 = 320 + i * 640
        ta = word_t(lid, panel[3]) - 0.2 if len(panel) > 3 else seg_bounds(lid)[0] + 0.1 + 0.5 * i
        u = EASE["out"](pop(t, ta, 0.4))
        if u <= 0:
            ghost(c, skia.Rect.MakeXYWH(70, y0, 940, 520), t, 30)
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
        if i == 1 and len(panel) > 3:  # step arrow
            c.drawLine(540, 850, 540, 950 * u + 850 * (1 - u), paint("#C8382E", u, 14))
    if p.get("stamp"):
        lab, at = p["stamp"]
        stamp(c, lab, t, word_t(lid, at), y=935, rot=-4)


shot_steps = shot_compare


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
    c.restore()


# ================================================================ 5. diagrams
TREE = [("Excavata", "excavata", "excavate", "#A8D8C8", 0.42), ("SAR", "sar", "dinoflagellate", "#D88A5A", 0.42),
        ("Archaeplastida", "archaeplastida", "chlamydomonas", "#8AC86A", 0.5), ("Unikonta", "unikonta", "amoeba", "#E8C8A0", 0.45)]


def shot_tree(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1240, 1)
    text(c, "PROTISTS: 4 SUPERGROUPS", 540, 430, 54, "#8A1F1A", face=SERIF, shadow=False)
    M.shape(c, M.rect(400, 500, 280, 100, 20), "#F4E8C8")
    text(c, "PROTISTS", 540, 568, 50, INK, face=BOLD, shadow=False)
    for i, (name, at, icon, col, s) in enumerate(TREE):
        v = 1.0 if p["reveal"] is None else pop(t, word_t(lid, at[:6]), 0.35)
        if v <= 0:
            continue
        hi = not p["hi"] or name in p["hi"]
        al = v * (1.0 if hi else 0.3)
        x, y = 190 + i * 233, 780
        c.drawLine(540, 600, x, y - 40, paint(INK, al, 6))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 105, y - 40, 210, 520), 22, 22), paint(col, al))
        c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 105, y - 40, 210, 520), 22, 22), paint(INK, al, 5))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(x - 100, y - 35, 200, 300))
        org(c, icon, x, y + 110, s, t)
        c.restore()
        if not hi:  # dim the groups already covered
            c.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 105, y - 40, 210, 520), 22, 22), paint("#F4E8C8", 0.55))
            pill(c, "PART 1", x, y + 540, 30, bg="#6A5A4A", alpha=v)
        c.save()
        c.translate(x, y + 360)
        c.rotate(-90)
        text(c, name.upper(), 0, 16, 50, INK, face=BOLD, shadow=False, alpha=al, clamp_safe=False, max_w=300)
        c.restore()
        if p["hi"] and name in p["hi"]:
            pill(c, p.get("tag", "THIS LESSON"), x, y + 540, 30, bg="#C8382E", alpha=v * pop(t, word_t(lid, name[:6])))


def shot_title(c, t, lid, p):
    t0, _ = seg_bounds(lid)
    vgrad(c, (0, 0, W, H), "#1E2A36", "#0E141A")
    u = EASE["out"](pop(t, t0, 0.5))
    M.radial(c, 540, 1150, 700, "#4A7A8A", 0.35 * u, plus=True)
    org(c, p["org"], 540, 1180, 1.6 * (0.8 + 0.2 * u), t)
    text(c, p["n"], 540, 470, 60, "#FFD27A", face=BOLD, shadow=False, alpha=u, max_w=940)
    text(c, p["name"], 540, 640, 150 * (0.9 + 0.1 * u), "#FFFFFF", face=BOLD, alpha=u, outline=10, max_w=940)
    if p.get("sub"):
        pill(c, p["sub"], 540, 790, 46, bg="#3E7A3A", alpha=pop(t, t0 + 0.8))


def shot_rows(c, t, lid, p):
    desk_bg(c)
    for i, (letter, name, sub, icon, at, s, kw) in enumerate(p["items"]):
        v = EASE["out"](pop(t, word_t(lid, at), 0.35))
        y0 = 300 + i * 420
        if v <= 0:
            ghost(c, skia.Rect.MakeXYWH(60, y0, 960, 380), t)
            continue
        r = skia.Rect.MakeXYWH(60, y0, 960, 380)
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint("#EAF4F6", v))
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint(INK, v, 6))
        c.save()
        c.clipRect(skia.Rect.MakeXYWH(70, y0 + 10, 380, 360))
        org(c, icon, 260, y0 + 200, s, t, **kw)
        c.restore()
        text(c, letter, 960, y0 + 120, 110, "#C8382E", face=BOLD, align="right", shadow=False, alpha=v, clamp_safe=False)
        text(c, name, 470, y0 + 200, 58, INK, face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=520)
        text(c, sub, 470, y0 + 280, 40, "#4A5A6A", face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=520)


def shot_tiles(c, t, lid, p):
    """Grid of organism tiles; each pops when its word is said. Short last row is centred."""
    desk_bg(c)
    items, cols = p["items"], p.get("cols", 2)
    rows = -(-len(items) // cols)
    gap, top, bot = 24, 300, 1560
    tw = (940 - (cols - 1) * gap) / cols
    th = (bot - top - (rows - 1) * gap) / rows
    for i, (lab, at, icon, kw, s) in enumerate(items):
        v = EASE["out"](pop(t, word_t(lid, at) - 0.1, 0.35))
        row, col = divmod(i, cols)
        in_row = min(cols, len(items) - row * cols)
        x0 = 70 + (940 - (in_row * tw + (in_row - 1) * gap)) / 2 + col * (tw + gap)
        y0 = top + row * (th + gap)
        if v <= 0:
            ghost(c, skia.Rect.MakeXYWH(x0, y0, tw, th), t)
            continue
        r = skia.Rect.MakeXYWH(x0, y0 + 30 * (1 - v), tw, th)
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint("#EAF4F6", v))
        c.save()
        c.clipRect(r)
        org(c, icon, x0 + tw / 2, y0 + th * 0.44, s, t, **kw)
        c.restore()
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint(INK, v, 6))
        pill(c, lab, x0 + tw / 2, y0 + th - 50, 38, bg="#2A1A12", alpha=v)


def shot_endo(c, t, lid, p):
    """Endosymbiosis: a heterotroph engulfs a cyanobacterium, which stays and becomes the chloroplast."""
    desk_bg(c)
    parchment(c, 60, 300, 960, 1260, 1)
    text(c, "ONE EVENT, ~1 BILLION YEARS AGO", 540, 420, 46, "#8A1F1A", face=SERIF, shadow=False, max_w=880)
    te, tc = word_t(lid, "engulfed"), word_t(lid, "chloroplast")
    e = EASE["io"](clamp((t - te) / 1.8))
    green = EASE["io"](clamp((t - tc) / 1.0))
    cx, cy = 500, 1000
    wrap = 0.25 * math.sin(e * math.pi)  # membrane reaches out while engulfing
    M.shape(c, M.blob(cx + 60 * wrap, cy, 300 + 60 * wrap, 260, t, 2, 0.05), "#E8C8A0", shade="#C8A880", sdx=14)
    M.shape(c, M.oval(cx - 110, cy - 40, 70, 64), "#8A6AB8", ow=4)
    bx, by = 860 - 260 * e, 640 + 420 * e
    c.save()
    c.translate(bx, by)
    c.rotate(-30 + 30 * e)
    if e >= 1:  # extra membrane around the guest
        c.drawPath(M.oval(0, 0, 110, 56), paint(INK, 1, 4))
    M.cyanobacterium(c, 0, 0, 1.15, t)
    if green > 0:
        M.shape(c, M.smooth_path([(-80, -32), (80, -32), (94, 0), (80, 32), (-80, 32), (-94, 0)]), "#4AA83A")
        c.drawPath(M.smooth_path([(-80, -32), (80, -32), (94, 0), (80, 32), (-80, 32), (-94, 0)]), paint("#2E7A24", 1, 4))
        for k in range(4):
            c.drawLine(-60, -12 + k * 8, 60, -12 + k * 8, paint("#DCF0C8", green, 3))
    c.restore()
    pill(c, "HETEROTROPH (eukaryote)", 420, 680, 40, bg="#2A1A12", alpha=pop(t, word_t(lid, "heterotrophic")))
    pill(c, "cyanobacterium-like", 760, 540, 40, bg="#2E8A7A", alpha=pop(t, word_t(lid, "cyanobacteria")) * (1 - e))
    pill(c, "NOT digested...", 330, 1330, 42, bg="#6A5A4A", alpha=pop(t, word_t(lid, "digested")))
    pill(c, "...it STAYED", 750, 1330, 42, bg="#2A1A12", alpha=pop(t, word_t(lid, "stayed")))
    pill(c, "→ CHLOROPLAST", 760, 1220, 44, bg="#3E7A3A", alpha=pop(t, tc))
    stamp(c, "ENDOSYMBIOSIS", t, word_t(lid, "endosymbiosis"), y=1490, rot=-4)


def shot_depth(c, t, lid, p):
    """Red algae get darker the deeper they live (phycoerythrin)."""
    vgrad(c, (0, 0, W, H), "#7AD0E8", "#040A18")
    for k in range(6):  # sun rays fading with depth
        x0 = 100 + k * 180 + 30 * math.sin(t * 0.4 + k)
        q = skia.Path()
        q.moveTo(x0, 0)
        q.lineTo(x0 + 60, 0)
        q.lineTo(x0 + 160, 1100)
        q.lineTo(x0 + 120, 1100)
        q.close()
        sh = skia.GradientShader.MakeLinear([skia.Point(0, 0), skia.Point(0, 1100)], [skia.Color(255, 255, 230, 90), skia.Color(255, 255, 230, 0)])
        c.drawPath(q, skia.Paint(AntiAlias=True, Shader=sh))
    rows = [(230, 720, 0.0, "SHALLOW", None), (540, 1020, 0.5, "DEEPER = DARKER", "deeper"), (850, 1390, 0.93, "DEEP: almost black", "black")]
    for x, y, d, lab, at in rows:
        v = 1.0 if at is None else pop(t, word_t(lid, at) - 0.2, 0.5)
        if v <= 0:
            continue
        c.save()
        c.translate(x, y)
        c.scale(v, v)
        c.translate(-x, -y)
        M.red_alga(c, x, y - 130, 0.8, t, depth=d)
        c.restore()
        pill(c, lab, x, y + 110, 36, bg="#2A1A12", alpha=v)
    pill(c, "PHYCOERYTHRIN = red pigment", 540, 400, 46, bg="#C8382E", alpha=pop(t, word_t(lid, "phycoerythrin")))


def wrap_lines(s, size, face, max_w):
    out, cur = [], ""
    for w_ in s.split():
        nxt = (cur + " " + w_).strip()
        if cur and text_width(nxt, size, face) > max_w:
            out.append(cur)
            cur = w_
        else:
            cur = nxt
    return out + ([cur] if cur else [])


def shot_question(c, t, lid, p):
    t0, t1 = seg_bounds(lid)
    vgrad(c, (0, 0, W, H), "#24384A", "#101A24")
    u = EASE["back"](pop(t, t0, 0.4))
    c.save()
    c.translate(540, 410)
    c.scale(0.7 + 0.3 * u, 0.7 + 0.3 * u)
    text(c, "THINK IT OVER", 0, 30, 100, "#FFD27A", face=BOLD, outline=10, alpha=clamp(u), clamp_safe=False)
    c.restore()
    for i, (name, s, cap) in enumerate(p["icons"]):
        x = 290 + i * 500
        v = EASE["out"](pop(t, t0 + 0.3 + 0.4 * i, 0.4))
        c.drawCircle(x, 760, 190, paint("#EAF4F6", v))
        c.save()
        c.clipPath(M.oval(x, 760, 186, 186), doAntiAlias=True)
        org(c, name, x, 780, s, t)
        c.restore()
        c.drawCircle(x, 760, 190, paint(INK, v, 6))
        pill(c, cap, x, 990, 34, bg="#2A1A12", alpha=v)
    va = pop(t, t0 + 1.0, 0.4)
    c.drawLine(500, 760, 500 + 70 * va, 760, paint("#FFD27A", va, 12))
    q = skia.Path()
    q.moveTo(560, 730)
    q.lineTo(590, 760)
    q.lineTo(560, 790)
    c.drawPath(q, paint("#FFD27A", va, 12))
    vq = EASE["out"](pop(t, t0 + 0.6, 0.5))
    parchment(c, 80, 1080, 920, 400, vq)
    for k, ln in enumerate(wrap_lines(p["q"], 56, BOLD, 800)):
        text(c, ln, 540, 1180 + k * 72, 56, INK, face=BOLD, shadow=False, alpha=vq, clamp_safe=False)
    tp = word_t(lid, p["pause"])
    vp = pop(t, tp, 0.3)
    if vp > 0:  # countdown ring while the viewer thinks
        prog = clamp((t - tp) / max(t1 - tp, 0.5))
        c.drawCircle(820, 1540, 46, paint("#1A120C", vp))
        c.drawArc(skia.Rect(774, 1494, 866, 1586), -90, 360 * (1 - prog), False, paint("#FFD27A", vp, 10))
        pill(c, "PAUSE & THINK", 470, 1540, 44, bg="#C8382E", alpha=vp)


def shot_split(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1260, 1)
    M.shape(c, M.rect(330, 540, 420, 110, 22), "#F4E8C8")
    text(c, p["root"], 540, 615, 54, INK, face=BOLD, shadow=False, max_w=380)
    for i, (name, icon, s, kw, at) in enumerate(p["kids"]):
        v = EASE["out"](pop(t, word_t(lid, at) - 0.15, 0.4))
        if v <= 0:
            continue
        x = 300 + i * 480
        c.drawLine(540, 650, 540 + (x - 540) * v, 650 + 150 * v, paint(INK, 1, 7))
        r = skia.Rect.MakeXYWH(x - 215, 800, 430, 620)
        c.drawRRect(skia.RRect.MakeRectXY(r, 26, 26), paint("#EAF4F6", v))
        c.save()
        c.clipRect(r)
        org(c, icon, x, 1060, s, t, **kw)
        c.restore()
        c.drawRRect(skia.RRect.MakeRectXY(r, 26, 26), paint(INK, v, 6))
        pill(c, name, x, 1360, 36, bg="#2A1A12", alpha=v)
    for lab, x, y, at, col in p.get("pills", []):
        pill(c, lab, x, y, 42, bg=col, alpha=pop(t, word_t(lid, at)))


def shot_chain(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1260, 1)
    t0, _ = seg_bounds(lid)
    for i, (lab, icon, s) in enumerate(p["items"]):
        v = EASE["out"](pop(t, t0 + 0.15 + 0.5 * i, 0.35))
        if v <= 0:
            continue
        y = 520 + i * 330
        c.drawCircle(360, y, 130, paint("#EAF4F6", v))
        c.save()
        c.clipPath(M.oval(360, y, 126, 126), doAntiAlias=True)
        org(c, icon, 360, y + 20, s, t)
        c.restore()
        c.drawCircle(360, y, 130, paint(INK, v, 6))
        text(c, lab, 520, y + 20, 48, INK, face=BOLD, align="left", shadow=False, alpha=v, clamp_safe=False, max_w=460)
        if i:
            c.drawLine(360, y - 200, 360, y - 200 + 60 * v, paint("#C8382E", 1, 12))
    lab, at = p["pill"]
    pill(c, lab, 540, 1470, 44, bg="#C8382E", alpha=pop(t, word_t(lid, at)))


def shot_slime(c, t, lid, p):
    """Forest floor: a plasmodial slime mold spreads over a decaying log."""
    vgrad(c, (0, 0, W, H), "#2E4A2E", "#1A2A1A")
    r = random.Random(8)
    for k in range(7):  # background tree trunks
        x = r.uniform(0, W)
        c.drawRect(skia.Rect(x - 40, 0, x + 40, 900), paint("#22301E", 0.8))
    M.shape(c, M.poly([(0, 1000), (W, 960), (W, H), (0, H)]), "#4A3A22")
    for k in range(70):  # leaf litter
        lx, ly = r.uniform(0, W), r.uniform(1000, 1650)
        c.save()
        c.translate(lx, ly)
        c.rotate(r.uniform(0, 180))
        M.shape(c, M.oval(0, 0, 34, 16), r.choice(["#A8642A", "#C8842A", "#7A4A22", "#8A6A2A"]), ow=2.5)
        c.restore()
    M.shape(c, M.rect(80, 1000, 920, 220, 100), "#7A5A3A", shade="#5A3E26", sdy=16, sdx=0)  # log
    M.shape(c, M.oval(140, 1110, 70, 108), "#B8946A", ow=5)
    for k in range(3):
        c.drawPath(M.oval(140, 1110, 50 - 15 * k, 80 - 24 * k), paint("#8A6A4A", 1, 3))
    for k in range(8):
        c.drawLine(260 + k * 95, 1030, 300 + k * 95, 1190, paint("#5A3E26", 1, 4))
    tsp = word_t(lid, "spores")
    grow = 0.15 + 0.85 * EASE["io"](clamp((t - tsp) / 3.0))
    c.save()
    c.clipRect(skia.Rect(80, 600, 1000, 1240))
    M.slime_mold(c, 600, 1150, 1.0, t, grow=grow)
    c.restore()
    if t < tsp + 1.0:  # spores drifting down before the plasmodium spreads
        rs = random.Random(5)
        for k in range(18):
            ph = (t * 0.2 + rs.random()) % 1
            c.drawCircle(rs.uniform(300, 900), 500 + ph * 600, 7, paint("#E8C84A", 0.8 * (1 - pop(t, tsp + 0.6, 0.4))))
    items = [("WORLDWIDE", 540, 420, "worldwide", "#2A1A12"), ("decaying plants", 280, 560, "decaying", "#6A4A22"),
             ("leaf litter", 300, 1460, "leaf", "#6A4A22"), ("tree bark", 800, 870, "bark", "#6A4A22"),
             ("spores → PLASMODIUM", 640, 690, "plasmodium", "#C8382E"), ("yellow / orange", 760, 1460, "yellow", "#D4901A")]
    for lab, x, y, at, col in items:
        pill(c, lab, x, y, 42, bg=col, alpha=pop(t, word_t(lid, at)))


def shot_house(c, t, lid, p):
    vgrad(c, (0, 0, W, 900), "#0E1430", "#1A2448")
    c.drawRect(skia.Rect(0, 900, W, H), paint("#2E4A78"))
    rs = random.Random(1)
    for k in range(40):
        c.drawCircle(rs.uniform(0, W), rs.uniform(0, 600), rs.uniform(1.5, 3.5), paint("#FFFFFF", 0.5 + 0.4 * math.sin(t * 2 + k)))
    M.house_sea(c, 540, 1020, 1.04, t)
    for k in range(8):
        c.drawLine(0, 1340 + k * 40, W, 1340 + k * 40, paint("#FFFFFF", 0.12 + 0.08 * math.sin(t * 2 + k), 3))
    pill(c, "CABUCGAYAN, BILIRAN", 540, 400, 48, bg="#2A1A12", alpha=pop(t, word_t(lid, "cabucgayan")))
    pill(c, "couple found UNCONSCIOUS", 540, 1430, 46, bg="#C8382E", alpha=pop(t, word_t(lid, "unconscious")))
    pill(c, "house facing the sea", 540, 1530, 40, bg="#2A1A12", alpha=pop(t, word_t(lid, "facing")))


def plate(c, x, y, s):
    M.shape(c, M.oval(x, y, 150 * s, 90 * s), "#F4F4F0", shade="#D8D8D0", sdx=0, sdy=8 * s)
    c.drawPath(M.oval(x, y, 110 * s, 64 * s), paint("#C8C8C0", 1, 3))
    c.drawCircle(x - 50 * s, y + 10 * s, 18 * s, paint("#E8E0C8"))  # leftover rice


def shot_table(c, t, lid, p):
    """The dinner table, seen from above: every clue labelled as it is named."""
    vgrad(c, (0, 0, W, H), "#5A4030", "#3A281C")
    for k in range(0, H, 110):
        c.drawLine(0, k, W, k + 20, paint("#2E1E14", 0.6, 4))
    M.shape(c, M.rect(70, 330, 940, 960, 30), "#8A5A34", shade="#6A4024", sdy=18, sdx=0)
    M.shape(c, M.rect(110, 370, 860, 880, 20), "#F0E4C8")
    for k in range(1, 8):  # checked tablecloth
        c.drawLine(110 + k * 107, 370, 110 + k * 107, 1250, paint("#D8B88A", 0.5, 6))
        c.drawLine(110, 370 + k * 110, 970, 370 + k * 110, paint("#D8B88A", 0.5, 6))
    for k in range(3):
        M.oyster(c, 220 + k * 90, 520 + (k % 2) * 40, 0.8, t, open_=False)
    c.save()
    c.translate(780, 520)
    c.rotate(70)
    M.puso(c, 0, 0, 0.9, t)
    c.restore()
    M.isaw(c, 300, 780, 1.1, t)
    M.pitcher(c, 780, 820, 0.85, t)
    for x in (300, 760):
        plate(c, x, 1100, 0.9)
        M.oyster(c, x + 10, 1090, 0.6, t, open_=True)
    for k, (gx, gy, rot) in enumerate(((440, 1420, 20), (560, 1460, -40), (640, 1400, 70), (500, 1500, 120))):  # broken glass
        c.save()
        c.translate(gx, gy)
        c.rotate(rot)
        M.shape(c, M.poly([(-40, 0), (30, -24), (46, 18)]), "#CDEAF4", ow=3)
        c.restore()
    items = [("fresh OYSTERS", 300, 410, "oysters"), ("PUSO", 780, 420, "puso"), ("ISAW", 300, 700, "isaw"),
             ("clear WATER", 780, 640, "pitcher"), ("2 unfinished plates", 540, 980, "unfinished"),
             ("EMPTY oyster shells", 540, 1240, "empty"), ("BROKEN GLASS", 830, 1450, "broken")]
    for lab, x, y, at in items:
        pill(c, lab, x, y, 40, bg="#C8382E" if at in ("empty", "broken") else "#2A1A12", alpha=pop(t, word_t(lid, at)))


def shot_props(c, t, lid, p):
    bg = p["bg"]
    if bg == "kitchen":
        vgrad(c, (0, 0, W, 1200), "#E8D8B8", "#D8C49A")
        M.shape(c, M.rect(-20, 1200, W + 40, 800), "#8A5A34")
        c.drawPath(M.oval(540, 1080, 460, 200), paint("#2A1A12", 0.2))
        M.shape(c, M.oval(540, 1040, 440, 170), "#F4F1EA", shade="#D8D2C4", sdx=0, sdy=10)  # serving plate
    elif bg == "room":
        vgrad(c, (0, 0, W, 1300), "#4A4A5A", "#34343E")
        M.shape(c, M.rect(-20, 1300, W + 40, 700), "#5A4636")
        M.shape(c, M.rect(560, 1180, 460, 120, 12), "#B8BEC4")  # basin counter
        M.shape(c, M.oval(790, 1200, 160, 30), "#8A9298")
        radial = M.radial
        radial(c, 540, 300, 600, "#FFE8B0", 0.25, plus=True)
    else:  # hospital
        vgrad(c, (0, 0, W, 1300), "#CDE4DA", "#B4D0C4")
        M.shape(c, M.rect(-20, 1240, W + 40, 800), "#8AA0A8")
        for k in range(0, W, 120):
            c.drawLine(k, 1240, k - 200, H, paint("#6A8088", 0.5, 3))
    for name, x, y, s, kw in p["items"]:
        org(c, name, x, y, s, t, **kw)
    for lab, x, y, at, col in p["pills"]:
        pill(c, lab, x, y, 44, bg=col, alpha=pop(t, word_t(lid, at)))
    vignette(c, 0.35)


def shot_lineup(c, t, lid, p):
    """Police line-up of the four protist suspects (no answer given: the viewer decides)."""
    vgrad(c, (0, 0, W, H), "#3A3E46", "#22252A")
    for k in range(10):  # height lines
        c.drawLine(0, 480 + k * 110, W, 480 + k * 110, paint("#FFFFFF", 0.12, 3))
    pill(c, "SUSPECT: a parasitic protist", 540, 400, 46, bg="#C8382E", alpha=pop(t, word_t(lid, "parasitic")))
    sus = [("PLASMODIUM", "plasmodium", "sporozoite", {"host": False, "enter": 1.13}, 1.1), ("ENTAMOEBA", "entamoeba", "amoeba", {}, 0.6),
           ("GIARDIA", "giardia", "giardia", {}, 0.55), ("PYRODINIUM", "pyrodinium", "dinoflagellate", {}, 0.7)]
    for i, (name, at, icon, kw, s) in enumerate(sus):
        v = EASE["out"](pop(t, word_t(lid, at) - 0.1, 0.35))
        x0, y0 = 70 + (i % 2) * 490, 500 + (i // 2) * 540
        if v <= 0:
            ghost(c, skia.Rect.MakeXYWH(x0, y0, 450, 500), t, 20)
            continue
        r = skia.Rect.MakeXYWH(x0, y0 + 40 * (1 - v), 450, 500)
        c.drawRRect(skia.RRect.MakeRectXY(r, 20, 20), paint("#DCE4E8", v))
        c.save()
        c.clipRect(r)
        org(c, icon, x0 + 225, y0 + 210, s, t, **kw)
        c.restore()
        c.drawRRect(skia.RRect.MakeRectXY(r, 20, 20), paint(INK, v, 6))
        M.shape(c, M.rect(x0 + 40, y0 + 380, 370, 90, 8), "#1A1A1E")  # name board
        text(c, f"{i + 1} · {name}", x0 + 225, y0 + 440, 40, "#FFFFFF", face=BOLD, shadow=False, alpha=v, clamp_safe=False, max_w=340)


def shot_montage(c, t, lid, p):
    desk_bg(c)
    for i, (lab, at, icon, kw, s) in enumerate(p["tiles"]):
        v = EASE["out"](pop(t, word_t(lid, at), 0.35))
        x0, y0 = 70 + (i % 2) * 480, 330 + (i // 2) * 600
        r = skia.Rect.MakeXYWH(x0, y0, 460, 560)
        if v <= 0:
            ghost(c, r, t)
            continue
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint("#EAF4F6", v))
        c.save()
        c.clipRect(r)
        if icon == "tide":
            M.M.tide(c, x0, y0, 460, 560, t, 0.9)
        else:
            org(c, icon, x0 + 230, y0 + 250, s, t, **kw)
        c.restore()
        c.drawRRect(skia.RRect.MakeRectXY(r, 28, 28), paint(INK, v, 6))
        pill(c, lab, x0 + 230, y0 + 500, 40, bg="#2A1A12", alpha=v)


def shot_recap(c, t, lid, p):
    desk_bg(c)
    parchment(c, 60, 300, 960, 1260, 1)
    t0, _ = seg_bounds(lid)
    text(c, "CASE FILE: PART 2", 540, 420, 56, "#8A1F1A", face=SERIF, shadow=False)
    cols = [("ARCHAEPLASTIDA", [("glaucophytes", "glaucophyte", 0.32), ("red algae", "red_alga", 0.3), ("green algae", "chlamydomonas", 0.4)]),
            ("UNIKONTA", [("amoebozoa", "amoeba", 0.38), ("slime molds", "slime_mold", 0.35), ("choanoflagellates", "choanoflagellate", 0.3)])]
    k = 0
    for ci, (head, items) in enumerate(cols):
        x = 300 + ci * 480
        text(c, head, x, 540, 48, "#C8382E", face=BOLD, shadow=False, alpha=pop(t, t0 + 0.1 + 0.9 * ci), max_w=440)
        for i, (name, icon, s) in enumerate(items):
            v = pop(t, t0 + 0.2 + 0.9 * ci + 0.22 * i, 0.3)
            k += 1
            if v <= 0:
                continue
            y = 610 + i * 290
            c.save()
            c.clipRect(skia.Rect.MakeXYWH(x - 200, y, 400, 220))
            org(c, icon, x, y + 110, s, t)
            c.restore()
            text(c, name, x, y + 260, 42, INK, face=BOLD, shadow=False, alpha=v, clamp_safe=False, max_w=420)
    v = pop(t, word_t(lid, "small"), 0.4)
    pill(c, "BIG THINGS · SMALL PACKAGES", 540, 1500, 46, bg="#2A1A12", alpha=v)


SHOT_FNS = {k[5:]: v for k, v in globals().items() if k.startswith("shot_")}


def draw_job(c, job, t):
    lid = job[2:]
    typ, params = PLAN[lid]
    if typ == "scope":  # the microscope already focuses in
        SHOT_FNS[typ](c, t, lid, params)
        return
    t0, t1 = seg_bounds(lid)
    u = clamp((t - t0) / max(t1 - t0, 0.1))
    k = 1.0 + 0.045 * u  # slow push so cards/diagrams never sit dead still
    c.save()
    c.translate(W / 2, H * 0.52)
    c.scale(k, k)
    c.rotate(0.4 * math.sin(t * 0.5))
    c.translate(-W / 2, -H * 0.52)
    c.drawPaint(paint("#2E2016"))  # fill the corners the slight rotation reveals
    SHOT_FNS[typ](c, t, lid, params)
    c.restore()
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
