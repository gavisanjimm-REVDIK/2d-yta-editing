"""dsp.py - small DSP toolkit for procedural SFX, music and mixing.

All functions work on float32/float64 numpy arrays at SR (48 kHz).
Mono = shape (n,), stereo = shape (n, 2).
"""
from __future__ import annotations

import numpy as np
from scipy import signal

SR = 48000
RNG = np.random.default_rng(1234)


# ---------------------------------------------------------------- basics
def secs(n: int) -> float:
    return n / SR


def samples(t: float) -> int:
    return int(round(t * SR))


def tvec(dur: float) -> np.ndarray:
    return np.arange(samples(dur)) / SR


def db(x: float) -> float:
    """dB -> linear gain."""
    return 10 ** (x / 20)


def to_db(x: float) -> float:
    return 20 * np.log10(max(abs(x), 1e-12))


def stereo(x: np.ndarray, pan: float = 0.0) -> np.ndarray:
    """Mono -> stereo with constant-power pan (-1 left .. +1 right)."""
    if x.ndim == 2:
        return x
    a = (pan + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


def mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) if x.ndim == 2 else x


def normalize(x: np.ndarray, peak: float = 0.89) -> np.ndarray:
    m = np.max(np.abs(x)) if x.size else 0
    return x * (peak / m) if m > 0 else x


def place(buf: np.ndarray, x: np.ndarray, t: float, gain: float = 1.0) -> None:
    """Add x into buf at time t (in place). Clips at buffer end."""
    i = samples(t)
    if i >= len(buf):
        return
    if i < 0:
        x = x[-i:]
        i = 0
    n = min(len(x), len(buf) - i)
    if buf.ndim == 2 and x.ndim == 1:
        x = stereo(x)
    buf[i:i + n] += x[:n] * gain


def pad_to(x: np.ndarray, n: int) -> np.ndarray:
    if len(x) >= n:
        return x[:n]
    shape = (n - len(x),) + x.shape[1:]
    return np.concatenate([x, np.zeros(shape, x.dtype)])


# ---------------------------------------------------------------- noise
def white(dur: float, rng=RNG) -> np.ndarray:
    return rng.standard_normal(samples(dur))


def _shaped_noise(dur: float, exponent: float, rng=RNG) -> np.ndarray:
    n = samples(dur)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1] if len(f) > 1 else 1
    spec /= f ** (exponent / 2)
    out = np.fft.irfft(spec, n)
    return out / (np.std(out) + 1e-12)


def pink(dur: float, rng=RNG) -> np.ndarray:
    return _shaped_noise(dur, 1.0, rng)


def brown(dur: float, rng=RNG) -> np.ndarray:
    return _shaped_noise(dur, 2.0, rng)


def blue(dur: float, rng=RNG) -> np.ndarray:
    return _shaped_noise(dur, -1.0, rng)


# ---------------------------------------------------------------- filters
def _sos(kind: str, f, order: int = 4):
    f = np.clip(np.atleast_1d(f), 10, SR / 2 - 100)
    return signal.butter(order, f if len(f) > 1 else f[0], btype=kind, fs=SR, output="sos")


def lowpass(x, f, order=4):
    return signal.sosfilt(_sos("lowpass", f, order), x, axis=0)


def highpass(x, f, order=4):
    return signal.sosfilt(_sos("highpass", f, order), x, axis=0)


def bandpass(x, lo, hi, order=4):
    return signal.sosfilt(_sos("bandpass", [lo, hi], order), x, axis=0)


def sweep_filter(x: np.ndarray, f0: float, f1: float, kind="lowpass", block=256, q=0.707) -> np.ndarray:
    """Time-varying biquad (exp sweep f0->f1). Mono only."""
    out = np.zeros_like(x)
    nblocks = int(np.ceil(len(x) / block))
    zi = np.zeros(2)
    for b in range(nblocks):
        fr = f0 * (f1 / f0) ** (b / max(nblocks - 1, 1))
        w = 2 * np.pi * np.clip(fr, 20, SR / 2.2) / SR
        alpha = np.sin(w) / (2 * q)
        cw = np.cos(w)
        if kind == "lowpass":
            bb = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        elif kind == "highpass":
            bb = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        else:  # bandpass
            bb = [alpha, 0, -alpha]
        aa = [1 + alpha, -2 * cw, 1 - alpha]
        seg = x[b * block:(b + 1) * block]
        y, zi = signal.lfilter(np.array(bb) / aa[0], np.array(aa) / aa[0], seg, zi=zi)
        out[b * block:b * block + len(seg)] = y
    return out


