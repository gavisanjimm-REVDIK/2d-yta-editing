"""Render mascot turnaround + expression sheet stills -> ASSETS/mascot/turnaround/.
Run: blender -b -P PIPELINE/blender_scripts/tools/mascot_turnaround.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from studio_lib import core, mascot, lights, cameras, perform  # noqa: E402

sc = core.reset_scene()
out = core.STUDIO / "ASSETS" / "mascot" / "turnaround"
out.mkdir(parents=True, exist_ok=True)
ch = mascot.load()
floor = core.prim("plane", "floor", (0, 0, 0), (5, 5, 1))
from studio_lib import materials as M  # noqa: E402
floor.data.materials.append(M.simple("#8C8C8C", 0.8))
lights.rig_for("neutral_day", (0, 0, 1.0), 4.0)
sc.render.resolution_percentage = 50

body = cameras.make("CAM_body", (0, -4.2, 0.9), (0, 0, 0.75), 45)
face = cameras.make("CAM_face", (0, -0.95, 1.3), (0, 0, 1.27), 70)
import os  # noqa: E402
QUICK = os.environ.get("QUICK")
for i, ang in enumerate((0, 90) if QUICK else (0, 45, 90, 180)):
    ch["rig"].rotation_euler.z = __import__("math").radians(ang)
    sc.camera = body
    sc.render.filepath = str(out / f"body_{ang:03d}.png")
    bpy.ops.render.render(write_still=True)
ch["rig"].rotation_euler.z = 0
sc.camera = face
for k, name in enumerate(["neutral", "happy", "surprised", "angry", "sad", "scared"]):
    perform.expression(ch, k * 1.0 + 0.5, name, blend=0.2)
for k, name in enumerate(["neutral", "happy", "surprised", "angry", "sad", "scared"]):
    sc.frame_set(core.frames(k * 1.0 + 0.5))
    sc.render.filepath = str(out / f"face_{name}.png")
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out / "mascot_preview.blend"))
print("turnaround ->", out)
