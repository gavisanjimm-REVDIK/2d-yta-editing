"""mascot.py - the orange-shirt mascot as a reusable rigged 3D character.

Two sources, same API:
  1) ASSETS/mascot/mascot.blend  (hand-finished asset built from the reference - PREFERRED once it exists)
     must contain a collection "MASCOT" with an armature named "MASCOT_rig" that uses the bone names below
     and a mesh "MASCOT_mouth" with shape keys open/smile/frown/O/wide.
  2) procedural build from ASSETS/mascot/mascot_spec.json (fallback / placeholder until the reference arrives)

Character API (returned dict "ch"):
  ch["rig"]       armature object          ch["mouth"]  mouth mesh (shape keys)
  ch["eye_target"] empty the eyes track    ch["name"]   prefix
Bone names (L/R suffix .L/.R):
  root hips spine chest neck head  shoulder upper_arm forearm hand  thumb1 thumb2 index1 index2 middle1 middle2
  ring1 ring2 pinky1 pinky2  thigh shin foot  eye lid_up lid_low brow  jaw
Facing: -Y. Height ~1.5 m (stylised ~4.2 heads).
"""
from __future__ import annotations

import math

import bmesh
import bpy
from mathutils import Vector, Matrix

from . import core, materials as M

SPEC_PATH = "ASSETS/mascot/mascot_spec.json"
BLEND_PATH = core.STUDIO / "ASSETS" / "mascot" / "mascot.blend"

FINGERS = ("thumb", "index", "middle", "ring", "pinky")


def spec():
    return core.load_json(SPEC_PATH)


# ================================================================ entry point
def load(name="MASCOT", location=(0, 0, 0), rotation_z=0.0, coll=None, look=None):
    """Load the mascot (asset .blend if present, else procedural). Additional characters can pass a `look`
    dict to override colours/proportions (re-uses the same generator so all characters share one style)."""
    sp = spec()
    if look:
        sp = _merge(sp, look)
    if BLEND_PATH.exists() and not look:
        ch = _append_blend(name)
    else:
        ch = build(sp, name, coll)
    ch["rig"].location = location
    ch["rig"].rotation_euler.z = rotation_z
    return ch


def _merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = _merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def _append_blend(name):
    with bpy.data.libraries.load(str(BLEND_PATH), link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "MASCOT"]
    col = dst.collections[0]
    col.name = name
    bpy.context.scene.collection.children.link(col)
    rig = next(o for o in col.all_objects if o.type == "ARMATURE")
    mouth = next((o for o in col.all_objects if o.name.startswith("MASCOT_mouth")), None)
    tgt = next((o for o in col.all_objects if o.name.startswith("MASCOT_eye_target")), None)
    return {"name": name, "rig": rig, "mouth": mouth, "eye_target": tgt, "collection": col}


# ================================================================ skeleton
def _skeleton(P):
    """Joint positions (metres), A-pose, facing -Y. P = proportions dict."""
    H = P["height"]
    hip = H * 0.48
    sh = H * 0.72
    shw = P["shoulder_width"] / 2
    J = {
        "root": (0, 0, 0), "hips": (0, 0, hip), "spine": (0, 0, hip + H * 0.07),
        "chest": (0, 0, hip + H * 0.16), "neck": (0, 0, sh + H * 0.02), "head": (0, 0, sh + H * 0.06),
        "head_top": (0, 0, H),
    }
    for s, x in (("L", 1), ("R", -1)):
        ax = P["arm_len"]
        J[f"shoulder.{s}"] = (x * 0.04, 0, sh - 0.01)
        J[f"upper_arm.{s}"] = (x * shw, 0.0, sh - 0.02)
        J[f"forearm.{s}"] = (x * (shw + ax * 0.33), 0.02, sh - 0.02 - ax * 0.42)
        J[f"hand.{s}"] = (x * (shw + ax * 0.55), -0.01, sh - 0.02 - ax * 0.8)
        J[f"hand_end.{s}"] = (x * (shw + ax * 0.6), -0.02, sh - 0.02 - ax * 0.88)
        J[f"thigh.{s}"] = (x * P["hip_width"] / 2, 0, hip - 0.02)
        J[f"shin.{s}"] = (x * P["hip_width"] / 2, -0.01, hip * 0.52)
        J[f"foot.{s}"] = (x * P["hip_width"] / 2, 0.02, 0.07)
        J[f"toe.{s}"] = (x * P["hip_width"] / 2, -0.13, 0.03)
    return {k: Vector(v) for k, v in J.items()}


