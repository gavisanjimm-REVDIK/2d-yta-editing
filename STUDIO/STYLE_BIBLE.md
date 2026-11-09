# Style Bible – original stylised cinematic 3D Shorts

The channel's art direction in one page. Every video follows it. Code defaults live in `config/style.json`,
the mascot in `ASSETS/mascot/`. Reference video (inspiration only) goes in `ASSETS/refs/style/`.

> Consistency in art direction. Variety in storytelling. Quality in every frame.

## 0. Originality
- The reference video is inspiration for **visual language only**: proportions, polished simplified geometry,
  expressive faces, cinematic environments, lighting, camera composition, clean typography.
- Never copy its characters, story, dialogue, scenes, branding or distinctive assets.
- Every video gets its own look (lighting, palette, shot list) inside one shared universe.

## 1. Visual style
**Characters:** rounded appealing proportions (~4 heads tall), smooth polished geometry, big expressive eyes,
readable faces, clean silhouette in 9:16. Natural hair/clothes with soft material detail.
**Avoid:** sphere-and-cylinder dolls, cheap primitives, tiny faces, plastic with no depth, realistic anatomy.

**Environments:** real places re-made in stylised 3D (subway, street, bedroom, school, office, nature,
disaster-scale). Background objects tell the story. Detail where the story looks, not everywhere.

**Materials** (`studio_lib/materials.py`): every surface has roughness/colour variation. Skin with
subsurface, fabric with sheen + weave bump, anisotropic hair, real metal/wood/glass/concrete/water.
Controlled highlights. One cohesive material language across videos.

## 2. Lighting follows the story (`studio_lib/lights.py`)
| mood | preset | look |
|---|---|---|
| suspense / mystery | `suspense` | low key, selective highlights, practicals, readable shadows |
| comedy | `comedy` | bright, inviting, clear faces, colour |
| adventure | `adventure` | sunlight, dynamic shadows, atmospheric depth |
| disaster / big scale | `disaster` | dramatic env light, haze only if it helps, light changes = escalation |
| emotional | `emotional_warm` / `emotional_cool` | soft directional, controlled contrast |
| night | `night` | believable practicals: lamps, screens, streetlights, headlights |

Rules: faces always readable · no flat uniform light · no pure-black shadows hiding action · AO on ·
volumetrics only when they serve the shot · practical lights visibly affect nearby surfaces ·
only `Key*` lights cast shadows (speed) · colour stays natural (view: *Khronos PBR Neutral*), grade per story
with the EDL `grade` effect, never an over-saturated "vibrant" grade unless asked.

## 3. Mascot – consistency is mandatory
- The orange-shirt mascot is the recurring lead. Identity source = `ASSETS/mascot/reference/`.
- Never redesign or reinterpret: face shape, hair silhouette, eyes, skin tone, orange shirt, proportions.
- One reusable rigged asset (`mascot.load()`), same bone names forever: body, fingers, eyes (target),
  upper/lower lids, brows, mouth shapes (open/smile/frown/O/wide), expressions (`perform.EXPRESSIONS`).
- He **acts**: idle (breathe, blink, weight shift, glances), gestures with anticipation, reacts to props and
  people, expression changes on the exact story beat. Subtle for suspense/emotion, bigger for comedy.
- Other characters reuse the same generator with a `look` override → same universe.

## 4. Camera (`studio_lib/cameras.py`)
Shot vocabulary: ECU (reactions) · CU (faces) · MCU/MS (interaction) · WS/EWS (establish) · low angle (scale,
threat) · high angle (vulnerable) · OTS (discoveries) · tracking (movement) · slow push-in (suspense) · timed reveals.
Use foreground elements for depth. No static "illustration" shots. Keep subject, props and action inside 9:16.

## 5. Animation
Anticipation → action → follow-through · weight and momentum · expressions change on time · real contact with
props/environment · secondary motion · good spacing. No stiff/robotic moves. Impossible scenarios: set rules, keep them.

## 6. Editing (`editing/edl_engine.py`)
The 3D establishes the world, the edit controls attention. Tools: motivated cuts, reaction shots, punch-ins,
controlled zooms, whip pans, speed ramps, brief freeze frames (comedy), motion blur, impact frames,
sound-synced transitions, sparse motion graphics. Not every scene is an effects showcase.
Rhythm: establish fast → problem → escalate → reactions → reveal/payoff → ending or loop. No repetitive cuts.

## 7. Subtitles & on-screen text
- Bold condensed sans (Anton, OFL), white, black outline + soft shadow, **red accent** (`#FF2D2D`) on key words.
- ≤4 words per phrase, word-timed, short pop-in (scale 0.88→1). No giant meme captions.
- Never on faces or key props: use `CAPTIONS["pos"]` overrides per time range.
- Everything inside the 36 px safe area (shrink to fit, never overflow).
- HUD elements (timers, clocks, counters, status) only when the story owns them.

## 8. Sound
Layered design, all synthesised by code: ambience, footsteps, cloth, object hits, impacts, whooshes, risers,
comedy SFX when fitting. Music matches the story (suspense / playful / epic / emotional / energetic) and ducks
under speech. Use silence on purpose (`music_gates`). Master −14 LUFS, ≤ −1 dBTP. Narration always intelligible.

## 9. Story
Before production: premise → central conflict → strong opening → visual escalation → main reveal → ending →
loop yes/no. Show, don't explain: the video must read with the sound off. Never reuse the same shot sequence,
lighting, jokes or transitions video after video.

## 10. Specs
YouTube Shorts · 9:16 · 1080×1920 · 30 fps · **30–40 s** unless told otherwise · H.264 CRF 18 + AAC 48 kHz.
Render smart: half-res EEVEE (540×960) + only frames the edit uses (`render_needed.py`).

## 11. Final check (every export – show video first, then QA)
**Visuals:** polished stylised 3D? characters well modelled? lighting fits story? environments coherent? clean shadows/materials?
**Animation:** smooth? convincing faces? natural acting? believable object interaction?
**Camera/edit:** intentional composition? enough meaningful shot variety? attention held? transitions motivated?
**Presentation:** captions readable + synced + off faces? sound balanced? one cohesive production?
Automatic checks: `qc_video.py` (+ `loop_test.py` for loops). Fix → re-export → re-check → write README report.
