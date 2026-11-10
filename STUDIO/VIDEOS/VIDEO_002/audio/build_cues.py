"""build_cues.py - VIDEO_002 SFX/ambience cues from EDL beats -> cues.json."""
import importlib.util
import json
import sys
from pathlib import Path

V = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(V))
spec = importlib.util.spec_from_file_location("edl", V / "edit_video002.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
B, D = E.B, E.DURATION


def amb(t0, t1, gain, name="amb_wind", fi=0.05, fo=0.3):
    return {"t": t0, "name": name, "bus": "amb", "dur": t1 - t0, "loop": True, "gain_db": gain,
            "fade_in": fi, "fade_out": fo, "offset": (t0 * 1.3) % 5}


sfx = [
    amb(0.0, B["ext"], -14),                       # blizzard muffled indoors
    amb(B["ext"], B["arrive"] + 1.0, 0.0, fi=0.02),  # outside: full wind
    amb(B["arrive"] + 1.0, D, -14),
    amb(0.0, D, -10, name="amb_room"),
    {"t": 0.0, "name": "spoon_clatter", "gain_db": -2, "note": "frame-0 event"},
    {"t": 0.05, "name": "pudding_plop", "gain_db": -6},
    {"t": B["poisoned"] - 0.02, "name": "impact_frame", "gain_db": -3},
    {"t": B["trio"] - 0.12, "name": "whoosh_fast", "gain_db": -8},
    {"t": B["one_killer"], "name": "impact_soft", "gain_db": -6},
    {"t": B["ext"] - 0.1, "name": "whoosh_slow", "gain_db": -10},
    {"t": B["arrive"], "name": "door_open", "gain_db": -6},
    {"t": B["arrive"] + 0.05, "name": "wind_gust", "gain_db": -4},
    {"t": B["arrive"] + 0.3, "name": "footstep_hard", "gain_db": -10},
    {"t": B["arrive"] + 0.65, "name": "footstep_hard", "gain_db": -10},
    {"t": B["arrive"] + 1.3, "name": "swish_cloth", "gain_db": -6, "note": "brushing snow off"},
    {"t": B["arrive"] + 1.6, "name": "swish_cloth", "gain_db": -8},
    {"t": B["gaston"] - 0.12, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["gaston"] + 1.6, "name": "chop", "gain_db": -12},
    {"t": B["crying"] + 0.4, "name": "comedy_sting", "gain_db": -8, "note": "sob gag"},
    {"t": B["prim"] - 0.12, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["prim"] + 1.4, "name": "typewriter", "gain_db": -14},
    {"t": B["cat_word"] + 0.05, "name": "meow", "gain_db": -4},
    {"t": B["cedric"] - 0.12, "name": "whoosh_fast", "gain_db": -9},
    {"t": B["cedric"] + 0.3, "name": "keys_jingle", "gain_db": -8},
    {"t": B["yours"] - 0.1, "name": "keys_jingle", "gain_db": -12},
    {"t": B["marcus_hmm"] + 0.3, "name": "pencil_scribble", "gain_db": -9},
    # the search: same treatment in every room
    {"t": B["room_kitchen"], "name": "footstep_hard", "gain_db": -10},
    {"t": B["room_kitchen"] + 1.0, "name": "ui_tick", "gain_db": -12},
    {"t": B["room_library"], "name": "footstep_hard", "gain_db": -10},
    {"t": B["room_library"] + 1.0, "name": "ui_tick", "gain_db": -12},
    {"t": B["room_hall"], "name": "footstep_hard", "gain_db": -10},
    {"t": B["room_hall"] + 1.0, "name": "ui_tick", "gain_db": -12},
    {"t": B["closed"] - 0.1, "name": "swish_cloth", "gain_db": -8},
    {"t": B["closed"] + 0.15, "name": "impact_frame", "gain_db": -8},
    {"t": B["n_gaston"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_prim"], "name": "ui_pop", "gain_db": -12},
    {"t": B["n_cedric"], "name": "ui_pop", "gain_db": -12},
    {"t": B["not_cat"] + 0.15, "name": "meow", "gain_db": -6, "note": "offended cat"},
    {"t": B["final"], "name": "riser_tension", "gain_db": -14},
    {"t": B["freeze"] - 0.02, "name": "sting_mystery", "gain_db": 0},
    {"t": B["freeze"] + 0.6, "name": "ui_pop", "gain_db": -8},
]
cues = {"duration": D, "music_db": -4.0, "duck_db": -8.0, "bus_db": {"sfx": -5.0, "amb": -1.0}, "music_gates": [], "sfx": sfx}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json", len(sfx), "events")
