# VIDEO_000 – pipeline test (2D, 10 s)

Purpose: prove the pipeline end-to-end (one character, one room, two narration lines). Not a channel video.

Story: quiet room → "Until the lamp turns on by itself" → lamp snaps on, mascot startles and points.

## Run
```bash
python STUDIO/studio.py VIDEO_000 narrate,sfx,cues,music,mix,render,export,qc
```

## Report (2026-11-09)
| step | result |
|---|---|
| narration | **placeholder backend** – silent track, estimated word timing (Chatterbox not installed yet) |
| render | 300 needed frames (room 245, face 55), 2D Skia: 13.8 s total (0.05 s/frame) |
| export | ~17 s (x264 slow CRF 18) |
| QC | 1080×1920 · 30 fps · h264 · aac 48 kHz · −14.0 LUFS · −1.0 dBTP · no black · no freeze → all pass |

Fixed after first QA pass:
- blink lid drew a big skin rectangle across the face in close-up → lid now clipped to the eye + lash line
- captions covered the face in the close-up → caption position override to top during that segment
- mascot lip-synced the narrator → narrator is off-screen, mouth now still
- 0.7 s near-freeze in the wide shot → glances, weight-shift sway, stronger push-in

Known weak spots: silent narration; 2D puppet is a test asset (channel videos are 3D).
