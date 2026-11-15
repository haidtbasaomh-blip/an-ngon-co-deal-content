"""Regression test: the inactive publisher must never contact the network."""
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class SocialPublishingGuardTests(unittest.TestCase):
    def test_inactive_publisher_is_held_before_external_calls(self):
        env = os.environ.copy()
        # Even with an enabled flag and a fictitious token, the disabled
        # publisher may not reach an external API or enqueue a Facebook post.
        env["FOOD_BUFFER_AUTO_QUEUE"] = "true"
        env["FOOD_BUFFER_API_KEY"] = "deliberately-invalid-test-key"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/food_buffer_rss.py")],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Food RSS publishing belongs to Zapier -> Buffer", completed.stdout)

if __name__ == "__main__":
    unittest.main()
