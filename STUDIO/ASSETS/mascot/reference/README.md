# Mascot reference (identity source)

Drop the supplied mascot reference here:
- `front.png`, `side.png`, `back.png`, `three_quarter.png` (turnaround, if available)
- `face_expressions.png` (any expression sheet)
- `colors.txt` or notes on exact skin / hair / shirt colours

Next step after references arrive:
1. Update `../mascot_spec.json` (colours, proportions, hair clumps) to match.
2. Render `python STUDIO/studio.py mascot-turnaround` and compare side by side.
3. Optionally finish a hand-tuned `../mascot.blend` (same bone names) – it then overrides the procedural build.
