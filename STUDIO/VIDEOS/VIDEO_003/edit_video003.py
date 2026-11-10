"""EDL - VIDEO_003 "The Three Doors of Doom". Beats from word timing.

Creator-only answer (never shown): DOOR 1. The signs were carved 3,000 years ago (the mummy says so):
  door 1 "fire that burns for 1,000 years"  -> burned out 2,000 years ago (cobweb on the handle, no glow)  SAFE
  door 2 "lions that have not eaten in 3 years" -> the classic answer, but they are MUMMY lions: they can't starve,
                                                  they only get hungrier (ROAR) - the sign stays true
  door 3 "a flood that arrives in 3,000 years"  -> it's due right now (water seeping under the door)
"""
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
    "slam": w("slammed", "L02"),
    "chamber": w("slammed", "L02") + 0.55,
    "mummy_up": L("L03") - 0.3,
    "cu_mummy": L("L04") - 0.1,
    "door1": L("L05") - 0.1,
    "door2": L("L06") - 0.1,
    "door3": L("L07") - 0.1,
    "marcus": L("L08") - 0.1,
    "pick": w("pick", "L08"),
    "mummy2": L("L09") - 0.1,
    "carved": w("carved", "L09"),
    "years_ago": w("ago", "L09"),
    "lunch": L("L10") - 0.1,
    "roar": L("L10", "end") + 0.25,
    "gulp": L("L11") - 0.25,
    "recap": L("L12") - 0.1,
    "n_fire": w("fire", "L12"),
    "n_lions": w("lions", "L12"),
    "n_flood": w("flood", "L12"),
    "final": w("which", "L12") - 0.05,
    "freeze": L("L12", "end") + 0.08,
}
DURATION = round(B["freeze"] + 4.0, 2)
BPM = 100
SIGNS = {1: "A FIRE THAT BURNS FOR 1,000 YEARS", 2: "LIONS THAT HAVE NOT EATEN IN 3 YEARS",
         3: "A FLOOD THAT ARRIVES IN 3,000 YEARS"}


def seg(t0, t1, src, fx=()):
    return {"t0": t0, "t1": t1, "src": src, "src_t": t0, "fx": list(fx)}


def push(t0, t1, a=1.0, b=1.06, cx=0.5, cy=0.5):
    return {"fx": "zoom", "keys": [(t0, a, cx, cy), (t1, b, cx, cy, "lin")]}


SEGMENTS = [
    seg(0.0, B["chamber"], "corridor", [{"fx": "shake", "t0": B["slam"] + 0.1, "t1": B["slam"] + 0.7, "amp": 26},
                                        {"fx": "flash", "t": B["slam"] + 0.1, "dur": 0.08}]),
    seg(B["chamber"], B["cu_mummy"], "chamber_wide", [push(B["chamber"], B["cu_mummy"], 1.0, 1.05)]),
    seg(B["cu_mummy"], B["door1"], "cu_mummy", [push(B["cu_mummy"], B["door1"], 1.0, 1.05, 0.5, 0.4)]),
    seg(B["door1"], B["door2"], "door1", [{"fx": "whip", "t": B["door1"], "dur": 0.2, "dir": -1},
                                          push(B["door1"], B["door2"], 1.0, 1.06)]),
    seg(B["door2"], B["door3"], "door2", [{"fx": "whip", "t": B["door2"], "dur": 0.2, "dir": -1},
                                          push(B["door2"], B["door3"], 1.0, 1.06)]),
    seg(B["door3"], B["marcus"], "door3", [{"fx": "whip", "t": B["door3"], "dur": 0.2, "dir": -1},
                                           push(B["door3"], B["marcus"], 1.0, 1.06)]),
    seg(B["marcus"], B["mummy2"], "cu_marcus", [{"fx": "zoom", "keys": [(B["pick"] - 0.05, 1.0, 0.5, 0.4),
                                                                        (B["pick"] + 0.12, 1.1, 0.5, 0.4, "out")]}]),
    seg(B["mummy2"], B["lunch"], "cu_mummy2", [push(B["mummy2"], B["lunch"], 1.0, 1.12, 0.5, 0.4)]),
    seg(B["lunch"], B["gulp"], "lunch", [{"fx": "shake", "t0": B["roar"], "t1": B["roar"] + 0.8, "amp": 30},
                                         {"fx": "zoom", "keys": [(B["roar"] - 0.05, 1.0, 0.45, 0.5),
                                                                 (B["roar"] + 0.15, 1.15, 0.45, 0.5, "out")]}]),
    seg(B["gulp"], B["recap"], "cu_gulp", [push(B["gulp"], B["recap"], 1.05, 1.15, 0.5, 0.4)]),
    {"t0": B["recap"], "t1": B["final"], "src": "split", "dir": "v", "gap": 10, "split": [
        {"src": "panel_1", "src_t": B["recap"]}, {"src": "panel_2", "src_t": B["recap"]},
        {"src": "panel_3", "src_t": B["recap"]}]},
    seg(B["final"], DURATION, "final", [{"fx": "freeze", "t0": B["freeze"], "t1": DURATION + 1, "tint": "#3A2A10",
                                         "amount": 0.18}]),
]

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "VIDEO_001"))
import gfx  # noqa: E402

OVERLAYS = [
    {"type": "custom", "t0": B["freeze"], "t1": DURATION + 1, "anim": 0.2,
     "draw": gfx.end_card(B["freeze"], "WHICH DOOR?", "COMMENT 1, 2 OR 3!")},
]
CAPTIONS = {"words": WORDS, "speakers": True,
            "emphasis": ["thief", "pyramid", "slammed", "shut", "visitor", "fire", "lions", "flood", "thousand",
                         "three", "two", "carved", "first", "mummies", "hungrier", "safe", "which"],
            "pos": [(B["cu_mummy"], B["recap"], 0.86), (B["recap"], B["final"], 0.955), (B["final"], B["freeze"], 0.86)],
            "max_words": 4}
AUDIO = "audio/mix_master.wav"