def _finger_joints(J, s, x, P):
    """Five fingers from the hand joint; returns {finger: (base, mid, tip)}."""
    hand, end = J[f"hand.{s}"], J[f"hand_end.{s}"]
    d = (end - hand).normalized()
    side = Vector((0, -1, 0))  # palm faces body side; fingers spread along -Y
    L = P["finger_len"]
    out = {}
    spread = {"thumb": -0.035, "index": -0.018, "middle": -0.004, "ring": 0.01, "pinky": 0.022}
    for f in FINGERS:
        base = end + side * spread[f] - d * (0.02 if f == "thumb" else 0.0)
        if f == "thumb":
            dd = (d * 0.5 + side * -0.9 + Vector((x * 0.2, 0, 0))).normalized()
            ln = L * 0.8
        else:
            dd = d
            ln = L * {"index": 0.95, "middle": 1.0, "ring": 0.95, "pinky": 0.75}[f]
        out[f] = (base, base + dd * ln * 0.55, base + dd * ln)
    return out


def _build_rig(J, P, name, coll):
    arm = bpy.data.armatures.new(name + "_rig")
    rig = bpy.data.objects.new(name + "_rig", arm)
    core.link(rig, coll)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones

    def bone(n, h, t, parent=None, connect=False, deform=True):
        b = eb.new(n)
        b.head, b.tail = h, t
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        b.use_deform = deform
        return b

    bone("root", J["root"], J["root"] + Vector((0, 0.25, 0)), deform=False)
    bone("hips", J["hips"], J["spine"], "root")
    bone("spine", J["spine"], J["chest"], "hips", True)
    bone("chest", J["chest"], J["neck"], "spine", True)
    bone("neck", J["neck"], J["head"], "chest", True)
    bone("head", J["head"], J["head_top"], "neck", True)
    hc = P["head_center"]
    for s, x in (("L", 1), ("R", -1)):
        bone(f"shoulder.{s}", J[f"shoulder.{s}"], J[f"upper_arm.{s}"], "chest")
        bone(f"upper_arm.{s}", J[f"upper_arm.{s}"], J[f"forearm.{s}"], f"shoulder.{s}", True)
        bone(f"forearm.{s}", J[f"forearm.{s}"], J[f"hand.{s}"], f"upper_arm.{s}", True)
        bone(f"hand.{s}", J[f"hand.{s}"], J[f"hand_end.{s}"], f"forearm.{s}", True)
        for f, (a, b_, c) in _finger_joints(J, s, x, P).items():
            bone(f"{f}1.{s}", a, b_, f"hand.{s}")
            bone(f"{f}2.{s}", b_, c, f"{f}1.{s}", True)
        bone(f"thigh.{s}", J[f"thigh.{s}"], J[f"shin.{s}"], "hips")
        bone(f"shin.{s}", J[f"shin.{s}"], J[f"foot.{s}"], f"thigh.{s}", True)
        bone(f"foot.{s}", J[f"foot.{s}"], J[f"toe.{s}"], f"shin.{s}", True)
        # face (non-deform control bones, objects are bone-parented)
        ex = x * P["eye_spacing"] / 2
        ec = Vector((ex, hc[1] - P["head_size"][1] * P["eye_inset"], hc[2] + P["eye_height"]))
        bone(f"eye.{s}", ec, ec + Vector((0, -0.05, 0)), "head", deform=False)
        bone(f"lid_up.{s}", ec, ec + Vector((0, -0.04, 0.01)), "head", deform=False)
        bone(f"lid_low.{s}", ec, ec + Vector((0, -0.04, -0.01)), "head", deform=False)
        bc = ec + Vector((0, P["eye_radius"] * 0.25, P["eye_radius"] * 1.5))
        bone(f"brow.{s}", bc, bc + Vector((0, -0.03, 0)), "head", deform=False)
    mc = Vector((0, hc[1] - P["head_size"][1] * 0.47, hc[2] + P["mouth_height"]))
    bone("jaw", mc + Vector((0, 0.04, 0.03)), mc, "head", deform=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.show_in_front = True
    arm.display_type = "STICK"
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    return rig


# ================================================================ body (skin modifier)
def _body_mesh(J, P, name, coll, mats):
    """Skin-modifier body from joint graph (neck->feet + hands/fingers). Head is separate."""
    verts, edges, radii = [], [], []

    def v(p, r):
        verts.append(tuple(p))
        radii.append(r)
        return len(verts) - 1

    T = P["torso"]
    hips = v(J["hips"] + Vector((0, 0, -0.02)), T["hip_r"])
    belly = v(J["spine"], T["belly_r"])
    chest = v(J["chest"], T["chest_r"])
    upper = v(J["neck"] + Vector((0, 0, -0.04)), T["shoulder_r"])
    neck = v(J["head"] + Vector((0, 0.01, 0.01)), P["neck_r"])
    edges += [(hips, belly), (belly, chest), (chest, upper), (upper, neck)]
    hand_ids = {}
    for s, x in (("L", 1), ("R", -1)):
        ua = v(J[f"upper_arm.{s}"], P["arm_r"][0])
        el = v(J[f"forearm.{s}"], P["arm_r"][1])
        wr = v(J[f"hand.{s}"], P["arm_r"][2])
        palm = v(J[f"hand_end.{s}"], P["palm_r"])
        edges += [(upper, ua), (ua, el), (el, wr), (wr, palm)]
        for f, (a, b, c) in _finger_joints(J, s, x, P).items():
            r = P["finger_r"] * (1.15 if f == "thumb" else 1.0)
            ia, ib, ic = v(a, r), v(b, r * 0.92), v(c, r * 0.8)
            edges += [(palm, ia), (ia, ib), (ib, ic)]
        th = v(J[f"thigh.{s}"], P["leg_r"][0])
        kn = v(J[f"shin.{s}"], P["leg_r"][1])
        an = v(J[f"foot.{s}"], P["leg_r"][2])
        toe = v(J[f"toe.{s}"], P["foot_r"])
        edges += [(hips, th), (th, kn), (kn, an), (an, toe)]
        hand_ids[s] = palm
    me = bpy.data.meshes.new(name + "_body")
    me.from_pydata(verts, edges, [])
    ob = bpy.data.objects.new(name + "_body", me)
    core.link(ob, coll)
    sk = ob.modifiers.new("skin", "SKIN")
    sk.use_smooth_shade = True
    sk.branch_smoothing = 0.6
    for i, r in enumerate(radii):
        rv = r if isinstance(r, (tuple, list)) else (r, r)
        me.skin_vertices[0].data[i].radius = (rv[0], rv[1])
    me.skin_vertices[0].data[hips].use_root = True
    sub = ob.modifiers.new("subd", "SUBSURF")
    sub.levels = sub.render_levels = 2
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="skin")
    bpy.ops.object.modifier_apply(modifier="subd")
    bpy.ops.object.shade_smooth()
    # material regions: shirt (torso + sleeves), pants, shoes, skin
    for m in ("skin", "shirt", "pants", "shoes"):
        ob.data.materials.append(mats[m])
    sleeve_z = J["upper_arm.L"].z - P["arm_len"] * P["sleeve_len"]
    for poly in ob.data.polygons:
        c = poly.center
        if c.z < 0.11 or (c.z < 0.16 and c.y < -0.02):
            idx = 3
        elif c.z < J["hips"].z + 0.06 and abs(c.x) < P["hip_width"] + 0.1:
            idx = 2
        elif c.z < J["neck"].z - 0.005 and (abs(c.x) < P["shoulder_width"] / 2 + 0.03 or c.z > sleeve_z):
            idx = 1
        else:
            idx = 0
        poly.material_index = idx
    ob.select_set(False)
    return ob


