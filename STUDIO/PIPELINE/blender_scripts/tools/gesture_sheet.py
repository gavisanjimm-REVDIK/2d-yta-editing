"""Render every gesture (R arm) from the front + 3/4 -> ASSETS/mascot/turnaround/gesture_*.png
Run: blender -b -P PIPELINE/blender_scripts/tools/gesture_sheet.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from studio_lib import core, mascot, lights, cameras, perform, materials as M  # noqa: E402

sc = core.reset_scene()
out = core.STUDIO / "ASSETS" / "mascot" / "turnaround"
out.mkdir(parents=True, exist_ok=True)
ch = mascot.load()
core.prim("plane", "floor", (0, 0, 0), (5, 5, 1), mat=M.simple("#8C8C8C", 0.8))
lights.rig_for("neutral_day", (0, 0, 1.0), 4.0)
cam = cameras.make("CAM", (1.6, -3.6, 1.0), (0, 0, 0.85), 40, dof_on=False)
sc.camera = cam
perform.relax_arms(ch, 0)
names = list(perform.GESTURES)
for i, n in enumerate(names):
    perform.gesture(ch, 1.0 + i, n, "R", anticipation=False)
    perform.gesture(ch, 1.0 + i, "rest", "L", anticipation=False)
for i, n in enumerate(names):
    sc.frame_set(core.frames(1.0 + i))
    sc.render.filepath = str(out / f"gesture_{n}.png")
    bpy.ops.render.render(write_still=True)

# walk cycle check: 1 s of walking, 4 frames
ch["rig"].animation_data_clear()
for pb in ch["rig"].pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.location = (0, 0, 0)
perform.relax_arms(ch, 0)
perform.walk(ch, 0, 2.0, [(0, 0), (0, -1.6)])
cam2 = cameras.make("CAM_side", (3.5, -0.8, 0.9), (0, -0.8, 0.8), 40, dof_on=False)
sc.camera = cam2
for k, f in enumerate((15, 19, 23, 27)):
    sc.frame_set(f)
    sc.render.filepath = str(out / f"walk_{k}.png")
    bpy.ops.render.render(write_still=True)
