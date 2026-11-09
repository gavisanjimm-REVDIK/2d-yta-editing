"""EDL for VIDEO_NNN. Beat times come from narration words -> re-recorded lines re-time the edit.
See PIPELINE/editing/edl_engine.py docstring for every segment effect and overlay type."""
import json
from pathlib import Path

HERE = Path(__file__).parent
T = json.loads((HERE / "audio" / "timing.json").read_text())
WORDS = T["words"]


def w(text, nth=0, edge="start"):
    hits = [x for x in WORDS if x["word"].strip(".,!?").lower() == text]
    return hits[nth][edge]


def line(lid, edge="start"):
    return next(l for l in T["lines"] if l["id"] == lid)[edge]


DURATION = round(T["duration"], 2)
BPM = 96
LOOP = False
BEATS = {
    "hook": 0.0,
    "turn": line("L02"),
    # "drop": ..., "silence": (t0, t1), "reveal": ...
}

SEGMENTS = [
    # jobs come from blender (jobs.json) or anim2d.py SHOTS; src_t = source time at t0
    {"t0": 0.0, "t1": BEATS["turn"], "src": "wide", "src_t": 0.0,
     "fx": [{"fx": "zoom", "keys": [(0.0, 1.0, 0.5, 0.5), (BEATS["turn"], 1.1, 0.5, 0.45, "lin")]}]},
    {"t0": BEATS["turn"], "t1": DURATION, "src": "cu", "src_t": BEATS["turn"],
     "fx": [{"fx": "whip", "t": BEATS["turn"], "dur": 0.2, "dir": 1}]},
]
OVERLAYS = [
    # {"type": "timer", "t0": 0, "t1": 10, "from": 10, "y": 150},
]
CAPTIONS = {"words": WORDS, "emphasis": [], "pos": [], "speakers": True}
AUDIO = "audio/mix_master.wav"
