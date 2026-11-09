"""lipsync.py - per-frame mouth data for every speaker: audio/lipsync.json.

open  = voice loudness of the speaker's own line wav (RMS, fast attack / slower release, gated)
wide / round = from the letters being spoken (word timing, letters spread across the word)
closed lips forced on m / b / p.   Usage: python lipsync.py VIDEO_001
In a shot: pose["vis"] = viseme(t, LIP, "daniel")
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

STUDIO = Path(__file__).resolve().parents[2]
FPS = 30
ROUND, WIDE, CLOSE = set("ouw"), set("eiy"), set("mbp")


def letter_track(word, n):
    w = [c for c in word.lower() if c.isalpha()] or ["a"]
    return [w[min(int(i / max(n, 1) * len(w)), len(w) - 1)] for i in range(n)]


def build(video):
    import soundfile as sf
    vdir = STUDIO / "VIDEOS" / video
    timing = json.loads((vdir / "audio" / "timing.json").read_text())
    nfr = int(np.ceil(timing["duration"] * FPS)) + 1
    tracks = {}
    for ln in timing["lines"]:
        who = ln["who"]
        x, sr = sf.read(str(vdir / "audio" / "lines" / f"{ln['id']}.wav"), always_2d=False)
        x = x.mean(1) if x.ndim > 1 else x
        hop = sr // FPS
        rms = np.array([np.sqrt(np.mean(x[i:i + hop * 2] ** 2) + 1e-12) for i in range(0, len(x), hop)])
        db = 20 * np.log10(rms + 1e-9)
        ref = np.percentile(db[db > -60], 90) if np.any(db > -60) else -20
        op = 0.9 * np.clip((db - (ref - 16)) / 16, 0, 1) ** 1.6  # gate ~16 dB below loud speech: lips close between syllables
        sm = np.zeros_like(op)  # fast attack, slower release
        for i, v in enumerate(op):
            prev = sm[i - 1] if i else 0
            sm[i] = prev + (v - prev) * (0.8 if v > prev else 0.55)
        tr = tracks.setdefault(who, np.zeros((nfr, 3)))
        f0 = int(round(ln["start"] * FPS))
        for i, v in enumerate(sm):
            if 0 <= f0 + i < nfr:
                tr[f0 + i, 0] = max(tr[f0 + i, 0], v)
        for wd in ln["words"]:
            a, b = int(wd["start"] * FPS), int(np.ceil(wd["end"] * FPS))
            letters = letter_track(wd["word"], max(b - a, 1))
            for k, ch in enumerate(letters):
                f = a + k
                if not 0 <= f < nfr:
                    continue
                tr[f, 1] = 1.0 if ch in WIDE else (0.35 if ch not in ROUND else 0.0)
                tr[f, 2] = 1.0 if ch in ROUND else 0.0
                if ch in CLOSE:
                    tr[f, 0] *= 0.15
    for who, tr in tracks.items():  # light smoothing: open a touch, shape channels more
        tr[:, 0] = np.convolve(tr[:, 0], [0.25, 0.5, 0.25], mode="same")
        for c in (1, 2):
            tr[:, c] = np.convolve(tr[:, c], np.ones(3) / 3, mode="same")
    out = {who: np.round(tr, 3).tolist() for who, tr in tracks.items()}
    (vdir / "audio" / "lipsync.json").write_text(json.dumps(out))
    print("lipsync ->", vdir / "audio" / "lipsync.json", {k: len(v) for k, v in out.items()})


@lru_cache(maxsize=4)
def load(video):
    p = STUDIO / "VIDEOS" / video / "audio" / "lipsync.json"
    return {k: np.array(v) for k, v in json.loads(p.read_text()).items()}


def viseme(t, lip, who):
    tr = lip.get(who)
    if tr is None:
        return (0.0, 0.0, 0.0)
    f = t * FPS
    i = int(f)
    if i >= len(tr) - 1:
        return tuple(tr[-1])
    u = f - i
    return tuple(tr[i] * (1 - u) + tr[i + 1] * u)


if __name__ == "__main__":
    build(sys.argv[1])
