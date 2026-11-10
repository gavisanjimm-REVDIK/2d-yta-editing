"""EDL - VIDEO_002 "Death by Pudding". Beats from narration word timing.

Creator-only answer (never shown): CEDRIC. He says his car "pulled in right before yours, detective", but through the
hall window his red car is buried under a deep mound of snow (parked for hours) while Marcus's blue car has only a
thin dusting. Also: Marcus walks in covered in snow, Cedric has none on him, and the doormat shows one set of wet
footprints. Red herrings: Gaston's cleaver and tears (onions), Miss Prim's motive (the will).
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
    "poisoned": w("poisoned", "L01"),
    "trio": L("L01", "end") + 0.2,
    "one_killer": w("one", "L02"),
    "ext": w("and", "L02") - 0.05,
    "arrive": L("L03") - 0.25,
    "nobody": w("nobody", "L03"),
    "gaston": L("L04") - 0.1,
    "crying": w("crying", "L04"),
    "prim": L("L05") - 0.1,
    "cat_word": w("cat", "L05"),
    "cedric": L("L06") - 0.1,
    "yours": w("yours", "L06"),
    "marcus_hmm": L("L07") - 0.15,
    "rooms": L("L07", "end") + 0.25,
    "marcus_end": L("L08") - 0.15,
    "closed": w("closed", "L08"),
    "recap": L("L09") - 0.1,
    "n_gaston": w("gaston", "L09"),
    "n_prim": w("prim", "L09"),
    "n_cedric": w("cedric", "L09"),
    "final": L("L10") - 0.1,
    "not_cat": w("cat", "L10"),
    "freeze": L("L10", "end") + 0.08,
}
ROOM_LEN = (B["marcus_end"] - B["rooms"]) / 3
B["room_kitchen"] = B["rooms"]
B["room_library"] = B["rooms"] + ROOM_LEN
B["room_hall"] = B["rooms"] + 2 * ROOM_LEN
DURATION = round(B["freeze"] + 5.0, 2)
BPM = 96


def seg(t0, t1, src, fx=()):
    return {"t0": t0, "t1": t1, "src": src, "src_t": t0, "fx": list(fx)}


def push(t0, t1, a=1.0, b=1.06, cx=0.5, cy=0.5):
    return {"fx": "zoom", "keys": [(t0, a, cx, cy), (t1, b, cx, cy, "lin")]}


WHIP = 0.2
SEGMENTS = [
    seg(0.0, B["trio"], "dining", [{"fx": "shake", "t0": B["poisoned"], "t1": B["poisoned"] + 0.4, "amp": 14},
                                   {"fx": "flash", "t": B["poisoned"], "dur": 0.1}]),
    seg(B["trio"], B["ext"], "trio", [{"fx": "zoom", "keys": [(B["trio"], 1.0, 0.5, 0.5), (B["one_killer"] - 0.05, 1.0, 0.5, 0.5),
                                                               (B["one_killer"] + 0.1, 1.12, 0.5, 0.45, "out"),
                                                               (B["ext"], 1.15, 0.5, 0.45, "lin")]}]),
    seg(B["ext"], B["arrive"], "ext", [push(B["ext"], B["arrive"], 1.0, 1.06, 0.5, 0.6)]),
    seg(B["arrive"], B["gaston"], "arrive", [push(B["arrive"], B["gaston"], 1.0, 1.04)]),
    seg(B["gaston"], B["prim"], "cu_gaston", [{"fx": "whip", "t": B["gaston"], "dur": WHIP, "dir": -1}]),
    seg(B["prim"], B["cedric"], "cu_prim", [{"fx": "whip", "t": B["prim"], "dur": WHIP, "dir": -1}]),
    seg(B["cedric"], B["marcus_hmm"], "cu_cedric", [{"fx": "whip", "t": B["cedric"], "dur": WHIP, "dir": -1}]),
    seg(B["marcus_hmm"], B["rooms"], "cu_marcus", [push(B["marcus_hmm"], B["rooms"], 1.0, 1.06, 0.5, 0.4)]),
    # the search: three rooms, equal length, same camera move, same sounds -> nobody singled out
    seg(B["room_kitchen"], B["room_library"], "room_kitchen"),
    seg(B["room_library"], B["room_hall"], "room_library"),
    seg(B["room_hall"], B["marcus_end"], "room_hall"),
    seg(B["marcus_end"], B["recap"], "marcus_end", [push(B["marcus_end"], B["recap"], 1.0, 1.06, 0.5, 0.4)]),
    {"t0": B["recap"], "t1": B["final"], "src": "split", "dir": "v", "gap": 10, "split": [
        {"src": "panel_kitchen", "src_t": B["recap"]},
        {"src": "panel_library", "src_t": B["recap"]},
        {"src": "panel_hall", "src_t": B["recap"]}]},
    seg(B["final"], DURATION, "final_lineup",
        [{"fx": "freeze", "t0": B["freeze"], "t1": DURATION + 1, "tint": "#2A3A6A", "amount": 0.2}]),
]

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "VIDEO_001"))
import gfx  # noqa: E402  (VIDEO_001 end card)

OVERLAYS = [
    {"type": "custom", "t0": B["freeze"], "t1": DURATION + 1, "anim": 0.2,
     "draw": gfx.end_card(B["freeze"], "WHO IS THE KILLER?")},
]
CAPTIONS = {"words": WORDS, "speakers": True,
            "emphasis": ["poisoned", "killer", "clue", "misses", "poisoner", "pudding", "onions", "crying", "will", "cat",
                         "yours", "closed", "everything", "arrived"],
            "pos": [(B["arrive"], B["rooms"], 0.86), (B["marcus_end"], B["recap"], 0.86), (B["recap"], B["final"], 0.955),
                    (B["final"], B["freeze"], 0.86)],
            "max_words": 4}
AUDIO = "audio/mix_master.wav"
