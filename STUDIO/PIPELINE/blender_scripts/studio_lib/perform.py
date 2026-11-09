"""perform.py - acting helpers: expressions, blinks, lip-sync, look, breathe, gestures, fingers, walks.

All times in seconds (converted with core.frames). Everything keyframes pose bones / shape keys / empties.
"""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from .core import frames, deg

# expression = brows (up/down m, inner tilt deg), lids (upper close 0..1), mouth shape keys, head tilt
EXPRESSIONS = {
    "neutral":   {"brow": (0.0, 0), "lid": 0.15, "mouth": {}, "tilt": 0},
    "happy":     {"brow": (0.004, -5), "lid": 0.25, "mouth": {"smile": 1.0}, "tilt": 4},
    "grin":      {"brow": (0.006, -5), "lid": 0.3, "mouth": {"wide": 0.8, "smile": 0.6}, "tilt": 3},
    "surprised": {"brow": (0.012, -8), "lid": 0.0, "mouth": {"O": 0.8}, "tilt": -2},
    "scared":    {"brow": (0.009, 18), "lid": 0.0, "mouth": {"open": 0.4, "frown": 0.4}, "tilt": -4},
    "worried":   {"brow": (0.004, 15), "lid": 0.2, "mouth": {"frown": 0.5}, "tilt": 3},
    "angry":     {"brow": (-0.006, -20), "lid": 0.35, "mouth": {"frown": 0.7}, "tilt": -3},
    "sad":       {"brow": (0.002, 20), "lid": 0.4, "mouth": {"frown": 0.8}, "tilt": 6},
    "suspicious": {"brow": (-0.003, -10), "lid": 0.5, "mouth": {"frown": 0.2}, "tilt": 5},
    "determined": {"brow": (-0.003, -12), "lid": 0.25, "mouth": {"smile": 0.15}, "tilt": -2},
    "shocked":   {"brow": (0.014, 10), "lid": 0.0, "mouth": {"open": 1.0}, "tilt": -6},
}


LID_OPEN_DEG = -75.0  # upper-lid shell rotation when fully open (0 = closed); bone local X = world -X


def lid_angle(closure):
    """closure 0 = open .. 1 = shut -> bone X rotation (radians)."""
    return deg(LID_OPEN_DEG * (1 - closure))


def _pb(ch, bone):
    return ch["rig"].pose.bones[bone]


def _key_rot(pb, f, rot=None):
    if rot is not None:
        pb.rotation_euler = rot
    pb.keyframe_insert("rotation_euler", frame=f)


def _key_loc(pb, f, loc=None):
    if loc is not None:
        pb.location = loc
    pb.keyframe_insert("location", frame=f)


def _shape(ch, name, value, f):
    m = ch.get("mouth")
    if not m or not m.data.shape_keys or name not in m.data.shape_keys.key_blocks:
        return
    kb = m.data.shape_keys.key_blocks[name]
    kb.value = value
    kb.keyframe_insert("value", frame=f)


# ---------------------------------------------------------------- face
def expression(ch, t, name, blend=0.2, hold_mouth=False):
    """Key an expression at t (eases in over `blend` s from the previous state)."""
    e = EXPRESSIONS[name]
    f0, f1 = frames(max(t - blend, 0)), frames(t)
    for s, sgn in (("L", 1), ("R", -1)):
        pb = _pb(ch, f"brow.{s}")
        _key_loc(pb, f0)
        _key_rot(pb, f0)
        # brow bones point -Y; local Z ~ world up
        _key_loc(pb, f1, (0, 0, e["brow"][0]))
        _key_rot(pb, f1, (0, -deg(e["brow"][1]) * sgn, 0))
        for lid in ("lid_up",):
            lp = _pb(ch, f"{lid}.{s}")
            _key_rot(lp, f0)
            _key_rot(lp, f1, (lid_angle(e["lid"]), 0, 0))
    if not hold_mouth:
        for k in ("open", "smile", "frown", "O", "wide"):
            _shape(ch, k, 0.0 if k not in e["mouth"] else _cur(ch, k), f0)
            _shape(ch, k, e["mouth"].get(k, 0.0), f1)
    hp = _pb(ch, "head")
    _key_rot(hp, f0)
    r = hp.rotation_euler.copy()
    _key_rot(hp, f1, (r.x, deg(e["tilt"]), r.z))


def _cur(ch, k):
    m = ch.get("mouth")
    return m.data.shape_keys.key_blocks[k].value if m and m.data.shape_keys else 0.0


