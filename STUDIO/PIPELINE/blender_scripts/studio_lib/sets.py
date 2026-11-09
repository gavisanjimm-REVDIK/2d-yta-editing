"""sets.py - reusable stylised environments built from code.

Each set returns a dict of named anchor points (where characters stand, where props sit) so video scripts
can stage action without hard-coding coordinates. Details that tell the story > detail everywhere.

    bedroom(night=False)   subway_car()   street(night=False)   classroom()   outdoor_field()
"""
from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

from . import core, materials as M


def _c(name):
    return core.collection(name)


def box(name, loc, size, mat, coll, bevel=0.01, rot=(0, 0, 0)):
    return core.prim("cube", name, loc, tuple(s / 2 for s in size), rot, coll, mat, bevel=bevel)


# ================================================================ bedroom
def bedroom(wall="#C9D6CF", floor="#9A6B47", night=False):
    c = _c("SET_bedroom")
    W, D, H = 4.0, 4.5, 2.7
    E = 4.0  # extra depth behind the camera side so wide shots stay inside the room
    yc = -E / 2
    box("floor", (0, yc, -0.05), (W, D + E, 0.1), M.wood(floor), c, 0)
    box("wall_back", (0, D / 2, H / 2), (W, 0.1, H), M.simple(wall, 0.85), c, 0)
    box("wall_left", (-W / 2, yc, H / 2), (0.1, D + E, H), M.simple(wall, 0.85), c, 0)
    box("wall_right", (W / 2, yc, H / 2), (0.1, D + E, H), M.simple(wall, 0.85), c, 0)
    box("ceiling", (0, yc, H + 0.05), (W, D + E, 0.1), M.simple("#EEEAE2", 0.9), c, 0)
    box("baseboard", (0, D / 2 - 0.06, 0.05), (W, 0.03, 0.1), M.simple("#F2EFE8", 0.5), c, 0.003)
    # bed
    box("bed_frame", (-1.0, 1.2, 0.2), (1.3, 2.0, 0.4), M.wood("#6E4A30"), c, 0.02)
    box("mattress", (-1.0, 1.2, 0.48), (1.25, 1.95, 0.18), M.fabric("#ECE8E0", "sheet"), c, 0.06)
    box("blanket", (-1.0, 0.95, 0.58), (1.3, 1.35, 0.08), M.fabric("#4F6D8F", "blanket"), c, 0.04)
    core.prim("uv_sphere", "pillow", (-1.0, 1.95, 0.64), (0.45, 0.2, 0.09), coll=c,
              mat=M.fabric("#F4F1EA", "pillow"), segments=24, ring_count=12)
    # desk + lamp + window
    box("desk", (1.3, 1.8, 0.75), (1.2, 0.6, 0.05), M.wood("#B08860"), c, 0.01)
    for dx in (-0.55, 0.55):
        box(f"desk_leg{dx}", (1.3 + dx, 1.8, 0.37), (0.05, 0.5, 0.74), M.metal("#3A3A3A", 0.4), c, 0.005)
    core.prim("cylinder", "lamp_base", (1.65, 1.9, 0.8), (0.08, 0.08, 0.02), coll=c, mat=M.metal("#222222"))
    core.prim("cone", "lamp_shade", (1.65, 1.9, 1.15), (0.14, 0.14, 0.12), coll=c,
              mat=M.emission("#FFE1B0", 4 if night else 0.5, "lampshade"))
    box("window_frame", (0, D / 2 - 0.02, 1.6), (1.2, 0.08, 1.0), M.simple("#F2EFE8", 0.5), c, 0.01)
    box("window_glass", (0, D / 2 - 0.01, 1.6), (1.05, 0.02, 0.85),
        M.emission("#1B2A4A" if night else "#CFE6FF", 0.6 if night else 2.5, "window_sky"), c, 0)
    box("rug", (0.2, 0.2, 0.005), (1.8, 1.2, 0.01), M.fabric("#B5655A", "rug"), c, 0.002)
    return {"stand": Vector((0.2, 0.0, 0)), "bed": Vector((-1.0, 1.2, 0.6)), "desk": Vector((1.3, 1.8, 0.78)),
            "lamp": Vector((1.65, 1.9, 1.15)), "window": Vector((0, D / 2, 1.6)), "door": Vector((-1.8, -1.5, 0))}


# ================================================================ subway car
def subway_car(length=12.0, lit=True):
    c = _c("SET_subway")
    W, H = 2.8, 2.3
    body = M.simple("#C8CDD2", 0.35, 0.3, "subway_wall")
    box("floor", (0, 0, -0.05), (W, length, 0.1), M.concrete("#5A5E63"), c, 0)
    box("ceiling", (0, 0, H), (W, length, 0.1), M.simple("#E6E8EA", 0.5), c, 0)
    for x in (-W / 2, W / 2):
        box(f"wall_{x}", (x, 0, H / 2), (0.08, length, H), body, c, 0)
    # windows, seats, poles, ceiling light strips, ads
    for i, y in enumerate([k for k in frange(-length / 2 + 1.0, length / 2 - 0.5, 1.6)]):
        for sx in (-1, 1):
            box(f"win_{i}_{sx}", (sx * (W / 2 - 0.03), y, 1.45), (0.02, 1.0, 0.6),
                M.emission("#0D1118", 0.3, "tunnel_dark"), c, 0.01)
            box(f"seat_{i}_{sx}", (sx * (W / 2 - 0.3), y, 0.45), (0.45, 1.2, 0.08),
                M.simple("#2F5D8C", 0.4, name="seat_blue"), c, 0.03)
            box(f"ad_{i}_{sx}", (sx * (W / 2 - 0.05), y + 0.8, 1.95), (0.02, 0.5, 0.3),
                M.simple(random.Random(i * 7 + sx).choice(["#E85D3C", "#3CA3E8", "#F2C14E", "#6BBF59"]), 0.6), c, 0)
        core.prim("cylinder", f"pole_{i}", (0, y + 0.8, H / 2), (0.022, 0.022, H / 2), coll=c,
                  mat=M.metal("#D9DCE0", 0.2))
    box("light_strip", (0, 0, H - 0.03), (0.25, length * 0.95, 0.03),
        M.emission("#F4F8FF", 6 if lit else 0.2, "strip_light"), c, 0)
    return {"stand": Vector((0, -1.0, 0)), "seat_l": Vector((-1.1, 0.6, 0.5)), "seat_r": Vector((1.1, 0.6, 0.5)),
            "door": Vector((1.4, -2.5, 0)), "far": Vector((0, length / 2 - 0.5, 1.0))}