def peaking_eq(x, f, gain_db, q=1.0):
    A = 10 ** (gain_db / 40)
    w = 2 * np.pi * f / SR
    alpha = np.sin(w) / (2 * q)
    b = [1 + alpha * A, -2 * np.cos(w), 1 - alpha * A]
    a = [1 + alpha / A, -2 * np.cos(w), 1 - alpha / A]
    return signal.lfilter(np.array(b) / a[0], np.array(a) / a[0], x, axis=0)


# ---------------------------------------------------------------- envelopes
def adsr(dur: float, a=0.01, d=0.1, s=0.7, r=0.2) -> np.ndarray:
    n = samples(dur)
    na, nd, nr = samples(a), samples(d), samples(r)
    ns = max(n - na - nd - nr, 0)
    env = np.concatenate([
        np.linspace(0, 1, na, endpoint=False),
        np.linspace(1, s, nd, endpoint=False),
        np.full(ns, s),
        np.linspace(s, 0, nr),
    ])
    return pad_to(env, n)


def exp_decay(dur: float, tau: float) -> np.ndarray:
    return np.exp(-tvec(dur) / tau)


def fade(x: np.ndarray, fin=0.005, fout=0.01) -> np.ndarray:
    x = x.copy()
    a, b = samples(fin), samples(fout)
    if a:
        x[:a] *= np.linspace(0, 1, a)[:, None] if x.ndim == 2 else np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)[:, None] if x.ndim == 2 else np.linspace(1, 0, b)
    return x


# ---------------------------------------------------------------- oscillators
def sine(freq, dur, phase=0.0):
    t = tvec(dur)
    if np.ndim(freq):
        return np.sin(2 * np.pi * np.cumsum(freq) / SR + phase)
    return np.sin(2 * np.pi * freq * t + phase)


def saw(freq, dur, harmonics=30):
    """Band-limited additive saw."""
    t = tvec(dur)
    out = np.zeros_like(t)
    for k in range(1, harmonics + 1):
        if k * freq > SR / 2.2:
            break
        out += ((-1) ** (k + 1)) * np.sin(2 * np.pi * k * freq * t) / k
    return out * (2 / np.pi)


def square(freq, dur, harmonics=30):
    t = tvec(dur)
    out = np.zeros_like(t)
    for k in range(1, 2 * harmonics, 2):
        if k * freq > SR / 2.2:
            break
        out += np.sin(2 * np.pi * k * freq * t) / k
    return out * (4 / np.pi)


def chirp(f0, f1, dur, curve="exp"):
    n = samples(dur)
    if curve == "exp":
        f = f0 * (f1 / f0) ** np.linspace(0, 1, n)
    else:
        f = np.linspace(f0, f1, n)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def fm_bell(freq, dur, ratio=3.5, index=4.0, tau=1.2):
    """Classic two-op FM bell."""
    t = tvec(dur)
    env = np.exp(-t / tau)
    mod = index * env * np.sin(2 * np.pi * freq * ratio * t)
    return np.sin(2 * np.pi * freq * t + mod) * env


