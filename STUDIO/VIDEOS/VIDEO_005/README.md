# VIDEO_005 – Protists Part 1: Excavata and the SAR Clade (2D explainer, 7:15)

Source: PSHS Biology 3, Learning Guide 9.2 (Protista – Model Organisms Part 1). Every concept in the guide is
covered. Framing: "Detective Marcus investigates the protist suspects". Storybook 2D style, vertical 1080×1920.

## Coverage (54 lines, one visual each – see `plan.py`)
| section | concepts |
|---|---|
| The case: Giardia | single cell + flagella; prokaryote vs eukaryote (bigger, nucleus → domain Eukarya); *Giardia lamblia*, protist, parasite, giardiasis |
| What is a protist? | eukaryotes that are not plants/animals/fungi; diverse; Haeckel 1866; old look-based groups (protozoa, protophyta/algae, slime & water molds) → phylogenetics; not closely related, many exceptions; 4 supergroups (Excavata, SAR, Archaeplastida, Unikonta) |
| Excavata | asymmetry + excavated feeding groove; parasites/photosynthetic/heterotrophic predators |
| › Diplomonads | parasitic, Giardia; mitosomes (leftover mitochondria, function not fully known); anaerobic, glycolysis; 2 identical nuclei, several flagella |
| › Parabasalids | hydrogenosomes (anaerobic, release H2); flagella + undulating membrane; *Trichomonas vaginalis* → trichomoniasis (STI); men rarely symptomatic; women: more vulnerable to HIV and genital wart virus (>90% of cervical cancer); pregnancy: preterm risk |
| › Euglenozoans | parasites/heterotrophs/autotrophs/mixotrophs, 10–500 µm; Euglena: 2 flagella, eyespot, phototaxis, mixotroph (light: photosynthesis / dark: chloroplasts shrink, absorbs food); kinetoplastids: kinetoplast = DNA mass in one big mitochondrion; trypanosomes; *T. brucei* tsetse life cycle (gut → salivary glands → next host); African sleeping sickness (central Africa, fatigue → coma, fatal if untreated) |
| SAR clade | S/A/R signatures: hairy + smooth flagella, alveoli under the membrane, threadlike pseudopodia |
| › Stramenopiles | diatoms, golden algae, brown algae; mastigonemes (tripartite hairs) push the cell; autotrophs + heterotrophs (Blastocystis, water molds/oomycetes, Opalina) |
| › Alveolates | dinoflagellates, apicomplexans, ciliates; unicellular/chains/mm-long cells; parasitic/heterotrophic/autotrophic/mixotrophic, kleptoplasty; dinoflagellates: cellulose plates, 2 flagella in grooves, spinning, dinos = whirling + flagellum = whip, red tides (HABs); apicomplexans: apical complex on the sporozoite, more than one host, Plasmodium/mosquitoes/malaria; ciliates: cilia vs flagella (same structure, shorter, many, wave-like beat) |
| › Rhizarians | free-living heterotrophs, hard to culture; secondary endosymbiosis (chlorarachniophytes + green alga), Paulinella + cyanobacterium; forams with filose, branching/anastomosing pseudopods; freshwater and soil; cercozoans = 30–60% of protists in some soils |
| Summary | definition, supergroups, subgroup recap, health + ecology (giardiasis, malaria, red tides, soil) |

## Build
- **Organism library** (`micro.py`, 21 animated vector drawings): Giardia, bacterium, excavate, mitochondrion/mitosome/hydrogenosome, Trichomonas, Euglena, Trypanosoma, stramenopile/alveolate/rhizarian signature cells, diatom, golden alga, kelp, dinoflagellate (spinning), sporozoite entering a host cell, ciliate (metachronal wave), foram, radiolarian, tsetse fly/mosquito, red tide.
- **Shot types** (`anim2d.py`): microscope view with word-synced callout labels, compare panels with a stamp, parchment cards with bullets popping on the spoken word, supergroup tree, Eukarya diagram, old-groups board, S/A/R signatures, trophic modes, T. brucei life cycle, red tide, engulfing (endosymbiosis), soil pie, recap and montage, Marcus host scenes. A section breadcrumb + progress dots sit at the top.
- **Voices:** Kokoro (narrator af_heart, Marcus am_michael). Whisper mishears science words, so `narrate.align_words()` (new, pipeline-wide) puts the script's exact spelling on Whisper's timings. Captions and word-synced graphics now always match the script (e.g. "eyespot", not "ice pot").
- **Music:** calm lo-fi loop (`cue_video005`) with a bell at each section.

## Numbers / QC
| item | result |
|---|---|
| render | 13,058 frames, 591 s (0.05 s/frame) |
| mix | voice −16, music −25.3, SFX −33.6 LUFS; master −14.0 LUFS, −1.5 dBTP |
| QC | 1080×1920, 30 fps, h264/aac 48k, 435.3 s, loudness/peak pass, no black frames. Freeze check: 17 short (0.6–1 s) flags on slow-push text cards; the motion is real but below the detector threshold (was 140 before the camera-drift fix) |

## Known limits
- The TTS pronounces some taxon names imperfectly (e.g. stramenopiles, kinetoplast); captions show the correct spelling.
- The organism drawings are schematic teaching cartoons, not to scale.
