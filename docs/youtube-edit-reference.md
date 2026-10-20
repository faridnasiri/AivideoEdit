# YouTube Edit — Reference

A complete reference for the `youtube-edit` Claude Code skill installed in this project, including its
pipeline, scripts, tests, local modifications, known gaps, and the projects and articles it was built from.

| | |
|---|---|
| Skill | `.claude/skills/youtube-edit/` |
| Rulebook | [SKILL.md](../.claude/skills/youtube-edit/SKILL.md) — 1,058 lines |
| Original kit | `C:\p\WeAreNoCode-YouTube-Editor-Skill\WeAreNoCode-YouTube-Editor` |
| Installed | 2026-10-17 |
| Last updated | 2026-10-19 |
| Platform verified | Windows 10, Python 3.12.10, Node 24.14.1 |
| Test status | **45/45 passing** |

---

## 1. What this is

`youtube-edit` turns raw talking-head footage, or a flat cut, into a finished video: the cut, animated
overlays, cutaways, B-roll, camera moves, sound, and a tagged 4K MP4 rendered locally with HyperFrames
(Chrome + FFmpeg). Nothing leaves the machine.

The core design:

- **Two human checkpoints.** Checkpoint A approves the cut (`PAPER-CUT.md`); Checkpoint B approves the
  storyboard (`storyboard.json` + `snaps/sheet.png`). Everything else runs unattended.
- **Cheap things first.** A storyboard edit is a number change; a re-render is minutes. Snapshot every
  card before rendering.
- **The brief drives the edit.** `BRIEF.md` carries style, brand, language, aspect, face position,
  assets folder, filler rules, confirmation mode, and delivery format.
- **Every stage checks its own work.** Transcripts are gated against audio, cut edges are measured,
  the composition is linted, the render is verified.

---

## 2. Where things live

| Path | What it is |
|---|---|
| `.claude/skills/youtube-edit/SKILL.md` | The rulebook Claude reads. Start here. |
| `.claude/skills/youtube-edit/scripts/` | 30 Python/Node tools: cut, compose, checks, render helpers |
| `.claude/skills/youtube-edit/scripts/tests/` | 10 test modules, 45 tests |
| `.claude/skills/youtube-edit/formats/` | Reusable format code (`claude_chat.py`) |
| `.claude/skills/youtube-edit/assets/fonts/` | DM Sans 400/500/700 (SIL OFL) |
| `.claude/skills/youtube-edit/assets/vendor/` | Local `gsap.min.js` 3.14.2 for offline renders |
| `.claude/skills/youtube-edit/assets/brief-template.md` | Per-video brief with defaults |
| `videos/<project>/` | One working folder per video |
| `videos/alaska-sample/` | The smoke-test sample edit from this install |
| `docs/youtube-edit-reference.md` | This document |
| `C:\p\WeAreNoCode-YouTube-Editor-Skill\WeAreNoCode-YouTube-Editor` | Original kit, outside the project |

A project folder typically contains:

```text
videos/<project>/
  raw/                 source clips (copied, never modified)
  public/
    input-video.mp4    the flat cut HyperFrames renders over
    index.html         composed page
    hyperframes.json   render manifest
  snaps/               pre-render and post-render sheets
  storyboard.json      the review artifact and source of truth
  cut-list.json        kept/removed ranges
  cut-map.json         where every jump cut landed
  transcript*.json     word-level transcripts
  PREFLIGHT.json       source check (new)
  captions.srt         optional subtitle deliverable
  VERIFY.md            post-render checks
  STORYBOARD.md        delivery notes
  output-4k-raw.mp4    HyperFrames render
  output-4k.mp4        BT.709-tagged final
```

---

## 3. Installed toolchain

