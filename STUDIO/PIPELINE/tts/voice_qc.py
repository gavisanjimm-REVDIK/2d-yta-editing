"""voice_qc.py - re-transcribe final narration and compare to script. Writes qc/voice_qc.json.

Usage: python voice_qc.py VIDEO_000
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audio"))
import dsp  # noqa: E402
from narrate import mismatches, whisper_words, STUDIO  # noqa: E402


def main(video):
    vdir = STUDIO / "VIDEOS" / video
    timing = json.loads((vdir / "audio" / "timing.json").read_text())
    if timing.get("backend") == "placeholder":
        print("voice_qc: placeholder narration (silent) - nothing to check")
        return
    res = []
    for ln in timing["lines"]:
        wav = dsp.read(vdir / "audio" / "lines" / f"{ln['id']}.wav")
        words = whisper_words(dsp.mono(wav))
        hyp = " ".join(w["word"] for w in words)
        mm = mismatches(ln["text"], hyp)
        res.append({"id": ln["id"], "text": ln["text"], "heard": hyp, "mismatch": mm})
        print(f"  {'OK ' if mm == 0 else 'BAD'} {ln['id']}: {hyp}")
    (vdir / "qc").mkdir(exist_ok=True)
    (vdir / "qc" / "voice_qc.json").write_text(json.dumps(res, indent=2))
    bad = sum(r["mismatch"] > 0 for r in res)
    print(f"voice_qc: {len(res) - bad}/{len(res)} lines clean")


if __name__ == "__main__":
    main(sys.argv[1])
