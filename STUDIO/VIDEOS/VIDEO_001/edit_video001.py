"""EDL - VIDEO_001 "The Man Who Knew It Was Raining" (v2: fair-play riddle, nobody singled out).
Every beat comes from narration word timing."""
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
    "hook_lineup": w("but", "L01") - 0.05,
    "hook_marcus": w("can", "L01") - 0.05,
    "detective": w("detective", "L01"),
    "safe": L("L02") - 0.1,
    "harrison_ms": w("gone", "L02", edge="end") + 0.1,
    "power": w("power", "L02"),
    "foyer": L("L03") - 0.1,
    "oliver": L("L04") - 0.1,
    "o_dark": w("dark", "L04"),
    "daniel": L("L05") - 0.1,
    "d_pipe": w("pipe", "L05"),
    "sophie": L("L06") - 0.1,
    "s_rattled": w("rattled", "L06"),
    "s_dropped": w("dropped", "L06"),
    "marcus_hmm": L("L07") - 0.12,
    "rooms": L("L07", "end") + 0.3,
    "marcus_end": L("L08") - 0.15,
    "lying": w("lying", "L08"),
    "recap": L("L09") - 0.1,
    "n_kitchen": w("kitchen", "L09"),
    "n_basement": w("basement", "L09"),
    "n_laundry": w("laundry", "L09"),
    "n_fit": w("one", "L09"),
    "final": L("L10") - 0.1,
    "freeze": L("L10", "end") + 0.08,
}
ROOM_LEN = (B["marcus_end"] - B["rooms"]) / 3
B["room_laundry"] = B["rooms"]
B["room_basement"] = B["rooms"] + ROOM_LEN
B["room_kitchen"] = B["rooms"] + 2 * ROOM_LEN
DURATION = round(B["freeze"] + 5.0, 2)
BPM = 84
# lightning strikes (global s). Rooms with windows light up; the basement never does (thunder only).
STRIKES = [0.0, 1.3, B["detective"] - 0.2, B["power"] + 0.1, B["o_dark"] - 0.6, B["s_rattled"] - 0.1,
           B["room_laundry"] + 0.9, B["room_basement"] + 1.0, B["room_kitchen"] + 0.9, B["final"] + 0.5]


def seg(t0, t1, src, fx=()):
    return {"t0": t0, "t1": t1, "src": src, "src_t": t0, "fx": list(fx)}


def push(t0, t1, a=1.0, b=1.06, cx=0.5, cy=0.5):
    return {"fx": "zoom", "keys": [(t0, a, cx, cy), (t1, b, cx, cy, "lin")]}


WHIP = 0.2
SEGMENTS = [
    seg(0.0, B["hook_lineup"], "ext", [{"fx": "shake", "t0": 0.0, "t1": 0.45, "amp": 18}]),
    seg(B["hook_lineup"], B["hook_marcus"], "hook_lineup", [push(B["hook_lineup"], B["hook_marcus"], 1.0, 1.08)]),
    seg(B["hook_marcus"], B["safe"], "hook_marcus", [push(B["hook_marcus"], B["safe"], 1.0, 1.05)]),
    seg(B["safe"], B["harrison_ms"], "study_safe", [push(B["safe"], B["harrison_ms"], 1.0, 1.1)]),
    seg(B["harrison_ms"], B["foyer"], "study"),
    seg(B["foyer"], B["oliver"], "foyer_wide", [push(B["foyer"], B["oliver"], 1.0, 1.05, 0.55)]),
    seg(B["oliver"], B["daniel"], "cu_oliver", [{"fx": "whip", "t": B["oliver"], "dur": WHIP, "dir": -1}]),
    seg(B["daniel"], B["sophie"], "cu_daniel", [{"fx": "whip", "t": B["daniel"], "dur": WHIP, "dir": -1}]),
    seg(B["sophie"], B["marcus_hmm"], "cu_sophie", [{"fx": "whip", "t": B["sophie"], "dur": WHIP, "dir": -1}]),
    seg(B["marcus_hmm"], B["rooms"], "cu_marcus", [push(B["marcus_hmm"], B["rooms"], 1.0, 1.06, 0.5, 0.4)]),
    # the investigation: three rooms, same length, same framing, same camera move -> nobody singled out
    seg(B["room_laundry"], B["room_basement"], "room_laundry"),
    seg(B["room_basement"], B["room_kitchen"], "room_basement"),
    seg(B["room_kitchen"], B["marcus_end"], "room_kitchen"),
    seg(B["marcus_end"], B["recap"], "marcus_end", [push(B["marcus_end"], B["recap"], 1.0, 1.08, 0.5, 0.4)]),
    {"t0": B["recap"], "t1": B["final"], "src": "split", "dir": "v", "gap": 10, "split": [
        {"src": "panel_kitchen", "src_t": B["recap"]},
        {"src": "panel_basement", "src_t": B["recap"]},
        {"src": "panel_laundry", "src_t": B["recap"]}]},
    seg(B["final"], DURATION, "final_lineup",
        [{"fx": "freeze", "t0": B["freeze"], "t1": DURATION + 1, "tint": "#2A3A6A", "amount": 0.22}]),
]

sys.path.insert(0, str(HERE))
import gfx  # noqa: E402

OVERLAYS = [
    {"type": "custom", "t0": B["freeze"], "t1": DURATION + 1, "anim": 0.2, "draw": gfx.end_card(B["freeze"])},
]
CAPTIONS = {"words": WORDS, "speakers": True,
            "emphasis": ["impossible", "gone", "nine", "nobody", "lightning", "window", "thunder", "lying", "kitchen",
                         "basement", "laundry", "fit"],
            # captions sit low (on torsos) in close-ups and on the panels' gap line in the recap
            "pos": [(B["foyer"], B["rooms"], 0.86), (B["marcus_end"], B["recap"], 0.86), (B["recap"], B["final"], 0.955),
                    (B["final"], B["freeze"], 0.86)],
            "max_words": 4}
AUDIO = "audio/mix_master.wav"