def _clothing_details(J, P, name, coll, mats, rig):
    """Collar + sleeve hems + waistband rings for a believable silhouette (bone-parented)."""
    objs = []

    def ring(n, loc, r, minor, rot, mat, bone):
        o = core.prim("torus", f"{name}_{n}", loc, (1, 1, 1), rot, coll, mat,
                      major_radius=r, minor_radius=minor, major_segments=32, minor_segments=10)
        _parent_bone(o, rig, bone)
        objs.append(o)

    ring("collar", J["head"] + Vector((0, 0.005, -0.03)), P["neck_r"] * 1.35, 0.012, (0.25, 0, 0), mats["shirt"], "chest")
    for s, x in (("L", 1), ("R", -1)):
        ua, fa = J[f"upper_arm.{s}"], J[f"forearm.{s}"]
        p = ua.lerp(fa, P["sleeve_len"] / 0.42 * 0.95)
        d = (fa - ua).normalized()
        rot = d.to_track_quat("Z", "Y").to_euler()
        ring(f"sleeve.{s}", p, P["arm_r"][0] * 1.25, 0.012, rot, mats["shirt"], f"upper_arm.{s}")
    ring("waist", J["hips"] + Vector((0, 0, 0.06)), P["torso"]["hip_r"][0] * 1.02, 0.014, (0, 0, 0), mats["pants"], "hips")
    return objs