def blinks(ch, t0, t1, every=3.0, seed=1, base_lid=0.15):
    rnd = random.Random(seed)
    t = t0 + rnd.uniform(0.3, every)
    while t < t1:
        for s in ("L", "R"):
            lp = _pb(ch, f"lid_up.{s}")
            for dt, v in ((-0.06, base_lid), (0.0, 1.0), (0.07, 1.0), (0.16, base_lid)):
                lp.rotation_euler = (lid_angle(v), 0, 0)
                lp.keyframe_insert("rotation_euler", frame=frames(t + dt))
        t += every * rnd.uniform(0.6, 1.4)


def lipsync(ch, words, who=None, t_offset=0.0, strength=1.0):
    """Mouth 'open'/'O'/'wide' shape keys from word timing (timing.json words)."""
    for w in words:
        if who and w.get("who") != who:
            continue
        s, e = w["start"] + t_offset, w["end"] + t_offset
        txt = w["word"].lower()
        vowels = [c for c in txt if c in "aeiouy"] or ["a"]
        n = max(1, len(vowels))
        step = (e - s) / n
        _shape(ch, "open", 0.0, frames(s - 0.04))
        for i, v in enumerate(vowels):
            tt = s + step * (i + 0.5)
            k = "O" if v in "ou" else ("wide" if v in "ie" else "open")
            for kk in ("open", "O", "wide"):
                _shape(ch, kk, (0.55 + 0.45 * strength) * (1.0 if kk == k else 0.15), frames(tt))
        for kk in ("open", "O", "wide"):
            _shape(ch, kk, 0.0, frames(e + 0.03))


def look_at(ch, t, world_point, blend=0.15):
    tgt = ch["eye_target"]
    tgt.keyframe_insert("location", frame=frames(max(t - blend, 0)))
    tgt.location = ch["rig"].matrix_world.inverted() @ Vector(world_point)
    tgt.keyframe_insert("location", frame=frames(t))


def head_turn(ch, t, yaw=0.0, pitch=0.0, roll=0.0, blend=0.3):
    for bone, k in (("neck", 0.35), ("head", 0.65)):
        pb = _pb(ch, bone)
        _key_rot(pb, frames(max(t - blend, 0)))
        _key_rot(pb, frames(t), (deg(pitch * k), deg(roll * k), deg(yaw * k)))


# ---------------------------------------------------------------- body
def breathe(ch, t0, t1, rate=0.25, amount=1.0):
    pb = _pb(ch, "chest")
    t = t0
    while t < t1:
        for ph, v in ((0, 0), (0.5, 1), (1.0, 0)):
            pb.rotation_euler.x = deg(-1.2 * v * amount)
            pb.scale = (1 + 0.01 * v * amount, 1 + 0.015 * v * amount, 1)
            pb.keyframe_insert("rotation_euler", frame=frames(t + ph / rate))
            pb.keyframe_insert("scale", frame=frames(t + ph / rate))
        t += 1 / rate


def weight_shift(ch, t, side=1, blend=0.6):
    """Shift hips toward one leg (idle life)."""
    hp = _pb(ch, "hips")
    _key_loc(hp, frames(max(t - blend, 0)))
    _key_rot(hp, frames(max(t - blend, 0)))
    _key_loc(hp, frames(t), (side * 0.02, 0, -0.005))
    _key_rot(hp, frames(t), (0, deg(side * 3), 0))


def arm(ch, t, side, shoulder=(0, 0, 0), elbow=(0, 0, 0), wrist=(0, 0, 0), blend=0.25):
    """Rotations in degrees (bone local XYZ)."""
    for bone, r in ((f"upper_arm.{side}", shoulder), (f"forearm.{side}", elbow), (f"hand.{side}", wrist)):
        pb = _pb(ch, bone)
        _key_rot(pb, frames(max(t - blend, 0)))
        _key_rot(pb, frames(t), tuple(deg(x) for x in r))


GESTURES = {  # side -> (shoulder, elbow, wrist)
    "rest": ((0, 0, 0), (0, 0, 0), (0, 0, 0)),
    "point": ((-75, 0, -10), (-5, 0, 0), (0, 0, 0)),
    "wave": ((-20, 0, -110), (0, 0, -60), (0, 0, 20)),
    "shrug": ((10, 0, -35), (-70, 0, 0), (0, 40, 0)),
    "think": ((-35, 0, -10), (-130, 0, 0), (20, 0, 0)),
    "stop": ((-80, 0, 0), (-20, 0, 0), (-70, 0, 0)),
    "cover_mouth": ((-40, 0, -5), (-140, 0, 0), (0, 0, 0)),
    "fist_pump": ((-20, 0, -40), (-120, 0, 0), (0, 0, 0)),
}


