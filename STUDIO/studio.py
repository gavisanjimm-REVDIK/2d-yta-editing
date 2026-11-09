"""studio.py - one command for every step. Every step is re-runnable.

    python STUDIO/studio.py VIDEO_000 all            narrate -> sfx -> cues -> music -> mix -> scene(3D) -> render -> export -> qc
    python STUDIO/studio.py VIDEO_000 narrate|sfx|cues|music|mix|scene|stills|render|export|preview|qc|loop
    python STUDIO/studio.py - mascot                 mascot turnaround + expression sheet (ASSETS/mascot/turnaround)
    python STUDIO/studio.py - new VIDEO_001 [2d|3d]  scaffold a new video folder from _TEMPLATE

Mode is auto: a video with scene.py-built jobs.json (or blender_scripts/videos/videoNNN.py) is 3D, anim2d.py is 2D.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

S = Path(__file__).resolve().parent
P = S / "PIPELINE"
PY = sys.executable


def run(*cmd, cwd=None):
    print("\n$", " ".join(str(c) for c in cmd), flush=True)
    t = time.time()
    subprocess.run([str(c) for c in cmd], check=True, cwd=cwd)
    print(f"  ({time.time() - t:.1f}s)")


def video_num(v):
    return v.split("_")[-1]


def blender_script(v):
    return P / "blender_scripts" / "videos" / f"video{video_num(v)}.py"


def step(v, name):
    vdir = S / "VIDEOS" / v
    if name == "narrate":
        run(PY, P / "tts" / "narrate.py", v)
    elif name == "voiceqc":
        run(PY, P / "tts" / "voice_qc.py", v)
    elif name == "sfx":
        run(PY, P / "audio" / "sfx_lib.py")
    elif name == "cues":
        run(PY, vdir / "audio" / "build_cues.py")
    elif name == "music":
        run(PY, P / "audio" / "music_gen.py", v)
    elif name == "mix":
        run(PY, P / "audio" / "mix.py", v)
    elif name == "scene":
        if blender_script(v).exists():
            run("blender", "-b", "-P", blender_script(v), "--", v)
        else:
            print("  (no 3D scene script - 2D video)")
    elif name == "stills":
        if (vdir / "scene.blend").exists():
            run("blender", "-b", vdir / "scene.blend", "-P", P / "rendering" / "test_stills.py", "--", v)
        run(PY, P / "editing" / "edl_engine.py", v, "--stills", "1.0")
    elif name == "render":
        run(PY, P / "rendering" / "render_needed.py", v)
    elif name == "export":
        run(PY, P / "editing" / "edl_engine.py", v)
    elif name == "preview":
        run(PY, P / "editing" / "edl_engine.py", v, "--preview", "--out", S / "EXPORTS" / f"{v}_preview.mp4")
    elif name == "qc":
        run(PY, P / "quality_control" / "qc_video.py", S / "EXPORTS" / f"{v}.mp4", "--video", v,
            *(["--min", "5"] if v == "VIDEO_000" else []))
    elif name == "loop":
        run(PY, P / "quality_control" / "loop_test.py", S / "EXPORTS" / f"{v}.mp4", "--video", v)
    else:
        raise SystemExit(f"unknown step {name}")


ALL = ["narrate", "sfx", "cues", "music", "mix", "scene", "render", "export", "qc"]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return
    v, cmd = sys.argv[1], sys.argv[2]
    if cmd == "mascot":
        run("blender", "-b", "-P", P / "blender_scripts" / "tools" / "mascot_turnaround.py")
        return
    if cmd == "new":
        new, mode = sys.argv[3], (sys.argv[4] if len(sys.argv) > 4 else "3d")
        dst = S / "VIDEOS" / new
        shutil.copytree(S / "VIDEOS" / "_TEMPLATE", dst)
        n = video_num(new)
        (dst / "edit_template.py").rename(dst / f"edit_video{n}.py")
        if mode == "3d":
            shutil.copy(P / "blender_scripts" / "videos" / "video_template.py", blender_script(new))
            print("  3D scene script:", blender_script(new))
        print("new video ->", dst)
        return
    t0 = time.time()
    for name in (ALL if cmd == "all" else cmd.split(",")):
        step(v, name)
    print(f"\ndone in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