# ================================================================ head & face
def _head(P, name, coll, mats, rig):
    hc = Vector(P["head_center"])
    sx, sy, sz = P["head_size"]
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=1, location=(0, 0, 0))
    head = bpy.context.active_object
    head.name = name + "_head"
    core.link(head, coll)
    for vtx in head.data.vertices:
        x, y, z = vtx.co
        # stylised skull: wide cranium, round cheeks, soft chin taper, flatter back
        taper = 1 - P["chin_taper"] * max(0, -z) ** 1.6
        cheek = 1 + P["cheek_puff"] * math.exp(-((z + 0.25) ** 2) / 0.05) * max(0, -y)
        back = 1 - 0.08 * max(0, y) ** 2
        vtx.co = Vector((x * sx * taper * cheek, y * sy * back * (0.95 + 0.05 * taper), z * sz))
    head.location = hc
    bpy.ops.object.shade_smooth()
    sub = head.modifiers.new("subd", "SUBSURF")
    sub.levels = sub.render_levels = 1
    head.data.materials.append(mats["skin"])
    _parent_bone(head, rig, "head")
    # nose (soft bump)
    nose = core.prim("uv_sphere", name + "_nose",
                     hc + Vector((0, -sy * 0.98, P["nose_height"])),
                     (P["nose_size"] * 0.8, P["nose_size"] * 0.7, P["nose_size"]), coll=coll, mat=mats["skin"],
                     segments=24, ring_count=16)
    _parent_bone(nose, rig, "head")
    # ears
    for s, x in (("L", 1), ("R", -1)):
        ear = core.prim("uv_sphere", f"{name}_ear.{s}", hc + Vector((x * sx * 0.98, 0.02, P["eye_height"] * 0.3)),
                        (0.02, 0.035, 0.05), coll=coll, mat=mats["skin"], segments=20, ring_count=12)
        _parent_bone(ear, rig, "head")
    return head


def _eyes(P, name, coll, mats, rig):
    r = P["eye_radius"]
    objs = []
    tgt = bpy.data.objects.new(name + "_eye_target", None)
    tgt.empty_display_type = "SPHERE"
    tgt.empty_display_size = 0.03
    core.link(tgt, coll)
    hc = Vector(P["head_center"])
    tgt.location = hc + Vector((0, -1.5, P["eye_height"]))
    tgt.parent = rig
    for s, x in (("L", 1), ("R", -1)):
        pb = rig.data.bones[f"eye.{s}"]
        c = rig.matrix_world @ pb.head_local
        ball = core.prim("uv_sphere", f"{name}_eyeball.{s}", c, (r, r * P["eye_depth"], r * P["eye_tall"]),
                         coll=coll, mat=mats["eye_white"], segments=32, ring_count=24)
        iris = core.prim("uv_sphere", f"{name}_iris.{s}", c + Vector((0, -r * P["eye_depth"] * 0.86, 0)),
                         (r * P["iris_size"], r * 0.18, r * P["iris_size"] * P["eye_tall"]), coll=coll,
                         mat=mats["iris"], segments=32, ring_count=16)
        hl = core.prim("uv_sphere", f"{name}_catchlight.{s}",
                       c + Vector((x * -r * 0.18, -r * P["eye_depth"] * 1.02, r * 0.25)),
                       (r * 0.12,) * 3, coll=coll, mat=mats["catchlight"], segments=12, ring_count=8)
        for o in (ball, iris, hl):
            _parent_bone(o, rig, f"eye.{s}")
        # lids: half shells slightly larger than eyeball; rotate lid bones on X to blink
        for lid, keep_up in (("lid_up", True), ("lid_low", False)):
            o = core.prim("uv_sphere", f"{name}_{lid}.{s}", c, (r * 1.1, r * P["eye_depth"] * 1.1, r * P["eye_tall"] * 1.1),
                          coll=coll, mat=mats["skin"], segments=32, ring_count=24)
            bm = bmesh.new()
            bm.from_mesh(o.data)
            kill = [v for v in bm.verts if (v.co.z < -0.05 if keep_up else v.co.z > -0.55)]
            bmesh.ops.delete(bm, geom=kill, context="VERTS")
            bm.to_mesh(o.data)
            bm.free()
            sol = o.modifiers.new("thick", "SOLIDIFY")
            sol.thickness = 0.004
            _parent_bone(o, rig, f"{lid}.{s}")
            # lashes line on the upper lid edge (dark)
            objs.append(o)
        # brows
        bpy.ops.curve.primitive_bezier_curve_add(location=(0, 0, 0))
        br = bpy.context.active_object
        br.name = f"{name}_brow.{s}"
        core.link(br, coll)
        bc = rig.matrix_world @ rig.data.bones[f"brow.{s}"].head_local
        sp = br.data.splines[0]
        w = r * 1.15
        sx_, sy_, sz_ = P["head_size"]

        def on_skin(px, pz, lift=0.005):
            u = 1 - ((px - hc.x) / sx_) ** 2 - ((pz - hc.z) / sz_) ** 2
            return Vector((px, hc.y - sy_ * math.sqrt(max(u, 0.0)) - lift, pz))

        pts = [on_skin(bc.x - x * w, bc.z - 0.003), on_skin(bc.x + x * w, bc.z - 0.008)]
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        br.data.bevel_depth = P["brow_thick"]
        br.data.bevel_resolution = 3
        br.data.use_fill_caps = True
        br.data.materials.append(mats["hair"])
        _parent_bone(br, rig, f"brow.{s}")
        objs += [ball, iris, hl, br]
    # eyes track target
    for s in ("L", "R"):
        pb = rig.pose.bones[f"eye.{s}"]
        c = pb.constraints.new("DAMPED_TRACK")
        c.target = tgt
        c.track_axis = "TRACK_Y"
    return objs, tgt


