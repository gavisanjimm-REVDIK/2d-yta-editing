"""build_cues.py - VIDEO_001 SFX/ambience cues from EDL beats -> cues.json."""
import importlib.util
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V))
spec = importlib.util.spec_from_file_location("edl", V / "edit_video001.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
B = E.B
D = E.DURATION


def amb(t0, t1, gain, name="amb_rain", fi=0.05, fo=0.3):
    return {"t": t0, "name": name, "bus": "amb", "dur": t1 - t0, "loop": True, "gain_db": gain,
            "fade_in": fi, "fade_out": fo, "offset": (t0 * 1.7) % 6}


sfx = [
    # rain: loud outside, muffled indoors, almost gone underground (no windows down there)
    amb(0.0, B["hook_lineup"] + 0.1, 0.0),
    amb(B["hook_lineup"], B["room_basement"], -8, fi=0.02),
    amb(B["room_basement"], B["room_kitchen"], -18, fi=0.02, fo=0.05),
    amb(B["room_kitchen"], D, -8, fi=0.05),
    {"t": 0.0, "name": "thunder_clap", "gain_db": 2.0, "note": "frame-0 lightning"},
    {"t": 1.3, "name": "thunder_rumble", "gain_db": -6},
    {"t": B["hook_lineup"] - 0.12, "name": "whoosh_fast", "gain_db": -6},
    {"t": B["detective"] - 0.2, "name": "thunder_clap", "gain_db": -8},
    {"t": B["detective"] + 0.2, "name": "swish_cloth", "gain_db": -8, "note": "hat tip"},
    {"t": B["safe"] - 0.05, "name": "safe_creak", "gain_db": -6},
    {"t": B["power"] + 0.1, "name": "thunder_clap", "gain_db": -4},
    {"t": B["foyer"] - 0.05, "name": "impact_frame", "gain_db": -12},
    {"t": B["o_dark"] - 0.6, "name": "thunder_rumble", "gain_db": -8},
    {"t": B["oliver"] - 0.12, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["daniel"] - 0.12, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["sophie"] - 0.12, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["s_rattled"] - 0.1, "name": "thunder_clap", "gain_db": -6},
    {"t": B["marcus_hmm"] + 0.3, "name": "pencil_scribble", "gain_db": -9},
    # the investigation: same sounds in every room (footsteps + magnifier/flashlight + thunder)
    {"t": B["room_laundry"], "name": "footstep_hard", "gain_db": -10},
    {"t": B["room_laundry"] + 0.9, "name": "thunder_clap", "gain_db": -6},
    {"t": B["room_basement"], "name": "stairs_wood", "gain_db": -8},
    {"t": B["room_basement"] + 0.15, "name": "flashlight_click", "gain_db": -4},
    {"t": B["room_basement"] + 1.0, "name": "thunder_clap", "gain_db": -12, "note": "heard, not seen"},
    {"t": B["room_kitchen"], "name": "footstep_hard", "gain_db": -10},
    {"t": B["room_kitchen"] + 0.9, "name": "thunder_clap", "gain_db": -6},
    {"t": B["lying"] - 0.1, "name": "swish_cloth", "gain_db": -8},
    {"t": B["lying"] + 0.15, "name": "impact_frame", "gain_db": -8},
    {"t": B["n_kitchen"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_basement"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_laundry"], "name": "ui_pop", "gain_db": -12},
    {"t": B["final"] + 0.5, "name": "thunder_rumble", "gain_db": -10},
    {"t": B["final"], "name": "riser_tension", "gain_db": -14},
    {"t": B["freeze"] - 0.02, "name": "sting_mystery", "gain_db": 0},
    {"t": B["freeze"] + 0.6, "name": "ui_pop", "gain_db": -8},
]
cues = {"duration": D, "music_db": -2.0, "duck_db": -8.0, "bus_db": {"sfx": -5.0, "amb": -7.0},
        "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
