"""mix.py - cues.json + narration + music -> mix_master.wav (+ stems, stats).

Chain:
  narration: HPF 80 Hz, presence EQ, compressor, -> -16 LUFS
  music:     side-chain ducked under speech (env follower), music gates from cues.json
  sfx/amb:   placed from cues.json, per-bus gain
  master:    sum, -> -14 LUFS integrated, true-peak limit <= -1 dBTP
Usage: python mix.py VIDEO_000 [--loop]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import dsp  # noqa: E402
from dsp import SR, samples  # noqa: E402

STUDIO = Path(__file__).resolve().parents[2]
SFX_DIR = STUDIO / "AUDIO" / "sound_effects"

TARGET_LUFS = -14.0
NARR_LUFS = -16.0
TP_CEIL = -1.0


def narration_chain(x):
    x = dsp.mono(x)
    x = dsp.highpass(x, 80, 2)
    x = dsp.peaking_eq(x, 3000, 2.0, 0.8)   # presence
    x = dsp.peaking_eq(x, 250, -1.5, 1.0)   # de-mud
    x = dsp.compressor(x, -20, 3.0, 0.004, 0.1)
    return dsp.match_lufs(dsp.stereo(x), NARR_LUFS)


def duck_gain(narr, depth_db=-10.0, attack=0.03, release=0.35, thresh=0.01):
    env = dsp.envelope_follower(narr, attack, release)
    on = np.clip(env / thresh, 0, 1)
    from scipy.ndimage import uniform_filter1d
    on = uniform_filter1d(on, samples(0.08))
    return 10 ** (depth_db * on / 20)


def circular_add(buf, x, t, gain):
    """Place with wrap-around (for seamless loops)."""
    i = samples(t) % len(buf)
    x = dsp.stereo(x) * gain
    while len(x):
        n = min(len(x), len(buf) - i)
        buf[i:i + n] += x[:n]
        x = x[n:]
        i = 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--music-db", type=float, default=-6.0)
    a = ap.parse_args()

    vdir = STUDIO / "VIDEOS" / a.video
    adir = vdir / "audio"
    cues = json.loads((adir / "cues.json").read_text()) if (adir / "cues.json").exists() else {}
    dur = cues.get("duration")
    narr_p = adir / "narration_raw.wav"
    narr = dsp.read(narr_p) if narr_p.exists() else np.zeros(samples(dur or 10))
    dur = dur or len(narr) / SR
    N = samples(dur)
    loop = a.loop or cues.get("loop", False)

    narr = dsp.pad_to(narration_chain(narr) if np.any(narr) else dsp.stereo(narr), N)

    # music
    mus_p = adir / "music.wav"
    music = dsp.pad_to(dsp.stereo(dsp.read(mus_p)), N) if mus_p.exists() else np.zeros((N, 2))
    music = music * dsp.db(cues.get("music_db", a.music_db))
    if np.any(narr):
        music *= duck_gain(narr, cues.get("duck_db", -10.0))[:, None]
    for g in cues.get("music_gates", []):
        a0, a1 = samples(g[0]), samples(g[1])
        music[a0:a1] = 0

    # sfx / ambience buses
    buses = {"sfx": np.zeros((N, 2)), "amb": np.zeros((N, 2))}
    lib_cache = {}
    for c in cues.get("sfx", []):
        name = c["name"]
        if name not in lib_cache:
            p = SFX_DIR / f"{name}.flac"
            if not p.exists():
                print(f"  ! missing sfx {name} (run sfx_lib.py)")
                lib_cache[name] = None
                continue
            lib_cache[name] = dsp.read(p)
        x = lib_cache[name]
        if x is None:
            continue
        if c.get("offset"):
            x = x[samples(c["offset"]):]
        if c.get("dur"):
            if c.get("loop") and len(x) < samples(c["dur"]):  # crossfaded tiling for ambience beds
                xf = samples(0.5)
                out = x.copy()
                while len(out) < samples(c["dur"]):
                    ramp = np.linspace(0, 1, xf)
                    ramp = ramp[:, None] if x.ndim == 2 else ramp
                    out[-xf:] = out[-xf:] * (1 - ramp) + x[:xf] * ramp
                    out = np.concatenate([out, x[xf:]])
                x = out
            x = dsp.fade(dsp.pad_to(x, samples(c["dur"])), c.get("fade_in", 0.01), c.get("fade_out", min(0.3, c["dur"] / 3)))
        x = dsp.stereo(x, c.get("pan", 0.0))
        bus = buses.setdefault(c.get("bus", "sfx"), np.zeros((N, 2)))
        gain = dsp.db(c.get("gain_db", 0.0))
        if loop:
            circular_add(bus, x, c["t"], gain)
        else:
            dsp.place(bus, x, c["t"], gain)
    bus_db = cues.get("bus_db", {"sfx": -8.0, "amb": -20.0})
    for k in buses:
        buses[k] *= dsp.db(bus_db.get(k, -10.0))

    master = narr + music + sum(buses.values())
    master = dsp.match_lufs(master, TARGET_LUFS)
    master = dsp.limiter(master, TP_CEIL - 0.2)
    # limiter can drop loudness slightly; one more trim pass
    master = dsp.limiter(dsp.match_lufs(master, TARGET_LUFS), TP_CEIL - 0.2)

    dsp.write(adir / "mix_master.wav", master)
    stems = {"narration": narr, "music": music, **buses}
    (adir / "stems").mkdir(exist_ok=True)
    for k, v in stems.items():
        dsp.write(adir / "stems" / f"{k}.wav", v)
    stats = {"duration": round(len(master) / SR, 3), "lufs": round(dsp.lufs(master), 2),
             "true_peak_dbtp": round(dsp.true_peak(master), 2), "loop": loop}
    (adir / "mix_stats.json").write_text(json.dumps(stats, indent=2))
    print("mix ->", adir / "mix_master.wav", stats)


if __name__ == "__main__":
    main()
