# Project rules (read every session)

Automated YouTube Shorts studio lives in `STUDIO/`. Start with `STUDIO/README.md` and `STUDIO/STYLE_BIBLE.md`.

- Free / open-source, CPU only. Ask before anything paid. Music + SFX are synthesised by code. Fonts OFL/Apache.
- Mascot (orange shirt) identity comes from `STUDIO/ASSETS/mascot/` – never redesign him.
- Original stories only; reference video = visual-language inspiration, never copied.
- Default: 1080×1920, 30 fps, 30–40 s. Text inside 36 px safe area. Captions never on faces.
- Natural colour by default. Lighting chosen per story mood.
- After every export: **show the video first**, then run QC (`studio.py VIDEO qc`), fix, re-export.
- Never claim something is tested when it isn't. Report render times + QA honestly in the video README.
- Fresh container? `bash STUDIO/setup.sh` (add `--tts` for Chatterbox + Whisper).
