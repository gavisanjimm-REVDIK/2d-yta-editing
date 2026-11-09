"""toon.py - optional stylisation pass.

outline(obj)       inverted-hull outline (solidify + backface-culled dark material), cheap & clean
soft_toon(mat)     insert a 3-step ramp between diffuse light and colour (keeps Principled specular)
Use sparingly: the house look is polished stylised 3D, not cel-shaded. Outline is good for small/far characters.
"""
from __future__ import annotations

import bpy

from .materials import hex2rgb


def _outline_mat(color="#1A1412"):
    m = bpy.data.materials.get("toon_outline")
    if m:
        return m
    m = bpy.data.materials.new("toon_outline")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs[0].default_value = hex2rgb(color)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs[0])
    m.use_backface_culling = True
    return m


def outline(obj, thickness=0.006, color="#1A1412"):
    mat = _outline_mat(color)
    obj.data.materials.append(mat)
    sol = obj.modifiers.new("outline", "SOLIDIFY")
    sol.thickness = -thickness
    sol.use_flip_normals = True
    sol.use_rim = False
    sol.material_offset = len(obj.data.materials) - 1
    return sol


def soft_toon(mat, steps=(0.0, 0.35, 0.7), shadow_mult=0.65):
    """Shader-to-RGB ramp for a mild painted look (EEVEE only)."""
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    out = nt.nodes.get("Material Output")
    if not bsdf or not out:
        return
    s2r = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    cr.elements[0].color = (shadow_mult,) * 3 + (1,)
    cr.elements[1].position = steps[2]
    em = nt.nodes.new("ShaderNodeEmission")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(bsdf.outputs[0], s2r.inputs[0])
    nt.links.new(s2r.outputs["Color"], ramp.inputs[0])
    src = bsdf.inputs["Base Color"]
    if src.links:
        nt.links.new(src.links[0].from_socket, mix.inputs[6])
    else:
        mix.inputs[6].default_value = src.default_value
    nt.links.new(ramp.outputs[0], mix.inputs[7])
    nt.links.new(mix.outputs[2], em.inputs[0])
    nt.links.new(em.outputs[0], out.inputs[0])
