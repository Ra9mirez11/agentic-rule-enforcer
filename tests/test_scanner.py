"""Unit tests for scanning engine and violation detection."""

import tempfile
import unittest
from pathlib import Path

from enforcer.parser import DEFAULT_RULEBOOK_TEMPLATE, parse_rulebook_content
from enforcer.scanner import run_scan, scan_file


class TestScanner(unittest.TestCase):
    """Test suite for code scanner."""

    def setUp(self):
        self.rules = parse_rulebook_content(DEFAULT_RULEBOOK_TEMPLATE)

    def test_detect_hardcoded_secrets(self):
        """Verify detection of hardcoded secrets and API keys."""
        dirty_code = """
import os

def connect_api():
    api_key = "mock_secret_agent_key_1234567890abcdef"
    return api_key
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(dirty_code)
            tf_path = Path(tf.name)

        try:
            violations = scan_file(tf_path, self.rules)
            self.assertEqual(len(violations), 1)
            v = violations[0]
            self.assertEqual(v.rule_id, "RULE-01-SECRETS")
            self.assertEqual(v.line_number, 5)
            self.assertIn("api_key", v.line_content)
            self.assertEqual(v.fix_action, "env_var")
        finally:
            tf_path.unlink()

    def test_detect_debug_fluff(self):
        """Verify detection of debug logs."""
        dirty_code = """
def process():
    data = {"id": 1}
    print("TODO_DEBUG check data:", data)
    return data
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(dirty_code)
            tf_path = Path(tf.name)

        try:
            violations = scan_file(tf_path, self.rules)
            self.assertEqual(len(violations), 1)
            v = violations[0]
            self.assertEqual(v.rule_id, "RULE-03-FLUFF")
            self.assertEqual(v.line_number, 4)
            self.assertEqual(v.fix_action, "remove")
        finally:
            tf_path.unlink()

    def test_clean_file_produces_no_violations(self):
        """Verify that compliant code produces zero violations."""
        clean_code = """
import os

def connect_api():
    api_key = os.environ.get("API_KEY", "")
    return api_key
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(clean_code)
            tf_path = Path(tf.name)

        try:
            violations = scan_file(tf_path, self.rules)
            self.assertEqual(len(violations), 0)
        finally:
            tf_path.unlink()


if __name__ == "__main__":
    unittest.main()