| Tool | Installed | Check | Install (Windows) |
|---|---|---|---|
| Node.js | 24.14.1 | `node -v` | nodejs.org or `winget install OpenJS.NodeJS` |
| HyperFrames CLI | 0.8.168 | `npx hyperframes --version` | comes through `npx` |
| FFmpeg / ffprobe | 9.0.2 full build | `ffmpeg -version` | `winget install Gyan.FFmpeg` |
| Python | 3.12.10 | `python --version` | python.org |
| numpy | 2.5.4 | `python -c "import numpy"` | `python -m pip install numpy` |
| auto-editor | 29.3.1 | `auto-editor --version` | `python -m pip install auto-editor` |
| yt-dlp (optional) | 2026.08.19 | `yt-dlp --version` | `python -m pip install yt-dlp` |
| Parakeet | TDT 0.6B v3 | transcribe a 5 s WAV | `npx hyperframes models install parakeet` |
| Google Chrome | system install | `npx hyperframes doctor` | google.com/chrome |
| GSAP | 3.14.2 local copy | `assets/vendor/gsap.min.js` | jsDelivr |

Optional connectors: **Tella** (screen tutorials) and **Epidemic Sound** (music/SFX). Neither is connected
in this project. Without them, use two-file tutorials (`sync-tracks.py`) and the free HyperFrames media
library.

**Windows PATH note:** winget updates PATH for new processes. A shell or app already running before the
install will not see `ffmpeg` until restarted. In a current PowerShell session:

```powershell
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
```

---

## 4. Routes

| Input | Route |
|---|---|
| Flat cut, no baked zooms/captions/transitions, 4K preferred | Pipeline |
| One raw clip with a brief | Director brief → Cut stage → storyboard → compose → render |
| One raw clip, 1–3 min | Cut stage → storyboard → compose → snap-beats → render |
| Several raw clips | `ingest.py` → the same on `source.mp4` |
| Long talking-head (>3 min) | Cut stage + `stutter-scan.py` + `CUT-REVIEW.html` → long-form storyboard → `gap-scan.py` + `beat-check.py` → render per section |
| Tella screen tutorial | Tella route (connector required) |
| Two-file tutorial (face + screen) | `sync-tracks.py` → Cut stage on face → screen as `clip` cutaways |
| Whole video | `assemble.py` → one 4K master + chapters |
| Short (9:16) | Separate 9:16 composition; see SKILL.md "Shorts" |
| Channel teardown | `teardown.py` |

---

## 5. Pipeline at a glance

```text
BRIEF.md ──► preflight ──► transcribe ──► gate words ──► paper cut ──► hand fixes
   │                                                            │
   │                                                     tighten / sliver / edge-audit
   │                                                            │
   │                                                       apply-cut
   │                                                            │
   │                                              re-transcribe + gate + dead-air
   │                                                            │
   └──────────────► storyboard.json ◄───────────────────────────┘
                         │
                  compose.py ──► hyperframes check ──► snapshots (Checkpoint B)
                         │
                  hyperframes render (4K) ──► BT.709 remux ──► verify-render
                         │
                  STORYBOARD.md / VERIFY.md / captions.srt / delivery
```

Stage gates from SKILL.md:

| Stage | Output | Gate |
|---|---|---|
| 1. Brief | `BRIEF.md` | user confirms |
| 2. Transcribe + cut | `PAPER-CUT.md` + `CUT-REVIEW.html` | Checkpoint A |
| 3. Storyboard | `storyboard.json` + `snaps/sheet.png` | Checkpoint B |
| 4. Build | `public/index.html` | `npx hyperframes check` passes |
| 5. Review | snapshots + `verify-render.py` | every check passes; entry/exit + every 5 s; max 5 fix rounds |
| 6. Deliver | 4K MP4 + storyboard + cut list | user confirms |

---

## 6. Stage detail

### 6.1 Brief

Create `$W/BRIEF.md` from [brief-template.md](../.claude/skills/youtube-edit/assets/brief-template.md).
Ask at most five questions in one round. Defaults: 16:9, house style, spoken language from the footage,
face centre, step-by-step confirmation on, 4K MP4 delivery.

