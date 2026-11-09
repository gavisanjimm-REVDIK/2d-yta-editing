"""core.py - scene setup, paths, small mesh helpers."""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

STUDIO = Path(__file__).resolve().parents[3]
FPS = 30
FULL_W, FULL_H = 1080, 1920


def load_json(rel):
    return json.loads((STUDIO / rel).read_text())


STYLE = None


def style():
    global STYLE
    if STYLE is None:
        STYLE = load_json("config/style.json")
    return STYLE


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.render.resolution_x, sc.render.resolution_y = FULL_W, FULL_H
    sc.render.resolution_percentage = 50  # 540x960 working res (edl upscales)
    sc.frame_start = 0
    setup_render(sc)
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    return sc


def setup_render(sc, samples=None):
    """CPU EEVEE (Next in 4.2+), cheap but clean."""
    r = style()["render"]
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    ee = sc.eevee
    ee.taa_render_samples = samples or r["eevee_samples"]
    for attr, val in (("use_raytracing", r.get("raytracing", False)), ("use_gtao", True),
                      ("gtao_distance", 0.6), ("use_shadows", True), ("shadow_ray_count", 1),
                      ("shadow_step_count", 4), ("use_volumetric_shadows", False),
                      ("volumetric_tile_size", "8"), ("use_bloom", False)):
        if hasattr(ee, attr):
            try:
                setattr(ee, attr, val)
            except Exception:
                pass
    sc.view_settings.view_transform = r.get("view_transform", "AgX")
    try:
        sc.view_settings.look = r.get("look", "AgX - Base Contrast")
    except TypeError:
        pass
    sc.view_settings.exposure = r.get("exposure", 0.0)
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.compression = 15
    # denoise via compositor (OpenImageDenoise) - only helps if engine is Cycles; EEVEE uses TAA
    sc.render.use_motion_blur = r.get("motion_blur", True)
    if hasattr(sc.render, "motion_blur_shutter"):
        sc.render.motion_blur_shutter = 0.35


def world_color(color=(0.05, 0.06, 0.08), strength=1.0, hdri=None):
    w = bpy.context.scene.world
    nt = w.node_tree
    bg = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
    out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    if hdri and Path(hdri).exists():
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(hdri))
        nt.links.new(env.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])


def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def link(obj, coll=None):
    for c in obj.users_collection:
        c.objects.unlink(obj)
    (coll or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_obj(name, verts, faces, coll=None, smooth=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    link(ob, coll)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def prim(kind, name, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), coll=None, mat=None, bevel=0.0,
         subdiv=0, **kw):
    """kind: cube|uv_sphere|ico_sphere|cylinder|cone|torus|plane."""
    getattr(bpy.ops.mesh, f"primitive_{kind}_add")(location=loc, rotation=rot, **kw)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale = scale
    link(ob, coll)
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width, m.segments = bevel, 3
        m.limit_method = "ANGLE"
    if subdiv:
        m = ob.modifiers.new("subd", "SUBSURF")
        m.levels = m.render_levels = subdiv
    if kind not in ("cube", "plane") or bevel:
        bpy.ops.object.shade_smooth()
    if mat:
        ob.data.materials.append(mat)
    return ob


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def frames(t):
    return int(round(t * FPS))


def deg(x):
    return math.radians(x)
