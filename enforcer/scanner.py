"""Code scanning engine for Agentic Rule Enforcer.

Applies active rules against files or directories, collecting line-accurate
violations with code context and suggested remediation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from enforcer.parser import Rule


@dataclass
class Violation:
    """Represents a single rule violation in a specific file and line."""

    rule_id: str
    rule_title: str
    severity: str
    file_path: Path
    line_number: int  # 1-indexed
    line_content: str
    description: str
    fix_action: str
    suggested_fix: Optional[str] = None
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)


IGNORED_DIRECTORIES = {
    ".git",
    ".agents",
    ".claude",
    ".gemini",
    "__pycache__",
    "node_modules",
    ".agentic-enforcer",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
}

IGNORED_FILES = {
    "agent_rules.md",
    "skills-lock.json",
    ".gitignore",
}


def matches_file_type(file_path: Path, allowed_types: List[str]) -> bool:
    """Check if file extension matches the rule's allowed file types."""
    if "*" in allowed_types or "all" in allowed_types:
        return True
    ext = file_path.suffix.lower()
    return ext in allowed_types or file_path.name.lower() in allowed_types


def scan_file(file_path: Path, rules: List[Rule]) -> List[Violation]:
    """Scan an individual file against all applicable rules."""
    violations: List[Violation] = []

    if file_path.name in IGNORED_FILES:
        return violations

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return violations

    lines = content.splitlines()

    for rule in rules:
        if not matches_file_type(file_path, rule.file_types):
            continue

        for idx, line in enumerate(lines):
            line_num = idx + 1  # 1-indexed

            for pattern in rule.compiled_patterns:
                match = pattern.search(line)
                if match:
                    # Capture context lines
                    start_ctx = max(0, idx - 2)
                    end_ctx = min(len(lines), idx + 3)
                    context_before = lines[start_ctx:idx]
                    context_after = lines[idx + 1:end_ctx]

                    # Prepare suggested remediation replacement
                    suggested_fix = None
                    if rule.fix_action == "remove":
                        suggested_fix = ""
                    elif rule.fix_action == "env_var":
                        # Replace matched assignment with environment variable
                        suggested_fix = _generate_env_var_fix(line, match)

                    violations.append(
                        Violation(
                            rule_id=rule.id,
                            rule_title=rule.title,
                            severity=rule.severity,
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line,
                            description=rule.description,
                            fix_action=rule.fix_action,
                            suggested_fix=suggested_fix,
                            context_before=context_before,
                            context_after=context_after,
                        )
                    )
                    break  # One violation per rule per line is sufficient

    return violations


def _generate_env_var_fix(line: str, match) -> str:
    """Generate a clean env var replacement for secret assignments."""
    matched_text = match.group(0)
    if "=" in matched_text:
        var_name, _ = matched_text.split("=", 1)
        var_clean = var_name.strip()
        env_key = var_clean.upper()
        # Detect if Python
        return f'{var_clean} = os.environ.get("{env_key}", "")'
    return line


def run_scan(target_path: Path, rules: List[Rule]) -> List[Violation]:
    """Recursively scan target path against all active rules."""
    all_violations: List[Violation] = []

    if target_path.is_file():
        return scan_file(target_path, rules)

    for root, dirs, files in os.walk(target_path):
        # Exclude ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES]

        # Don't scan inside devpost folder (which holds rules & specs)
        if "devpost" in Path(root).parts:
            continue

        for filename in files:
            file_p = Path(root) / filename
            file_violations = scan_file(file_p, rules)
            all_violations.extend(file_violations)

    return all_violations