The brief records:

- Source, output aspect, spoken language, reference video
- Video type, visual style, feel, goal, audience
- Brand colours, font, logo, face position, assets folder
- Filler words, room-tone margins, confirmation mode, unattended end condition
- Copy-only invariant, paid-services approval, first-edit size cap
- Optional moments ("when I say X, show Y")
- Graphics defaults: official logo for named tools, big number for key numbers, typed window for code
- Delivery format and NLE handoff

### 6.2 Preflight (new)

```powershell
python .claude/skills/youtube-edit/scripts/preflight.py `
  --video "raw.mp4" `
  --transcript "transcript-gated.json" `
  --out "PREFLIGHT.json"
```

Reports duration, width/height, fps, aspect recommendation, audio activity fraction, hard-cut density,
and transcript words per minute.

Verdicts:

- **REFUSE** — no video stream, or shorter than `--min-dur` (default 3 s). Exit code 2.
- **REVIEW** — no audio, almost no audio activity, many hard cuts, empty transcript, or a transcript rate
  outside 40–300 wpm.
- **PASS** — none of the above.

Not machine-checked: burned-in text and multiple speakers. Inspect a 1 fps contact sheet and listen.

### 6.3 Transcribe and gate

```powershell
ffmpeg -y -v error -i raw.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio-raw.wav
npx hyperframes transcribe audio-raw.wav -d . --engine parakeet --json
python .claude/skills/youtube-edit/scripts/gate-words.py `
  --transcript transcript-raw.json --audio audio-raw.wav --out transcript-gated.json
```

`gate-words.py` removes any word whose window never rises above −50 dBFS. This prevents an ASR
hallucination over digital silence from entering the cut.

After `apply-cut`, re-transcribe the flat cut and gate that transcript again in place; it is in final
timeline time and drives `dead-air.py`, `beat-check.py`, captions, and phrase timing.

### 6.4 Cut stage

Canonical order on every clip:

```text
paper cut → hand fixes → tighten-cut → sliver → edge-audit to 0
→ apply-cut → re-transcribe + gate → dead-air
→ patch-cut --drop-flat → edge-audit → apply-cut → re-transcribe + gate
→ dead-air prints 0
```

Key behavior:

- **paper-cut.py** keeps the last take, cuts restarts, honours "cut that / scratch that", drops false
  starts, trims pauses, merges kept pieces under `--merge-gap` (0.30 s), and warns when a kept segment
  starts on a filler.
- **edge-audit.py** measures every cut edge on the waveform; 0 issues is the gate.
- **apply-cut.py** does one frame-accurate re-encode, snaps every edge to the source frame grid, adds
  20 ms audio fades, writes `cut-map.json`, and fails loudly on A/V drift.
- **dead-air.py** targets no pause over 0.40 s after a sentence end, 0.45 s elsewhere; `--plan` proposes
  trims to 0.30 s in room tone.
- **Never cut with `-c copy`.** H.264 keyframes are 2–10 s apart; a stream copy lands on the nearest
  keyframe and freezes. Every cut is re-encoded.

### 6.5 Storyboard and composition

`storyboard.json` is the review artifact and the source of truth. A beat has `type`, `id`, `in`, `out`,
and `anchor` (the spoken phrase). The composer supports 40+ formats: lower lines, glass cards, bullets,
chips, logos, sites, clips, stats, pipelines, world camera, deck, pills, chat, doc, and more.

```powershell
python .claude/skills/youtube-edit/scripts/compose.py `
  --spec "$W/storyboard.json" --out "$W/public" --shared "videos/_shared"
npx hyperframes check "$W/public"
python .claude/skills/youtube-edit/scripts/beat-check.py `
  --index "$W/public/index.html" --transcript "$W/transcript.json"
python .claude/skills/youtube-edit/scripts/snap-beats.py --project "$W"
```

