"""EDL - VIDEO_004 "The Day Evil Disappeared". Dramatic, date-stamped. Beats from word timing."""
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
    "midnight": w("midnight", "L01") + 0.35,      # clock hits 12, bell, golden wave
    "prison": L("L02") - 0.25,
    "gone": w("gone", "L02"),
    "news": L("L03") - 0.2,
    "p1": w("prisons", "L03"), "p2": w("wars", "L03"), "p3": w("nobody", "L03"),
    "office": L("L04") - 0.3,
    "cu_marcus": L("L05") - 0.25,
    "hat_drop": w("anymore", "L05"),
    "summer": L("L06") - 0.5,
    "fade": L("L07"),
    "winter": L("L08") - 0.1,
    "coat": w("thank", "L08"),
    "light": L("L09") - 0.1,
    "white": L("L09", "end") + 0.15,
    "park": L("L09", "end") + 0.55,
    "cu_lily": L("L10") - 0.2,
    "cu_marcus2": L("L11") - 0.25,
    "two_shot": L("L12") - 0.2,
    "final": L("L13") - 0.35,
    "end": L("L13", "end") + 0.3,
}
DURATION = round(B["end"] + 4.3, 2)
BPM = 66

# date stamps at the top: (time, big line, small line or callable(t) -> str)
def _midnight_clock(t):
    if t < B["midnight"]:
        sec = 60 + int((t - B["midnight"]) // 1)
        return f"23:59:{max(sec, 50):02d}"
    return "00:00:00"


STAMPS = [
    (0.25, "DECEMBER 31, 2030", _midnight_clock),
    (B["midnight"], "JANUARY 1, 2031", _midnight_clock),
    (B["prison"] + 0.15, "JANUARY 1, 2031", "06:12 AM"),
    (B["news"] + 0.15, "JANUARY 2, 2031", "DAY 2"),
    (B["office"] + 0.15, "MARCH 14, 2031", "DAY 72"),
    (B["summer"] + 0.2, "AUGUST 9, 2033", "YEAR 3"),
    (B["winter"] + 0.1, "DECEMBER 20, 2035", "YEAR 5"),
    (B["park"] + 0.3, "APRIL 2, 2041", "YEAR 10"),
    (B["final"] + 0.4, "TODAY", None),
]


def seg(t0, t1, src, fx=()):
    return {"t0": t0, "t1": t1, "src": src, "src_t": t0, "fx": list(fx)}


def push(t0, t1, a=1.0, b=1.06, cx=0.5, cy=0.5):
    return {"fx": "zoom", "keys": [(t0, a, cx, cy), (t1, b, cx, cy, "lin")]}


SEGMENTS = [
    seg(0.0, B["prison"], "city", [push(0.0, B["prison"], 1.0, 1.1, 0.5, 0.36),
                                   {"fx": "flash", "t": B["midnight"], "dur": 0.35, "color": "#FFF2C8"}]),
    seg(B["prison"], B["news"], "prison", [push(B["prison"], B["news"], 1.0, 1.06)]),
    seg(B["news"], B["office"], "news"),
    seg(B["office"], B["cu_marcus"], "office", [push(B["office"], B["cu_marcus"], 1.0, 1.05, 0.45, 0.6)]),
    seg(B["cu_marcus"], B["summer"], "cu_marcus", [push(B["cu_marcus"], B["summer"], 1.0, 1.1, 0.5, 0.35)]),
    seg(B["summer"], B["park"], "street", [push(B["summer"], B["light"], 1.0, 1.04),
                                           {"fx": "zoom", "keys": [(B["light"], 1.04, 0.5, 0.5),
                                                                   (B["park"], 1.5, 0.82, 0.58, "in")]}]),
    seg(B["park"], B["cu_lily"], "park_wide", [push(B["park"], B["cu_lily"], 1.0, 1.05, 0.5, 0.65)]),
    seg(B["cu_lily"], B["cu_marcus2"], "cu_lily", [push(B["cu_lily"], B["cu_marcus2"], 1.0, 1.06, 0.5, 0.45)]),
    seg(B["cu_marcus2"], B["two_shot"], "cu_marcus2", [push(B["cu_marcus2"], B["two_shot"], 1.0, 1.12, 0.5, 0.4)]),
    seg(B["two_shot"], B["final"], "two_shot", [push(B["two_shot"], B["final"], 1.0, 1.05, 0.5, 0.55)]),
    seg(B["final"], DURATION, "final", [{"fx": "zoom", "keys": [(B["final"], 1.25, 0.55, 0.62),
                                                               (DURATION, 1.0, 0.5, 0.5, "out")]}]),
]

sys.path.insert(0, str(HERE))
import gfx  # noqa: E402

OVERLAYS = [
    {"type": "custom", "t0": 0.0, "t1": DURATION + 1, "anim": 0.01, "draw": gfx.date_stamps(STAMPS)},
    {"type": "custom", "t0": B["white"] - 0.6, "t1": B["park"] + 0.6, "anim": 0.01,
     "draw": gfx.white_dip(B["white"], B["park"])},
    {"type": "custom", "t0": B["end"] - 0.2, "t1": DURATION + 1, "anim": 0.01, "draw": gfx.end_card(B["end"])},
]
CAPTIONS = {"words": WORDS, "speakers": True,
            "emphasis": ["midnight", "evil", "gone", "nothing", "perfect", "fade", "choice", "weather", "light",
                         "hero", "chooses", "good", "heroes"],
            "pos": [(0.0, DURATION, 0.84)], "max_words": 4}
AUDIO = "audio/mix_master.wav"
