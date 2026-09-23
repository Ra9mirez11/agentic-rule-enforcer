"""Unit tests for rulebook parser."""

import unittest
from pathlib import Path

from enforcer.parser import DEFAULT_RULEBOOK_TEMPLATE, parse_rulebook_content


class TestRuleParser(unittest.TestCase):
    """Test suite for Markdown rulebook parsing."""

    def test_parse_default_template(self):
        """Ensure default rulebook template extracts all built-in rules."""
        rules = parse_rulebook_content(DEFAULT_RULEBOOK_TEMPLATE)
        self.assertGreaterEqual(len(rules), 4)

        rule_ids = [r.id for r in rules]
        self.assertIn("RULE-01-SECRETS", rule_ids)
        self.assertIn("RULE-02-ETH-KEY", rule_ids)
        self.assertIn("RULE-03-FLUFF", rule_ids)
        self.assertIn("RULE-04-PASS-TODO", rule_ids)

        rule_01 = next(r for r in rules if r.id == "RULE-01-SECRETS")
        self.assertEqual(rule_01.severity, "CRITICAL")
        self.assertEqual(rule_01.fix_action, "env_var")
        self.assertGreater(len(rule_01.compiled_patterns), 0)

    def test_custom_developer_rule(self):
        """Ensure developers can define custom rules via clean Markdown sections."""
        custom_md = """
### RULE-CUSTOM-TEST: Disallow Hardcoded IP Addresses
- Severity: HIGH
- Pattern: `\\b\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\b`
- FileTypes: .py, .yaml, .json
- Fix: remove
- Message: Do not hardcode raw IP addresses in configuration.
"""
        rules = parse_rulebook_content(custom_md)
        self.assertEqual(len(rules), 1)
        r = rules[0]
        self.assertEqual(r.id, "RULE-CUSTOM-TEST")
        self.assertEqual(r.title, "Disallow Hardcoded IP Addresses")
        self.assertEqual(r.severity, "HIGH")
        self.assertEqual(r.file_types, [".py", ".yaml", ".json"])
        self.assertEqual(r.fix_action, "remove")
        self.assertEqual(r.description, "Do not hardcode raw IP addresses in configuration.")


if __name__ == "__main__":
    unittest.main()