def karplus(freq, dur, decay=0.996, bright=0.5, rng=RNG):
    """Karplus-Strong plucked string."""
    n = samples(dur)
    p = max(int(SR / freq), 2)
    buf = rng.uniform(-1, 1, p)
    buf = lowpass(buf, 1000 + 9000 * bright, 2) if p > 20 else buf
    out = np.zeros(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = decay * 0.5 * (buf[i % p] + buf[(i + 1) % p])
    return out


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {n: i for i, n in enumerate("C C# D D# E F F# G G# A A# B".split())}


def note_hz(name: str) -> float:
    """'A4', 'C#3' -> Hz."""
    pitch, octv = name[:-1], int(name[-1])
    return midi_hz(12 * (octv + 1) + NOTE[pitch])


# ---------------------------------------------------------------- reverb
def make_ir(dur=2.0, decay=0.5, bright=6000, stereo_ir=True, predelay=0.01, rng=RNG):
    n = samples(dur)
    t = np.arange(n) / SR
    env = np.exp(-t * 6.9 / max(decay * dur, 1e-3))
    chans = []
    for _ in range(2 if stereo_ir else 1):
        x = rng.standard_normal(n) * env
        x = lowpass(x, bright, 2)
        x = np.concatenate([np.zeros(samples(predelay)), x])
        chans.append(x / np.sqrt(np.sum(x ** 2) + 1e-12))
    return np.stack(chans, axis=1) if stereo_ir else chans[0]


def convolve_reverb(x, ir, wet=0.25):
    xs = stereo(x)
    irs = ir if ir.ndim == 2 else np.stack([ir, ir], 1)
    out = np.zeros((len(xs) + len(irs) - 1, 2))
    for c in range(2):
        out[:, c] = signal.fftconvolve(xs[:, c], irs[:, c])
    dry = pad_to(xs, len(out))
    return dry * (1 - wet) + out * wet


# ---------------------------------------------------------------- dynamics
def saturate(x, drive=2.0):
    return np.tanh(x * drive) / np.tanh(drive)


def envelope_follower(x, attack=0.005, release=0.1):
    m = np.abs(mono(x))
    a = np.exp(-1 / (attack * SR))
    r = np.exp(-1 / (release * SR))
    # vectorised approx: smooth with release filter then peak-hold attack
    env = signal.lfilter([1 - r], [1, -r], m)
    env = np.maximum(env, signal.lfilter([1 - a], [1, -a], m))
    return env


def compressor(x, thresh_db=-18, ratio=3.0, attack=0.005, release=0.12, makeup_db=0.0):
    env = envelope_follower(x, attack, release)
    lvl = 20 * np.log10(env + 1e-9)
    over = np.maximum(lvl - thresh_db, 0)
    gain_db = -over * (1 - 1 / ratio) + makeup_db
    g = 10 ** (gain_db / 20)
    return x * (g[:, None] if x.ndim == 2 else g)


def true_peak(x, oversample=4) -> float:
    """True peak in dBTP (4x oversampled)."""
    y = signal.resample_poly(x, oversample, 1, axis=0)
    return to_db(np.max(np.abs(y)))


def limiter(x, ceiling_db=-1.0, lookahead=0.005, release=0.05, oversample=4):
    """Look-ahead brickwall limiter targeting true-peak ceiling."""
    ceil = db(ceiling_db)
    xs = x if x.ndim == 2 else x[:, None]
    up = signal.resample_poly(xs, oversample, 1, axis=0)
    pk = np.max(np.abs(up), axis=1)
    pk = pk.reshape(-1, oversample).max(axis=1)[:len(xs)]
    pk = pad_to(pk, len(xs))
    need = np.minimum(1.0, ceil / np.maximum(pk, 1e-9))
    la = samples(lookahead)
    # look-ahead: min over window ahead
    from scipy.ndimage import minimum_filter1d
    from scipy.ndimage import uniform_filter1d
    # min over 2L window, then box-smooth over L: result never exceeds `need`
    g = minimum_filter1d(need, size=2 * la + 1)
    g = uniform_filter1d(g, size=la + 1)
    # slow release: one-pole smoothing upward only
    rel = samples(release)
    if rel > 1:
        g = np.minimum(g, uniform_filter1d(minimum_filter1d(need, size=2 * rel + 1), size=rel + 1))
    out = xs * g[:, None]
    # safety clip at ceiling
    out = np.clip(out, -ceil, ceil)
    return out if x.ndim == 2 else out[:, 0]


def lufs(x) -> float:
    import pyloudnorm as pyln
    meter = pyln.Meter(SR)
    return meter.integrated_loudness(stereo(x) if x.ndim == 1 else x)


def match_lufs(x, target=-16.0):
    cur = lufs(x)
    if not np.isfinite(cur):
        return x
    return x * db(target - cur)


# ---------------------------------------------------------------- io
def write(path, x, sr=SR):
    import soundfile as sf
    sf.write(str(path), np.asarray(x, dtype=np.float32), sr)


def read(path, sr=SR):
    import soundfile as sf
    x, r = sf.read(str(path), always_2d=False)
    if r != sr:
        x = signal.resample_poly(x, sr, r, axis=0)
    return x.astype(np.float64)
