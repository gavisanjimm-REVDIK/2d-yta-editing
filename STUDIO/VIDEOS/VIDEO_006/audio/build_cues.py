"""build_cues.py - VIDEO_006 SFX cues: whoosh on every shot change, pops when labels/bullets/pills appear,
typewriter keys for the case-file stamps, mystery sting + heartbeat for the crime case."""
import importlib.util
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V))
spec = importlib.util.spec_from_file_location("edl", V / "edit_video006.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
from plan import PLAN  # noqa: E402
import anim2d as A  # noqa: E402

D = E.DURATION
sfx = [{"t": 0.0, "name": "amb_room", "bus": "amb", "dur": D, "loop": True, "gain_db": -6, "fade_in": 0.5, "fade_out": 1.0}]
for s in E.SEGMENTS[1:]:
    sfx.append({"t": s["t0"] - 0.12, "name": "whoosh_fast", "gain_db": -16})
for lid, (typ, p) in PLAN.items():
    keys = [lab[2] for lab in p.get("labels", [])] + [at for _, at in p.get("bullets", [])]
    keys += [pl[3] for pl in p.get("pills", [])] + [k[4] for k in p.get("kids", [])]
    keys += [it[4] for it in p.get("items", []) if typ == "rows"] + [it[1] for it in p.get("items", []) if typ == "tiles"]
    keys += [tl[1] for tl in p.get("tiles", [])]
    if p.get("stamp"):
        keys.append(p["stamp"][1])
    for at in keys:
        sfx.append({"t": A.word_t(lid, at), "name": "ui_pop", "gain_db": -15})
    if p.get("stamp"):
        sfx.append({"t": A.word_t(lid, p["stamp"][1]), "name": "impact_soft", "gain_db": -12})
    if typ == "question":
        sfx.append({"t": A.seg_bounds(lid)[0] + 0.1, "name": "ui_ding", "gain_db": -12})
        sfx.append({"t": A.word_t(lid, p["pause"]), "name": "ui_tick", "gain_db": -14})
for lid, words in (("L42", ["oysters", "puso", "isaw", "pitcher", "unfinished", "empty", "broken"]),
                   ("L45", ["parasitic", "plasmodium", "entamoeba", "giardia", "pyrodinium"]),
                   ("L41", ["cabucgayan", "unconscious", "facing"]), ("L34", ["worldwide", "decaying", "leaf", "bark", "plasmodium", "yellow"])):
    for w in words:
        sfx.append({"t": A.word_t(lid, w), "name": "ui_pop" if lid != "L45" else "impact_soft", "gain_db": -14})
sfx.append({"t": A.word_t("L05", "endosymbiosis"), "name": "impact_soft", "gain_db": -12})
for t0, t1, big, small in E.STAMPS:  # typewriter keys as the case stamp types itself
    for i, ch in enumerate(big):
        if ch != " ":
            sfx.append({"t": t0 + i / 26, "name": "type_key", "gain_db": -17, "pan": 0.15 * ((i % 3) - 1)})
c0, c1 = E.CASE_T
sfx.append({"t": c0 + 0.1, "name": "sting_mystery", "gain_db": -10})
sfx.append({"t": A.seg_bounds("L44")[0] + 1.0, "name": "heartbeat", "gain_db": -16})
sfx.append({"t": A.word_t("L41", "december") - 0.3, "name": "amb_wind", "bus": "amb", "dur": 8.0, "gain_db": -8, "fade_in": 0.5, "fade_out": 1.5})
sfx.append({"t": E.END_T, "name": "ui_ding", "gain_db": -10})
for t0, _ in E.SECTION_T[1:]:
    sfx.append({"t": t0, "name": "whoosh_slow", "gain_db": -14})
cues = {"duration": D, "music_db": -4.0, "duck_db": -9.0, "bus_db": {"sfx": 0.0, "amb": -12.0}, "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
