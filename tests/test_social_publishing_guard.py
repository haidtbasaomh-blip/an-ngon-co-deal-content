"""Regression: a DISABLED Food publisher never reaches the network.

The production policy may be enabled after the owner-approved Zapier cutover.
This test explicitly simulates the disabled state instead of assuming that
the checked-in production policy is permanently set to Zapier.
"""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "food_buffer_rss.py"
spec = importlib.util.spec_from_file_location("food_buffer_guard_under_test", SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


class SocialPublishingGuardTests(unittest.TestCase):
    def test_inactive_publisher_is_held_before_external_calls(self):
        original_read_text = Path.read_text

        def disabled_policy_read(path, *args, **kwargs):
            data = original_read_text(path, *args, **kwargs)
            if Path(path) != ROOT / "config" / "social_publishing_policy.json":
                return data
            policy = json.loads(data)
            policy["activePublisher"] = "zapier-to-buffer"
            policy["otherPublishers"]["github_buffer_direct"]["mayPublish"] = False
            return json.dumps(policy)

        output = io.StringIO()
        with (
            patch.object(Path, "read_text", disabled_policy_read),
            patch.object(
                bridge.urllib.request,
                "urlopen",
                side_effect=AssertionError("Disabled publisher attempted network access"),
            ) as network,
            patch.dict(os.environ, {
                "FOOD_BUFFER_AUTO_QUEUE": "true",
                "FOOD_BUFFER_API_KEY": "offline-invalid-test-key",
            }),
            contextlib.redirect_stdout(output),
        ):
            bridge.main()

        self.assertIn("SAFE HOLD", output.getvalue())
        network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
