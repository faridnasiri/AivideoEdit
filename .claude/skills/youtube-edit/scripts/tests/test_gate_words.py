import json, math, os, struct, subprocess, sys, tempfile, unittest, wave

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "gate-words.py")


def make_wav(path, rate=16000):
    frames = []
    for i in range(rate):                      # 1 s of digital silence
        frames.append(0)
    for i in range(rate):                      # 1 s of a quiet tone
        frames.append(int(0.3 * 32767 * math.sin(2 * math.pi * 440 * i / rate)))
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<%dh" % len(frames), *frames))


class GateWords(unittest.TestCase):
    def run_gate(self, payload):
        d = tempfile.mkdtemp(prefix="gate-test-")
        audio = os.path.join(d, "audio.wav")
        make_wav(audio)
        tp = os.path.join(d, "transcript.json")
        with open(tp, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        out = os.path.join(d, "gated.json")
        r = subprocess.run([sys.executable, SCRIPT, "--transcript", tp, "--audio", audio, "--out", out],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def test_drops_words_in_digital_silence(self):
        got = self.run_gate({"words": [
            {"text": "ghost", "start": 0.2, "end": 0.6},
            {"text": "real", "start": 1.2, "end": 1.6},
        ]})
        self.assertEqual([w["text"] for w in got["words"]], ["real"])
        self.assertEqual(got["gated"]["dropped"], 1)

    def test_preserves_other_keys(self):
        got = self.run_gate({"words": [{"text": "real", "start": 1.2, "end": 1.6}],
                             "language": "en", "duration": 2.0})
        self.assertEqual(got["language"], "en")
        self.assertEqual(got["duration"], 2.0)


if __name__ == "__main__":
    unittest.main()
