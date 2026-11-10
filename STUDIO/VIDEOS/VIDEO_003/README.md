# VIDEO_003 – The Three Doors of Doom (2D, 56.9 s)

Three-door riddle with a twist, in the same storybook 2D style. Detective Marcus + Mr. Whiskers (the cat from
VIDEO_002, now a cat burglar) + Mumford the mummy gatekeeper.

## Story
Marcus chases the cat, who has a golden scarab, into a pyramid. A stone slab slams shut behind him. The cat escapes
through a tiny hole. A cheery mummy pops out of his sarcophagus: "My first visitor in three thousand years!" Three
doors, one way out:
1. **A fire that burns for 1,000 years**
2. **Lions that have not eaten in 3 years**
3. **A flood that arrives in 3,000 years**

Marcus picks the classic answer: "Those lions starved ages ago, door two!" The mummy: "I carved these signs on my
very first day… three thousand years ago." Then "Lunch time, kitties!" A hatch opens, glowing eyes, ROAR. "Okay…
maybe not door two." Recap of the three signs, then WHICH DOOR? / COMMENT 1, 2 OR 3!

## Creator-only answer (never in the video)
**Door 1.** The signs are 3,000 years old:
- **Door 1:** the fire burned out 2,000 years ago. Quiet clue: a cobweb over the door handle.
- **Door 2:** the lions are fed every day by the mummy, and roar. This kills the classic answer.
- **Door 3:** the flood is due right now. Quiet clues: water seeping under the door and drip sounds.

## Pipeline numbers
| step | result |
|---|---|
| voices | Kokoro only (per the user). Narrator bm_george, Marcus am_michael, Mummy a bm_lewis + bm_fable blend at 0.9 speed. Character lines get a stone-room echo (`"fx": "cave"`), and every line is loudness-matched |
| new assets | `mummy` cast (bandage wraps, loose tail); corridor + chamber sets with three doors, torches, sarcophagus, meat cart, cat hole, lion eyes in the hatch; 6 SFX (lion roar, stone slam, tomb ambience, drip, cart, lid creak); "ancient mode" music cue |
| render | 1808 frames, 157 s |
| mix | voice −16, music −26, SFX −21.9, tomb ambience −37.3 LUFS. Master −14.1 LUFS, −1.5 dBTP |
| QC | all checks pass except the freeze check: 53.8 s onward is the intended end freeze-frame |

## Fixed after QA
- true peak −0.7 dBTP after AAC encode → the limiter now aims 0.6 dB under the ceiling (all videos)
- black strips (cameras past the room edge), Marcus half off-frame at the roar, meat cart hidden → reframed
