import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "transcript-to-srt.py")


class Srt(unittest.TestCase):
    def srt(self, words, max_chars=40):
        d = tempfile.mkdtemp(prefix="srt-test-")
        tp = os.path.join(d, "transcript.json")
        with open(tp, "w", encoding="utf-8") as f:
            json.dump({"words": words}, f)
        out = os.path.join(d, "captions.srt")
        r = subprocess.run([sys.executable, SCRIPT, "--transcript", tp, "--out", out,
                            "--max-chars", str(max_chars)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(out, encoding="utf-8") as f:
            return f.read()

    def test_breaks_on_sentence_and_gap(self):
        text = self.srt([
            {"text": "Hello", "start": 0.0, "end": 0.4},
            {"text": "world.", "start": 0.4, "end": 0.9},
            {"text": "Second", "start": 2.0, "end": 2.4},
        ])
        self.assertIn("1\n00:00:00,000 --> 00:00:00,900\nHello world.", text)
        self.assertIn("2\n00:00:02,000 --> 00:00:02,500\nSecond", text)
        self.assertEqual(text.count("-->"), 2)

    def test_breaks_on_max_chars(self):
        text = self.srt([
            {"text": "one", "start": 0.0, "end": 0.2},
            {"text": "two", "start": 0.2, "end": 0.4},
            {"text": "three", "start": 0.4, "end": 0.6},
            {"text": "four", "start": 0.6, "end": 0.8},
            {"text": "five", "start": 0.8, "end": 1.0},
            {"text": "six", "start": 1.0, "end": 1.2},
            {"text": "seven", "start": 1.2, "end": 1.4},
            {"text": "eight", "start": 1.4, "end": 1.6},
        ], max_chars=20)
        self.assertEqual(text.count("-->"), 2)

    def test_min_duration(self):
        text = self.srt([
            {"text": "Hi", "start": 0.0, "end": 0.15},
            {"text": "there", "start": 2.0, "end": 2.3},
        ])
        self.assertIn("00:00:00,000 --> 00:00:00,500", text)

    def test_empty_transcript(self):
        self.assertEqual(self.srt([]), "")


if __name__ == "__main__":
    unittest.main()
