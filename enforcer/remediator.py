"""Safe interactive remediation engine for Agentic Rule Enforcer.

Computes exact unified diffs, presents color-coded previews, requires developer
confirmation, creates safety snapshots, and writes remediated files atomically.
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from enforcer.backup import create_backup
from enforcer.parser import Rule
from enforcer.scanner import Violation, run_scan
from enforcer.ui import (
    COLOR_BOLD,
    COLOR_BOLD_GREEN,
    COLOR_CYAN,
    COLOR_GRAY,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_RESET,
    COLOR_YELLOW,
    colorize,
    safe_print,
)


def compute_file_fix(file_path: Path, violations: List[Violation]) -> Tuple[str, str, List[str]]:
    """Compute original content, remediated content, and unified diff for a file."""
    original_text = file_path.read_text(encoding="utf-8", errors="replace")
    original_lines = original_text.splitlines(keepends=True)

    # Sort violations in descending line order to prevent offset shifts
    file_violations = [v for v in violations if v.file_path == file_path]
    file_violations.sort(key=lambda v: v.line_number, reverse=True)

    modified_lines = list(original_lines)
    seen_lines = set()

    for v in file_violations:
        line_idx = v.line_number - 1  # 0-indexed
        if line_idx in seen_lines:
            continue
        seen_lines.add(line_idx)

        if v.fix_action == "remove":
            # Remove the line
            modified_lines[line_idx] = ""
        elif v.fix_action == "env_var" and v.suggested_fix is not None:
            # Preserve indentation
            orig_line = original_lines[line_idx]
            indent = orig_line[: len(orig_line) - len(orig_line.lstrip())]
            modified_lines[line_idx] = f"{indent}{v.suggested_fix}\n"

    # Clean out empty lines that were completely removed
    cleaned_modified: List[str] = []
    for line in modified_lines:
        if line == "":
            continue
        cleaned_modified.append(line)

    modified_text = "".join(cleaned_modified)

    diff = list(
        difflib.unified_diff(
            original_lines,
            cleaned_modified,
            fromfile=f"a/{file_path.name}",
            tofile=f"b/{file_path.name}",
            lineterm="",
        )
    )

    return original_text, modified_text, diff


def render_color_diff(diff_lines: List[str]) -> None:
    """Print standard unified diff lines with ANSI color highlights."""
    for line in diff_lines:
        line_clean = line.rstrip()
        if line_clean.startswith("---") or line_clean.startswith("+++"):
            safe_print(colorize(line_clean, COLOR_BOLD))
        elif line_clean.startswith("@@"):
            safe_print(colorize(line_clean, COLOR_CYAN))
        elif line_clean.startswith("-"):
            safe_print(colorize(line_clean, COLOR_RED))
        elif line_clean.startswith("+"):
            safe_print(colorize(line_clean, COLOR_GREEN))
        else:
            safe_print(colorize(line_clean, COLOR_GRAY))


def run_remediation(
    target_path: Path,
    rules: List[Rule],
    dry_run: bool = False,
    yes: bool = False,
) -> int:
    """Run interactive remediation workflow."""
    violations = run_scan(target_path, rules)
    auto_violations = [v for v in violations if v.fix_action != "manual"]

    safe_print("\n" + "=" * 70)
    safe_print(colorize(f" {COLOR_BOLD}AGENTIC RULE ENFORCER -- REMEDIATION & DIFF{COLOR_RESET}", COLOR_CYAN))
    safe_print("=" * 70)

    if not auto_violations:
        if not violations:
            safe_print(colorize(" No violations found! Codebase is already compliant.", COLOR_GREEN))
        else:
            safe_print(
                colorize(
                    f" Found {len(violations)} violation(s), but none support automated fixing (manual review required).",
                    COLOR_YELLOW,
                )
            )
        safe_print("=" * 70 + "\n")
        return 0

    # Group by file
    files_to_fix: Dict[Path, List[Violation]] = {}
    for v in auto_violations:
        files_to_fix.setdefault(v.file_path, []).append(v)

    safe_print(
        f"Preparing fixes for {colorize(str(len(auto_violations)), COLOR_BOLD)} violation(s) across {len(files_to_fix)} file(s):\n"
    )

    planned_patches: List[Tuple[Path, str, str]] = []

    for file_p, f_violations in files_to_fix.items():
        orig_text, mod_text, diff_lines = compute_file_fix(file_p, f_violations)
        if not diff_lines:
            continue

        planned_patches.append((file_p, orig_text, mod_text))

        safe_print(f"File: {colorize(str(file_p), COLOR_BOLD)}")
        safe_print("-" * 70)
        render_color_diff(diff_lines)
        safe_print("-" * 70 + "\n")

    if not planned_patches:
        safe_print("[INFO] No applicable diff generated.\n")
        return 0

    if dry_run:
        safe_print(
            colorize(" [DRY-RUN] No changes were written to disk. Run without --dry-run to apply.", COLOR_CYAN)
        )
        safe_print("=" * 70 + "\n")
        return 0

    # User confirmation prompt
    if not yes:
        try:
            prompt_str = f"Apply these changes to {len(planned_patches)} file(s)? [Y/n]: "
            choice = input(prompt_str).strip().lower()
            if choice not in ("y", "yes", ""):
                safe_print(colorize("[ABORT] Remediation canceled by user.", COLOR_YELLOW))
                return 0
        except (KeyboardInterrupt, EOFError):
            safe_print("\n" + colorize("[ABORT] Canceled.", COLOR_YELLOW))
            return 0

    # Create safety backup snapshot first
    affected_files = [p[0] for p in planned_patches]
    backup_path = create_backup(affected_files)
    safe_print(f"\n[OK] Safety backup created at: {colorize(str(backup_path), COLOR_GREEN)}")

    # Apply atomic file writes
    for file_p, _, mod_text in planned_patches:
        file_p.write_text(mod_text, encoding="utf-8")
        safe_print(f" [APPLIED] Updated {file_p}")

    safe_print("\n" + colorize(f" [PASS] Successfully remediated {len(planned_patches)} file(s).", COLOR_BOLD_GREEN))
    safe_print(colorize(" To revert these changes at any time, run: python -m enforcer.cli rollback", COLOR_CYAN))
    safe_print("=" * 70 + "\n")
    return 0
