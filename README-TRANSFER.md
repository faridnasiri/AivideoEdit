# YouTube Edit skill — transfer bundle

This folder contains the installed `youtube-edit` skill and its reference documentation, ready to copy to
another computer. Raw GoPro footage, rendered MP4s, public working files and caches are deliberately
excluded.

| | |
|---|---|
| Bundle created | 2026-10-19 |
| Skill version | Local install, updated 2026-10-19 |
| Test status | 45/45 passing |
| Source project | `C:\p\alaska2025` |
| Original kit | WeAreNoCode YouTube Editor |

## What is included

```text
alaska2025-skill-transfer/
  .claude/skills/youtube-edit/     the full skill: SKILL.md, 30 scripts, formats, fonts, GSAP, tests
  docs/youtube-edit-reference.md   comprehensive reference: pipeline, scripts, rules, sources
  examples/alaska-sample/          storyboard, STORYBOARD.md, VERIFY.md, contact sheets (no video)
  LICENSES/                        DM Sans OFL + MIT starter-kit notice
  requirements.txt                 Python packages
  README-TRANSFER.md               this file
```

Not included: raw `.MP4/.LRV/.THM` footage, `input-video.mp4`, rendered `output-4k*.mp4`, and
`__pycache__` files.

## Install on the other computer

### 1. Copy the skill into a project

Copy the folder:

```text
.claude\skills\youtube-edit
```

into the target project:

```text
<your project>\.claude\skills\youtube-edit
```

Optional: copy `docs\youtube-edit-reference.md` into `<your project>\docs\`.

Do **not** copy over a newer `youtube-edit` folder without checking for local changes. Merge deliberately.

### 2. Install prerequisites

**Windows (PowerShell):**

```powershell
winget install OpenJS.NodeJS
winget install Gyan.FFmpeg
python -m pip install -r requirements.txt
npx hyperframes models install parakeet
```

**macOS:**

```bash
brew install node ffmpeg
python3 -m pip install -r requirements.txt
npx hyperframes models install parakeet
```

**Linux:** use your package manager for Node 22+, FFmpeg and Python 3, then:

```bash
python3 -m pip install -r requirements.txt
npx hyperframes models install parakeet
```

Also required:

- Google Chrome
- HyperFrames through `npx` (no global install needed)
- Parakeet TDT 0.6B v3 (about 639 MB, installed by the command above)

Optional: Tella and Epidemic Sound connectors, and `yt-dlp` for reference downloads.

### 3. Verify

```powershell
Set-Location "<your project>\.claude\skills\youtube-edit\scripts"
python -m unittest tests -v
```

macOS/Linux: use `python3`. The suite must end with `OK`. Media tests skip themselves without FFmpeg.

```powershell
npx hyperframes doctor
```

FFmpeg and ffprobe must be found.

### 4. Start a new Claude Code thread

Skills load at the start of a thread. In the new thread, ask for an edit and name the skill, for
example: "Use my youtube-edit skill to edit this hook."

## Windows notes

- Restart the app or shell after winget installs, or refresh `$env:Path` in the current session.
- Use `python`, not `python3`, if `python3` is a Microsoft Store alias.
- Keep text output UTF-8. The installed `compose.py` already does.
- Never place `C:\...` paths inside an FFmpeg filter option; the installed `teardown.py` uses a temp cwd
  and relative names.

## The first edit

1. Put a raw clip in `<project>\videos\<name>\raw\`.
2. Fill in `BRIEF.md` from `.claude\skills\youtube-edit\assets\brief-template.md`.
3. Run `preflight.py` on the source.
4. Follow the cut-stage order in `SKILL.md`.
5. Approve the cut at Checkpoint A and the storyboard at Checkpoint B.
6. Render 4K and run `verify-render.py` before delivery.

See `docs/youtube-edit-reference.md` for every stage, script option, known gap and source link.

## Sources and licenses

- The skill comes from the WeAreNoCode YouTube Editor kit:
  "I Fully Automated My Video Editing Using Claude Code (Full Walkthrough)".
  Community: https://www.skool.com/wearenocode
- HyperFrames: https://github.com/heygen-com/hyperframes and https://hyperframes.heygen.com
- DM Sans is under the SIL Open Font License (`LICENSES/OFL-DM-Sans.txt`).
- Parts adapted from an MIT-licensed starter kit (`LICENSES/MIT-starter-kit.txt`).
- No music, sound effects, footage or logos are included.
