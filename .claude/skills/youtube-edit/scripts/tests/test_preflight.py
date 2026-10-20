import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "preflight.py")
HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def make_video(path, w, h, seconds=4, audio=True):
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "lavfi", "-i", "testsrc2=size=%dx%d:rate=30:duration=%d" % (w, h, seconds)]
    if audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:duration=%d" % seconds,
                "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise unittest.SkipTest(r.stderr[-400:])


@unittest.skipUnless(HAVE_FFMPEG, "needs ffmpeg and ffprobe")
class Preflight(unittest.TestCase):
    def run_preflight(self, w, h, seconds=4, words=20, audio=True):
        d = tempfile.mkdtemp(prefix="preflight-test-")
        video = os.path.join(d, "in.mp4")
        make_video(video, w, h, seconds, audio)
        tp = os.path.join(d, "words.json")
        with open(tp, "w", encoding="utf-8") as f:
            json.dump({"words": [{"text": "w%d" % i, "start": i * 0.1, "end": i * 0.1 + 0.08}
                                 for i in range(words)]}, f)
        out = os.path.join(d, "report.json")
        r = subprocess.run([sys.executable, SCRIPT, "--video", video, "--transcript", tp, "--out", out],
                           capture_output=True, text=True)
        self.assertIn(r.returncode, (0, 2), r.stdout + r.stderr)
        with open(out, encoding="utf-8") as f:
            return json.load(f)

    def test_landscape_passes_or_reviews_with_audio(self):
        got = self.run_preflight(640, 360)
        self.assertEqual(got["checks"]["aspect"], "16:9")
        self.assertGreater(got["checks"]["audio_activity_fraction"], 0.05)
        self.assertIn(got["verdict"], ("PASS", "REVIEW"))

    def test_vertical_recommendation(self):
        self.assertEqual(self.run_preflight(360, 640)["checks"]["aspect"], "9:16")

    def test_square_recommendation(self):
        self.assertEqual(self.run_preflight(540, 675)["checks"]["aspect"], "4:5")

    def test_short_clip_refuses(self):
        got = self.run_preflight(640, 360, seconds=2)
        self.assertEqual(got["verdict"], "REFUSE")

    def test_sparse_transcript_reviews(self):
        got = self.run_preflight(640, 360, words=2)
        self.assertEqual(got["verdict"], "REVIEW")
        self.assertTrue(any("wpm" in i for i in got["issues"]))

    def test_no_audio_reviews_not_refuses(self):
        got = self.run_preflight(640, 360, audio=False)
        self.assertEqual(got["verdict"], "REVIEW")
        self.assertIn("no audio stream", got["issues"])


if __name__ == "__main__":
    unittest.main()
