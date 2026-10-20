#!/usr/bin/env python3
"""preflight.py: check a source clip before planning the edit.

Reports duration, resolution, fps, the aspect recommendation, audio activity, hard cuts and the transcript's
words-per-minute, then prints PASS / REVIEW / REFUSE. REFUSE means no video or under the minimum duration; no speech
is REVIEW (silent B-roll is legitimate). Burned-in text and multiple speakers are not machine-checked; inspect a 1 fps
contact sheet and listen to the clip.

Usage:
  python3 preflight.py --video raw.mp4 [--transcript transcript-raw.json] [--out PREFLIGHT.json]
      [--min-dur 3] [--cut-threshold 0.4] [--speech-db -40] [--scan-seconds 120]
"""
import argparse, json, os, shutil, subprocess, tempfile, wave
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--video", required=True)
ap.add_argument("--transcript", default="")
ap.add_argument("--out", default="")
ap.add_argument("--min-dur", type=float, default=3.0)
ap.add_argument("--cut-threshold", type=float, default=0.4)
ap.add_argument("--speech-db", type=float, default=-40.0)
ap.add_argument("--scan-seconds", type=float, default=120.0)
args = ap.parse_args()


def recommend_aspect(w, h):
    r = float(w) / float(h) if h else 0.0
    if r >= 1.5:
        return "16:9"
    if r <= 0.7:
        return "9:16"
    return "4:5"


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,r_frame_rate", "-show_entries", "format=duration",
                        "-of", "json", path], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    return d, v, a


def audio_activity(path, db_floor):
    tmp = tempfile.mkdtemp(prefix="preflight-audio-")
    try:
        wav = os.path.join(tmp, "a.wav")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-acodec", "pcm_s16le",
                        "-ar", "16000", "-ac", "1", wav], check=True)
        with wave.open(wav, "rb") as w:
            rate = w.getframerate()
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
        step = max(1, int(rate * 0.02))
        usable = (len(pcm) // step) * step
        if usable == 0:
            return 0.0
        frames = pcm[:usable].reshape(-1, step)
        rms = np.sqrt(np.mean(frames ** 2, axis=1))
        return float(np.mean(rms > 10.0 ** (db_floor / 20.0)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def hard_cuts(path, threshold, scan):
    tmp = tempfile.mkdtemp(prefix="preflight-scene-")
    try:
        cmd = (["ffmpeg", "-v", "error", "-y", "-t", "%.3f" % scan, "-i", path, "-an",
                "-vf", "select='gt(scene,%.2f)',metadata=print:file=scene.txt" % threshold,
                "-f", "null", "-"])
        subprocess.run(cmd, cwd=tmp, check=True)
        meta = os.path.join(tmp, "scene.txt")
        if not os.path.exists(meta):
            return 0
        return sum(1 for line in open(meta) if line.startswith("pts_time:"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


result = {"video": os.path.abspath(args.video), "checks": {}, "issues": [], "verdict": "PASS",
          "not_checked": ["burned-in text (inspect a 1 fps contact sheet)",
                          "multiple speakers (listen to the clip)"]}

try:
    data, v, a = probe(args.video)
except Exception as e:
    result["checks"]["probe"] = str(e)
    result["issues"].append("cannot probe the file")
    result["verdict"] = "REFUSE"
    data, v, a = {}, None, None

duration = float(data.get("format", {}).get("duration") or 0.0)
result["checks"]["duration_s"] = round(duration, 3)

if v:
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    result["checks"].update({"width": w, "height": h, "aspect": recommend_aspect(w, h),
                             "fps": v.get("r_frame_rate", "")})
else:
    result["issues"].append("no video stream")

if duration < args.min_dur:
    result["issues"].append("shorter than %.1f s" % args.min_dur)

if not a:
    result["issues"].append("no audio stream")
    result["checks"]["audio_activity_fraction"] = 0.0
else:
    frac = audio_activity(args.video, args.speech_db)
    result["checks"]["audio_activity_fraction"] = round(frac, 3)
    if frac < 0.02:
        result["issues"].append("almost no audio activity above %.0f dBFS" % args.speech_db)

if duration > 0 and v:
    cuts = hard_cuts(args.video, args.cut_threshold, min(duration, args.scan_seconds))
    scanned = min(duration, args.scan_seconds)
    per_min = cuts / (scanned / 60.0) if scanned else 0.0
    result["checks"].update({"hard_cuts": cuts, "cuts_per_minute": round(per_min, 1)})
    if per_min > 6:
        result["issues"].append("many hard cuts (%.1f/min): confirm this is one intended shot" % per_min)

if args.transcript:
    raw = json.load(open(args.transcript, encoding="utf-8"))
    words = raw["words"] if isinstance(raw, dict) and "words" in raw else raw
    result["checks"]["words"] = len(words)
    if not words:
        result["issues"].append("transcript has no words")
    elif duration > 0:
        wpm = len(words) / (duration / 60.0)
        result["checks"]["words_per_minute"] = round(wpm, 1)
        if wpm < 40 or wpm > 300:
            result["issues"].append("transcript rate %.0f wpm is outside 40-300; review it" % wpm)

if any(i.startswith(("no video", "shorter")) for i in result["issues"]):
    result["verdict"] = "REFUSE"
elif result["issues"]:
    result["verdict"] = "REVIEW"

print("PREFLIGHT %s  %s" % (result["verdict"], result["video"]))
for k, val in result["checks"].items():
    print("  %-18s %s" % (k, val))
for i in result["issues"]:
    print("  ISSUE  %s" % i)
if result["verdict"] != "PASS":
    print("  not checked: " + "; ".join(result["not_checked"]))

if args.out:
    json.dump(result, open(args.out, "w", encoding="utf-8"), indent=1)
    print("-> %s" % args.out)

raise SystemExit(2 if result["verdict"] == "REFUSE" else 0)
