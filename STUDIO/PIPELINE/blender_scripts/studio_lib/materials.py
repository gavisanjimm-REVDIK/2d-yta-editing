"""materials.py - stylised-but-believable material library (Principled BSDF based).

Every material has a small procedural roughness/colour variation so nothing looks like flat plastic.
get(name, **overrides) caches by name+overrides.
"""
from __future__ import annotations

import bpy

_CACHE = {}


def hex2rgb(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)


def _base(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    return m, nt, bsdf


def _inp(bsdf, *names):
    for n in names:
        if n in bsdf.inputs:
            return bsdf.inputs[n]
    return None


def _variation(nt, bsdf, scale=8.0, rough=(0.45, 0.6), color=None, color_amt=0.06, bump=0.0):
    """Noise-driven roughness (+ optional colour mottling + bump)."""
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs[3].default_value, mr.inputs[4].default_value = rough
    nt.links.new(noise.outputs["Fac"], mr.inputs[0])
    nt.links.new(mr.outputs[0], bsdf.inputs["Roughness"])
    if color:
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = color_amt
        mix.inputs[6].default_value = hex2rgb(color)
        nt.links.new(noise.outputs["Color"], mix.inputs[7])
        nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    if bump:
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump
        b.inputs["Distance"].default_value = 0.02
        nt.links.new(noise.outputs["Fac"], b.inputs["Height"])
        nt.links.new(b.outputs[0], bsdf.inputs["Normal"])


def skin(color="#F2C6A0", name="skin"):
    m, nt, b = _base(name)
    b.inputs["Base Color"].default_value = hex2rgb(color)
    sss = _inp(b, "Subsurface Weight", "Subsurface")
    if sss:
        sss.default_value = 0.25
    rad = _inp(b, "Subsurface Radius")
    if rad:
        rad.default_value = (1.0, 0.35, 0.2)
    sc = _inp(b, "Subsurface Scale")
    if sc:
        sc.default_value = 0.03
    _variation(nt, b, 30, (0.42, 0.55), color, 0.05)
    spec = _inp(b, "Specular IOR Level", "Specular")
    if spec:
        spec.default_value = 0.4
    return m


def fabric(color, name=None, sheen=0.12, rough=(0.7, 0.85), bump=0.08):
    m, nt, b = _base(name or f"fabric_{color}")
    b.inputs["Base Color"].default_value = hex2rgb(color)
    sh = _inp(b, "Sheen Weight", "Sheen")
    if sh:
        sh.default_value = sheen
    _variation(nt, b, 60, rough, color, 0.08, bump)
    return m


def hair(color="#3B2A20", name="hair"):
    m, nt, b = _base(name)
    b.inputs["Base Color"].default_value = hex2rgb(color)
    an = _inp(b, "Anisotropic")
    if an:
        an.default_value = 0.6
    coat = _inp(b, "Coat Weight", "Clearcoat")
    if coat:
        coat.default_value = 0.15
    _variation(nt, b, 40, (0.5, 0.65), color, 0.12, 0.04)
    return m


def eye_white():
    m, nt, b = _base("eye_white")
    b.inputs["Base Color"].default_value = hex2rgb("#F4F1EC")
    b.inputs["Roughness"].default_value = 0.08
    coat = _inp(b, "Coat Weight", "Clearcoat")
    if coat:
        coat.default_value = 1.0
    return m


def iris(color="#4A2E1F", name="iris"):
    """Radial iris + dark pupil via gradient on object Z axis (eye points -Y)."""
    m, nt, b = _base(name)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    # distance from eye axis
    vm = nt.nodes.new("ShaderNodeVectorMath")
    vm.operation = "LENGTH"
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(sep.outputs["X"], comb.inputs["X"])
    nt.links.new(sep.outputs["Z"], comb.inputs["Z"])
    nt.links.new(comb.outputs[0], vm.inputs[0])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.interpolation = "EASE"
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.005, 0.005, 0.005, 1)
    cr.elements[1].position, cr.elements[1].color = 0.38, hex2rgb(color)
    e = cr.elements.new(0.9)
    e.color = tuple(c * 0.45 for c in hex2rgb(color)[:3]) + (1,)
    nt.links.new(vm.outputs["Value"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.05
    coat = _inp(b, "Coat Weight", "Clearcoat")
    if coat:
        coat.default_value = 1.0
    return m


def simple(color, rough=0.5, metal=0.0, name=None, var=True):
    key = (name or color, rough, metal)
    if key in _CACHE:
        return _CACHE[key]
    m, nt, b = _base(name or f"mat_{color}")
    b.inputs["Base Color"].default_value = hex2rgb(color)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if var:
        _variation(nt, b, 12, (max(rough - 0.1, 0), min(rough + 0.1, 1)), color, 0.06)
    _CACHE[key] = m
    return m


def metal(color="#B8BCC2", rough=0.3):
    return simple(color, rough, 1.0, f"metal_{color}")


def wood(color="#8A5A3A"):
    m, nt, b = _base(f"wood_{color}")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 9
    wave.inputs["Distortion"].default_value = 6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    c = hex2rgb(color)
    ramp.color_ramp.elements[0].color = tuple(x * 0.7 for x in c[:3]) + (1,)
    ramp.color_ramp.elements[1].color = c
    nt.links.new(wave.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    return m


def glass(tint="#DDEEFF", rough=0.03):
    m, nt, b = _base(f"glass_{tint}")
    b.inputs["Base Color"].default_value = hex2rgb(tint)
    b.inputs["Roughness"].default_value = rough
    tr = _inp(b, "Transmission Weight", "Transmission")
    if tr:
        tr.default_value = 1.0
    b.inputs["IOR"].default_value = 1.45
    if hasattr(m, "surface_render_method"):
        m.surface_render_method = "BLENDED"
    elif hasattr(m, "blend_method"):
        m.blend_method = "BLEND"
    return m


def concrete(color="#9A9890"):
    m, nt, b = _base(f"concrete_{color}")
    b.inputs["Base Color"].default_value = hex2rgb(color)
    _variation(nt, b, 25, (0.75, 0.95), color, 0.18, 0.25)
    return m


def water(color="#2D5C70"):
    m, nt, b = _base(f"water_{color}")
    b.inputs["Base Color"].default_value = hex2rgb(color)
    b.inputs["Roughness"].default_value = 0.04
    tr = _inp(b, "Transmission Weight", "Transmission")
    if tr:
        tr.default_value = 0.6
    _variation(nt, b, 4, (0.02, 0.08), None, 0, 0.3)
    return m


def emission(color="#FFE7B0", strength=5.0, name=None):
    m, nt, b = _base(name or f"emit_{color}")
    b.inputs["Base Color"].default_value = hex2rgb(color)
    e = _inp(b, "Emission Color", "Emission")
    e.default_value = hex2rgb(color)
    s = _inp(b, "Emission Strength")
    if s:
        s.default_value = strength
    return m
