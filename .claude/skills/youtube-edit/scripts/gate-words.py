#!/usr/bin/env python3
"""gate-words.py: drop transcript words that sit in digital silence.

ASR models can invent words over pure ambience. This measures the peak level inside each word's window on the
cut stage's 16 kHz mono WAV and removes words that never rise above the threshold.

Usage:
  python3 gate-words.py --transcript transcript-raw.json --audio audio-raw.wav \
      --out transcript-gated.json [--threshold -50]
"""
import argparse, json, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--transcript", required=True)
ap.add_argument("--audio", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--threshold", type=float, default=-50.0, help="peak dBFS below which a word is silence")
args = ap.parse_args()

with open(args.transcript, encoding="utf-8") as f:
    raw = json.load(f)
words = raw["words"] if isinstance(raw, dict) and "words" in raw else raw

with wave.open(args.audio, "rb") as w:
    if w.getnchannels() != 1 or w.getsampwidth() != 2:
        raise SystemExit("expected a 16-bit mono WAV; got %d channel(s), %d-byte samples"
                         % (w.getnchannels(), w.getsampwidth()))
    rate = w.getframerate()
    pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0

def peak_db(a, b):
    a, b = max(0, int(a * rate)), min(len(pcm), int(b * rate))
    if b <= a:
        return None
    return 20.0 * np.log10(max(float(np.max(np.abs(pcm[a:b]))), 1e-9))

kept, dropped = [], []
for w in words:
    level = peak_db(float(w["start"]), float(w["end"]))
    if level is None:
        dropped.append(dict(w, peak_db=None, reason="outside audio"))
    elif level < args.threshold:
        dropped.append(dict(w, peak_db=round(level, 1), reason="silence"))
    else:
        kept.append(w)

out = dict(raw) if isinstance(raw, dict) else kept
if isinstance(out, dict):
    out["words"] = kept
    out["gated"] = {"threshold_dbfs": args.threshold, "kept": len(kept), "dropped": len(dropped)}
with open(args.out, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)

print("kept %d words, dropped %d in silence (threshold %.0f dBFS) -> %s"
      % (len(kept), len(dropped), args.threshold, args.out))
for d in dropped[:10]:
    print("  %.2f-%.2f  %s  [%s]" % (float(d["start"]), float(d["end"]), d.get("text", ""), d["reason"]))
