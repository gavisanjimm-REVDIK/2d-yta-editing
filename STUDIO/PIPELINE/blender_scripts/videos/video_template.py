"""video_template.py - copy to videoNNN.py for each 3D video.

    blender -b -P PIPELINE/blender_scripts/videos/videoNNN.py -- VIDEO_NNN
Builds the scene, performs the characters from narration word timing, defines cameras and JOBS,
saves VIDEOS/VIDEO_NNN/scene.blend + jobs.json. Then:
    blender -b VIDEOS/VIDEO_NNN/scene.blend -P PIPELINE/rendering/test_stills.py -- VIDEO_NNN
    python PIPELINE/rendering/render_needed.py VIDEO_NNN
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy  # noqa: E402
from studio_lib import core, mascot, perform, lights, cameras, sets  # noqa: E402

VIDEO = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "VIDEO_TEMPLATE"
VDIR = core.STUDIO / "VIDEOS" / VIDEO
timing_p = VDIR / "audio" / "timing.json"
timing = json.loads(timing_p.read_text()) if timing_p.exists() else {"words": [], "duration": 10.0}
WORDS = timing["words"]
DUR = timing["duration"]


def word_t(text, nth=0, default=0.0):
    """Time of the nth occurrence of a word in the narration (beats come from words, never hard-coded)."""
    hits = [w for w in WORDS if w["word"].strip(".,!?").lower() == text.lower()]
    return hits[nth]["start"] if len(hits) > nth else default


# ---------------------------------------------------------------- scene
sc = core.reset_scene()
sc.frame_end = core.frames(DUR)
anchors = sets.bedroom(night=False)          # pick/compose a set that fits the story
ch = mascot.load(location=anchors["stand"])  # the mascot: never redesign, only perform
lights.rig_for("comedy", target=(anchors["stand"].x, anchors["stand"].y, 1.2))  # lighting matches the story

# ---------------------------------------------------------------- performance
perform.idle(ch, 0, DUR, seed=1)
perform.lipsync(ch, WORDS, who="narrator")   # or the character's own lines (who="mascot")
perform.expression(ch, 0.0, "neutral")
perform.expression(ch, word_t("what", default=1.5), "surprised")
perform.gesture(ch, word_t("look", default=2.5), "point", "R")
perform.look_at(ch, 3.0, (anchors["stand"].x - 1.5, anchors["stand"].y - 3, 1.3))  # glance off to the side
perform.smooth_all(ch)

# ---------------------------------------------------------------- cameras (each = a job)
s = anchors["stand"]
head = (s.x, s.y, 1.27)
A = cameras.shot("CAM_wide", (s.x, s.y, 0.85), "mws", az=-15, el=6)
B = cameras.shot("CAM_cu", head, "cu", az=10, el=2)
cameras.push_in(B, 0.0, DUR, 0.2)
cameras.smooth(B)

JOBS = {
    "wide": {"camera": A.name, "start": 0, "end": core.frames(DUR)},
    "cu": {"camera": B.name, "start": 0, "end": core.frames(DUR)},
}
sc["JOBS"] = json.dumps(JOBS)
VDIR.mkdir(parents=True, exist_ok=True)
(VDIR / "jobs.json").write_text(json.dumps(JOBS, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(VDIR / "scene.blend"))
print("scene ->", VDIR / "scene.blend")
