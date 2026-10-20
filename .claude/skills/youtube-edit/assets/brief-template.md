# Brief — <project>

Fill this in before the cut. Unknown fields can stay blank; the defaults below apply.

## Source
- Footage: `<path or folder>`
- Output: YouTube 16:9 (default) | Shorts 9:16
- Spoken language:
- Reference video (optional): `<path>` — match its pacing and format; run `teardown.py` on it

## Intent
- Video type: tutorial | talking head | cinematic | other
- Visual style: minimal | clean | Apple-like | other
- Feel: energetic and trustworthy | calm | other
- Goal: after watching, the viewer can …
- Audience:

## Brand
- Colors: (hex values)
- Font: (default: DM Sans 700)
- Logo: `<path>`
- Face position: left | centre | right — overlays must never cover it
- Assets folder: `<path>` with music/, sfx/, img/, logos/

## Editing rules
- Filler words to remove: um, uh, …
- Keep 0.08–0.15 s of room tone at cut edges; never cut mid-word
- Step-by-step confirmation: on (default) | off
- Unattended run: off (default) | on — if on, state the end condition (e.g. "stop when verify-render passes");
  never combine with step-by-step confirmation
- Work on a copy: never modify, overwrite or move the source footage
- Paid services: none by default — ask before any paid API, stock tier or AI generation credits
- First edit: keep it to 60 s or less until the pipeline is proven on this footage
- Creative freedom: low | medium | high
- Optional moments: when I say “X”, show “Y”
- Sound: silence by default; a sound only when something on screen makes it

## Graphics defaults
- A named tool, company or product gets its official logo
- A key number gets a big number, never a generic card
- Code, commands and prompts get a typed window
- The speaker's face is a no-go zone; overlays move opposite it

## Delivery
- Default: 4K MP4 + storyboard + cut list
- Premiere project: only if asked. HyperFrames has no native Premiere export; offer an EDL/XML
  generated from the edit decisions as a separate deliverable, with a separate SRT
