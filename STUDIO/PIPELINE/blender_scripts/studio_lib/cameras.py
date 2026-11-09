"""cameras.py - camera rigs with keyframed moves.

Each camera = empty TARGET + camera with Track-To, so moves are "where am I" + "what do I look at".
Shot vocabulary helpers: ecu/cu/mcu/ms/ws distances; push_in, pull_out, track, orbit, crane, handheld, rack focus.
"""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from . import core

# framing presets -> (distance from subject, lens mm) for a ~1.5 m character, vertical 9:16
FRAMING = {"ecu": (0.45, 85), "cu": (0.8, 70), "mcu": (1.25, 55), "ms": (1.9, 45), "mws": (2.8, 35),
           "ws": (4.5, 28), "ews": (9.0, 24)}


def make(name, loc, target, lens=40, dof_on=None, fstop=2.8, sensor=36):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = "AUTO"
    cd.clip_start, cd.clip_end = 0.05, 500
    cam = bpy.data.objects.new(name, cd)
    core.link(cam, core.collection("CAMERAS"))
    cam.location = loc
    tgt = bpy.data.objects.new(name + "_target", None)
    tgt.empty_display_size = 0.1
    core.link(tgt, core.collection("CAMERAS"))
    tgt.location = target
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    if dof_on is not False:
        cd.dof.use_dof = True
        cd.dof.focus_object = dof_on if dof_on else tgt
        cd.dof.aperture_fstop = fstop
    return cam


def shot(name, subject, framing="ms", az=0, el=5, height=None, lens=None, **kw):
    """Camera framed on subject point by preset. az: 0 = front (camera at -Y), + = to subject's left."""
    dist, l = FRAMING[framing]
    a, e = math.radians(az), math.radians(el)
    tgt = Vector(subject)
    loc = tgt + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
    if height is not None:
        loc.z = height
    return make(name, loc, tgt, lens or l, **kw)


def target(cam):
    return cam.constraints["Track To"].target


def key(cam, t, loc=None, look=None, lens=None, roll=None):
    f = core.frames(t)
    if loc is not None:
        cam.location = loc
    cam.keyframe_insert("location", frame=f)
    tg = target(cam)
    if look is not None:
        tg.location = look
    tg.keyframe_insert("location", frame=f)
    if lens is not None:
        cam.data.lens = lens
    cam.data.keyframe_insert("lens", frame=f)


def push_in(cam, t0, t1, amount=0.25, lens_to=None):
    """Slow dolly toward target by `amount` of distance (suspense)."""
    key(cam, t0)
    tg = target(cam).location
    new = cam.location.lerp(tg, amount)
    key(cam, t1, loc=new, lens=lens_to)


def pull_out(cam, t0, t1, amount=0.4):
    key(cam, t0)
    tg = target(cam).location
    new = tg + (cam.location - tg) * (1 + amount)
    key(cam, t1, loc=new)


def track(cam, t0, t1, offset):
    """Move camera and target together (tracking shot)."""
    key(cam, t0)
    key(cam, t1, loc=cam.location + Vector(offset), look=target(cam).location + Vector(offset))


def orbit(cam, t0, t1, degrees=30, steps=12):
    tg = target(cam).location.copy()
    rel = cam.location - tg
    for i in range(steps + 1):
        a = math.radians(degrees) * i / steps
        r = Vector((rel.x * math.cos(a) - rel.y * math.sin(a), rel.x * math.sin(a) + rel.y * math.cos(a), rel.z))
        key(cam, t0 + (t1 - t0) * i / steps, loc=tg + r)


def crane(cam, t0, t1, dz):
    key(cam, t0)
    key(cam, t1, loc=cam.location + Vector((0, 0, dz)))


def handheld(cam, t0, t1, amount=0.01, freq=1.3, seed=0):
    """Subtle noise on rotation via a child offset (keeps main path editable)."""
    r = random.Random(seed)
    ad = cam.animation_data_create()
    if not ad.action:
        cam.keyframe_insert("rotation_euler", frame=core.frames(t0))
    for i in range(3):
        fc = cam.animation_data.action.fcurves.find("rotation_euler", index=i) or \
            cam.animation_data.action.fcurves.new("rotation_euler", index=i)
        if not fc.keyframe_points:
            fc.keyframe_points.insert(core.frames(t0), 0)
        mod = fc.modifiers.new("NOISE")
        mod.scale = 30 / freq
        mod.strength = amount
        mod.phase = r.uniform(0, 100)
        mod.use_restricted_range = True
        mod.frame_start, mod.frame_end = core.frames(t0), core.frames(t1)
        mod.blend_in = mod.blend_out = 5


def rack_focus(cam, t, focus_obj_or_dist, blend=0.4):
    d = cam.data.dof
    d.keyframe_insert("focus_distance", frame=core.frames(max(t - blend, 0)))
    if isinstance(focus_obj_or_dist, (int, float)):
        d.focus_object = None
        d.focus_distance = focus_obj_or_dist
    else:
        d.focus_distance = (cam.location - focus_obj_or_dist.location).length
    d.keyframe_insert("focus_distance", frame=core.frames(t))


def smooth(cam):
    for ob in (cam, target(cam)):
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = "BEZIER"
                    kp.handle_left_type = kp.handle_right_type = "AUTO_CLAMPED"
