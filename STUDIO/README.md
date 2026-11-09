# STUDIO – automated short-video pipeline (3D + 2D)

Story idea → finished vertical Short (1080×1920, 30 fps, H.264/AAC) with no manual editing.
Free / open-source, CPU only. Art direction: [`STYLE_BIBLE.md`](STYLE_BIBLE.md).

## Setup
```bash
bash STUDIO/setup.sh            # python deps, Blender 4.2 LTS, Mesa (CPU EEVEE), fonts
bash STUDIO/setup.sh --tts      # + Chatterbox TTS + faster-whisper (big: torch CPU)
```

## One command
```bash
python STUDIO/studio.py VIDEO_000 all                      # narrate→sfx→cues→music→mix→scene→render→export→qc
python STUDIO/studio.py VIDEO_000 stills                   # test stills of every shot + edit stills
python STUDIO/studio.py VIDEO_000 export,qc                # re-cut only (2D fixes never need a re-render)
python STUDIO/studio.py - new VIDEO_001 3d                 # new video from _TEMPLATE (+ blender script)
python STUDIO/studio.py - mascot                           # mascot turnaround + expression sheet
```

## Layout
```
STUDIO/
  studio.py              one-command runner
  STYLE_BIBLE.md         art direction rules + final checklist
  config/style.json      fonts, caption style, accent colour, render + loudness targets
  PIPELINE/
    tts/                 narrate.py (takes → whisper check → best take → word timing.json), voice_qc.py
    audio/               dsp.py, sfx_lib.py (@reg effects → AUDIO/sound_effects + LIBRARY.json),
                         music_gen.py (Score + cue_videoNNN), mix.py (cues.json → mix_master.wav)
    blender_scripts/     studio_lib/ core, materials, mascot, perform, lights, cameras, sets, toon
                         videos/videoNNN.py (scene + acting + cameras + JOBS), tools/mascot_turnaround.py
    twod/                flat.py (vector puppet + paint helpers), kit.py (keys, blink, text, perspective cam)
    rendering/           render_shot.py, render_needed.py, test_stills.py
    editing/             edl_engine.py (EDL → mp4: effects, overlays, captions, encode)
    quality_control/     qc_video.py, loop_test.py
  VIDEOS/_TEMPLATE/      script.json, edit_template.py, audio/build_cues.py, README.md
  VIDEOS/VIDEO_NNN/      script.json, edit_videoNNN.py, anim2d.py (2D) | scene.blend (3D), audio/, qc/, README.md
  ASSETS/                fonts/ (OFL), mascot/ (spec, reference/, turnaround/), refs/style/ (reference video)
  AUDIO/sound_effects/   generated SFX library (regenerate with sfx_lib.py)
  EXPORTS/               final mp4s
```

## How a video is made
1. **Story** – 2–3 concepts → pick one → beat sheet → score 3 hooks → loop plan. Fill the video README.
2. **Script** – `script.json` → `narrate` (N takes/line, Whisper-checked, word timing).
3. **Picture** – 3D: `videos/videoNNN.py` (set, mascot acting from word timing, cameras, `JOBS`) → `stills` → fix framing.
   2D: `anim2d.py` with one `shot_NAME(canvas, t)` per shot.
4. **Edit** – `edit_videoNNN.py`: `SEGMENTS`, `OVERLAYS`, `CAPTIONS`, beats from words → `build_cues.py` → `music` → `mix`.
5. **Render** only needed frames → **export** → *show the video* → **qc** → fix → final export → README report → commit.

## Status (honest)
| part | state |
|---|---|
| audio: dsp, 20 SFX, music, mix | working – VIDEO_000 mix measured −14.0 LUFS / −1.0 dBTP |
| 2D: puppet, kit, anim2d | working – 0.05 s/frame on this container |
| edit engine + captions + encode | working – VIDEO_000 exported, all QC checks pass |
| QC: qc_video, loop_test | qc_video run on VIDEO_000; loop_test written, not yet run on a loop video |
| Blender studio_lib + mascot | builds & renders (EEVEE on CPU, ~6–11 s per 540×960 frame); 3D template scene + test stills checked |
| acting | expressions, blinks, brows, eye target (limited ±32°), relaxed arms, walk cycle checked in renders; gestures `wave`/`think`/`shrug` still rough |
| mascot look | **placeholder** – waiting for reference images (`ASSETS/mascot/reference/`) |
| TTS (Chatterbox) | code written, **not installed/tested** here; `placeholder` backend = silent audio + estimated word timing |
