# VIDEO_002 – Death by Pudding (2D, 59.9 s) – v2

Comedy murder-mystery riddle in the same storybook 2D style. Detective Marcus returns.

## Story
Lord Pumpernickel is found face-down in his pudding: poisoned. A blizzard rages outside. Marcus walks in covered in
snow ("Phew, what a blizzard!") and interviews three suspects:
- **Chef Gaston** waves a giant cleaver and sobs: "I made the pudding at six, then chopped onions all night. That's
  why I'm crying!" (red herring)
- **Miss Prim** was typing the Lord's new will: "He left everything to his cat." (red herring: motive)
- **Nephew Cedric**: "I only just got here. My car pulled in right before yours, detective."

Marcus searches the kitchen, the library and the hall. Each room gets the same time, framing and sounds. "Case
closed." The recap shows three room cards. "And no, it wasn't the cat." / WHO IS THE KILLER?

## Creator-only answer (never in the video)
**Cedric.** Through the hall window (seen in the trio shot, Marcus's arrival, the hall search and the recap card),
Marcus's blue car has only a thin dusting of snow, while Cedric's red car is buried under a deep mound. Only a
tail light and a mirror peek out, so it has been parked for hours. Backup clues:
- Marcus walks in covered in snow, but Cedric has none on him.
- The doormat shows only one set of wet footprints (Marcus's).
- The mansion exterior shows both cars, at the exact moment the narrator says "one tiny clue that almost everyone
  misses".

## v2 changes (from feedback)
| request | fix |
|---|---|
| messy hand placement | `toon.py`: arms whose hand is above the shoulder now draw in front of the face and hat (fist under the chin, salute, raised cleaver were hidden behind the head). Hands-on-hips fit each body (Gaston's belly). New presets: `chin`, `salute`, `magnify`, `brush`, `raise_tool`. Magnifier held out to the side, keys hang from Cedric's hand |
| voices all the same tone | five distinct voices. Suspects use ElevenLabs eleven_v4 with acting tags: Gaston = Henri (French, crying), Prim = Philippa (crisp, haughty), Cedric = Rowan (young, posh, smug). Narrator = Kokoro bm_george. Marcus = Kokoro am_michael (clearer than am_adam). After the ElevenLabs free tier was busy, the user said to stop using it, so the narrator and Marcus stay on Kokoro for all their lines and no character changes voice mid-video. Every line is now loudness-matched (−20 LUFS per line, all within 1.5 dB in the mix) |
| "Phew…" line unclear | Marcus speaks it slower (0.84) with pauses: "Phew... what a blizzard! Right... nobody leaves, until I find the poisoner." The video is not slowed; the edit re-times from the words |
| length | the slower lines made it longer, so the search montage is tighter (1.8 s per room) and the end card is 3.5 s → 59.9 s |

## Fun beats
- Victim face-down in pudding; a spoon clatters on frame 0.
- Chef cries over the onions, with a comedic "bwomp" sting.
- The smug cat pops up on "his cat" (meow). On "it wasn't the cat" the cat looks offended and meows again.

## Pipeline numbers
| step | result |
|---|---|
| voices | v2: Kokoro (narrator, Marcus) + ElevenLabs takes in `audio/eleven/` (`narrate.py` line `"source": "eleven"`), all Whisper-checked; captions use the script's spelling |
| new assets | cast: Gaston (toque, mustache, chef jacket), Prim (bob, glasses, cardigan), Cedric (scarf); snow on hat and shoulders; tears; cleaver, papers and keys props; sets: blizzard mansion, entry hall with the drive, dining room, library; cat + victim drawings; 8 new SFX |
| render | 1882 frames, 156 s (0.08 s/frame) + fixes 574 frames, 41 s |
| mix | voice −16, music −25.7, SFX −23.6, wind/room −38.5 LUFS. Master −14.1 LUFS, −1.1 dBTP |
| QC | v2: −14.0 LUFS, −1.1 dBTP, 59.93 s; all checks pass except the freeze check: 57.3 s onward is the intended end freeze-frame. Full render 2046 frames in 205 s |

## Fixed after QA
- black strip under the mansion shot, and black side strips in close-ups → cameras clamped
- Cedric was hidden in his recap card → moved up

## Known weak spots
- TTS voices, no French accent for Gaston
- the cat meow is synthesised and sounds a bit electronic
