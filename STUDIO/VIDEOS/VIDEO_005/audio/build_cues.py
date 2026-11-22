"""build_cues.py - VIDEO_005 SFX cues: whoosh on every shot change, pops when labels/bullets appear."""
import importlib.util
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V))
spec = importlib.util.spec_from_file_location("edl", V / "edit_video005.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
from plan import PLAN  # noqa: E402
import anim2d as A  # noqa: E402

D = E.DURATION
sfx = [{"t": 0.0, "name": "amb_room", "bus": "amb", "dur": D, "loop": True, "gain_db": -6, "fade_in": 0.5, "fade_out": 1.0}]
for s in E.SEGMENTS[1:]:
    sfx.append({"t": s["t0"] - 0.12, "name": "whoosh_fast", "gain_db": -16})
for lid, (typ, p) in PLAN.items():
    keys = [at for _, _, at in p.get("labels", [])] + [at for _, at in p.get("bullets", [])]
    if p.get("stamp"):
        keys.append(p["stamp"][1])
    for at in keys:
        sfx.append({"t": A.word_t(lid, at), "name": "ui_pop", "gain_db": -15})
    if p.get("stamp"):
        sfx.append({"t": A.word_t(lid, p["stamp"][1]), "name": "impact_soft", "gain_db": -12})
for t0, _ in E.SECTION_T[1:]:
    sfx.append({"t": t0, "name": "whoosh_slow", "gain_db": -14})
cues = {"duration": D, "music_db": -4.0, "duck_db": -9.0, "bus_db": {"sfx": -7.0, "amb": -20.0}, "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
