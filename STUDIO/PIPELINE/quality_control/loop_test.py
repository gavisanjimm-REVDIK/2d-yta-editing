"""loop_test.py - checks a looping short plays seamlessly.

Plays the export 3x back-to-back (concat) and checks at each seam:
  - black / silence at the seam
  - clicks (sample jump at seam vs normal sample-to-sample deltas)
  - audio gap / A-V length mismatch
  - picture change at seam vs normal frame-to-frame motion (ratio; < ~2.5 is good)
Writes qc/loop_report.json + qc/loop_3x.mp4.
Usage: python loop_test.py EXPORTS/VIDEO_000.mp4 [--video VIDEO_000]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np

STUDIO = Path(__file__).resolve().parents[2]


def frames(path, w=135, h=240):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vf", f"scale={w}:{h}",
                        "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w).astype(np.float32)


def audio(path, sr=48000):
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "2",
                        "-ar", str(sr), "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--video")
    a = ap.parse_args()
    mp4 = Path(a.mp4)
    qdir = STUDIO / "VIDEOS" / (a.video or mp4.stem) / "qc"
    qdir.mkdir(parents=True, exist_ok=True)

    f = frames(mp4)
    x = audio(mp4)
    sr = 48000
    vdur, adur = len(f) / 30, len(x) / sr

    diffs = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    seam_pic = float(np.abs(f[0] - f[-1]).mean())
    pic_ratio = seam_pic / (np.median(diffs) + 1e-6)

    d = np.abs(np.diff(x, axis=0)).max(axis=1)
    seam_jump = float(np.abs(x[0] - x[-1]).max())
    click_ratio = seam_jump / (np.percentile(d, 99.5) + 1e-9)

    win = int(0.1 * sr)
    edge_rms = float(np.sqrt(np.mean(np.concatenate([x[:win], x[-win:]]) ** 2)))
    body_rms = float(np.sqrt(np.mean(x ** 2)))
    edge_luma = float((f[0].mean() + f[-1].mean()) / 2)

    lst = qdir / "_loop.txt"
    lst.write_text(f"file '{mp4.resolve()}'\n" * 3)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(qdir / "loop_3x.mp4")])
    lst.unlink()

    res = {
        "video_dur": round(vdur, 3), "audio_dur": round(adur, 3), "av_mismatch_ms": round((adur - vdur) * 1000, 1),
        "seam_picture_ratio": round(pic_ratio, 2), "click_ratio": round(click_ratio, 2),
        "edge_rms_db": round(20 * np.log10(edge_rms + 1e-9), 1), "body_rms_db": round(20 * np.log10(body_rms + 1e-9), 1),
        "edge_luma": round(edge_luma, 1),
    }
    res["checks"] = {
        "av_match_<40ms": abs(res["av_mismatch_ms"]) < 40,
        "picture_seam_ok_(ratio<3)": pic_ratio < 3,
        "no_click_(ratio<1.5)": click_ratio < 1.5,
        "no_silence_at_seam": res["edge_rms_db"] > res["body_rms_db"] - 20,
        "no_black_at_seam": edge_luma > 12,
    }
    (qdir / "loop_report.json").write_text(json.dumps(res, indent=2))
    for k, ok in res["checks"].items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {k}")
    print(json.dumps({k: v for k, v in res.items() if k != "checks"}))


if __name__ == "__main__":
    main()