The composer now probes the video and clamps the composition duration to the source. Any beat past the
source is skipped; a beat that crosses the end is clamped. This prevents a black tail.

### 6.6 Render and verify

```powershell
$env:PRODUCER_BROWSER_GPU_MODE = "hardware"
$env:NODE_OPTIONS = "--max-old-space-size=8192"
npx hyperframes render "$W/public" --resolution 4k --video-bitrate 45M --gpu --workers 4 -o "$W/output-4k-raw.mp4"

ffmpeg -y -v error -i "$W/output-4k-raw.mp4" -c copy `
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv `
  -movflags +write_colr+faststart "$W/output-4k.mp4"

python .claude/skills/youtube-edit/scripts/verify-render.py `
  --render "$W/output-4k.mp4" --index "$W/public/index.html"
```

`verify-render.py` checks black runs, resolution, BT.709 tags, bitrate (≥40 Mb/s at 4K), duration within
one frame, A/V alignment, and optionally clipped words. Exit 1 means do not deliver.

### 6.7 Assembly

`assemble.py` takes `assembly.json` and produces one 4K master at −14 LUFS with `ASSEMBLY.md` and
`chapters.txt`. Each segment is conformed and loudness-normalised, then joined with stream copy and tagged
BT.709.

### 6.8 Captions

- Burned-in captions follow the spec in SKILL.md: 2–5 words per group at clause boundaries, ≥0.5 s on
  screen, group window contains all word times, one hero at a time, ≥30% of the face uncovered, and
  luminance-based contrast (below 60 light text; 60–180 add a scrim; above 180 opaque text plus a scrim).
- **Standalone SRT:** `transcript-to-srt.py` groups on speech gaps, sentence ends, max characters, and
  max duration, and extends short cues to at least 0.5 s without overlapping the next cue.

```powershell
python .claude/skills/youtube-edit/scripts/transcript-to-srt.py `
  --transcript transcript.json --out captions.srt
```

---

## 7. Script reference

### 7.1 Intake and analysis

| Script | Does | Options |
|---|---|---|
| `preflight.py` | source suitability check; PASS/REVIEW/REFUSE | `--video [--transcript] [--out] [--min-dur 3] [--cut-threshold 0.4] [--speech-db -40] [--scan-seconds 120]` |
| `ingest.py` | probe, order, join raw clips; maps source time to clip time | `--raw --out [--concat] [--order A,B] [--only A,B] [--name]` |
| `sync-tracks.py` | audio cross-correlation offset for face + screen files | `--a cam --b screen [--write-aligned DIR] [--window 180]` |
| `teardown.py` | measure a video; contact sheets; storyboard counts; compare reports | `--video` / `--storyboard` / `--compare`, `--out [--transcript] [--every 2]` |
| `screen-activity.py` | how much a screen recording changes over time | `--video --out [--fps 2]` |
| `phrase-times.py` | start/end of a spoken phrase | `--transcript "phrase" ... [--after T]` |
| `gate-words.py` | drop ASR words that sit in digital silence | `--transcript --audio --out [--threshold -50]` |

### 7.2 Cut

| Script | Does | Options |
|---|---|---|
| `paper-cut.py` | remove restarts, markers, retakes, false starts, long pauses; merge gaps; warn on filler starts | `--transcript --duration --out-dir --speech [--merge-gap 0.30]` |
| `hand-cut.py` | rebuild `cut-list.json` from kept lines | `--keep A-B` (`A-B!` keeps whole) `--transcript --speech --duration --out-dir` |
| `tighten-cut.py` | trim lead-ins, tails and inner pauses | `--audio --cut-list --out [--lead 0.07] [--tail 0.11] [--maxgap 0.30]` |
| `sliver.py` | catch breath-only heads, dropped-word decays, tails leaking the next onset | `--cut-list --audio [--fix]` |
| `edge-audit.py` | every cut edge measured on the audio | `--audio --cut-list --transcript [--keeps FILE] [--fix] [--threshold 300]` |
| `apply-cut.py` | frame-accurate re-encode + `cut-map.json` | `--input --cut-list --out [--fps 30] [--crf 16]` |
| `dead-air.py` | pause scan and trim plan | `W [--plan] [--keep T] [--max 0.45] [--max-sentence 0.40] [--target 0.30]` |
| `patch-cut.py` | small fixes: add, drop, drop-flat | `--cut-list --add A-B` / `--drop T` / `--drop-flat A-B` |
| `stutter-scan.py` | second opinion on word-level stutters and retakes | `--transcript --out-dir` |
| `cutlist-to-edl.py` | EDL for the side-by-side review page | `--cut-list --out` |

