"""edl_engine.py - compositor: EDL module -> finished mp4.

EDL = python module (VIDEOS/VIDEO_NNN/edit_videoNNN.py) with:
  DURATION   seconds
  SEGMENTS   list of dicts:
      {"t0": 0.0, "t1": 2.5, "src": "shot_room",        # job name -> frames/<job>/f_00000.png
       "src_t": 0.0,            # source time at t0 (number) or callable(t_global)->source time
       "speed": 1.0,            # source speed (ignored when src_t is callable)
       "fx": [ ...effects... ]}
      special src: "black", or "split" with {"split": [segA, segB], "dir": "v"|"h"}
  OVERLAYS   list of dicts {"type": title|chip|counter|timer|lower_third|hud|choice|stamp|custom, "t0", "t1", ...}
  CAPTIONS   dict {"words": [...timing words...] or None, "emphasis": [...], "pos": [(t0, t1, y)], "speakers": bool}
  AUDIO      path to mix (default audio/mix_master.wav)
  BEATS      dict of named times (computed from narration words) - optional, used by music/cues

Effects (times are GLOBAL seconds):
  {"fx": "zoom", "keys": [(t, scale, cx, cy[, ease]), ...]}   punch-in / slow push (cx, cy = 0..1 focus)
  {"fx": "shake", "t0", "t1", "amp": 18, "freq": 14}
  {"fx": "flash", "t": t, "dur": 0.12, "color": "#FFFFFF"}
  {"fx": "whip", "t": t, "dur": 0.2, "dir": 1}                 horizontal whip pan with motion blur
  {"fx": "freeze", "t0", "t1", "tint": "#3060FF", "amount": 0.35}  hold frame at t0, tinted
  {"fx": "rewind", "t0", "t1", "from_t": src_time}            VHS rewind (scrub source backwards + noise)
  {"fx": "pixelate", "t0", "t1", "size": 24}
  {"fx": "vignette", "strength": 0.5}
  {"fx": "speed_ramp", "keys": [(t, speed), ...]}             source-time integration (replaces speed)
  {"fx": "grade", "exposure": 0, "contrast": 1, "saturation": 1, "temp": 0}  gentle per-shot grade
  {"fx": "black", "t0", "t1"}                                 hard cut to black

Usage:
  python edl_engine.py VIDEO_000                 full export -> EXPORTS/VIDEO_000.mp4
  python edl_engine.py VIDEO_000 --stills 0.5    contact frames every 0.5 s -> qc/stills/
  python edl_engine.py VIDEO_000 --needed        print needed (job, frame) list as json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import skia

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "twod"))
from kit import W, H, FPS, SAFE, key, rgb, paint, text, text_width, typeface, clamp, EASE  # noqa: E402

STUDIO = HERE.parents[1]
STYLE = json.loads((STUDIO / "config" / "style.json").read_text())

_EDL = None
_VDIR = None


# ================================================================ loading
def load_edl(video: str):
    vdir = STUDIO / "VIDEOS" / video
    cands = sorted(vdir.glob("edit_*.py"))
    if not cands:
        raise SystemExit(f"no edit_*.py in {vdir}")
    spec = importlib.util.spec_from_file_location("edl_" + video, cands[0])
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(vdir))
    spec.loader.exec_module(m)
    return m, vdir


def _init(video):
    global _EDL, _VDIR
    _EDL, _VDIR = load_edl(video)


# ================================================================ time mapping
def seg_at(t, segs):
    for s in segs:
        if s["t0"] <= t < s["t1"]:
            return s
    return segs[-1] if segs and t >= segs[-1]["t0"] else None


def fx_of(seg, name):
    return [f for f in seg.get("fx", []) if f["fx"] == name]


def source_time(seg, t):
    for f in fx_of(seg, "freeze"):
        if f["t0"] <= t < f["t1"]:
            t = f["t0"]
    for f in fx_of(seg, "rewind"):
        if f["t0"] <= t < f["t1"]:
            u = (t - f["t0"]) / (f["t1"] - f["t0"])
            cur = source_time({**seg, "fx": []}, f["t0"])
            return cur + (f["from_t"] - cur) * EASE["io"](u)
    st = seg.get("src_t", 0.0)
    if callable(st):
        return st(t)
    ramps = fx_of(seg, "speed_ramp")
    if ramps:
        keys = ramps[0]["keys"]
        n = max(int((t - seg["t0"]) * FPS * 4), 1)
        ts = np.linspace(seg["t0"], t, n + 1)
        sp = [key(x, [(k[0], k[1], "io") for k in keys]) for x in ts]
        return st + float(np.trapz(sp, ts))
    return st + (t - seg["t0"]) * seg.get("speed", 1.0)


def frame_index(src_t):
    return max(int(round(src_t * FPS)), 0)


def needed_frames(edl, step=1):
    """{job: sorted frames} actually shown by the edit."""
    need: dict[str, set] = {}
    n = int(round(edl.DURATION * FPS))
    for i in range(0, n, step):
        t = i / FPS
        seg = seg_at(t, edl.SEGMENTS)
        if not seg:
            continue
        subs = seg["split"] if seg.get("src") == "split" else [seg]
        for s in subs:
            if s.get("src") in (None, "black"):
                continue
            need.setdefault(s["src"], set()).add(frame_index(source_time(s, t)))
    return {k: sorted(v) for k, v in need.items()}


# ================================================================ source frames
def frame_path(job, idx):
    return _VDIR / "frames" / job / f"f_{idx:05d}.png"


@lru_cache(maxsize=64)
def load_frame(job, idx):
    p = frame_path(job, idx)
    if not p.exists():
        # nearest existing frame (render_needed may skip) else placeholder
        d = p.parent
        if d.exists():
            for k in range(1, 4):
                for j in (idx - k, idx + k):
                    q = frame_path(job, j)
                    if q.exists():
                        return skia.Image.open(str(q))
        return _placeholder(job, idx)
    return skia.Image.open(str(p))


def _placeholder(job, idx):
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(rgb("#402040"))
    text(c, "MISSING FRAME", W / 2, H / 2 - 60, 80, "#FF66CC")
    text(c, f"{job}  f{idx}", W / 2, H / 2 + 60, 60, "#FFFFFF")
    return surf.makeImageSnapshot()


def draw_cover(canvas, img, rect):
    """Draw img scaled to cover rect (x, y, w, h)."""
    x, y, w, h = rect
    s = max(w / img.width(), h / img.height())
    dw, dh = img.width() * s, img.height() * s
    canvas.save()
    canvas.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    canvas.drawImageRect(img, skia.Rect.MakeXYWH(x + (w - dw) / 2, y + (h - dh) / 2, dw, dh),
                         skia.SamplingOptions(skia.FilterMode.kLinear, skia.MipmapMode.kLinear))
    canvas.restore()


# ================================================================ picture
def draw_segment(canvas, seg, t, rect=(0, 0, W, H)):
    if seg.get("src") == "black":
        canvas.drawRect(skia.Rect.MakeXYWH(*rect), paint("#000000"))
        return
    if seg.get("src") == "split":
        subs = seg["split"]
        n = len(subs)
        x, y, w, h = rect
        gap = seg.get("gap", 8)
        for i, s in enumerate(subs):
            if seg.get("dir", "v") == "v":
                r = (x, y + i * (h + gap) / n, w, h / n - gap * (n - 1) / n)
            else:
                r = (x + i * (w + gap) / n, y, w / n - gap * (n - 1) / n, h)
            draw_segment(canvas, s, t, r)
        return

    img = load_frame(seg["src"], frame_index(source_time(seg, t)))
    x, y, w, h = rect
    canvas.save()
    canvas.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    # zoom (punch-in / push)
    for z in fx_of(seg, "zoom"):
        keys = [(k[0], (k[1], k[2], k[3]), k[4] if len(k) > 4 else "io") for k in z["keys"]]
        sc, cx, cy = key(t, keys)
        px, py = x + cx * w, y + cy * h
        canvas.translate(px, py)
        canvas.scale(sc, sc)
        canvas.translate(-px, -py)
    # shake
    for f in fx_of(seg, "shake"):
        if f["t0"] <= t < f["t1"]:
            u = (t - f["t0"]) / (f["t1"] - f["t0"])
            a = f.get("amp", 18) * (1 - u) ** 1.5
            fr = f.get("freq", 14)
            canvas.translate(a * math.sin(t * fr * 6.1), a * math.cos(t * fr * 7.3))
    # whip pan
    blur = 0
    for f in fx_of(seg, "whip"):
        d = f.get("dur", 0.2)
        if abs(t - f["t"]) < d / 2:
            u = (t - f["t"]) / d + 0.5
            canvas.translate(f.get("dir", 1) * (u - 0.5) * w * 0.6, 0)
            blur = 60 * math.sin(u * math.pi)
    p = skia.Paint()
    if blur > 1:
        p.setImageFilter(skia.ImageFilters.Blur(blur, 0.5))
    canvas.saveLayer(None, p)
    draw_cover(canvas, img, rect)
    canvas.restore()
    canvas.restore()

    # post effects within rect
    r = skia.Rect.MakeXYWH(x, y, w, h)
    for f in fx_of(seg, "grade"):
        _grade(canvas, r, f)
    for f in fx_of(seg, "freeze"):
        if f["t0"] <= t < f["t1"]:
            canvas.drawRect(r, paint(f.get("tint", "#3060FF"), alpha=f.get("amount", 0.3),
                                     blend=skia.BlendMode.kColor))
    for f in fx_of(seg, "rewind"):
        if f["t0"] <= t < f["t1"]:
            _vhs(canvas, r, t)
    for f in fx_of(seg, "pixelate"):
        if f["t0"] <= t < f["t1"]:
            _pixelate(canvas, r, f.get("size", 24))
    for f in fx_of(seg, "vignette"):
        from flat import vignette
        vignette(canvas, f.get("strength", 0.5))


def _grade(canvas, r, f):
    c = f.get("contrast", 1.0)
    s = f.get("saturation", 1.0)
    e = 2 ** f.get("exposure", 0.0)
    tmp = f.get("temp", 0.0)
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    sat = [lr * (1 - s) + s, lg * (1 - s), lb * (1 - s),
           lr * (1 - s), lg * (1 - s) + s, lb * (1 - s),
           lr * (1 - s), lg * (1 - s), lb * (1 - s) + s]
    m = []
    for row, tint in zip(range(3), (1 + tmp * 0.08, 1.0, 1 - tmp * 0.08)):
        k = c * e * tint
        m += [sat[row * 3] * k, sat[row * 3 + 1] * k, sat[row * 3 + 2] * k, 0, (1 - c) * 0.5]
    m += [0, 0, 0, 1, 0]
    p = skia.Paint(ColorFilter=skia.ColorFilters.Matrix(m))
    surf = canvas.getSurface()
    if surf is None:
        return
    snap = surf.makeImageSnapshot()
    canvas.save()
    canvas.resetMatrix()
    canvas.clipRect(r)
    canvas.drawImage(snap, 0, 0, skia.SamplingOptions(), p)
    canvas.restore()


def _vhs(canvas, r, t):
    rng = np.random.default_rng(int(t * 1000))
    for _ in range(6):
        yy = r.top() + rng.uniform(0, r.height())
        canvas.drawRect(skia.Rect(r.left(), yy, r.right(), yy + rng.uniform(4, 22)),
                        paint("#FFFFFF", alpha=rng.uniform(0.08, 0.25)))
    text(canvas, "◀◀", r.left() + 120, r.top() + 160, 70, "#FFFFFF", face="DejaVuSans-Bold.ttf", align="left")


def _pixelate(canvas, r, size):
    surf = canvas.getSurface()
    if surf is None:
        return
    snap = surf.makeImageSnapshot()
    small_w, small_h = max(int(r.width() / size), 1), max(int(r.height() / size), 1)
    small = skia.Surface(small_w, small_h)
    small.getCanvas().drawImageRect(snap, r, skia.Rect(0, 0, small_w, small_h), skia.SamplingOptions())
    canvas.save()
    canvas.clipRect(r)
    canvas.drawImageRect(small.makeImageSnapshot(), r, skia.SamplingOptions(skia.FilterMode.kNearest))
    canvas.restore()


def global_fx(canvas, t, segs):
    seg = seg_at(t, segs)
    if not seg:
        return
    for f in fx_of(seg, "flash"):
        d = f.get("dur", 0.12)
        if f["t"] <= t < f["t"] + d:
            canvas.drawPaint(paint(f.get("color", "#FFFFFF"), alpha=1 - (t - f["t"]) / d))
    for f in fx_of(seg, "black"):
        if f["t0"] <= t < f["t1"]:
            canvas.drawPaint(paint("#000000"))


# ================================================================ overlays
def safe_rect(x, y, w, h, margin=SAFE):
    """Clamp a box into safe area; scale down if bigger than safe area. Returns (x, y, scale)."""
    sw, sh = W - 2 * margin, H - 2 * margin
    s = min(1.0, sw / max(w, 1), sh / max(h, 1))
    w, h = w * s, h * s
    return clamp(x, margin, W - margin - w), clamp(y, margin, H - margin - h), s


def paste(canvas, img, x, y, anchor="center", alpha=1.0, scale=1.0):
    """Paste a skia.Image respecting safe area. anchor: center|topleft."""
    w, h = img.width() * scale, img.height() * scale
    if anchor == "center":
        x, y = x - w / 2, y - h / 2
    x, y, s = safe_rect(x, y, w, h)
    p = skia.Paint()
    p.setAlphaf(alpha)
    canvas.drawImageRect(img, skia.Rect.MakeXYWH(x, y, w * s, h * s),
                         skia.SamplingOptions(skia.FilterMode.kLinear), p)


def _anim_in_out(t, t0, t1, dur=0.15):
    a = clamp((t - t0) / dur)
    b = clamp((t1 - t) / dur)
    return EASE["back"](a) if a < 1 else 1.0, min(a, b)


def _pill(canvas, label, cx, cy, size, fg, bg, alpha, scale=1.0):
    face = STYLE["fonts"]["ui"]
    size *= scale
    while size > 12 and text_width(label, size, face) + size > W - 2 * SAFE:
        size *= 0.95
    tw = text_width(label, size, face)
    pw, ph = tw + size * 0.9, size * 1.35
    x, y, _ = safe_rect(cx - pw / 2, cy - ph / 2, pw, ph)
    canvas.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, pw, ph), ph / 2, ph / 2),
                     paint(bg, alpha=0.9 * alpha))
    text(canvas, label, x + pw / 2, y + ph * 0.5 + size * 0.36, size, fg, face=face, shadow=False, alpha=alpha)
    return x, y, pw, ph


def draw_overlay(canvas, o, t):
    if not (o["t0"] <= t < o["t1"]):
        return
    sc, al = _anim_in_out(t, o["t0"], o["t1"], o.get("anim", 0.15))
    acc = STYLE["colors"]["accent"]
    typ = o["type"]
    if typ == "title":
        size = o.get("size", 120) * (0.85 + 0.15 * sc)
        text(canvas, o["text"], W / 2, o.get("y", H * 0.18), size, o.get("color", "#FFFFFF"),
             face=STYLE["fonts"]["title"], alpha=al)
    elif typ in ("chip", "stamp"):
        _pill(canvas, o["text"], o.get("x", W / 2), o.get("y", H * 0.12), o.get("size", 48),
              o.get("fg", "#FFFFFF"), o.get("bg", acc), al, sc)
    elif typ == "counter":
        v = key(t, [(k[0], k[1], k[2] if len(k) > 2 else "out") for k in o["keys"]])
        label = o.get("fmt", "{:,.0f}").format(v)
        _pill(canvas, (o.get("prefix", "") + label + o.get("suffix", "")), o.get("x", W / 2),
              o.get("y", H * 0.12), o.get("size", 56), "#FFFFFF", "#000000", al)
    elif typ == "timer":
        rem = max(o["from"] - (t - o["t0"]) * o.get("rate", 1.0), 0)
        label = f"{int(rem // 60):02d}:{rem % 60:05.2f}" if o.get("ms") else f"{int(rem // 60):02d}:{int(rem % 60):02d}"
        hot = rem < o.get("warn", 5)
        _pill(canvas, label, o.get("x", W / 2), o.get("y", H * 0.1), o.get("size", 60),
              "#FFFFFF", acc if hot else "#000000", al)
    elif typ == "lower_third":
        y = o.get("y", H * 0.8)
        x0 = SAFE + 20 - (1 - sc) * 400
        canvas.drawRect(skia.Rect.MakeXYWH(x0, y, 10, 120), paint(acc, alpha=al))
        text(canvas, o["name"], x0 + 30, y + 60, 62, "#FFFFFF", face=STYLE["fonts"]["title"], align="left", alpha=al)
        if o.get("sub"):
            text(canvas, o["sub"], x0 + 30, y + 112, 36, "#DDDDDD", face=STYLE["fonts"]["ui"], align="left", alpha=al)
    elif typ == "hud":
        items = o["items"]  # [(label, value_or_keys, flash_times)]
        n = len(items)
        cw = (W - 2 * SAFE) / n
        for i, it in enumerate(items):
            label, val = it[0], it[1]
            if isinstance(val, list):
                val = key(t, [(k[0], k[1], "step") for k in val])
            flash = any(0 <= t - ft < 0.4 for ft in (it[2] if len(it) > 2 else []))
            cx = SAFE + cw * (i + 0.5)
            _pill(canvas, f"{label} {val}", cx, o.get("y", SAFE + 50), o.get("size", 34),
                  "#FFFFFF", acc if flash else "#000000", al)
    elif typ == "choice":
        opts = o["options"]
        y0 = o.get("y", H * 0.62)
        for i, op in enumerate(opts):
            _pill(canvas, f"{i + 1}  {op}", W / 2, y0 + i * 110, 46, "#FFFFFF", "#000000", al,
                  clamp((t - o["t0"] - i * 0.12) / 0.2))
    elif typ == "custom":
        o["draw"](canvas, t, al)


# ================================================================ captions
def build_phrases(words, max_words=4, max_gap=0.35):
    """Group words into short phrases: <=max_words, break at punctuation or pauses or line change."""
    phrases, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        brk = (len(cur) >= max_words or w["word"].rstrip()[-1:] in ".,!?;:" or nxt is None
               or nxt["start"] - w["end"] > max_gap or nxt.get("line") != w.get("line"))
        if brk:
            phrases.append({"t0": cur[0]["start"], "t1": cur[-1]["end"], "words": cur,
                            "who": cur[0].get("who")})
            cur = []
    for i, p in enumerate(phrases):  # hold until next phrase (max +0.4s)
        nxt = phrases[i + 1]["t0"] if i + 1 < len(phrases) else p["t1"] + 0.4
        p["t1"] = min(nxt, p["t1"] + 0.4)
    return phrases


@lru_cache(maxsize=1)
def _phrases_cached(key_):
    cap = _EDL.CAPTIONS
    return build_phrases(cap["words"], cap.get("max_words", 4))


def draw_captions(canvas, t):
    cap = getattr(_EDL, "CAPTIONS", None)
    if not cap or not cap.get("words"):
        return
    st = STYLE["captions"]
    phrases = _phrases_cached(id(cap))
    ph = next((p for p in phrases if p["t0"] <= t < p["t1"]), None)
    if not ph:
        return
    y = st["y"] * H
    for (a, b, yy) in cap.get("pos", []):
        if a <= t < b:
            y = yy * H if yy <= 1 else yy
    emph = {e.lower() for e in cap.get("emphasis", [])}
    face = STYLE["fonts"]["caption"]
    size = st["size"]
    toks = [w["word"].strip() for w in ph["words"]]
    if st.get("uppercase", True):
        toks = [x.upper() for x in toks]
    space = size * 0.25
    while size > 30:
        widths = [text_width(x, size, face) for x in toks]
        total = sum(widths) + space * (len(toks) - 1)
        if total <= W - 2 * SAFE - 20:
            break
        size *= 0.94
        space = size * 0.25
    pop = clamp((t - ph["t0"]) / 0.09)
    scale = 0.88 + 0.12 * EASE["back"](pop)
    canvas.save()
    canvas.translate(W / 2, y)
    canvas.scale(scale, scale)
    if cap.get("speakers") and ph.get("who") and ph["who"] != "narrator":
        text(canvas, ph["who"].upper(), 0, -size * 1.05, size * 0.42, st["speaker_color"], face=face,
             max_w=W - 2 * SAFE)
    x = -total / 2
    for w, tok, wd in zip(ph["words"], toks, widths):
        clean = "".join(ch for ch in w["word"].lower() if ch.isalnum() or ch == "'")
        col = STYLE["colors"]["accent"] if clean in emph else st["color"]
        if st.get("karaoke") and t < w["start"]:
            col = st["upcoming_color"]
        font = skia.Font(typeface(face), size)
        blob = skia.TextBlob(tok, font)
        canvas.drawTextBlob(blob, x, 0, paint(st["outline_color"], stroke=st["outline"] * size / 100))
        sp = paint("#000000", alpha=0.5)
        sp.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, size * 0.08))
        canvas.drawTextBlob(blob, x + 2, size * 0.06, sp)
        canvas.drawTextBlob(blob, x, 0, paint(col))
        x += wd + space
    canvas.restore()


# ================================================================ frame render
def render_frame(i):
    t = i / FPS
    surf = skia.Surface(W, H)
    c = surf.getCanvas()
    c.clear(skia.ColorBLACK)
    seg = seg_at(t, _EDL.SEGMENTS)
    if seg:
        draw_segment(c, seg, t)
    global_fx(c, t, _EDL.SEGMENTS)
    for o in getattr(_EDL, "OVERLAYS", []):
        draw_overlay(c, o, t)
    draw_captions(c, t)
    return surf.makeImageSnapshot()


def frame_bytes(i):
    img = render_frame(i)
    return img.toarray(colorType=skia.kRGBA_8888_ColorType).tobytes()


def _worker_init(video):
    _init(video)


def export(video, out=None, workers=None, crf=18, preset="slow"):
    _init(video)
    n = int(round(_EDL.DURATION * FPS))
    out = Path(out or STUDIO / "EXPORTS" / f"{video}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    audio = _VDIR / getattr(_EDL, "AUDIO", "audio/mix_master.wav")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if audio.exists():
        cmd += ["-i", str(audio)]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-color_range", "tv", "-r", str(FPS)]
    if audio.exists():
        cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-af", "apad", "-t", f"{n / FPS:.3f}"]
    else:
        print("  ! no audio mix found - exporting silent video")
    cmd += ["-movflags", "+faststart", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    workers = workers or max(os.cpu_count() - 1, 1)
    with Pool(workers, initializer=_worker_init, initargs=(video,)) as pool:
        for k, b in enumerate(pool.imap(frame_bytes, range(n), chunksize=4)):
            proc.stdin.write(b)
            if k % 60 == 0:
                print(f"  frame {k}/{n}", end="\r")
    proc.stdin.close()
    proc.wait()
    print(f"\nexport -> {out}")
    return out


def stills(video, every=0.5):
    _init(video)
    d = _VDIR / "qc" / "stills"
    d.mkdir(parents=True, exist_ok=True)
    t = 0.0
    while t < _EDL.DURATION:
        img = render_frame(int(round(t * FPS)))
        img.save(str(d / f"t{t:06.2f}.png"), skia.kPNG)
        t += every
    print("stills ->", d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--stills", type=float)
    ap.add_argument("--needed", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--preview", action="store_true", help="fast encode (veryfast, crf 23)")
    a = ap.parse_args()
    if a.needed:
        _init(a.video)
        print(json.dumps(needed_frames(_EDL)))
    elif a.stills:
        stills(a.video, a.stills)
    else:
        export(a.video, a.out, a.workers, *((23, "veryfast") if a.preview else (18, "slow")))


if __name__ == "__main__":
    main()
