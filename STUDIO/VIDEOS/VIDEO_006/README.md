# VIDEO_006 – Protists Part 2: Archaeplastida and Unikonta (2D explainer, 6:30)

Source: PSHS Biology 3, Learning Guide 9.3 (Protista – Model Organisms Part 2). Every concept in the guide is
covered, plus both "Think it over" questions and the NAVIGATE crime case. Same format as VIDEO_005: Detective Marcus
hosts, storybook 2D style, vertical 1080×1920.

## Coverage (50 lines, one visual each – see `plan.py`)
| section | concepts |
|---|---|
| Intro | recap of part 1 (Excavata, SAR) and the 4-supergroup tree; today: Archaeplastida + Unikonta |
| Archaeplastida | "ancient plastids"; shared chloroplasts from one event ~1 billion years ago; endosymbiosis (heterotroph engulfs a cyanobacterium-like cell, not digested, becomes the chloroplast); Schimper 1883; McFadden: merged in structure, metabolism, genes → light-powered lineage; molecular clocks still difficult; 3 subgroups |
| › Glaucophytes | little known; near the surface of fresh water; cyanelles keep cyanobacterial traits; *Cyanophora paradoxa* as model species |
| › Red algae | rhodophytes; ≥6,000 species, mostly marine; single-celled / filamentous / multicellular; phycoerythrin, darker with depth, almost black in deep water; warm tropical seas; carrageenan, agar; nori = *Pyropia* |
| › Green algae | Chloroplastida = green algae + land plants; ~12,000 species; chlorophyll a and b, carotene, xanthophyll; motile / non-motile; mostly fresh water, also land and marine; oxygen producers; unicellular, colonial, multicellular, filamentous, tubular; *Chlamydomonas*, *Volvox*, *Ulva* (sea lettuce), *Caulerpa taxifolia* (largest single-celled organism) |
| Think it over 1 | how ancestral green algae could move onto land; suggested answer: charophytes in fresh water, dry glaciated Earth, photorespiration |
| Unikonta | most mixed group; Amoebozoa + Opisthokonta; exact relationship still being tested |
| › Amoebozoa | amoebas for all/most of the life cycle; pseudopodia (mostly lobose, a few filose/reticulate); naked or glycocalyx coat; cysts when food runs low, phagocytosis when conditions improve; aquatic food-web link; slime molds (*Physarum*), plasmodial slime molds most species-rich; worldwide on decaying plants, leaf litter, bark; spores → yellow/orange plasmodium |
| › Opisthokonta | nucleariids (filose amoebae, ancestral to fungi); choanoflagellates (closest known relatives of animals, single/colonial, fresh + salt water); collar of microvilli + flagellum → current → food filtered on the collar → phagocytosis |
| Think it over 2 | choanoflagellates vs sponge choanocytes: what pushed them to become multicellular? |
| NAVIGATE: the case | 22 Dec 2016, 8:24 PM, Cabucgayan, Biliran; couple unconscious, house facing the sea; table clues (oysters, puso, isaw, clear water, two unfinished plates with empty oyster shells, broken glass); earthen jar smelling of rotten eggs; empty paracetamol blister packs; 28 °C, 83 % humidity; stable but unconscious; suspects *Plasmodium*, *Entamoeba*, *Giardia*, *Pyrodinium bahamense*; task: most probable suspect + why, profile (general info, symptoms, diagnosis, local treatment) |
| Wrap-up | protists still surprising (new species: harmful, helpful, animal origins); "big things come in small packages"; recap |

**The case answer is deliberately not given.** It is a graded task in the learning guide, so the video gives every
clue and asks viewers to comment their suspect (end card "WHO DID IT? / COMMENT YOUR SUSPECT!").

## Build
- **New drawings** (`micro6.py`, reuses all of VIDEO_005's `micro.py`): cyanobacterium, glaucophyte (cyanelles),
  red alga (darkens with depth), Chlamydomonas, Volvox, Ulva, Caulerpa, Spirogyra-type filament, lobose/filose amoeba
  (+ glycocalyx, + prey in a food vacuole), cyst, slime-mold plasmodium (grows), choanoflagellate (food current),
  choanoflagellate colony, sponge collar cells, mushroom, sprout, fish; case props: sushi, oyster, puso, isaw,
  pitcher, earthen jar (banga), blister pack, house by the sea at night, hospital beds with monitor.
- **New shot types** (`anim2d.py`): endosymbiosis animation, depth column, rows/tiles grids, "Think it over" card with
  a pause countdown ring, split tree, steps, food chain, slime-mold log scene, crime-scene house, dinner table with
  clue labels, prop scenes, suspect line-up. Empty slots show faint "?" placeholders until their word is spoken.
- **Overlays** (`gfx.py`): section breadcrumb; typed case-file stamps at the top for the case (date/time/place, weather);
  end card.
- **Audio:** Kokoro (narrator af_heart, Marcus am_michael); captions use the script's spelling on Whisper timings
  (all 50 lines match). Music `cue_video006`: lo-fi in F, turns minor and sparse (ticking pulse) during the case.
  SFX: whooshes, word-synced pops, typewriter keys under the stamps, mystery sting, heartbeat at the hospital.

## Numbers / QC
| item | result |
|---|---|
| render | 11,695 frames, 481 s full render (0.04 s/frame); export 477 s; 12 shots re-rendered after the freeze fix |
| mix | master −14.0 LUFS, −1.4 dBTP |
| QC (first export) | 1080×1920, 30 fps, h264/aac 48k, 389.8 s, loudness/peak pass, no black frames. Duration check "fails" by design (30–90 s rule is for Shorts; this is a full lesson). 11 freeze flags, all at shot starts where the desk was empty until the first tile's word → fixed with placeholders |
| QC (final) | see below |

## Known limits
- TTS pronounces some names imperfectly (e.g. Cabucgayan, phycoerythrin, Pyrodinium); captions show the correct spelling.
- Drawings are schematic teaching cartoons, not to scale.