### 7.3 Storyboard and graphics

| Script | Does | Options |
|---|---|---|
| `compose.py` | `storyboard.json` → `public/index.html`; clamps to source duration | `--spec --out [--shared DIR]` |
| `beat-check.py` | each element enters within its word window; stale transcript fails | `--index --transcript [--suggest] [--allow-stale] [--video]` |
| `snap-beats.py` | one snapshot per beat and state, tiled into `snaps/sheet.png` | `--project [--at T ...]` |
| `gap-scan.py` | long-form coverage and density | `--index [--early 15] [--body 20] [--max 30]` |
| `storyboard-md.py` | delivery `STORYBOARD.md` | `--title --project dir:slug:title --out [--note] [--concern]` |
| `broll-conform.py` | stock/generated/still → 30 fps cutaway + sheet | `--in --out [--start] [--dur] [--4k] [--grade] [--push 1.08] [--vf FILTERS]` |
| `window-patch.py` | render-ready copy of a time window for a fix | `--public --t0 --t1 --out` |

### 7.4 Audio, delivery, Tella

| Script | Does | Options |
|---|---|---|
| `assemble.py` | `assembly.json` → one 4K master at −14 LUFS | `--manifest --out [--gpu] [--keep-work]` |
| `verify-render.py` | file checks; exit 1 on FAIL | `--render [--index] [--res] [--words --kept] [--out]` |
| `transcript-to-srt.py` | SRT with ≥0.5 s cues | `--transcript --out [--max-chars 80] [--max-dur 5] [--min-dur 0.5] [--gap 0.7]` |
| `tella-pull-source.py` | download a Tella raw recording from a signed URL | `--url-file --out [--wav] [--audio-only]` |
| `tella-cuts.py` | cut list → Tella `cuts` array | `--cut-list --source-duration --clip-max` |
| `tella-timeline.py` | Tella sentences on the playback timeline | `--clip-dir --cuts-json --key [--tella-words] [--clicks] [--activity]` |

---

## 8. Rules worth knowing

### Cut and audio

- Transcript timestamps are ±120 ms (~4 frames). Snap to the frame grid and confirm by audio.
- Correcting a misread changes text only, never its `start`/`end`.
- Drop transcript words that sit in digital silence.
- Merge kept pieces under 0.3 s; never start a kept segment on a filler.
- No pause over 0.40 s after a sentence end, 0.45 s elsewhere; target 0.30 s in room tone.
- Never digital silence: use a room-tone segment under a cutaway.
- 20–40 ms audio fades at joins; 20 ms is the floor in `apply-cut.py`.
- −14 LUFS for YouTube; true peak under −1 dBTP.

### Camera

- Top-anchored origin, always: `52% 0%` centred, `38% 0%` when the speaker sits left.
- Punch-in 118–125% over 0.30–0.35 s; creep 110–112% over 5–10 s; snap back to 100% at cuts.
- 1080p source: 112% maximum. 4K: 150% freely, 200% for a deliberate crash-in.
- Jump cuts stay naked by default; dress one when the energy changes.

### Pacing and graphics

