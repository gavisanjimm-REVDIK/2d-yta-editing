"""lights.py - mood lighting presets. Rule: only lights named Key* cast shadows (speed + clean look).

rig_for(mood, target=(0,0,1.3)) builds key/fill/rim(+practicals) around a subject.
Moods: suspense, comedy, adventure, disaster, emotional_warm, emotional_cool, night, neutral_day.
Every preset keeps faces readable: fill never 0, world ambient never pure black.
"""
from __future__ import annotations

import math

import bpy
from mathutils import Vector

from . import core
from .materials import hex2rgb

PRESETS = {
    #            key (color, W, size, az, el)    fill ratio  rim (color, W)       world (color, strength)
    "neutral_day": (("#FFF4E6", 900, 2.0, 35, 40), 0.45, ("#FFFFFF", 500), ("#BFD4F0", 0.6)),
    "comedy":      (("#FFF1DC", 450, 2.5, 30, 35), 0.45, ("#FFE2B8", 300), ("#CFE0FF", 0.35)),
    "adventure":   (("#FFE3B5", 1400, 0.6, 55, 45), 0.3, ("#FFD08A", 900), ("#8FB6E8", 0.7)),
    "suspense":    (("#DCE6FF", 700, 0.8, 70, 25), 0.12, ("#7FA0FF", 700), ("#0B1020", 0.25)),
    "disaster":    (("#FFB070", 1500, 1.0, 80, 15), 0.18, ("#FF6A2A", 1200), ("#3A2418", 0.4)),
    "emotional_warm": (("#FFD9A8", 700, 3.0, 40, 30), 0.35, ("#FFE9CF", 350), ("#5A4636", 0.35)),
    "emotional_cool": (("#CFE0FF", 650, 3.0, 40, 30), 0.3, ("#E8F0FF", 350), ("#2A3448", 0.35)),
    "night":       (("#FFC27A", 600, 0.4, 50, 20), 0.15, ("#8AB4FF", 500), ("#0A0F1C", 0.2)),
}


def area(name, color, power, size, loc, target, shadows=None):
    ld = bpy.data.lights.new(name, "AREA")
    ld.color = hex2rgb(color)[:3]
    ld.energy = power
    ld.size = size
    cast = name.startswith("Key") if shadows is None else shadows
    if hasattr(ld, "use_shadow"):
        ld.use_shadow = cast
    ob = bpy.data.objects.new(name, ld)
    core.link(ob, core.collection("LIGHTS"))
    ob.location = loc
    core.look_at(ob, target)
    return ob


def point(name, color, power, loc, radius=0.1, shadows=None):
    ld = bpy.data.lights.new(name, "POINT")
    ld.color = hex2rgb(color)[:3]
    ld.energy = power
    ld.shadow_soft_size = radius
    if hasattr(ld, "use_shadow"):
        ld.use_shadow = name.startswith("Key") if shadows is None else shadows
    ob = bpy.data.objects.new(name, ld)
    core.link(ob, core.collection("LIGHTS"))
    ob.location = loc
    return ob


def sun(name, color, strength, rot_deg):
    ld = bpy.data.lights.new(name, "SUN")
    ld.color = hex2rgb(color)[:3]
    ld.energy = strength
    ld.angle = math.radians(1.5)
    if hasattr(ld, "use_shadow"):
        ld.use_shadow = name.startswith("Key")
    ob = bpy.data.objects.new(name, ld)
    core.link(ob, core.collection("LIGHTS"))
    ob.rotation_euler = [math.radians(r) for r in rot_deg]
    return ob


def _sph(dist, az, el, target):
    a, e = math.radians(az), math.radians(el)
    return Vector(target) + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist


def rig_for(mood, target=(0, 0, 1.3), dist=3.0, side=1):
    (kc, kw, ks, kaz, kel), fill, (rc, rw), (wc, ws) = PRESETS[mood]
    core.world_color(hex2rgb(wc)[:3], ws)
    key = area("Key", kc, kw, ks, _sph(dist, side * kaz, kel, target), target)
    fl = area("Fill", kc, kw * fill, 3.0, _sph(dist, -side * 50, 10, target), target)
    rim = area("Rim", rc, rw, 1.0, _sph(dist, side * -150, 35, target), target)
    return {"key": key, "fill": fl, "rim": rim}


def practical(name, loc, color="#FFD8A0", power=60, radius=0.05, flicker=None, t0=0, t1=0):
    """Visible-source light (lamp, screen, streetlight). Optional flicker keys (0..1 amount)."""
    p = point(name, color, power, loc, radius)
    if flicker:
        import random
        r = random.Random(hash(name) & 0xFFFF)
        f = core.frames(t0)
        while f < core.frames(t1):
            p.data.energy = power * (1 - flicker * r.random() ** 3)
            p.data.keyframe_insert("energy", frame=f)
            f += r.randint(1, 4)
    return p


def key_energy(light, t, energy, blend=0.5):
    """Animate light intensity (lighting changes that communicate escalation)."""
    light.data.keyframe_insert("energy", frame=core.frames(max(t - blend, 0)))
    light.data.energy = energy
    light.data.keyframe_insert("energy", frame=core.frames(t))


def volume(density=0.01, color="#FFFFFF"):
    """Scene-wide volumetric haze - use only when it serves the shot."""
    w = bpy.context.scene.world
    nt = w.node_tree
    vol = nt.nodes.new("ShaderNodeVolumePrincipled")
    vol.inputs["Density"].default_value = density
    vol.inputs["Color"].default_value = hex2rgb(color)
    nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])