# ================================================================ street
def street(night=False, blocks=6, seed=3):
    c = _c("SET_street")
    rnd = random.Random(seed)
    box("road", (0, 20, -0.05), (8, 60, 0.1), M.concrete("#3C3D40"), c, 0)
    for sx in (-1, 1):
        box(f"sidewalk_{sx}", (sx * 5.5, 20, 0.05), (3, 60, 0.2), M.concrete("#A4A29C"), c, 0.01)
        for b in range(blocks):
            h = rnd.uniform(6, 18)
            col = rnd.choice(["#C98F6B", "#D9C7A8", "#8D9AA6", "#B65F4B", "#E2D6C2"])
            y = b * 9 + rnd.uniform(-0.5, 0.5)
            box(f"bld_{sx}_{b}", (sx * 10.5, y, h / 2), (7, 8.5, h), M.concrete(col), c, 0.03)
            for fl in range(1, int(h / 3)):
                for k in (-2.5, 0, 2.5):
                    lit = night and rnd.random() < 0.45
                    box(f"win_{sx}_{b}_{fl}_{k}", (sx * 6.98, y + k, fl * 3 + 0.2), (0.04, 1.2, 1.4),
                        M.emission("#FFD9A0", 3, "win_lit") if lit else M.glass("#9FB4C8", 0.1), c, 0)
        for k in range(0, 50, 12):
            core.prim("cylinder", f"lamp_pole_{sx}_{k}", (sx * 4.3, k, 2.5), (0.06, 0.06, 2.5), coll=c,
                      mat=M.metal("#2E3135", 0.4))
            core.prim("uv_sphere", f"lamp_head_{sx}_{k}", (sx * 4.0, k, 5.0), (0.25, 0.25, 0.12), coll=c,
                      mat=M.emission("#FFC983", 8 if night else 0.3, "street_lamp"))
    for k in range(0, 50, 4):
        box(f"lane_{k}", (0, k, 0.002), (0.15, 2.0, 0.01), M.simple("#E8E2C8", 0.6, name="lane_paint"), c, 0)
    return {"stand": Vector((4.8, 2.0, 0.15)), "road": Vector((0, 8, 0)), "far": Vector((0, 45, 2))}


# ================================================================ classroom
def classroom():
    c = _c("SET_classroom")
    W, D, H = 7, 8, 3
    box("floor", (0, 0, -0.05), (W, D, 0.1), M.wood("#B48A5E"), c, 0)
    box("wall_back", (0, D / 2, H / 2), (W, 0.1, H), M.simple("#E4DCC8", 0.85), c, 0)
    box("board", (0, D / 2 - 0.07, 1.6), (3.5, 0.04, 1.2), M.simple("#25402F", 0.9, name="chalkboard"), c, 0.01)
    for r in range(3):
        for k in range(3):
            x, y = -2 + k * 2, 1.5 - r * 1.6
            box(f"desk_{r}_{k}", (x, y, 0.72), (1.0, 0.6, 0.04), M.wood("#C9A87C"), c, 0.01)
            box(f"chair_{r}_{k}", (x, y - 0.55, 0.42), (0.45, 0.42, 0.04), M.simple("#3D6FA8", 0.5, name="chair"), c, 0.01)
    return {"stand": Vector((0, 2.8, 0)), "desk_front": Vector((0, 1.5, 0.75)), "board": Vector((0, D / 2, 1.6))}


# ================================================================ outdoor
def outdoor_field(seed=5, trees=14):
    c = _c("SET_field")
    rnd = random.Random(seed)
    g = core.prim("plane", "ground", (0, 0, 0), (60, 60, 1), coll=c, mat=M.fabric("#5E8A3C", "grass", 0.6, (0.8, 0.95), 0.3))
    disp = g.modifiers.new("sub", "SUBSURF")
    disp.subdivision_type = "SIMPLE"
    disp.levels = disp.render_levels = 5
    tex = bpy.data.textures.new("terrain", "CLOUDS")
    tex.noise_scale = 6
    d = g.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = 0.6
    for i in range(trees):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(8, 30)
        x, y = math.cos(a) * r, abs(math.sin(a)) * r + 4
        h = rnd.uniform(3, 6)
        core.prim("cylinder", f"trunk{i}", (x, y, h * 0.3), (0.18, 0.18, h * 0.3), coll=c, mat=M.wood("#5B3E2A"))
        core.prim("ico_sphere", f"canopy{i}", (x, y, h * 0.75), (h * 0.35,) * 3, coll=c,
                  mat=M.fabric(rnd.choice(["#4C7A34", "#3E6B2E", "#5C8C3F"]), "leaves", 0.5, (0.7, 0.9), 0.4),
                  subdiv=1, subdivisions=2)
    return {"stand": Vector((0, 0, 0)), "far": Vector((0, 30, 2))}


def frange(a, b, step):
    x = a
    while x < b:
        yield x
        x += step