- Hooks: about 6 overlay moments per 37 s; cards hold 3–7 s.
- Long form: no stretch without an overlay or camera move over 15 s (first 90 s), 20 s after, 30 s ever.
- `secPerCard` by runtime: <60 s 6–8 s; 1–3 min 8–12 s; 3–10 min 12–20 s; 10–30 min 20–35 s; >30 min
  30–60 s. Density ×0.7 / ×1.0 / ×1.5.
- One element at full brightness at a time; context dims to .56, spent to .33.
- A card never covers the face; check the edge against the hair in a snapshot.

### Determinism and verification

- No `Date.now()`, unseeded `Math.random()`, `setTimeout`, promises or `play()` in a composition.
- Build one paused timeline synchronously; keep repeats finite; seek back into a beat after seeking past.
- Snapshot every element entry/exit plus every 5 s on the finished file.
- Prove a change on a 5–8 s slice before touching the full render.
- A fresh-eyes pass sees only the sheet and checklist and answers PASS/FIX; cap at five rounds.

---

## 9. Local modifications in this install

> **Do not re-copy the original kit over `.claude/skills/youtube-edit/`.** The installed copy contains local
> fixes and additions (UTF-8 writes, FFmpeg path handling, preflight, word gating, SRT, duration clamping).
> Re-copying would overwrite them. Merge upstream changes deliberately.

### 2026-10-17 — install and Windows fixes

| Change | Reason |
|---|---|
| Installed all skill files under `.claude/skills/youtube-edit/` | Requested install |
| Installed FFmpeg, numpy, auto-editor, yt-dlp, Parakeet | Missing prerequisites |
| Downloaded GSAP 3.14.2 locally | Offline renders |
| `compose.py` writes HTML as UTF-8 | Windows cp1252 crashed on `→` |
| `teardown.py` uses relative FFmpeg metadata paths in a temp cwd | Windows drive-letter `:` broke filter graphs |
| Built `videos/alaska-sample/` | End-to-end smoke test |

### 2026-10-18 — research-derived rules

Added to SKILL.md and the brief:

- Preflight gate and aspect recommendation (16:9 / 4:5 / 9:16), max five questions
- Transcript timestamp accuracy, audio gating, merge and filler rules
- Caption specification (timing, grouping, face coverage, luminance contrast)
- Card pacing formula, duration clamping, determinism checklist
- Vision pass (one still per shot), matte-leak warning
- Caption/SRT delivery checks, 5–8 s slice testing, fresh-eyes review
- Asset priority, non-Latin/RTL guidance, rule-of-two learning
- NLE handoff contract: linked cuts, transparent overlays, SFX, markers, SRT, frame accuracy

### 2026-10-19 — scripts and tests

| Change | What it enforces |
|---|---|
| Added `preflight.py` | Source suitability gate; PASS/REVIEW/REFUSE |
| Added `gate-words.py` | No ASR words from digital silence |
| Added `transcript-to-srt.py` (2026-10-18) and `--min-dur 0.5` | Caption minimum duration |
| `compose.py` clamps duration to the probed source and skips late beats | No black tail |
| `paper-cut.py` `--merge-gap` 0.30 and filler-start WARN | Merge and filler-start rules |
| Added tests: preflight, gate-words, SRT, paper-cut, compose clamp | 45 tests total |

---

## 10. Testing

```powershell
Set-Location "C:\p\alaska2025\.claude\skills\youtube-edit\scripts"
python -m unittest tests -v
```

Current result: **45 tests, OK**. Coverage includes:

- Beat anchoring and stale transcripts
- B-roll conform (fps, silence, trim)
- Compose formats and duration clamping
- Gap scanning
- Apply-cut duration, teardown, verify-render
- Patch-cut guards and range mapping
- Gate words against silence
- SRT grouping, min duration, empty input
- Paper-cut filler warning
- Preflight aspect, duration, audio, transcript rate

Media tests skip themselves if FFmpeg is unavailable.

---

## 11. Windows notes and known pitfalls