def _mouth(P, name, coll, mats, rig):
    """2.5D stylised mouth sitting on the face: dark interior + teeth + tongue, shape keys for visemes."""
    hc = Vector(P["head_center"])
    sy = P["head_size"][1]
    mw, mh = P["mouth_width"], P["mouth_width"] * 0.55
    cz = hc.z + P["mouth_height"]
    cy = hc.y - sy * 0.93
    seg = 24
    verts, faces = [(0, 0, 0)], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        verts.append((math.cos(a), 0, math.sin(a)))
    for i in range(seg):
        faces.append((0, 1 + i, 1 + (i + 1) % seg))
    me = bpy.data.meshes.new(name + "_mouth")
    me.from_pydata(verts, [], faces)
    mouth = bpy.data.objects.new(name + "_mouth", me)
    core.link(mouth, coll)
    mouth.location = (0, cy, cz)
    mouth.data.materials.append(mats["mouth"])

    def shape(fn):
        return [Vector(fn(*v)) for v in verts]

    def ellipse(w, h, smile=0.0, oy=0.0):
        # corners pushed back (+Y) to wrap the face; smile lifts corners
        return lambda x, y, z: (x * w, x * x * w * 0.35, z * h + smile * (x * x - 0.4) * h + oy)

    mouth.shape_key_add(name="Basis")
    base = ellipse(mw * 0.85, mh * 0.04, 0.0)
    for v, p in zip(me.vertices, shape(base)):
        v.co = p
    me.shape_keys.key_blocks["Basis"].data.foreach_set("co", [c for v in me.vertices for c in v.co])
    keys = {
        "open": ellipse(mw * 0.8, mh * 0.9, 0.0, -mh * 0.35),
        "smile": ellipse(mw * 1.0, mh * 0.12, 1.4),
        "frown": ellipse(mw * 0.8, mh * 0.1, -1.4),
        "O": ellipse(mw * 0.45, mh * 0.6, 0.0, -mh * 0.2),
        "wide": ellipse(mw * 1.1, mh * 0.45, 0.6, -mh * 0.1),
    }
    for k, fn in keys.items():
        kb = mouth.shape_key_add(name=k, from_mix=False)
        for i, p in enumerate(shape(fn)):
            kb.data[i].co = p
    sol = mouth.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.004
    _parent_bone(mouth, rig, "jaw")
    return mouth


