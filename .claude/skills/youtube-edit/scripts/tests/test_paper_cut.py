import json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "paper-cut.py")


class PaperCut(unittest.TestCase):
    def test_flags_a_segment_starting_on_a_filler(self):
        d = tempfile.mkdtemp(prefix="paper-cut-test-")
        tp = os.path.join(d, "transcript.json")
        words = [
            {"text": "So", "start": 0.0, "end": 0.2},
            {"text": "today", "start": 0.2, "end": 0.5},
            {"text": "we", "start": 0.5, "end": 0.7},
            {"text": "build", "start": 0.7, "end": 1.0},
            {"text": "it", "start": 1.0, "end": 1.2},
        ]
        with open(tp, "w", encoding="utf-8") as f:
            json.dump({"words": words}, f)
        r = subprocess.run([sys.executable, SCRIPT, "--transcript", tp, "--duration", "2.0", "--out-dir", d],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        with open(os.path.join(d, "PAPER-CUT.md"), encoding="utf-8") as f:
            md = f.read()
        self.assertIn("Kept segments start on a filler", md)
        self.assertIn("WARN: 1 kept segment", r.stdout)


if __name__ == "__main__":
    unittest.main()