def gesture(ch, t, name, side="R", blend=0.3, anticipation=True):
    sh, el, wr = GESTURES[name]
    if anticipation and name != "rest":  # small opposite move first
        arm(ch, t - blend * 0.4, side, tuple(-x * 0.08 for x in sh), el, wr, blend * 0.6)
    arm(ch, t, side, sh, el, wr, blend)
    if name in ("point", "stop"):
        fingers(ch, t, side, curl=0.9 if name == "point" else 0.0, except_=("index",) if name == "point" else ())
    elif name in ("fist_pump",):
        fingers(ch, t, side, curl=1.0)


def fingers(ch, t, side, curl=0.0, spread=0.0, except_=(), blend=0.15):
    for f in ("thumb", "index", "middle", "ring", "pinky"):
        c = 0.0 if f in except_ else curl
        for seg in ("1", "2"):
            pb = _pb(ch, f"{f}{seg}.{side}")
            _key_rot(pb, frames(max(t - blend, 0)))
            _key_rot(pb, frames(t), (deg(-80 * c), 0, deg(spread * 8)))


def walk(ch, t0, t1, path, stride=0.55, cadence=1.9, bounce=0.025):
    """Walk along list of (x, y) points (world), facing direction of travel. cadence = steps/s."""
    rig = ch["rig"]
    pts = [Vector((p[0], p[1], 0)) for p in path]
    segs = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum((b - a).length for a, b in segs)
    n = frames(t1) - frames(t0)
    hips = _pb(ch, "hips")
    for i in range(n + 1):
        u = i / max(n, 1)
        d = total * u
        acc = 0.0
        for a, b in segs:
            L = (b - a).length
            if acc + L >= d or (a, b) == segs[-1]:
                k = (d - acc) / max(L, 1e-6)
                pos = a.lerp(b, min(k, 1))
                direc = (b - a).normalized()
                break
            acc += L
        f = frames(t0) + i
        rig.location = (pos.x, pos.y, rig.location.z)
        rig.rotation_euler.z = math.atan2(direc.x, -direc.y)
        rig.keyframe_insert("location", frame=f)
        rig.keyframe_insert("rotation_euler", frame=f)
        ph = (i / 30) * cadence * math.pi
        hips.location = (0, 0, -abs(math.sin(ph)) * bounce)
        hips.rotation_euler = (0, deg(3 * math.sin(ph)), deg(4 * math.sin(ph)))
        hips.keyframe_insert("location", frame=f)
        hips.keyframe_insert("rotation_euler", frame=f)
        for s, sg in (("L", 1), ("R", -1)):
            swing = math.sin(ph + (0 if s == "L" else math.pi))
            th, sn = _pb(ch, f"thigh.{s}"), _pb(ch, f"shin.{s}")
            th.rotation_euler = (deg(28 * swing), 0, 0)
            sn.rotation_euler = (deg(-35 * max(0, -math.cos(ph + (0 if s == "L" else math.pi)))), 0, 0)
            th.keyframe_insert("rotation_euler", frame=f)
            sn.keyframe_insert("rotation_euler", frame=f)
            ua = _pb(ch, f"upper_arm.{s}")
            ua.rotation_euler = (deg(-20 * swing), 0, 0)
            ua.keyframe_insert("rotation_euler", frame=f)
    return total


def idle(ch, t0, t1, seed=0):
    """Breathing + blinks + occasional weight shift and glance - call on every on-screen character."""
    breathe(ch, t0, t1)
    blinks(ch, t0, t1, seed=seed)
    rnd = random.Random(seed)
    t = t0 + rnd.uniform(1.0, 2.5)
    side = 1
    while t < t1:
        weight_shift(ch, t, side)
        side *= -1
        t += rnd.uniform(2.5, 4.5)


def smooth_all(ch, interp="BEZIER"):
    for ob in (ch["rig"], ch.get("mouth"), ch.get("eye_target")):
        ad = getattr(ob, "animation_data", None) if ob else None
        if ad and ad.action:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = interp
                    kp.easing = "AUTO"