- **PATH:** restart the app or shell after winget installs; refresh `$env:Path` in an existing session.
- **`python3`:** on this machine use `python`; `python3` is not on PATH.
- **FFmpeg filter paths:** never put `C:\...` inside a filter option. Use `cwd=<temp>` and relative names
  (the `teardown.py` fix).
- **UTF-8:** write text output with `encoding="utf-8"`; the Windows default is cp1252.
- **GoPro partial files:** `GH014921.MP4`, `GH014923.MP4`, `GH014924.MP4` are 0.1 s and cannot supply a
  2–5 s segment. The first usable clips start at `GH014922.MP4`.
- **Long renders:** 4K capture stores frames first; over ~2 minutes use streaming encode with one worker.
  Check free disk before a long assembly.
- **Hardware encoder:** `--gpu` ignores CRF; always pass `--video-bitrate 45M`.
- **Colour:** the render drops two colour tags; always run the BT.709 remux.

---

## 12. Known gaps

| Gap | Detail |
|---|---|
| Native NLE export | HyperFrames renders MP4/WebM. A FCP7 XML handoff is a contract, not a built exporter. |
| Burned-in caption format | SRT is supported; the composer has no dedicated caption-track format. |
| Multi-speaker detection | Not automated. Preflight reports it as unchecked. |
| Burned-in text detection | Not automated. Inspect a 1 fps contact sheet. |
| Audio activity ≠ speech | Preflight measures non-silent audio, not voice. A noisy B-roll clip looks active. |
| Tella / Epidemic Sound | Connectors are not configured in this project. |
| CapCut project files | A research source claims CapCut 10.4+ encrypts project files; test the separate `capcut-edit` skill before relying on it. |

---

## 13. Source projects and references

### Original skill kit

- **WeAreNoCode YouTube Editor** — the skill installed here.
  `C:\p\WeAreNoCode-YouTube-Editor-Skill\WeAreNoCode-YouTube-Editor`
  - `README.md` — what is inside, install steps, costs
  - `SETUP.md` — 30-minute setup, recording guidance
  - `PROMPTS.md` — the prompts the creator types
  - `STYLE-GUIDE.md` — colours, font, cards, motion, camera, sound, cuts
  - `LICENSES/` — DM Sans OFL, MIT starter-kit notice
  - Original video: "I Fully Automated My Video Editing Using Claude Code (Full Walkthrough)"
  - Community: https://www.skool.com/wearenocode

### HyperFrames (engine and official skills)

- Repository: https://github.com/heygen-com/hyperframes
- Documentation: https://hyperframes.heygen.com
- Plugin guide: https://hyperframes.heygen.com/guides/plugins
- Captions and recuts guide: https://hyperframes.heygen.com/guides/captions-and-recuts
- `talking-head-recut` skill:
  https://github.com/heygen-com/hyperframes/blob/main/skills/talking-head-recut/SKILL.md
- `embedded-captions` skill:
  https://github.com/heygen-com/hyperframes/blob/main/skills/embedded-captions/SKILL.md
- Media library (`media-use`): https://github.com/heygen-com/hyperframes
- Agent requirements (`AGENTS.md`):
  https://github.com/heygen-com/hyperframes/blob/main/AGENTS.md
- Introductory article: https://apidog.com/blog/hyperframes-agentic-video/

### Tools

- FFmpeg: https://ffmpeg.org
- auto-editor: https://github.com/WyattBlue/auto-editor — cookbook: https://auto-editor.com/docs/cookbook
- Parakeet / sherpa-onnx models: installed through `npx hyperframes models install parakeet`
- GSAP: https://gsap.com
- DM Sans: https://fonts.google.com/specimen/DM+Sans (SIL Open Font License)
- Tella MCP / agent skills: https://docs.tella.com/help/integrations/agent-skills

### Research read during the 2026-10-18 update

