"""build_cues.py - VIDEO_003 SFX/ambience cues from EDL beats -> cues.json."""
import importlib.util
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V))
spec = importlib.util.spec_from_file_location("edl", V / "edit_video003.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
B, D = E.B, E.DURATION

sfx = [
    {"t": 0.0, "name": "amb_tomb", "bus": "amb", "dur": D, "loop": True, "gain_db": 0, "fade_in": 0.05, "fade_out": 0.5},
    {"t": 0.0, "name": "whoosh_fast", "gain_db": -4, "note": "frame-0 dash"},
    {"t": 0.15, "name": "meow", "gain_db": -10},
]
for k in range(9):  # running footsteps until the slam
    sfx.append({"t": 0.25 + k * 0.42, "name": "footstep_hard", "gain_db": -9})
sfx += [
    {"t": B["slam"] + 0.05, "name": "stone_slam", "gain_db": 0, "note": "trapped"},
    {"t": B["chamber"] + 0.05, "name": "comedy_boing", "gain_db": -16, "note": "cat squeezes out"},
    {"t": B["mummy_up"] - 0.1, "name": "sarcophagus_creak", "gain_db": -4},
    {"t": B["cu_mummy"] - 0.1, "name": "whoosh_fast", "gain_db": -10},
    {"t": B["door1"] - 0.1, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["door2"] - 0.1, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["door3"] - 0.1, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["door3"] + 1.2, "name": "water_drip", "gain_db": -10, "note": "quiet clue"},
    {"t": B["door3"] + 2.6, "name": "water_drip", "gain_db": -12},
    {"t": B["pick"] + 0.1, "name": "ui_pop", "gain_db": -8},
    {"t": B["carved"], "name": "chop", "gain_db": -16, "note": "chisel taps"},
    {"t": B["lunch"] + 0.1, "name": "cart_roll", "gain_db": -6},
    {"t": B["roar"] - 0.3, "name": "door_open", "gain_db": -14, "note": "hatch"},
    {"t": B["roar"], "name": "lion_roar", "gain_db": 2, "note": "LUNCH TIME"},
    {"t": B["gulp"] + 0.3, "name": "pudding_plop", "gain_db": -12, "note": "gulp"},
    {"t": B["n_fire"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_lions"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_flood"], "name": "ui_pop", "gain_db": -12},
    {"t": B["final"], "name": "riser_tension", "gain_db": -14},
    {"t": B["freeze"] - 0.02, "name": "sting_mystery", "gain_db": 0},
    {"t": B["freeze"] + 0.6, "name": "ui_pop", "gain_db": -8},
]
cues = {"duration": D, "music_db": 0.0, "duck_db": -8.0, "bus_db": {"sfx": -7.0, "amb": -4.0}, "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
