"""qc_video.py - QA on the real export.

Checks: resolution / fps / codecs, duration, loudness + true peak, black segments, frozen segments,
contact sheet (every --every s). Writes VIDEOS/<V>/qc/qc_report.json + contact_sheet.jpg.
Usage: python qc_video.py EXPORTS/VIDEO_000.mp4 [--video VIDEO_000] [--every 1.0] [--min 30 --max 90]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

import numpy as np

STUDIO = Path(__file__).resolve().parents[2]


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = sh(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    return json.loads(r.stdout)


def loudness(path):
    r = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"])
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    lra = re.search(r"LRA:\s+(-?[\d.]+) LU", tail)
    return {"lufs": float(i.group(1)) if i else None, "true_peak": float(tp.group(1)) if tp else None,
            "lra": float(lra.group(1)) if lra else None}


def blacks(path, min_d=0.1):
    r = sh(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", f"blackdetect=d={min_d}:pix_th=0.08",
            "-an", "-f", "null", "-"])
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]


def freezes(path, min_d=0.6):
    r = sh(["ffmpeg", "-hide_banner", "-i", str(path), "-vf", f"freezedetect=n=0.001:d={min_d}",
            "-an", "-f", "null", "-"])
    st = [float(x) for x in re.findall(r"freeze_start: ([\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"freeze_end: ([\d.]+)", r.stderr)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def silences(path, min_d=1.0):
    r = sh(["ffmpeg", "-hide_banner", "-i", str(path), "-af", f"silencedetect=n=-50dB:d={min_d}",
            "-vn", "-f", "null", "-"])
    st = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", r.stderr)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    return list(zip(st, en + [None] * (len(st) - len(en))))


def contact_sheet(path, out, every=1.0, cols=6, tw=270):
    from PIL import Image, ImageDraw
    tmp = out.parent / "_cs"
    tmp.mkdir(parents=True, exist_ok=True)
    for f in tmp.glob("*.jpg"):
        f.unlink()
    sh(["ffmpeg", "-loglevel", "error", "-i", str(path), "-vf", f"fps=1/{every},scale={tw}:-1",
        str(tmp / "c_%04d.jpg")])
    ims = sorted(tmp.glob("c_*.jpg"))
    if not ims:
        return None
    a = Image.open(ims[0])
    th = a.height
    rows = int(np.ceil(len(ims) / cols))
    sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), "black")
    d = ImageDraw.Draw(sheet)
    for k, p in enumerate(ims):
        x, y = (k % cols) * tw, (k // cols) * (th + 24)
        sheet.paste(Image.open(p), (x, y + 24))
        d.text((x + 4, y + 4), f"{k * every:.1f}s", fill="white")
        p.unlink()
    tmp.rmdir()
    sheet.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mp4")
    ap.add_argument("--video")
    ap.add_argument("--every", type=float, default=1.0)
    ap.add_argument("--min", type=float, default=30)
    ap.add_argument("--max", type=float, default=90)
    a = ap.parse_args()
    mp4 = Path(a.mp4)
    video = a.video or mp4.stem
    qdir = STUDIO / "VIDEOS" / video / "qc"
    qdir.mkdir(parents=True, exist_ok=True)

    info = probe(mp4)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    num, den = map(int, v["r_frame_rate"].split("/"))
    dur = float(info["format"]["duration"])
    res = {"file": str(mp4), "width": v["width"], "height": v["height"], "fps": round(num / den, 3),
           "vcodec": v["codec_name"], "pix_fmt": v.get("pix_fmt"), "color_space": v.get("color_space"),
           "acodec": au["codec_name"] if au else None, "sample_rate": int(au["sample_rate"]) if au else None,
           "duration": round(dur, 3)}
    res.update(loudness(mp4) if au else {})
    res["black"] = blacks(mp4)
    res["frozen"] = freezes(mp4)
    res["silence"] = silences(mp4) if au else []
    checks = {
        "resolution_1080x1920": (res["width"], res["height"]) == (1080, 1920),
        "fps_30": abs(res["fps"] - 30) < 0.01,
        "h264": res["vcodec"] == "h264",
        "aac_48k": res["acodec"] == "aac" and res["sample_rate"] == 48000,
        f"duration_{a.min:g}-{a.max:g}s": a.min <= dur <= a.max,
        "lufs_-14_+-1": res.get("lufs") is not None and abs(res["lufs"] + 14) <= 1.0,
        "true_peak_<=-1": res.get("true_peak") is not None and res["true_peak"] <= -0.9,
        "no_black_>0.1s": not res["black"],
        "no_freeze_>0.6s": not res["frozen"],
    }
    res["checks"] = checks
    cs = contact_sheet(mp4, qdir / "contact_sheet.jpg", a.every)
    res["contact_sheet"] = str(cs) if cs else None
    (qdir / "qc_report.json").write_text(json.dumps(res, indent=2))
    for k, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {k}")
    print(f"  lufs={res.get('lufs')} tp={res.get('true_peak')} dur={dur:.2f}s")
    print("  black:", res["black"], " frozen:", res["frozen"])
    print("qc ->", qdir / "qc_report.json")


if __name__ == "__main__":
    main()
