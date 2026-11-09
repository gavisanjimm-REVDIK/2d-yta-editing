"""EDL - VIDEO_001 "The Man Who Knew It Was Raining". Every beat comes from narration word timing."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
T = json.loads((HERE / "audio" / "timing.json").read_text())
WORDS = T["words"]
LINES = {l["id"]: l for l in T["lines"]}


def w(text, line=None, nth=0, edge="start"):
    hits = [x for x in WORDS if x["word"].strip(".,!?'").lower() == text and (line is None or x["line"] == line)]
    return hits[nth][edge]


def L(lid, edge="start"):
    return LINES[lid][edge]


B = {
    "basement_hook": 1.7,
    "detective": w("detective", "L01"),
    "safe": L("L01", "end") + 0.35,
    "harrison_ms": w("gone", "L02", edge="end") + 0.1,
    "power": w("power", "L02"),
    "foyer": L("L02", "end") + 0.2,
    "marcus_q": L("L03", "end") + 0.25,
    "oliver": L("L04", "end") + 0.12,
    "daniel": L("L05", "end") + 0.1,
    "lightning_word": w("lightning", "L06"),
    "basement_word": w("basement", "L06"),
    "sophie": L("L06", "end") + 0.1,
    "thunder_word": w("thunder", "L07"),
    "turn": L("L07", "end") + 0.1,
    "daniel_name": w("daniel", "L08"),
    "daniel2": L("L08", "end") + 0.12,
    "descend": L("L09", "end") + 0.05,
    "explain": L("L10"),
    "daniel_ecu": L("L10", "end") + 0.15,
    "silence": L("L10", "end") + 0.05,
    "lineup": L("L11") - 0.02,
    "n_oliver": w("oliver", "L11"),
    "n_sophie": w("sophie", "L11"),
    "n_daniel": w("daniel", "L11"),
    "recap_end": L("L11", "end") + 0.2,
    "zoom": L("L12"),
    "who": w("who", "L12"),
    "freeze": L("L12", "end") + 0.05,
}
DURATION = round(B["freeze"] + 5.0, 2)
BPM = 84
# lightning strikes (global s). The basement shots never light up from these: no windows down there.
STRIKES = [0.0, 1.25, B["power"] + 0.1, B["lightning_word"] + 0.05, B["thunder_word"] - 0.1,
           B["explain"] + 0.6, B["n_daniel"] + 1.2]


def seg(t0, t1, src, fx=()):
    return {"t0": t0, "t1": t1, "src": src, "src_t": t0, "fx": list(fx)}


SEGMENTS = [
    seg(0.0, B["basement_hook"], "ext", [{"fx": "shake", "t0": 0.0, "t1": 0.5, "amp": 22}]),
    seg(B["basement_hook"], B["safe"], "basement_hook",
        [{"fx": "zoom", "keys": [(B["basement_hook"], 1.25, 0.5, 0.45), (B["basement_hook"] + 0.35, 1.0, 0.5, 0.45, "out")]}]),
    seg(B["safe"], B["harrison_ms"], "study_safe",
        [{"fx": "zoom", "keys": [(B["safe"], 1.0, 0.5, 0.5), (B["harrison_ms"], 1.12, 0.5, 0.5, "lin")]}]),
    seg(B["harrison_ms"], B["foyer"], "study"),
    seg(B["foyer"], B["marcus_q"], "foyer_wide",
        [{"fx": "zoom", "keys": [(B["foyer"], 1.0, 0.5, 0.5), (B["marcus_q"], 1.08, 0.45, 0.5, "lin")]}]),
    seg(B["marcus_q"], B["oliver"], "cu_marcus"),
    seg(B["oliver"], B["daniel"], "cu_oliver", [{"fx": "whip", "t": B["oliver"], "dur": 0.22, "dir": -1}]),
    seg(B["daniel"], B["sophie"], "cu_daniel",
        [{"fx": "whip", "t": B["daniel"], "dur": 0.22, "dir": -1},
         {"fx": "zoom", "keys": [(B["lightning_word"] - 0.1, 1.0, 0.5, 0.35), (B["lightning_word"] + 0.1, 1.1, 0.5, 0.35, "out")]}]),
    seg(B["sophie"], B["turn"], "cu_sophie", [{"fx": "whip", "t": B["sophie"], "dur": 0.22, "dir": -1}]),
    seg(B["turn"], B["daniel2"], "marcus_turn",
        [{"fx": "zoom", "keys": [(B["turn"], 1.0, 0.5, 0.45), (B["daniel2"], 1.15, 0.5, 0.4, "lin")]}]),
    seg(B["daniel2"], B["descend"], "cu_daniel",
        [{"fx": "zoom", "keys": [(B["daniel2"], 1.12, 0.5, 0.35), (B["descend"], 1.0, 0.5, 0.35, "out")]}]),
    seg(B["descend"], B["daniel_ecu"], "basement_pan"),
    seg(B["daniel_ecu"], B["lineup"], "cu_daniel",
        [{"fx": "zoom", "keys": [(B["daniel_ecu"], 1.55, 0.5, 0.3), (B["lineup"], 1.75, 0.5, 0.3, "lin")]},
         {"fx": "shake", "t0": B["daniel_ecu"], "t1": B["daniel_ecu"] + 0.35, "amp": 12},
         {"fx": "flash", "t": B["daniel_ecu"], "dur": 0.1}]),
    seg(B["lineup"], DURATION, "lineup",
        [{"fx": "freeze", "t0": B["freeze"], "t1": DURATION + 1, "tint": "#2A3A6A", "amount": 0.25},
         {"fx": "vignette", "strength": 0.35}]),
]

sys.path.insert(0, str(HERE))
import gfx  # noqa: E402

OVERLAYS = [
    {"type": "custom", "t0": B["lineup"] + 0.1, "t1": B["zoom"] - 0.1, "anim": 0.25,
     "draw": gfx.case_file(B["n_oliver"], B["n_sophie"], B["n_daniel"])},
    {"type": "custom", "t0": B["freeze"], "t1": DURATION + 1, "anim": 0.2, "draw": gfx.end_card(B["freeze"])},
]
CAPTIONS = {"words": WORDS, "speakers": True, "emphasis": ["lying", "one", "gone", "nine", "nobody", "lightning",
                                                             "window", "explain", "who"],
            # close-ups: faces fill the upper/middle frame -> captions drop to the torso
            "pos": [(B["marcus_q"], B["turn"], 0.88), (B["daniel2"], B["descend"], 0.88),
                    (B["daniel_ecu"], B["lineup"], 0.88), (B["lineup"], B["zoom"], 0.84), (B["zoom"], B["freeze"], 0.88)],
            "max_words": 4}
AUDIO = "audio/mix_master.wav"
