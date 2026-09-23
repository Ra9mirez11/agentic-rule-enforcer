"""Rulebook parser for Agentic Rule Enforcer.

Parses human-readable Markdown rulebooks (such as agent_rules.md) into
executable Rule definitions with compiled regular expressions and metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Rule:
    """Represents an enforceable policy rule."""

    id: str
    title: str
    description: str
    severity: str = "HIGH"
    patterns: List[str] = field(default_factory=list)
    compiled_patterns: List[re.Pattern] = field(default_factory=list)
    file_types: List[str] = field(default_factory=lambda: ["*"])
    fix_action: str = "manual"  # 'remove', 'env_var', 'manual'
    fix_template: Optional[str] = None


DEFAULT_RULEBOOK_TEMPLATE = """# Project Agent Rules

Engineering guidelines and safety boundaries for developers and AI coding agents.

## Section 1: Security & Secrets
Strict boundaries against committing sensitive credentials or private keys.

### RULE-01-SECRETS: Hardcoded Secrets and Tokens
- Severity: CRITICAL
- Description: Detects hardcoded API keys, private keys, passwords, and tokens.
- FileTypes: *
- Pattern: `(?i)(?:api_key|apikey|secret_key|private_key|auth_token|bearer_token|password)\\s*=\\s*['"][a-zA-Z0-9_\\-]{16,}['"]`
- Fix: env_var
- Message: Replace hardcoded credential with environment variable lookup (e.g., os.environ or process.env).

### RULE-02-ETH-KEY: Private Key Hex Constants
- Severity: CRITICAL
- Description: Detects raw 32-byte hexadecimal private keys.
- FileTypes: .py, .ts, .js, .sol, .env
- Pattern: `0x[a-fA-F0-9]{64}`
- Fix: env_var
- Message: Do not hardcode Ethereum/ECDSA private keys in repository files.

## Section 2: Agent Cleanliness & Log Fluff
Ensures code is clean and free of debug statements or unhandled placeholder patterns.

### RULE-03-FLUFF: Debug and Console Dumps
- Severity: HIGH
- Description: Detects forbidden debug logging statements.
- FileTypes: .py, .js, .ts
- Pattern: `(?i)(?:console\\.log\\(|print\\(.*\\b(?:TODO_DEBUG|DEBUG_LOG|DUMP_OUTPUT)\\b)`
- Fix: remove
- Message: Remove debug print/console statements before finalizing commits.

### RULE-04-PASS-TODO: Silent Error Swallowing
- Severity: MEDIUM
- Description: Detects bare pass blocks in except handlers.
- FileTypes: .py
- Pattern: `except\\s+Exception:\\s*pass`
- Fix: manual
- Message: Do not silently swallow exceptions; implement proper error handling or logging.

## Section 3: Scope Guard
Protects project configuration and core policies from unauthorized agent drift.

### RULE-05-PROTECTED-SCOPE: Unauthorized Edits to Root Secrets
- Severity: HIGH
- Description: Prevents creation or modification of tracked local secret files.
- FileTypes: .env, .env.local, .env.production
- Pattern: `^.*$`
- Fix: manual
- Message: Local environment secret files must remain gitignored and untracked.
"""


def parse_rulebook(rulebook_path: Path) -> List[Rule]:
    """Parse a Markdown rulebook file and return a list of active Rules."""
    if not rulebook_path.exists():
        raise FileNotFoundError(f"Rulebook file not found at: {rulebook_path}")

    content = rulebook_path.read_text(encoding="utf-8", errors="replace")
    return parse_rulebook_content(content)


def parse_rulebook_content(content: str) -> List[Rule]:
    """Extract and compile rules from Markdown text."""
    rules: List[Rule] = []

    # Match sections starting with ### RULE-...
    rule_blocks = re.split(r"(?=^###\s+RULE-)", content, flags=re.MULTILINE)

    for block in rule_blocks:
        block = block.strip()
        if not block.startswith("###"):
            continue

        lines = block.splitlines()
        header = lines[0].lstrip("#").strip()

        # Parse Header format: RULE-ID: Title
        if ":" in header:
            rule_id, title = header.split(":", 1)
            rule_id = rule_id.strip()
            title = title.strip()
        else:
            rule_id = header
            title = header

        severity = "HIGH"
        description = title
        patterns: List[str] = []
        file_types: List[str] = ["*"]
        fix_action = "manual"
        fix_template = None
        message = ""

        for line in lines[1:]:
            line_str = line.strip()
            if not line_str.startswith("-"):
                continue

            entry = line_str.lstrip("-").strip()
            if ":" not in entry:
                continue

            key, value = entry.split(":", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "severity":
                severity = value.upper()
            elif key == "description":
                description = value
            elif key == "pattern":
                # Extract regex, optionally wrapped in backticks
                pattern_val = value.strip("`").strip()
                if pattern_val:
                    patterns.append(pattern_val)
            elif key == "filetypes":
                types = [ft.strip().lower() for ft in value.split(",") if ft.strip()]
                if types:
                    file_types = types
            elif key == "fix":
                fix_action = value.lower()
            elif key == "template":
                fix_template = value
            elif key == "message":
                message = value

        if message:
            description = message

        compiled_patterns: List[re.Pattern] = []
        for pat in patterns:
            try:
                compiled = re.compile(pat)
                compiled_patterns.append(compiled)
            except re.error as err:
                # Store a dummy regex or skip with warning
                continue

        if rule_id and (compiled_patterns or patterns):
            rule = Rule(
                id=rule_id,
                title=title,
                description=description,
                severity=severity,
                patterns=patterns,
                compiled_patterns=compiled_patterns,
                file_types=file_types,
                fix_action=fix_action,
                fix_template=fix_template,
            )
            rules.append(rule)

    return rules
