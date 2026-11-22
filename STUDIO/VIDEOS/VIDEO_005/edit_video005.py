"""EDL - VIDEO_005 "Protists Part 1: Excavata and the SAR Clade" (educational explainer).
One segment per narration line (job s_Lxx). Source: PSHS Biology 3, Learning Guide 9.2."""
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
BPM = 92
SECTIONS = [("L01", "THE CASE: GIARDIA"), ("L05", "WHAT IS A PROTIST?"), ("L14", "SUPERGROUP 1 · EXCAVATA"),
            ("L17", "EXCAVATA › DIPLOMONADS"), ("L21", "EXCAVATA › PARABASALIDS"), ("L26", "EXCAVATA › EUGLENOZOANS"),
            ("L33", "SUPERGROUP 2 · SAR CLADE"), ("L36", "SAR › STRAMENOPILES"), ("L39", "SAR › ALVEOLATES"),
            ("L46", "SAR › RHIZARIANS"), ("L50", "CASE SUMMARY")]
SECTION_T = [(bounds(lid)[0], name) for lid, name in SECTIONS]

SEGMENTS = []
for lid in IDS:
    t0, t1 = bounds(lid)
    fx = []
    if lid in ("L14", "L34"):
        fx.append({"fx": "flash", "t": t0, "dur": 0.15, "color": "#FFFFFF"})
    SEGMENTS.append({"t0": t0, "t1": t1, "src": "s_" + lid, "src_t": t0, "fx": fx})

sys.path.insert(0, str(HERE))
import gfx  # noqa: E402

OVERLAYS = [{"type": "custom", "t0": 0.0, "t1": DURATION + 1, "anim": 0.01, "draw": gfx.breadcrumb(SECTION_T)}]
CAPTIONS = {"words": WORDS, "speakers": False, "emphasis": [], "pos": [(0.0, DURATION, 0.875)], "max_words": 5}
AUDIO = "audio/mix_master.wav"
