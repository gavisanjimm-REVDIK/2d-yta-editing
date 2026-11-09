"""build_cues.py - SFX/ambience cues from EDL beat times -> cues.json (read by mix.py)."""
import importlib.util
import json
from pathlib import Path

V = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("edl", V / "edit_video000.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

cues = {
    "duration": E.DURATION,
    "music_db": -8.0,
    "duck_db": -10.0,
    "bus_db": {"sfx": -6.0, "amb": -16.0},
    "music_gates": [[E.LAMP_ON - 0.4, E.LAMP_ON + 0.9]],  # strategic silence before the reveal
    "sfx": [
        {"t": 0.0, "name": "amb_room", "bus": "amb", "dur": E.DURATION, "note": "room tone"},
        {"t": 0.35, "name": "ui_pop", "gain_db": -6, "note": "chip"},
        {"t": E.BEATS["until"] - 0.25, "name": "whoosh_fast", "gain_db": -4, "note": "cut to face"},
        {"t": E.LAMP_ON - 0.05, "name": "ui_tick", "gain_db": 0, "note": "lamp switch click"},
        {"t": E.LAMP_ON + 0.9, "name": "impact_frame", "gain_db": -2, "note": "flash cut"},
    ],
}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json")