def _hair(P, name, coll, mats, rig):
    """Clumped stylised hair: scalp cap + sculpted clumps (spec hair.clumps)."""
    hc = Vector(P["head_center"])
    sx, sy, sz = P["head_size"]
    hp = P["hair"]
    cap = core.prim("uv_sphere", name + "_hair_cap", hc + Vector((0, 0.005, 0.01)),
                    (sx * 1.04, sy * 1.05, sz * 1.04), coll=coll, mat=mats["hair"], segments=48, ring_count=32)
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    line = hp["hairline"]  # z (unit sphere) where front hairline sits
    kill = [v for v in bm.verts if v.co.z < (line if v.co.y < 0 else line - 0.55) - 0.25 * (1 - abs(v.co.x)) * (v.co.y > 0)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(cap.data)
    bm.free()
    sol = cap.modifiers.new("thick", "SOLIDIFY")
    sol.thickness = 0.01
    sub = cap.modifiers.new("subd", "SUBSURF")
    sub.levels = sub.render_levels = 1
    _parent_bone(cap, rig, "head")
    parts = [cap]
    for i, c in enumerate(hp["clumps"]):
        # c: [theta_deg (around Z, 0=front), phi_deg (from top), length, width, sweep_x, sweep_z]
        th, ph = math.radians(c[0]), math.radians(c[1])
        n = Vector((math.sin(ph) * math.sin(th), -math.sin(ph) * math.cos(th), math.cos(ph)))
        base = hc + Vector((n.x * sx, n.y * sy, n.z * sz)) * 0.97
        o = core.prim("uv_sphere", f"{name}_hair_clump{i}", (0, 0, 0), (1, 1, 1), coll=coll, mat=mats["hair"],
                      segments=16, ring_count=12)
        for vtx in o.data.vertices:
            x, y, z = vtx.co
            u = (z + 1) / 2  # 0 root .. 1 tip
            w = c[3] * (1 - u) ** 0.45 + 0.003
            vtx.co = Vector((x * w, y * w * 0.6, u * c[2]))
        o.location = base
        # lie along the scalp: mostly tangent sweep, a little lift off the normal
        d = (n * 0.45 + Vector((c[4], -0.5 * math.cos(th), c[5]))).normalized()
        o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
        sub = o.modifiers.new("subd", "SUBSURF")
        sub.levels = sub.render_levels = 1
        _parent_bone(o, rig, "head")
        parts.append(o)
    return parts


# ================================================================ helpers
def _parent_bone(obj, rig, bone):
    """Parent obj to a bone while keeping its world transform."""
    bpy.context.view_layer.update()
    mw = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_parent_inverse = Matrix.Identity(4)
    bpy.context.view_layer.update()
    obj.matrix_world = mw


def _skin_to_rig(body, rig):
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    bpy.ops.object.select_all(action="DESELECT")


# ================================================================ build
def build(sp, name="MASCOT", coll=None):
    coll = coll or core.collection(name)
    P = sp["proportions"]
    C = sp["colors"]
    mats = {
        "skin": M.skin(C["skin"], f"{name}_skin"),
        "shirt": M.fabric(C["shirt"], f"{name}_shirt"),
        "pants": M.fabric(C["pants"], f"{name}_pants", 0.2, (0.6, 0.8), 0.12),
        "shoes": M.simple(C["shoes"], 0.45, name=f"{name}_shoes"),
        "hair": M.hair(C["hair"], f"{name}_hair"),
        "eye_white": M.eye_white(),
        "iris": M.iris(C["iris"], f"{name}_iris"),
        "catchlight": M.emission("#FFFFFF", 3.0, "catchlight"),
        "mouth": M.simple(C["mouth"], 0.6, name=f"{name}_mouth", var=False),
    }
    J = _skeleton(P)
    rig = _build_rig(J, P, name, coll)
    body = _body_mesh(J, P, name, coll, mats)
    _skin_to_rig(body, rig)
    if P.get("clothing_rings"):
        _clothing_details(J, P, name, coll, mats, rig)
    _head(P, name, coll, mats, rig)
    _, tgt = _eyes(P, name, coll, mats, rig)
    mouth = _mouth(P, name, coll, mats, rig)
    _hair(P, name, coll, mats, rig)
    from .perform import lid_angle
    for s_ in ("L", "R"):
        rig.pose.bones[f"lid_up.{s_}"].rotation_euler.x = lid_angle(0.15)
    return {"name": name, "rig": rig, "mouth": mouth, "eye_target": tgt, "collection": coll, "body": body}
