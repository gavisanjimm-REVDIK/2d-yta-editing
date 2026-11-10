# VIDEO_002 – Death by Pudding (2D, 55.9 s)

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

## Fun beats
- Victim face-down in pudding; a spoon clatters on frame 0.
- Chef cries over the onions, with a comedic "bwomp" sting.
- The smug cat pops up on "his cat" (meow). On "it wasn't the cat" the cat looks offended and meows again.

## Pipeline numbers
| step | result |
|---|---|
| voices | Kokoro-82M, 10 lines (narrator bm_george, Marcus am_adam, Gaston am_onyx, Prim bf_alice, Cedric am_liam). All Whisper-clean except "Phew" heard as "few" (captions use the script) |
| new assets | cast: Gaston (toque, mustache, chef jacket), Prim (bob, glasses, cardigan), Cedric (scarf); snow on hat and shoulders; tears; cleaver, papers and keys props; sets: blizzard mansion, entry hall with the drive, dining room, library; cat + victim drawings; 8 new SFX |
| render | 1882 frames, 156 s (0.08 s/frame) + fixes 574 frames, 41 s |
| mix | voice −16, music −25.7, SFX −23.6, wind/room −38.5 LUFS. Master −14.1 LUFS, −1.1 dBTP |
| QC | all checks pass except the freeze check: 51.8 s onward is the intended end freeze-frame |

## Fixed after QA
- black strip under the mansion shot, and black side strips in close-ups → cameras clamped
- Cedric was hidden in his recap card → moved up

## Known weak spots
- TTS voices, no French accent for Gaston
- the cat meow is synthesised and sounds a bit electronic
