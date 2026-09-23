"""Terminal UI and output formatter for Agentic Rule Enforcer.

Provides high-contrast ANSI colored tables, status badges, contextual code
snippets, and exit codes for CI/CD and pre-commit integrations.
Uses ASCII-safe frames for maximum compatibility across Windows CP1250 and UTF-8.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from enforcer.parser import Rule
from enforcer.scanner import Violation

# ANSI Color codes (supported natively in Windows 10/11 Terminal, PowerShell, Linux, macOS)
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[92m"
COLOR_BOLD_GREEN = "\033[1;92m"
COLOR_RED = "\033[91m"
COLOR_BOLD_RED = "\033[1;91m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_GRAY = "\033[90m"


def supports_color() -> bool:
    """Check if stdout supports ANSI color output."""
    return sys.stdout.isatty() or "WT_SESSION" in sys.platform or True


def colorize(text: str, color_code: str) -> str:
    """Wrap text in ANSI color codes if terminal supports it."""
    if not supports_color():
        return text
    return f"{color_code}{text}{COLOR_RESET}"


def safe_print(text: str = "") -> None:
    """Safely print text handling Windows terminal encoding fallbacks."""
    try:
        print(text)
    except UnicodeEncodeError:
        safe_encoded = text.encode(sys.stdout.encoding or "ascii", errors="replace").decode(
            sys.stdout.encoding or "ascii"
        )
        print(safe_encoded)


def render_scan_results(
    violations: List[Violation],
    rules: List[Rule],
    target_path: Path,
) -> int:
    """Render structured scan report to terminal and return exit code (0 or 1)."""
    safe_print("\n" + "=" * 70)
    safe_print(colorize(f" {COLOR_BOLD}AGENTIC RULE ENFORCER -- SCAN REPORT{COLOR_RESET}", COLOR_CYAN))
    safe_print("=" * 70)
    safe_print(f"Target:       {target_path.resolve()}")
    safe_print(f"Active Rules: {len(rules)}")

    if not violations:
        safe_print("\n" + colorize(" [PASS] ALL CHECKS PASSED ", COLOR_BOLD_GREEN))
        safe_print(colorize(" Clean codebase: no agent rule violations detected.", COLOR_GREEN))
        safe_print("=" * 70 + "\n")
        return 0

    # Group violations by file
    files_with_violations = len(set(v.file_path for v in violations))
    auto_fixable = sum(1 for v in violations if v.fix_action != "manual")

    safe_print(
        colorize(
            f"\n [FAIL] {len(violations)} VIOLATION(S) DETECTED across {files_with_violations} file(s)",
            COLOR_BOLD_RED,
        )
    )
    safe_print("-" * 70)

    for idx, v in enumerate(violations, 1):
        rel_path = v.file_path
        try:
            rel_path = v.file_path.relative_to(Path.cwd())
        except ValueError:
            pass

        sev_color = COLOR_BOLD_RED if v.severity == "CRITICAL" else COLOR_YELLOW
        sev_badge = colorize(f"[{v.severity}]", sev_color)
        fix_badge = (
            colorize("[AUTO-FIXABLE]", COLOR_GREEN)
            if v.fix_action != "manual"
            else colorize("[MANUAL REVIEW]", COLOR_GRAY)
        )

        safe_print(
            f"\n{colorize(f'#{idx}', COLOR_CYAN)} {sev_badge} {colorize(v.rule_id, COLOR_BOLD)}: {v.rule_title} {fix_badge}"
        )
        safe_print(f"  Location: {colorize(f'{rel_path}:{v.line_number}', COLOR_BOLD)}")
        safe_print(f"  Details:  {v.description}")

        # Code snippet with line numbers (ASCII safe)
        safe_print("  " + colorize("+" + "-" * 64, COLOR_GRAY))
        for ctx_line in v.context_before:
            safe_print(f"  {colorize('|', COLOR_GRAY)} {colorize('   ', COLOR_GRAY)} {ctx_line}")

        # Offending line highlighted in red
        offending_str = f"  {colorize('|', COLOR_GRAY)} {colorize('>> ', COLOR_BOLD_RED)}{v.line_number:4d} | {colorize(v.line_content, COLOR_RED)}"
        safe_print(offending_str)

        for ctx_line in v.context_after:
            safe_print(f"  {colorize('|', COLOR_GRAY)} {colorize('   ', COLOR_GRAY)} {ctx_line}")
        safe_print("  " + colorize("+" + "-" * 64, COLOR_GRAY))

    safe_print("\n" + "=" * 70)
    safe_print(colorize(" SUMMARY STATISTICS", COLOR_BOLD))
    safe_print(f" Total Violations:     {colorize(str(len(violations)), COLOR_BOLD_RED)}")
    safe_print(f" Auto-Fixable:         {colorize(str(auto_fixable), COLOR_GREEN)}")
    safe_print(f" Manual Action Needed: {colorize(str(len(violations) - auto_fixable), COLOR_YELLOW)}")
    safe_print("-" * 70)
    if auto_fixable > 0:
        safe_print(
            colorize(
                f" Run 'python -m enforcer.cli fix' to review and apply {auto_fixable} automatic fix(es).",
                COLOR_CYAN,
            )
        )
    safe_print("=" * 70 + "\n")

    return 1  # Exit 1 signals failure to pre-commit and CI gates
