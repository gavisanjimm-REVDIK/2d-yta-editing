"""EDL for VIDEO_000 - 10 s 2D pipeline test. Beat times come from narration words."""
import json
from pathlib import Path

HERE = Path(__file__).parent
T = json.loads((HERE / "audio" / "timing.json").read_text())
WORDS = T["words"]


def w(text, nth=0, edge="start"):
    hits = [x for x in WORDS if x["word"].strip(".,!?").lower() == text]
    return hits[nth][edge]


DURATION = round(max(T["duration"], 10.0), 2)
BEATS = {
    "until": w("until"),
    "reveal": w("lamp"),          # lamp switches on
    "end": DURATION,
}
LAMP_ON = BEATS["reveal"] + 0.15  # anim2d reads this too

SEGMENTS = [
    {"t0": 0.0, "t1": BEATS["until"], "src": "room", "src_t": 0.0,
     "fx": [{"fx": "zoom", "keys": [(0.0, 1.0, 0.5, 0.55), (BEATS["until"], 1.2, 0.5, 0.48, "lin")]}]},
    {"t0": BEATS["until"], "t1": LAMP_ON + 0.9, "src": "face", "src_t": BEATS["until"],
     "fx": [{"fx": "zoom", "keys": [(BEATS["until"], 1.0, 0.5, 0.4), (LAMP_ON, 1.12, 0.5, 0.4, "in")]}]},
    {"t0": LAMP_ON + 0.9, "t1": DURATION, "src": "room", "src_t": LAMP_ON + 0.9,
     "fx": [{"fx": "flash", "t": LAMP_ON + 0.9, "dur": 0.12},
            {"fx": "zoom", "keys": [(LAMP_ON + 0.9, 1.25, 0.72, 0.5), (DURATION, 1.15, 0.65, 0.5, "out")]},
            {"fx": "shake", "t0": LAMP_ON + 0.9, "t1": LAMP_ON + 1.4, "amp": 14}]},
]
OVERLAYS = [
    {"type": "chip", "text": "TEST 000", "t0": 0.3, "t1": 2.5, "y": 140},
]
# captions move to the top while the face close-up is on screen (never cover faces)
CAPTIONS = {"words": WORDS, "emphasis": ["nothing", "lamp", "itself"],
            "pos": [(BEATS["until"], LAMP_ON + 0.9, 0.17)]}
AUDIO = "audio/mix_master.wav"
