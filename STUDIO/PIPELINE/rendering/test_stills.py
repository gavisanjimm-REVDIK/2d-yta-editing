"""test_stills.py - render first/middle/last frame of every job BEFORE the full render (fix framing first).

    blender -b VIDEOS/VIDEO_NNN/scene.blend -P test_stills.py -- VIDEO_NNN
-> VIDEOS/VIDEO_NNN/qc/test_stills/<job>_<frame>.png
"""
import json
import sys
from pathlib import Path

import bpy

video = sys.argv[sys.argv.index("--") + 1]
STUDIO = Path(__file__).resolve().parents[2]
sc = bpy.context.scene
jobs = json.loads(sc.get("JOBS", "{}"))
out = STUDIO / "VIDEOS" / video / "qc" / "test_stills"
out.mkdir(parents=True, exist_ok=True)
for name, J in jobs.items():
    sc.camera = bpy.data.objects[J["camera"]]
    for f in sorted({J["start"], (J["start"] + J["end"]) // 2, J["end"]}):
        sc.frame_set(f)
        sc.render.filepath = str(out / f"{name}_{f:05d}.png")
        bpy.ops.render.render(write_still=True)
print("test stills ->", out)
