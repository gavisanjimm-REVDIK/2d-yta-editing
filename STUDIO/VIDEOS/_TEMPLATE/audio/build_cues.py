"""build_cues.py - SFX/ambience cues from EDL beat times (rename edit file below) -> cues.json (read by mix.py)."""
import importlib.util
import json
from pathlib import Path

V = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("edl", next(V.glob("edit_*.py")))
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

cues = {
    "duration": E.DURATION,
    "music_db": -8.0,
    "duck_db": -10.0,
    "bus_db": {"sfx": -6.0, "amb": -16.0},
    "music_gates": [],          # [[t0, t1]] strategic silence
    "sfx": [
        # {"t": E.BEATS["turn"] - 0.2, "name": "whoosh_fast", "gain_db": -4, "note": "whip"},
        # {"t": 0.0, "name": "amb_room", "bus": "amb", "dur": E.DURATION},
    ],
}
(V / "audio" / "cues.json").write_text(json.dumps(cues, indent=2))
print("cues ->", V / "audio" / "cues.json")
