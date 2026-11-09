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
    # rain: loud outside, muffled inside, almost gone underground (no windows down there)
    amb(0.0, B["basement_hook"] + 0.1, 0.0),
    amb(B["basement_hook"], B["safe"], -16, fi=0.02),
    amb(B["safe"], B["descend"], -7),
    amb(B["descend"], B["daniel_ecu"], -16),
    amb(B["daniel_ecu"], D, -8),
    {"t": 0.0, "name": "thunder_clap", "gain_db": 2.0, "note": "frame-0 lightning"},
    {"t": 1.25, "name": "thunder_rumble", "gain_db": -6},
    {"t": B["basement_hook"] - 0.05, "name": "whoosh_fast", "gain_db": -6, "note": "zoom into the house"},
    {"t": B["basement_hook"] + 0.15, "name": "flashlight_click", "gain_db": -2},
    {"t": B["safe"] - 0.05, "name": "safe_creak", "gain_db": -6},
    {"t": B["power"] + 0.1, "name": "thunder_clap", "gain_db": -3, "note": "lightning in study window"},
    {"t": B["foyer"] - 0.1, "name": "impact_frame", "gain_db": -10},
    {"t": B["marcus_q"] + 0.3, "name": "pencil_scribble", "gain_db": -8},
    {"t": B["oliver"] - 0.12, "name": "whoosh_fast", "gain_db": -8},
    {"t": B["daniel"] - 0.12, "name": "whoosh_fast", "gain_db": -8},
    {"t": B["lightning_word"] + 0.05, "name": "thunder_rumble", "gain_db": -6},
    {"t": B["sophie"] - 0.12, "name": "whoosh_fast", "gain_db": -8},
    {"t": B["thunder_word"] - 0.1, "name": "thunder_clap", "gain_db": -6},
    {"t": B["turn"] + 0.1, "name": "swish_cloth", "gain_db": -10},
    {"t": B["descend"] + 0.05, "name": "door_open", "gain_db": -12},
    {"t": B["descend"] + 0.2, "name": "stairs_wood", "gain_db": -6},
    {"t": B["explain"] + 0.6, "name": "thunder_rumble", "gain_db": -16, "note": "heard, not seen (no windows)"},
    {"t": B["daniel_ecu"] - 0.02, "name": "impact_heavy", "gain_db": -2, "note": "reveal hit, music silent"},
    {"t": B["daniel_ecu"] + 0.2, "name": "heartbeat", "gain_db": -4},
    {"t": B["n_oliver"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_sophie"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_daniel"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_daniel"] + 1.2, "name": "thunder_rumble", "gain_db": -10},
    {"t": B["zoom"], "name": "riser_tension", "gain_db": -14},
    {"t": B["freeze"] - 0.02, "name": "sting_mystery", "gain_db": 0, "note": "freeze + question"},
    {"t": B["freeze"] + 0.6, "name": "ui_pop", "gain_db": -8},
]
cues = {"duration": D, "music_db": -2.0, "duck_db": -8.0, "bus_db": {"sfx": -5.0, "amb": -7.0},
        "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
