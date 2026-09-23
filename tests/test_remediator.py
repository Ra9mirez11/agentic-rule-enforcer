"""Unit tests for remediation and diff generation."""

import tempfile
import unittest
from pathlib import Path

from enforcer.parser import DEFAULT_RULEBOOK_TEMPLATE, parse_rulebook_content
from enforcer.remediator import compute_file_fix
from enforcer.scanner import scan_file


class TestRemediator(unittest.TestCase):
    """Test suite for remediator module."""

    def setUp(self):
        self.rules = parse_rulebook_content(DEFAULT_RULEBOOK_TEMPLATE)

    def test_compute_fix_and_diff(self):
        dirty_code = """
import os

def run():
    api_key = "mock_secret_agent_key_1234567890abcdef"
    print("TODO_DEBUG test run")
    return api_key
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(dirty_code)
            tf_path = Path(tf.name)

        try:
            violations = scan_file(tf_path, self.rules)
            self.assertGreaterEqual(len(violations), 2)

            orig_text, mod_text, diff = compute_file_fix(tf_path, violations)
            self.assertGreater(len(diff), 0)

            # Confirm secret replaced with os.environ
            self.assertIn('api_key = os.environ.get("API_KEY", "")', mod_text)
            # Confirm debug print removed
            self.assertNotIn('print("TODO_DEBUG test run")', mod_text)
        finally:
            tf_path.unlink()


if __name__ == "__main__":
    unittest.main()