- **HozhiLearn** — "AI Video Editing with Claude Code & Codex":
  https://hozhilearn.com/post.php?slug=video-editing-with-AI
- **Claude Video Editor blueprint** by Jason Cooperson (artifact):
  https://claude.ai/artifact/BYH6Mcma5to3kt2KogkEzB
  and https://www.skool.com/leveragelab/about
- **zn yupup / ai-video-editing-skill** — ffmpeg + Whisper + vision vlog pipeline:
  https://github.com/znyupup/ai-video-editing-skill
- **different-ai / agent-bank** — `video-subtitle-cutter` skill:
  https://github.com/different-ai/agent-bank
- **Neelshah1810 / Claude-Video-Skills** — 11 motion-graphics skills, verify pipeline:
  https://github.com/Neelshah1810/Claude-Video-Skills
- **ella-wang-opus / awesome-video-skills** — curated video skill index:
  https://github.com/ella-wang-opus/awesome-video-skills
- **zhuyansen / awesome-claude-video-skills** — 180 repos, security-graded:
  https://github.com/zhuyansen/awesome-claude-video-skills
- **ScreenKite / awesome-ai-video-editing**:
  https://github.com/ScreenKite/awesome-ai-video-editing
- **Cutback / Selects** — "Claude for Video Editing in 2026: What Works, What Breaks":
  https://cutback.video/blog/claude-for-video-editing-in-2026-what-works-what-breaks-and-the-real-pipeline
- **Cole Medin knowledge base** — build entire videos with Claude Code:
  https://github.com/coleam00/cole-medin-knowledge-base

---

## 14. Attribution and licensing

- The skill was installed from the WeAreNoCode kit. Its licences live in the original kit's `LICENSES/`
  folder, outside this project.
- **DM Sans** is licensed under the SIL Open Font License (`OFL-DM-Sans.txt` in the original kit).
- Some scripts started from an open-source starter kit under the MIT License; its notice is in
  `LICENSES/MIT-starter-kit.txt` and stays with the code.
- No music, sound effects, footage or logos ship with the skill. Use your own or openly licensed assets.
- This reference document and the local modifications listed in §9 are project-specific notes, not a
  redistribution of the original kit.

---

## 15. Change log

| Date | Change |
|---|---|
| 2026-10-17 | Installed skill; fixed Windows UTF-8 and FFmpeg path issues; installed dependencies; built sample edit; 31 tests passing |
| 2026-10-18 | Added research-derived rules; added SRT script; 34 tests passing |
| 2026-10-19 | Added preflight, word gating, duration clamp, paper-cut merge/filler warning; expanded tests to 45 |

---

## 16. Quick commands

```powershell
# Test the skill
Set-Location "C:\p\alaska2025\.claude\skills\youtube-edit\scripts"
python -m unittest tests -v
```

```powershell
# Check a source clip
python "C:\p\alaska2025\.claude\skills\youtube-edit\scripts\preflight.py" `
  --video "C:\p\alaska2025\GH014922.MP4" --out "C:\p\alaska2025\videos\alaska-sample\PREFLIGHT.json"
```

```powershell
# Gate a transcript
python "C:\p\alaska2025\.claude\skills\youtube-edit\scripts\gate-words.py" `
  --transcript transcript-raw.json --audio audio-raw.wav --out transcript-gated.json
```

```powershell
# Make an SRT
python "C:\p\alaska2025\.claude\skills\youtube-edit\scripts\transcript-to-srt.py" `
  --transcript transcript.json --out captions.srt
```

```powershell
# Compose and render the sample
Set-Location "C:\p\alaska2025"
python ".claude\skills\youtube-edit\scripts\compose.py" `
  --spec "videos\alaska-sample\storyboard.json" --out "videos\alaska-sample\public"
npx hyperframes render "videos\alaska-sample\public" --resolution 4k --video-bitrate 45M --gpu --workers 4 `
  -o "videos\alaska-sample\output-4k-raw.mp4"
```
