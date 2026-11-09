"""music_gen.py - procedural score, one cue_videoNNN() per video.

Score has buses (pad/bass/lead/perc/fx). Instruments are plain functions.
gate(t0, t1) silences all buses in a window (strategic silence).
Usage:
    python music_gen.py VIDEO_000          -> VIDEOS/VIDEO_000/audio/music.wav (+ stems)
    python music_gen.py VIDEO_000 --loop   -> fold tail into start for seamless loop
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import dsp  # noqa: E402
from dsp import SR, samples, tvec, note_hz  # noqa: E402

STUDIO = Path(__file__).resolve().parents[2]
BUSES = ("pad", "bass", "lead", "perc", "fx")


# ---------------------------------------------------------------- instruments (mono out)
def inst_pad(freq, dur, bright=1500, detune=0.006):
    x = sum(dsp.saw(freq * (1 + d), dur, 20) for d in (-detune, 0, detune))
    return dsp.lowpass(x, bright, 2) * dsp.adsr(dur, 0.6, 0.4, 0.8, min(1.0, dur * 0.4)) * 0.3


def inst_strings(freq, dur, bright=2500):
    t = tvec(dur)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t / 0.5, 0, 1)
    x = sum(dsp.sine(freq * k * vib, dur) / k ** 1.2 for k in range(1, 9))
    return dsp.lowpass(x, bright, 2) * dsp.adsr(dur, 0.35, 0.3, 0.85, min(0.8, dur * 0.4)) * 0.4


def inst_pluck(freq, dur, bright=0.5):
    return dsp.karplus(freq, dur, 0.995, bright) * 0.7


def inst_bell(freq, dur):
    return dsp.fm_bell(freq, dur, 3.5, 2.0, min(dur, 1.5)) * 0.5


def inst_bass(freq, dur):
    x = dsp.sine(freq, dur) + 0.3 * dsp.saw(freq, dur, 8)
    return dsp.lowpass(x, 400, 2) * dsp.adsr(dur, 0.01, 0.1, 0.8, 0.08) * 0.6


def inst_stab(freq, dur=0.3):
    x = sum(dsp.saw(freq * r, dur, 25) for r in (1, 1.26, 1.5))
    return dsp.lowpass(x, 3000, 2) * dsp.exp_decay(dur, 0.08) * 0.4


def inst_tremolo(freq, dur, rate=8):
    return inst_strings(freq, dur) * (0.6 + 0.4 * np.sin(2 * np.pi * rate * tvec(dur)))


def drum_kick(dur=0.4):
    f = 50 + 90 * np.exp(-tvec(dur) / 0.03)
    return dsp.sine(f, dur) * dsp.exp_decay(dur, 0.12)


def drum_snare(dur=0.3, seed=0):
    n = dsp.bandpass(dsp.white(dur, np.random.default_rng(seed)), 1500, 8000) * dsp.exp_decay(dur, 0.06)
    return n * 0.6 + dsp.sine(190, dur) * dsp.exp_decay(dur, 0.04) * 0.5


def drum_hat(dur=0.08, seed=0):
    return dsp.highpass(dsp.white(dur, np.random.default_rng(seed)), 7000) * dsp.exp_decay(dur, 0.015) * 0.4


# ---------------------------------------------------------------- score
class Score:
    def __init__(self, duration: float, bpm: float = 100):
        self.dur = duration
        self.bpm = bpm
        self.n = samples(duration) + samples(4)  # tail room
        self.bus = {b: np.zeros((self.n, 2)) for b in BUSES}
        self.gates: list[tuple[float, float, float]] = []

    @property
    def beat(self):
        return 60 / self.bpm

    def add(self, bus, x, t, gain=1.0, pan=0.0):
        dsp.place(self.bus[bus], dsp.stereo(x, pan), t, gain)

    def note(self, bus, inst, name_or_hz, t, dur, gain=1.0, pan=0.0):
        f = note_hz(name_or_hz) if isinstance(name_or_hz, str) else name_or_hz
        self.add(bus, inst(f, dur), t, gain, pan)

    def chord(self, bus, inst, notes, t, dur, gain=1.0, spread=0.4):
        for i, n in enumerate(notes):
            pan = spread * (2 * i / max(len(notes) - 1, 1) - 1)
            self.note(bus, inst, n, t, dur, gain / np.sqrt(len(notes)), pan)

    def drums(self, t0, t1, pattern="kick:0,2 snare:1,3 hat:0,.5,1,1.5,2,2.5,3,3.5", gain=1.0):
        """pattern positions in beats within a 4-beat bar."""
        parts = dict(p.split(":") for p in pattern.split())
        bar = 4 * self.beat
        t = t0
        k = 0
        while t < t1:
            for name, pos in parts.items():
                for b in pos.split(","):
                    tt = t + float(b) * self.beat
                    if tt >= t1:
                        continue
                    x = {"kick": drum_kick, "snare": lambda: drum_snare(seed=k),
                         "hat": lambda: drum_hat(seed=k)}[name]()
                    self.add("perc", x, tt, gain)
                    k += 1
            t += bar

    def gate(self, t0, t1, fade=0.05):
        """Silence all music between t0..t1 (strategic silence)."""
        self.gates.append((t0, t1, fade))

    def render(self, loop=False):
        for name in BUSES:
            self.bus[name] = self._apply_gates(self.bus[name])
        mix = sum(self.bus.values())
        ir = dsp.make_ir(2.2, 0.5, 5000)
        mix = dsp.convolve_reverb(mix, ir, 0.18)[: self.n]
        stems = {k: v[: self.n] for k, v in self.bus.items()}
        if loop:
            L = samples(self.dur)
            tail = mix[L:]
            mix = mix[:L].copy()
            mix[: len(tail)] += tail
            stems = {k: v[:L] for k, v in stems.items()}
        else:
            mix = mix[: samples(self.dur)]
            stems = {k: v[: samples(self.dur)] for k, v in stems.items()}
        return dsp.normalize(mix, 0.7), stems

    def _apply_gates(self, x):
        g = np.ones(len(x))
        for t0, t1, f in self.gates:
            a, b, fs = samples(t0), samples(t1), samples(f)
            g[a:b] = 0
            if fs:
                g[max(a - fs, 0):a] *= np.linspace(1, 0, len(g[max(a - fs, 0):a]))
                g[b:b + fs] *= np.linspace(0, 1, len(g[b:b + fs]))
        return x * g[:, None]


# ---------------------------------------------------------------- cues
def load_edl(video: str):
    p = STUDIO / "VIDEOS" / video / f"edit_{video.lower().replace('_', '')}.py"
    if not p.exists():
        cands = list((STUDIO / "VIDEOS" / video).glob("edit_*.py"))
        p = cands[0]
    spec = importlib.util.spec_from_file_location("edl", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cue_template(edl) -> Score:
    """Generic cue: pad bed, bass on beats, drums after BEATS['drop'] if present."""
    beats = getattr(edl, "BEATS", {})
    s = Score(edl.DURATION, bpm=getattr(edl, "BPM", 96))
    prog = [["A3", "C4", "E4"], ["F3", "A3", "C4"], ["C3", "E3", "G3"], ["G3", "B3", "D4"]]
    bar = 4 * s.beat
    t, i = 0.0, 0
    while t < s.dur:
        s.chord("pad", inst_pad, prog[i % 4], t, bar + 0.3, 0.8)
        s.note("bass", inst_bass, prog[i % 4][0][:-1] + "2", t, bar * 0.9, 0.9)
        t += bar
        i += 1
    if "drop" in beats:
        s.drums(beats["drop"], s.dur)
    if "silence" in beats:
        s.gate(*beats["silence"])
    return s


def cue_video000(edl) -> Score:
    """10 s pipeline test: soft playful pluck motif."""
    s = Score(edl.DURATION, bpm=110)
    bar = 4 * s.beat
    prog = [["C4", "E4", "G4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"], ["G3", "B3", "D4"]]
    mel = ["E5", "G5", "A5", "G5", "E5", "D5", "C5", "D5"]
    t, i = 0.0, 0
    while t < s.dur:
        s.chord("pad", inst_pad, prog[i % 4], t, bar + 0.2, 0.5)
        s.note("bass", inst_bass, prog[i % 4][0][:-1] + "2", t, bar * 0.9, 0.7)
        for j in range(4):
            s.note("lead", inst_pluck, mel[(i * 4 + j) % len(mel)], t + j * s.beat, s.beat * 1.5, 0.5, 0.2)
        t += bar
        i += 1
    beats = getattr(edl, "BEATS", {})
    if "reveal" in beats:
        s.add("fx", inst_bell(note_hz("C6"), 1.5), beats["reveal"], 0.6)
    return s


def cue_video001(edl) -> Score:
    """Mystery: low drone + ticking pizzicato under the interrogation, eerie bells for the clue,
    total silence before the reveal, slow build for the question, sting at the freeze."""
    B = edl.B
    s = Score(edl.DURATION, bpm=edl.BPM)
    beat = s.beat
    # 0-1.7 hook: thunder carries it; drone swells in under the narration
    s.note("pad", lambda f, d: inst_pad(f, d, bright=700), "D2", 0.3, B["foyer"] - 0.3, 0.9)
    s.note("pad", lambda f, d: inst_strings(f, d, 900), "A2", 1.7, B["safe"] - 1.7, 0.5)
    # study: tremolo strings (panic)
    s.chord("pad", lambda f, d: inst_tremolo(f, d, 10), ["D3", "F3", "G#3"], B["safe"], B["foyer"] - B["safe"], 0.55)
    # interrogation: pizzicato pulse + bass ostinato (quick cuts)
    pat = ["D3", "F3", "A3", "G#3"]
    t, i = B["foyer"], 0
    while t < B["turn"]:
        s.note("lead", lambda f, d: inst_pluck(f, d, 0.35), pat[i % 4], t, beat * 0.9, 0.45, 0.25 * (-1) ** i)
        if i % 2 == 0:
            s.note("bass", inst_bass, "D2" if (i // 8) % 2 == 0 else "A#1", t, beat * 1.8, 0.7)
        t += beat / 2
        i += 1
    s.note("pad", lambda f, d: inst_pad(f, d, bright=600), "D2", B["foyer"], B["turn"] - B["foyer"] + 0.5, 0.6)
    # the clue: slower, eerie bells, low pulse
    t = B["turn"]
    for k, n in enumerate(["A5", "G#5", "D5", "F5", "A5", "G#5"]):
        s.note("lead", inst_bell, n, t + k * beat * 2, beat * 3, 0.35, 0.3 * (-1) ** k)
    s.note("pad", lambda f, d: inst_strings(f, d, 700), "D2", B["turn"], B["silence"] - B["turn"], 0.7)
    s.note("pad", lambda f, d: inst_strings(f, d, 1200), "G#3", B["daniel2"], B["silence"] - B["daniel2"], 0.4)
    # silence for the reveal moment
    s.gate(B["silence"], B["lineup"] + 0.1, 0.04)
    # recap + question: slow build
    s.note("pad", lambda f, d: inst_pad(f, d, bright=900), "D2", B["lineup"], B["freeze"] - B["lineup"] + 0.3, 0.8)
    s.chord("pad", lambda f, d: inst_strings(f, d, 1500), ["D3", "F3", "A3"], B["lineup"], B["zoom"] - B["lineup"], 0.5)
    s.chord("pad", lambda f, d: inst_tremolo(f, d, 7), ["D3", "G#3", "C4"], B["zoom"], B["freeze"] - B["zoom"], 0.6)
    t = B["zoom"]
    while t < B["freeze"] - 0.1:  # ticking clock under the question
        s.note("perc", lambda f, d: drum_hat(0.05) * 1.5, 100, t, 0.05, 0.6)
        t += beat / 2
    # end: low drone tail under the end card (sting comes from SFX)
    s.note("pad", lambda f, d: inst_strings(f, d, 600), "D2", B["freeze"] + 0.2, edl.DURATION - B["freeze"] - 0.2, 0.5)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--loop", action="store_true")
    a = ap.parse_args()
    edl = load_edl(a.video)
    fn = globals().get(f"cue_{a.video.lower().replace('_', '')}", cue_template)
    score = fn(edl)
    mix, stems = score.render(loop=a.loop or getattr(edl, "LOOP", False))
    out = STUDIO / "VIDEOS" / a.video / "audio"
    out.mkdir(parents=True, exist_ok=True)
    dsp.write(out / "music.wav", mix)
    for k, v in stems.items():
        if np.any(v):
            dsp.write(out / f"music_stem_{k}.wav", v)
    print(f"music -> {out / 'music.wav'}  ({len(mix) / SR:.2f}s, cue={fn.__name__})")


if __name__ == "__main__":
    main()
