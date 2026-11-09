"""render_needed.py - render ONLY the frames the edit actually shows, in parallel lanes, resumable.

    python render_needed.py VIDEO_NNN [--lanes 3] [--jobs shot_a shot_b] [--step 1] [--dry]

- Walks the EDL through the compositor (edl_engine.needed_frames).
- 3D jobs (in scene.blend JOBS) -> Blender lanes;  2D jobs -> VIDEOS/.../anim2d.py (multiprocessing).
- Skips frames already on disk, so a crashed run just continues.
- --step 2 renders every 2nd needed frame for a fast preview (compositor falls back to nearest frame).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "editing"))
import edl_engine as E  # noqa: E402

STUDIO = HERE.parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--lanes", type=int, default=2)
    ap.add_argument("--jobs", nargs="*")
    ap.add_argument("--step", type=int, default=1)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    E._init(a.video)
    vdir = E._VDIR
    need = E.needed_frames(E._EDL)
    jobs3d = {}
    jf = vdir / "jobs.json"
    if jf.exists():
        jobs3d = json.loads(jf.read_text())
    todo2d, todo3d = {}, {}
    for job, frames in need.items():
        if a.jobs and job not in a.jobs:
            continue
        frames = frames[::a.step]
        missing = [f for f in frames if not E.frame_path(job, f).exists()]
        if not missing:
            continue
        (todo3d if job in jobs3d else todo2d)[job] = missing
    total = sum(map(len, todo3d.values())) + sum(map(len, todo2d.values()))
    print(f"needed: {sum(map(len, need.values()))} frames, to render: {total}")
    for j, f in {**todo3d, **todo2d}.items():
        print(f"  {j:24s} {len(f):5d} frames {'(3D)' if j in todo3d else '(2D)'}")
    if a.dry or not total:
        return
    t0 = time.time()
    if todo2d:
        anim = vdir / "anim2d.py"
        args = [sys.executable, str(anim), "--frames-json", json.dumps(todo2d)]
        subprocess.run(args, check=True)
    if todo3d:
        blend = vdir / "scene.blend"
        tmp = vdir / "_lanes"
        tmp.mkdir(exist_ok=True)
        procs = []
        lane_items = [[] for _ in range(a.lanes)]
        k = 0
        for job, frames in todo3d.items():
            for f in frames:
                lane_items[k % a.lanes].append((job, f))
                k += 1
        for li, items in enumerate(lane_items):
            by_job = {}
            for job, f in items:
                by_job.setdefault(job, []).append(f)
            script = []
            for job, frames in by_job.items():
                ff = tmp / f"lane{li}_{job}.txt"
                ff.write_text(" ".join(map(str, frames)))
                script.append(["blender", "-b", str(blend), "-P", str(HERE / "render_shot.py"), "--",
                               a.video, job, str(ff)])
            cmd = " && ".join(" ".join(f'"{c}"' for c in s) + " > /dev/null 2>&1" for s in script)
            if cmd:
                procs.append(subprocess.Popen(["bash", "-c", cmd]))
        for p in procs:
            p.wait()
    dt = time.time() - t0
    print(f"rendered {total} frames in {dt:.1f}s ({dt / max(total, 1):.2f}s/frame)")
    log = vdir / "qc" / "render_log.json"
    log.parent.mkdir(exist_ok=True)
    hist = json.loads(log.read_text()) if log.exists() else []
    hist.append({"time": time.strftime("%F %T"), "frames": total, "seconds": round(dt, 1),
                 "jobs": {k: len(v) for k, v in {**todo3d, **todo2d}.items()}})
    log.write_text(json.dumps(hist, indent=2))


if __name__ == "__main__":
    main()
