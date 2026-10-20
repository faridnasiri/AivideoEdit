#!/usr/bin/env python3
"""transcript-to-srt.py: turn a word-level transcript into an SRT for the flat cut.

Input : Parakeet / whisper JSON ([{text,start,end}] or {"words":[...]})
Output: an SRT whose cues break on a speech gap, sentence punctuation, max characters or max duration.

Usage:
  python3 transcript-to-srt.py --transcript W/transcript.json --out W/captions.srt
      [--max-chars 80] [--max-dur 5] [--min-dur 0.5] [--gap 0.7]
"""
import argparse, json, textwrap

SENTENCE_END = (".", "!", "?")


def stamp(t):
    ms = max(0, int(round(float(t) * 1000)))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def cues(words, max_chars, max_dur, gap):
    out, cur = [], []
    for w in words:
        text = (w.get("text") or "").strip()
        if not text:
            continue
        start, end = float(w["start"]), float(w["end"])
        if cur:
            prev = cur[-1]
            joined = " ".join([x["text"] for x in cur] + [text])
            if (start - float(prev["end"]) > gap
                    or end - float(cur[0]["start"]) > max_dur
                    or len(joined) > max_chars
                    or str(prev["text"]).rstrip().endswith(SENTENCE_END)):
                out.append(cur)
                cur = []
        cur.append({"text": text, "start": start, "end": end})
    if cur:
        out.append(cur)
    return out


ap = argparse.ArgumentParser()
ap.add_argument("--transcript", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--max-chars", type=int, default=80)
ap.add_argument("--max-dur", type=float, default=5.0)
ap.add_argument("--min-dur", type=float, default=0.5)
ap.add_argument("--gap", type=float, default=0.7)
a = ap.parse_args()

raw = json.load(open(a.transcript, encoding="utf-8"))
words = raw["words"] if isinstance(raw, dict) and "words" in raw else raw
blocks = cues(words, a.max_chars, a.max_dur, a.gap)

# Every cue holds for at least min_dur, but never runs into the next cue's first word.
for i, block in enumerate(blocks):
    start, end = block[0]["start"], block[-1]["end"]
    if end - start >= a.min_dur:
        continue
    target = start + a.min_dur
    if i + 1 < len(blocks):
        target = min(target, blocks[i + 1][0]["start"] - 0.001)
    block[-1]["end"] = max(end, target)
lines = []
for i, block in enumerate(blocks, 1):
    text = " ".join(x["text"] for x in block)
    wrapped = textwrap.wrap(text, width=max(20, a.max_chars // 2)) or [text]
    lines += [str(i), "%s --> %s" % (stamp(block[0]["start"]), stamp(block[-1]["end"])),
              "\n".join(wrapped), ""]
open(a.out, "w", encoding="utf-8").write("\n".join(lines))
print("wrote %s (%d cues)" % (a.out, len(blocks)))
