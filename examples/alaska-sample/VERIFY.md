# Render check: output-4k.mp4

**PASS**  (2026-10-17 20:52)

| Check | Result | Measured | Expected |
|---|---|---|---|
| Resolution | PASS | 3840x2160 | 3840x2160 |
| Colour tags | PASS | primaries bt709, transfer bt709, space bt709 | bt709 x3 (else run the step-8 remux) |
| Video bitrate | PASS | 46.5 Mb/s | >= 40.0 Mb/s |
| Duration | PASS | 15.500 s | 15.500 s +/- 0.033 (data-duration) |
| Video vs audio | PASS | 15.500 / 15.500 s | within 0.12 s |
| Black frames | PASS | 0 interval(s), 0 flash(es) | none (pix_th 0.08; d 0.1 plus shorter flashes) |

## Frame sheet

`render-sheet.png`: 2 frame(s), read it before delivering: first frame, every card at data-start + 0.9 s, last frame.

0.00 15.45
