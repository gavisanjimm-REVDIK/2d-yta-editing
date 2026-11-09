# VIDEO_001 – The Man Who Knew It Was Raining (2D, 55.7 s) – v2

Fair-play detective riddle in storybook 2D (`PIPELINE/twod/toon.py`). The mascot plays Detective Marcus
(`marcus_detective`: same face, hair and brown tee, plus a trench coat, fedora and magnifying glass).

## Story v2: the thief is not obvious
- **All three alibis mention the storm at a window.** Oliver: lightning lit the kitchen window. Daniel: lightning
  flashed through the basement window. Sophie: thunder rattled the laundry-room window. Daniel's line no longer
  stands out.
- **Every suspect shows the same kind of nerves.** Oliver fiddles with his tie, Daniel scratches his neck, Sophie
  startles at the thunder. All three sweat in the final shot.
- **The detective searches all three rooms the same way.** Laundry room, basement, kitchen: same length, same camera
  move, same sounds. The laundry room and the kitchen have windows that flash. The basement has none: thunder is heard
  down there, but nothing lights up.
- **Each alibi has a detail that fits** (dropped sheets in the laundry room, a toolbox and a puddle under the leaky
  pipe, a pot on the stove), so viewers must look past the obvious.
- **The recap** shows three framed room cards that light up as the narrator names each one. The video ends on all
  three suspects with "WHO IS LYING?". Nobody is singled out and the answer is never said.
- Creator-only answer: Daniel. The basement has no window.

## Changes in v2 (from feedback)
| request | fix |
|---|---|
| bald spot in the boy's hair | the bangs' top edge now follows the skull (`toon.py hair_front`) |
| models and fonts too big | close-ups 2650 → 1550 px tall; captions 88 → 66 px; speaker names smaller |
| floating elements | contact shadows under every character; candles on brass holders standing on surfaces; desk candelabra; table feet; real basement staircase; sheets lie on the floor |
| mouth animation | `twod/lipsync.py`: how far the mouth opens comes from the speaker's voice loudness per frame; its shape (wide/E, round/O, closed on M/B/P) comes from the letters; drawn as a viseme mouth. Measured: open 0.45 on average, closed 16% of speaking frames, ~7 changes/s (≈ syllable rate). Daniel's mouth now draws on top of his beard |
| proper detective | trench coat, belt, lapels, fedora, magnifying glass, notebook, flashlight |
| reactions fit the story | expression tracks per line (Harrison panic → shock; Marcus determined → suspicious → smug; suspects' reactions tied to their own words) |
| thief too obvious | new plot (see above) |

## Pipeline numbers
| step | result |
|---|---|
| voices | Kokoro-82M, 10 lines, all Whisper-clean (captions use the script's spelling, e.g. "Hmm") |
| render | 1821 frames, 160 s (0.09 s/frame); partial re-render 530 frames, 47 s |
| mix | master −14.2 LUFS, −1.1 dBTP |
| QC | all checks pass except the freeze check: frames from 51.6 s on are the intended end freeze-frame |

## Known weak spots
- TTS voices: clean, but less acted than a human performance
- walking is a simple bob (the search shots use standing poses)
- the mascot's shirt is brown, as in the reference sheet (an orange shirt was mentioned earlier; open question)
