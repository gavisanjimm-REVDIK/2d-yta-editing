"""build_cues.py - VIDEO_004 SFX/ambience cues from EDL beats -> cues.json."""
import importlib.util
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V))
spec = importlib.util.spec_from_file_location("edl", V / "edit_video004.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
import gfx  # noqa: E402

B, D = E.B, E.DURATION


def amb(name, t0, t1, gain, fi=0.4, fo=0.6):
    return {"t": t0, "name": name, "bus": "amb", "dur": t1 - t0, "loop": True, "gain_db": gain, "fade_in": fi, "fade_out": fo}


sfx = [
    amb("amb_city", 0.0, B["prison"], -6),
    amb("amb_room", B["prison"], B["summer"], -4),
    amb("birds", B["summer"], B["fade"] + 2.5, -2, fo=2.0),
    amb("amb_wind", B["winter"] - 0.5, B["light"] + 0.6, -6, fi=1.0),
    amb("birds", B["park"], D, -10, fi=1.5, fo=2.0),
    amb("amb_wind", B["park"], D, -16, fi=1.5),
    {"t": B["midnight"] - 0.05, "name": "clock_bell", "gain_db": 0, "note": "midnight"},
    {"t": B["midnight"] + 0.05, "name": "riser_tension", "gain_db": -20},
]
for k, dt in enumerate((0.05, 0.35, 0.75, 1.2, 1.6)):
    sfx.append({"t": B["midnight"] + dt, "name": "firework_pop", "gain_db": -12 - 2 * (k % 2), "pan": 0.4 * (-1) ** k})
for t0, big, small in E.STAMPS:  # one key strike per typed character of each date stamp
    for i in range(len(big)):
        if big[i] != " ":
            sfx.append({"t": t0 + i / gfx.CPS, "name": "type_key", "gain_db": -16, "pan": 0.15 * ((i % 3) - 1)})
    sfx.append({"t": t0 + len(big) / gfx.CPS + 0.05, "name": "ui_ding", "gain_db": -28})
sfx += [
    {"t": B["gone"] - 0.6, "name": "cell_slide", "gain_db": -4},
    {"t": B["p1"] - 0.05, "name": "paper_slap", "gain_db": -4},
    {"t": B["p2"] - 0.05, "name": "paper_slap", "gain_db": -4},
    {"t": B["p3"] - 0.05, "name": "paper_slap", "gain_db": -4},
    {"t": B["hat_drop"] + 0.6, "name": "impact_soft", "gain_db": -16, "note": "hat into the box"},
    {"t": B["light"] + 0.4, "name": "ui_tick", "gain_db": -14, "note": "street lamp clicks on"},
    {"t": B["white"] - 0.5, "name": "whoosh_slow", "gain_db": -16},
    {"t": B["two_shot"] + 1.6, "name": "heartbeat", "gain_db": -12},
]
cues = {"duration": D, "music_db": 1.0, "duck_db": -7.0, "bus_db": {"sfx": -7.0, "amb": -8.0}, "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
