# VIDEO_001 – The Man Who Knew It Was Raining (2D, 56.6 s)

Detective riddle. Style: storybook 2D (`PIPELINE/twod/toon.py`), mascot = Detective Marcus, built from
`ASSETS/mascot/reference/character_sheet.webp`.

## Script changes (and why)
- **The answer is no longer said out loud.** The original Scene 4/5 lines ("HOW did you see lightning when this
  basement has NO WINDOWS?", "a window that doesn't even exist") give the answer away, which the brief forbids.
  The detective now stops at *"Then explain something to me…"* while his flashlight sweeps solid stone walls.
  The narrator ends with *"So, who is lying? And how did he know?"*
- **The clue stays fair and visual.** The hook already shows the basement: bare stone, pipes, no window. Lightning
  lights up every room that has windows (exterior, study, foyer). Inside the basement there is thunder but never a
  flash. Viewers who watch closely can solve it.
- **Tighter, more natural dialogue.** For example Oliver: *"In the kitchen, sir, preparing dinner. I never left."*
  Daniel: *"Yes! Clear as day. What's wrong with that?"*
- **The recap is a parchment "case file"** listing what each suspect said (kitchen, upstairs, basement). It does not
  give the answer.
- Creator-only answer (not in the video): Daniel's alibi is impossible because the basement has no windows.

## Pipeline
| step | result |
|---|---|
| voices | Kokoro-82M: narrator bm_george, Harrison bm_lewis, Marcus am_adam, Oliver bm_fable, Daniel am_eric, Sophie bf_emma. 12/12 lines Whisper-clean. ~60 s total. |
| shots | 14 segments, 10 shot functions; backgrounds cached per process |
| render | 1548 needed frames, 153 s (0.10 s/frame, 2D Skia, all cores); close-up re-render 543 frames, 38 s |
| export | ~105 s (x264 slow, CRF 18) |
| mix | voice −16 LUFS, music −26, SFX −25, rain −38 (stems). Master −14.1 LUFS, −1.1 dBTP |
| QC | 1080×1920 · 30 fps · h264/aac 48k · 56.57 s · loudness/peak pass · no black. The "freeze" check flags 52.5–56.5 s: this is the intentional end freeze-frame |

## Fixed after QA
- captions covered faces in the close-ups → captions drop to the torso (y 0.88) for every close-up
- caption showed "NINE O / 'CLOCK" → Whisper apostrophe splits are merged (fixed in narrate.py too)
- black strips at the edges of close-ups → the background camera is clamped
- speaker names were tiny and off-centre → bigger, centred, outlined
- foyer wide: the detective hid Oliver → reframed as an over-the-shoulder shot

## Known weak spots
- the voices are TTS: clean, but less acted than a human performance
- the "folded laundry" prop is a plain white block
- the mascot's shirt is **brown**, as in the reference sheet (earlier notes said orange; needs your call)
- walking is simple: front-step bob only, no side-view walk cycle
