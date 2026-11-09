"""render_shot.py - one Blender render job (runs INSIDE Blender).

    blender -b VIDEOS/VIDEO_NNN/scene.blend -P render_shot.py -- VIDEO_NNN JOB [frames.txt | start end]

JOB must exist in the scene's "JOBS" custom property (written by videos/videoNNN.py):
    {"job": {"camera": "CAM_A", "start": 0, "end": 120}}   (scene frames)
Output frame index i (source time i/30 within the job) = scene frame start + i
  -> VIDEOS/VIDEO_NNN/frames/JOB/f_iiiii.png   (half res 540x960; skips files that exist -> resumable)
"""
import json
import sys
from pathlib import Path

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
video, job = argv[0], argv[1]
STUDIO = Path(__file__).resolve().parents[2]
sc = bpy.context.scene
jobs = json.loads(sc.get("JOBS", "{}"))
J = jobs[job]
if len(argv) > 2 and argv[2].endswith(".txt"):
    idxs = [int(x) for x in Path(argv[2]).read_text().split()]
elif len(argv) > 3:
    idxs = list(range(int(argv[2]), int(argv[3]) + 1))
else:
    idxs = list(range(0, J["end"] - J["start"] + 1))

sc.camera = bpy.data.objects[J["camera"]]
for k, v in J.get("hide", {}).items():  # per-job visibility overrides {"obj": true}
    if k in bpy.data.objects:
        bpy.data.objects[k].hide_render = v
out = STUDIO / "VIDEOS" / video / "frames" / job
out.mkdir(parents=True, exist_ok=True)
for i in idxs:
    p = out / f"f_{i:05d}.png"
    if p.exists():
        continue
    sc.frame_set(J["start"] + i)
    sc.render.filepath = str(p)
    bpy.ops.render.render(write_still=True)
    print(f"RENDERED {job} {i}", flush=True)
