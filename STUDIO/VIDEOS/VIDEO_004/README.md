# VIDEO_004 – The Day Evil Disappeared (2D, 57.1 s)

A dramatic "what if" short in the storybook 2D style. Its tone comes from colour grading and pacing. Typewriter
date stamps at the top mark each time skip.

## Story
| date stamp | scene | feeling |
|---|---|---|
| DEC 31, 2030 · 23:59:57 → JAN 1, 2031 · 00:00:00 | the clock tower strikes midnight; fireworks; a golden wave of light rolls over the city: evil stops existing | awe |
| JAN 1, 2031 · 06:12 AM | cell bars slide open; prisoner and guard open their arms to each other | wonder |
| JAN 2, 2031 · DAY 2 | newspapers slap onto a desk: ALL PRISONS EMPTY / WARS END OVERNIGHT / NOBODY REMEMBERS WHY | momentum |
| MARCH 14, 2031 · DAY 72 | Marcus packs his detective life into a box: "I guess the world doesn't need me anymore." | loss |
| AUGUST 9, 2033 · YEAR 3 | perfect bright street: open doors, Gaston hands bread to Sophie, birdsong | warmth |
| DECEMBER 20, 2035 · YEAR 5 | same street; the colour slowly drains, snow falls; Daniel gives Prim his scarf, and nobody reacts. "Kindness wasn't a choice. It was just… weather." A street lamp turns on in daylight: "Without the dark, nobody noticed the light." Over-exposure to white | emptiness |
| APRIL 2, 2041 · YEAR 10 | park bench at sunset. Lily finds his old badge: "Uncle Marcus, what's a hero?" / "Someone who chooses to do good. Even when they could choose not to." / "Why would anyone choose not to?" Silence | bittersweet |
| TODAY | "Maybe a world without evil is also a world without heroes." → WOULD YOU ERASE EVIL? | reflection |

## Craft
- **Date stamps** (`gfx.date_stamps`): Special Elite typewriter font (Apache-2.0), types at 26 characters/s with a
  blinking cursor, a rule that draws in, and a key-strike sound per letter. The old stamp is wiped just before the
  next one. The midnight counter ticks live: 23:59:57 → 00:00:00 lands on the word "midnight".
- **Colour as story** (`graded()`): warm night → bright saturated summer → saturation drains to 0.25 and goes cool
  in 2035 → warm sunset for 2041 → dusk falls in the last shot.
- **New toon features:** `lily` (child proportions, pigtails), `prisoner`, `guard` (cap, badge), `marcus_cardigan`;
  a seated pose (`pose["sit"]`); a child voice made by pitching up a Kokoro voice (`"pitch": 1.2` in script.json).
- **Score:** felt piano + strings (`inst_piano`). Hopeful D-major arpeggios; lonely single notes in the office;
  the same arpeggio thinning into minor in 2035; near-silence for the white dip; a bittersweet theme for 2041;
  silence after Lily's question.
- **SFX:** clock bell, firework pops, cell door slide, newspaper slaps, typewriter keys, birdsong (6 new); wind,
  city and room ambience.

## Numbers
| step | result |
|---|---|
| voices | Kokoro: narrator af_heart (0.88–0.95 speed), Marcus am_michael (slow), Lily af_bella pitched ×1.2; 13 lines |
| render | 1712 frames, 198 s (+ fixes) |
| mix | voice −16, music −22.2, SFX −25.1, ambience −35.1 LUFS. Master −14.0 LUFS, −1.0 dBTP |
| QC | all checks pass (no black, no freeze), 57.07 s |

## Fixed after QA
- the newspaper shot froze for 4 s → slow camera drift, settling papers, coffee steam
- the prisoner stood outside the bars before they opened → he is now inside the cell; the bars slide into the wall
- the fedora was drawn huge across Marcus's body → small, held in both hands
- the summer street was crowded → spaced out so the bread hand-over reads
- the grade layer was applied after drawing (no effect) → it now wraps each shot
