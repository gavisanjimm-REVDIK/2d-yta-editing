"""EDL - VIDEO_006 "Protists Part 2: Archaeplastida and Unikonta" (educational explainer).
One segment per narration line (job s_Lxx). Source: PSHS Biology 3, Learning Guide 9.3."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
T = json.loads((HERE / "audio" / "timing.json").read_text())
WORDS = T["words"]
IDS = [l["id"] for l in T["lines"]]
LINES = {l["id"]: l for l in T["lines"]}


def bounds(lid):
    i = IDS.index(lid)
    t0 = 0.0 if i == 0 else LINES[lid]["start"] - 0.15
    t1 = LINES[IDS[i + 1]]["start"] - 0.15 if i + 1 < len(IDS) else LINES[lid]["end"] + 4.0
    return t0, t1


DURATION = round(bounds(IDS[-1])[1], 2)
BPM = 90
SECTIONS = [("L01", "PROTISTS · PART 2"), ("L03", "SUPERGROUP 3 · ARCHAEPLASTIDA"), ("L10", "ARCHAEPLASTIDA › GLAUCOPHYTES"),
            ("L12", "ARCHAEPLASTIDA › RED ALGAE"), ("L18", "ARCHAEPLASTIDA › GREEN ALGAE"), ("L24", "THINK IT OVER"),
            ("L26", "SUPERGROUP 4 · UNIKONTA"), ("L28", "UNIKONTA › AMOEBOZOA"), ("L35", "UNIKONTA › OPISTHOKONTA"),
            ("L39", "THINK IT OVER"), ("L40", "NAVIGATE: THE CASE"), ("L48", "CASE SUMMARY")]
SECTION_T = [(bounds(lid)[0], name) for lid, name in SECTIONS]
CASE_T = (bounds("L40")[0], bounds("L47")[1])
END_T = LINES["L50"]["end"] + 0.4

SEGMENTS = []
for lid in IDS:
    t0, t1 = bounds(lid)
    fx = []
    if lid in ("L03", "L26", "L40"):
        fx.append({"fx": "flash", "t": t0, "dur": 0.15, "color": "#FFFFFF"})
    SEGMENTS.append({"t0": t0, "t1": t1, "src": "s_" + lid, "src_t": t0, "fx": fx})

sys.path.insert(0, str(HERE))
import gfx  # noqa: E402

STAMPS = [(bounds("L41")[0] + 0.1, bounds("L41")[1], "DECEMBER 22, 2016", "8:24 PM · CABUCGAYAN, BILIRAN"),
          (bounds("L44")[0] + 0.1, bounds("L44")[1], "28°C · 83% HUMIDITY", "WEATHER · HOSPITAL UPDATE")]
HIDE = [(a - 0.05, b + 0.05) for a, b, _, _ in STAMPS] + [(END_T - 0.1, DURATION + 1)]

OVERLAYS = [{"type": "custom", "t0": 0.0, "t1": DURATION + 1, "anim": 0.01, "draw": gfx.breadcrumb(SECTION_T, HIDE)},
            {"type": "custom", "t0": 0.0, "t1": DURATION + 1, "anim": 0.01, "draw": gfx.case_stamps(STAMPS)},
            {"type": "custom", "t0": END_T - 0.1, "t1": DURATION + 1, "anim": 0.2, "draw": gfx.end_card(END_T)}]
CAPTIONS = {"words": WORDS, "speakers": False, "emphasis": [], "pos": [(0.0, DURATION, 0.875)], "max_words": 5}
AUDIO = "audio/mix_master.wav"
