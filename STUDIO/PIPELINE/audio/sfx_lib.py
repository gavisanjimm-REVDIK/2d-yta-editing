"""sfx_lib.py - procedural SFX library.

Each effect = small function, registered with @reg(name, description).
Run:  python sfx_lib.py            -> writes all to STUDIO/AUDIO/sound_effects/*.flac + LIBRARY.json
      python sfx_lib.py whoosh_fast -> one effect
Add new effects per video at bottom (or in sfx_videoNNN.py that imports `reg`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import dsp  # noqa: E402
from dsp import SR, tvec, samples  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "AUDIO" / "sound_effects"
REGISTRY: dict[str, tuple] = {}


def reg(name: str, desc: str, tags: tuple = ()):
    def deco(fn):
        REGISTRY[name] = (fn, desc, tags)
        return fn
    return deco


def rng(seed=0):
    return np.random.default_rng(seed)


# ================================================================ impacts
@reg("impact_soft", "Soft body/cushion thud", ("impact",))
def impact_soft():
    d = 0.5
    body = dsp.sine(np.linspace(110, 55, samples(d)), d) * dsp.exp_decay(d, 0.08)
    n = dsp.lowpass(dsp.white(d, rng(1)), 900) * dsp.exp_decay(d, 0.03) * 0.5
    return dsp.fade(dsp.normalize(body + n))


@reg("impact_heavy", "Big cinematic boom hit", ("impact", "trailer"))
def impact_heavy():
    d = 2.5
    f = 60 * (35 / 60) ** np.linspace(0, 1, samples(d))
    sub = dsp.sine(f, d) * dsp.exp_decay(d, 0.6)
    crack = dsp.highpass(dsp.white(d, rng(2)), 1500) * dsp.exp_decay(d, 0.02)
    body = dsp.lowpass(dsp.brown(d, rng(3)), 400) * dsp.exp_decay(d, 0.25)
    x = sub + 0.6 * crack + 0.5 * body
    x = dsp.saturate(x, 1.8)
    return dsp.fade(dsp.normalize(dsp.convolve_reverb(x, dsp.make_ir(2.5, 0.6, 3000), 0.25)))


@reg("impact_metal", "Metal clang", ("impact", "metal"))
def impact_metal():
    d = 1.5
    x = sum(dsp.fm_bell(f, d, ratio=1.41 + i * 0.37, index=2 + i, tau=0.3 + 0.1 * i)
            for i, f in enumerate([310, 487, 733, 1121]))
    x += dsp.highpass(dsp.white(d, rng(4)), 2000) * dsp.exp_decay(d, 0.01)
    return dsp.fade(dsp.normalize(x))


@reg("impact_frame", "Short punchy hit for impact frames / cuts", ("impact", "edit"))
def impact_frame():
    d = 0.6
    k = dsp.sine(np.linspace(180, 45, samples(d)), d) * dsp.exp_decay(d, 0.09)
    s = dsp.bandpass(dsp.white(d, rng(5)), 1200, 6000) * dsp.exp_decay(d, 0.04)
    return dsp.fade(dsp.normalize(dsp.saturate(k + 0.5 * s, 2.5)))


# ================================================================ whooshes
def _whoosh(d, f0, f1, seed, peak_at=0.6):
    n = dsp.pink(d, rng(seed))
    t = np.linspace(0, 1, samples(d))
    env = np.where(t < peak_at, (t / peak_at) ** 2, ((1 - t) / (1 - peak_at)) ** 1.5)
    x = dsp.sweep_filter(n, f0, f1, "bandpass", q=1.2) * env
    return dsp.fade(dsp.normalize(x))


@reg("whoosh_fast", "Fast whip-pan whoosh", ("whoosh", "edit"))
def whoosh_fast():
    return _whoosh(0.35, 400, 4000, 6, 0.55)


@reg("whoosh_slow", "Slow airy pass-by", ("whoosh",))
def whoosh_slow():
    return _whoosh(1.4, 200, 2500, 7, 0.65)


@reg("swish_cloth", "Clothing movement swish", ("foley",))
def swish_cloth():
    return _whoosh(0.25, 1500, 5000, 8, 0.4) * 0.6


# ================================================================ risers / UI
@reg("riser_tension", "Rising tension riser (4s)", ("riser", "trailer"))
def riser_tension():
    d = 4.0
    t = tvec(d)
    tone = sum(dsp.sine(110 * 2 ** (k / 12) * (1 + (t / d) ** 2), d)
               for k in (0, 7, 12))
    noise = dsp.sweep_filter(dsp.white(d, rng(9)), 300, 8000, "bandpass", q=0.8)
    env = (t / d) ** 2.5
    return dsp.fade(dsp.normalize((tone * 0.4 + noise) * env), 0.01, 0.02)


@reg("ui_pop", "Small pop for chips/titles", ("ui",))
def ui_pop():
    d = 0.15
    x = dsp.sine(np.linspace(900, 1500, samples(d)), d) * dsp.exp_decay(d, 0.025)
    return dsp.fade(dsp.normalize(x) * 0.8)


@reg("ui_tick", "Clock / counter tick", ("ui",))
def ui_tick():
    d = 0.06
    x = dsp.bandpass(dsp.white(d, rng(10)), 2500, 7000) * dsp.exp_decay(d, 0.006)
    return dsp.fade(dsp.normalize(x), 0.0005, 0.005)


@reg("ui_ding", "Bright bell ding", ("ui",))
def ui_ding():
    return dsp.fade(dsp.normalize(dsp.fm_bell(dsp.note_hz("E6"), 1.2, 3.5, 2.5, 0.35)))


@reg("comedy_boing", "Cartoon boing", ("comedy",))
def comedy_boing():
    d = 0.7
    t = tvec(d)
    f = 220 + 160 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.3)
    return dsp.fade(dsp.normalize(dsp.sine(f, d) * dsp.exp_decay(d, 0.25)))


@reg("record_scratch", "Record scratch stop", ("comedy", "edit"))
def record_scratch():
    d = 0.5
    t = tvec(d)
    f = 600 + 900 * np.sin(2 * np.pi * 3 * t)
    x = dsp.bandpass(dsp.white(d, rng(11)), 800, 5000) * (0.5 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    return dsp.fade(dsp.normalize(x * dsp.exp_decay(d, 0.2)))


# ================================================================ foley
@reg("footstep_hard", "Footstep on hard floor", ("foley", "footstep"))
def footstep_hard():
    d = 0.25
    heel = dsp.lowpass(dsp.white(d, rng(12)), 2500) * dsp.exp_decay(d, 0.012)
    body = dsp.sine(np.linspace(140, 80, samples(d)), d) * dsp.exp_decay(d, 0.03) * 0.6
    return dsp.fade(dsp.normalize(heel + body) * 0.7)


@reg("door_open", "Wooden door creak + latch", ("foley", "door"))
def door_open():
    d = 1.4
    t = tvec(d)
    f = 180 + 60 * np.sin(2 * np.pi * 1.3 * t) + 30 * dsp.lowpass(dsp.white(d, rng(13)), 8)
    creak = dsp.bandpass(np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)), 300, 3000) * 0.3
    creak *= dsp.adsr(d, 0.2, 0.3, 0.6, 0.4)
    latch = np.zeros_like(t)
    dsp.place(latch, footstep_hard() * 0.6, 0.0)
    return dsp.fade(dsp.normalize(creak + latch))


@reg("door_slam", "Door slam", ("foley", "door", "impact"))
def door_slam():
    x = impact_soft() * 0.8
    x = dsp.pad_to(x, samples(1.2))
    return dsp.fade(dsp.normalize(dsp.mono(dsp.convolve_reverb(x, dsp.make_ir(1.0, 0.4, 4000), 0.3))[: samples(1.2)]))


# ================================================================ ambiences (loopable-ish beds)
@reg("amb_room", "Quiet room tone", ("ambience",))
def amb_room():
    d = 10.0
    return dsp.lowpass(dsp.brown(d, rng(14)), 300) * 0.15 + dsp.lowpass(dsp.pink(d, rng(15)), 2000) * 0.02


@reg("amb_city", "Distant city / traffic bed", ("ambience",))
def amb_city():
    d = 10.0
    rumble = dsp.lowpass(dsp.brown(d, rng(16)), 250)
    hiss = dsp.bandpass(dsp.pink(d, rng(17)), 400, 3000) * 0.25
    lfo = 0.8 + 0.2 * np.sin(2 * np.pi * 0.07 * tvec(d))
    return dsp.normalize((rumble + hiss) * lfo, 0.3)


@reg("amb_wind", "Outdoor wind", ("ambience", "nature"))
def amb_wind():
    d = 10.0
    n = dsp.pink(d, rng(18))
    out = dsp.sweep_filter(n, 400, 1200, "bandpass", q=0.9)
    return dsp.normalize(out * (0.6 + 0.4 * np.sin(2 * np.pi * 0.13 * tvec(d))), 0.35)


@reg("amb_subway", "Subway car rumble + rail clacks", ("ambience", "transport"))
def amb_subway():
    d = 10.0
    t = tvec(d)
    rumble = dsp.lowpass(dsp.brown(d, rng(19)), 180)
    x = rumble.copy()
    for k in np.arange(0.3, d, 0.85):
        dsp.place(x, footstep_hard() * 0.5, k)
        dsp.place(x, footstep_hard() * 0.4, k + 0.12)
    return dsp.normalize(x * (0.9 + 0.1 * np.sin(2 * np.pi * 0.2 * t)), 0.4)


# ================================================================ generator
def build(names=None):
    OUT.mkdir(parents=True, exist_ok=True)
    lib_path = OUT / "LIBRARY.json"
    lib = json.loads(lib_path.read_text()) if lib_path.exists() else {}
    for name, (fn, desc, tags) in REGISTRY.items():
        if names and name not in names:
            continue
        x = np.asarray(fn(), dtype=np.float64)
        p = OUT / f"{name}.flac"
        dsp.write(p, x)
        lib[name] = {"file": p.name, "desc": desc, "tags": list(tags),
                     "dur": round(len(x) / SR, 3), "peak_db": round(dsp.to_db(np.max(np.abs(x))), 2)}
        print(f"  sfx {name:18s} {len(x) / SR:5.2f}s  {desc}")
    lib_path.write_text(json.dumps(lib, indent=2))
    return lib


if __name__ == "__main__":
    build(sys.argv[1:] or None)
