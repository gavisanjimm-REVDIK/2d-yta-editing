"""narrate.py - script.json -> per-line wavs + narration_raw.wav + timing.json (word level).

Backends (pick with --backend):
  chatterbox  local open-source TTS, voice clone from reference clip (default if installed)
  placeholder silent audio with estimated word timing (so edit/captions can be built before TTS exists)

For each line: generate N takes, transcribe each with faster-whisper, keep the take with fewest word
mismatches (digits vs number words count as equal). Word timings come from whisper on the chosen take.

script.json:
{
  "voice_ref": "ASSETS/voices/narrator.wav",
  "lines": [
    {"id": "L01", "who": "narrator", "text": "...", "delivery": "calm", "exaggeration": 0.5,
     "pause_after": 0.3, "voice_ref": null, "at": null}
  ]
}
"at" (optional) = fixed story time in seconds (else lines go back-to-back).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audio"))
import dsp  # noqa: E402
from dsp import SR, samples  # noqa: E402

STUDIO = Path(__file__).resolve().parents[2]

NUMS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
        "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
        "twenty": "20", "thirty": "30", "hundred": "100", "thousand": "1000"}


def norm_words(s: str) -> list[str]:
    w = re.findall(r"[a-z0-9']+", s.lower())
    return [NUMS.get(x, x) for x in w]


def mismatches(ref: str, hyp: str) -> int:
    a, b = norm_words(ref), norm_words(hyp)
    # Levenshtein on words
    d = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, d[0] = d[0], i
        for j, y in enumerate(b, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (x != y))
            prev, d[j] = d[j], cur
    return d[-1]


# ---------------------------------------------------------------- backends
class Placeholder:
    name = "placeholder"
    WPS = 2.7

    def synth(self, line, ref):
        n = len(line["text"].split())
        return np.zeros(samples(n / self.WPS + 0.15))

    def words(self, line, wav):
        toks = line["text"].split()
        dur = len(wav) / SR - 0.1
        weights = np.array([max(len(re.sub(r"\W", "", t)), 2) for t in toks], float)
        edges = np.concatenate([[0], np.cumsum(weights / weights.sum() * dur)]) + 0.05
        return [{"word": t, "start": round(edges[i], 3), "end": round(edges[i + 1] - 0.03, 3)}
                for i, t in enumerate(toks)]


class Chatterbox:
    name = "chatterbox"

    def __init__(self):
        from chatterbox.tts import ChatterboxTTS  # noqa
        self.model = ChatterboxTTS.from_pretrained(device="cpu")

    def synth(self, line, ref):
        import torch  # noqa
        wav = self.model.generate(line["text"], audio_prompt_path=ref,
                                  exaggeration=line.get("exaggeration", 0.5),
                                  cfg_weight=line.get("cfg_weight", 0.5))
        x = wav.squeeze().cpu().numpy().astype(np.float64)
        from scipy.signal import resample_poly
        return resample_poly(x, SR, self.model.sr)


_WHISPER = None


def whisper_words(wav: np.ndarray):
    global _WHISPER
    from faster_whisper import WhisperModel
    from scipy.signal import resample_poly
    if _WHISPER is None:
        _WHISPER = WhisperModel("small.en", device="cpu", compute_type="int8")
    x16 = resample_poly(wav, 16000, SR).astype(np.float32)
    segs, _ = _WHISPER.transcribe(x16, word_timestamps=True, language="en", beam_size=5)
    out = []
    for s in segs:
        for w in s.words or []:
            out.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    return out


def trim_silence(x, thresh_db=-45, pad=0.04):
    env = np.abs(x)
    idx = np.where(env > dsp.db(thresh_db))[0]
    if not len(idx):
        return x
    a, b = max(idx[0] - samples(pad), 0), min(idx[-1] + samples(pad), len(x))
    return x[a:b]


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--backend", default="auto", choices=["auto", "chatterbox", "placeholder"])
    ap.add_argument("--takes", type=int, default=3)
    ap.add_argument("--only", nargs="*", help="re-do only these line ids")
    a = ap.parse_args()

    vdir = STUDIO / "VIDEOS" / a.video
    script = json.loads((vdir / "script.json").read_text())
    adir = vdir / "audio"
    (adir / "lines").mkdir(parents=True, exist_ok=True)

    be = None
    if a.backend in ("auto", "chatterbox"):
        try:
            be = Chatterbox()
        except Exception as e:  # noqa
            if a.backend == "chatterbox":
                raise
            print(f"  chatterbox not available ({e.__class__.__name__}); using placeholder timing")
    be = be or Placeholder()
    can_whisper = be.name != "placeholder"

    report = []
    line_data = {}
    old_timing = json.loads((adir / "timing.json").read_text()) if (adir / "timing.json").exists() else {}
    for ln in script["lines"]:
        lp = adir / "lines" / f"{ln['id']}.wav"
        if a.only and ln["id"] not in a.only and lp.exists():
            prev = next((l for l in old_timing.get("lines", []) if l["id"] == ln["id"]), None)
            if prev:
                line_data[ln["id"]] = (dsp.read(lp), prev["words_local"], prev.get("mismatch", 0))
                continue
        ref = ln.get("voice_ref") or script.get("voice_ref")
        ref = str(STUDIO / ref) if ref else None
        best = None
        for k in range(a.takes if can_whisper else 1):
            wav = trim_silence(be.synth(ln, ref)) if can_whisper else be.synth(ln, ref)
            if can_whisper:
                words = whisper_words(wav)
                mm = mismatches(ln["text"], " ".join(w["word"] for w in words))
            else:
                words, mm = be.words(ln, wav), 0
            print(f"  {ln['id']} take {k + 1}: mismatches={mm}")
            if best is None or mm < best[2]:
                best = (wav, words, mm)
            if mm == 0:
                break
        dsp.write(lp, best[0])
        line_data[ln["id"]] = best
        if best[2] > 0:
            report.append(f"{ln['id']}: {best[2]} word mismatch(es) - consider rewriting line")

    # assemble
    t = script.get("start_offset", 0.3)
    timeline, lines_out = [], []
    for ln in script["lines"]:
        wav, words, mm = line_data[ln["id"]]
        start = ln["at"] if ln.get("at") is not None else t
        timeline.append((start, wav))
        gw = [{**w, "start": round(w["start"] + start, 3), "end": round(w["end"] + start, 3),
               "line": ln["id"], "who": ln.get("who", "narrator")} for w in words]
        lines_out.append({"id": ln["id"], "who": ln.get("who", "narrator"), "text": ln["text"],
                          "start": round(start, 3), "end": round(start + len(wav) / SR, 3),
                          "words": gw, "words_local": words, "mismatch": mm})
        t = start + len(wav) / SR + ln.get("pause_after", 0.25)
    total = t + script.get("tail", 0.5)
    out = np.zeros(samples(total))
    for st, w in timeline:
        dsp.place(out, w, st)
    dsp.write(adir / "narration_raw.wav", out)
    timing = {"backend": be.name, "duration": round(total, 3), "lines": lines_out,
              "words": [w for l in lines_out for w in l["words"]]}
    (adir / "timing.json").write_text(json.dumps(timing, indent=2))
    print(f"narration -> {adir / 'narration_raw.wav'} ({total:.2f}s, backend={be.name})")
    if be.name == "placeholder":
        print("  NOTE: placeholder = SILENT narration with estimated timing. Install chatterbox for real voice.")
    for r in report:
        print("  !", r)


if __name__ == "__main__":
    main()
