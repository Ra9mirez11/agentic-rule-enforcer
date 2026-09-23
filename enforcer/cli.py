"""Command-line interface for Agentic Rule Enforcer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from enforcer.parser import DEFAULT_RULEBOOK_TEMPLATE, parse_rulebook


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize a customizable agent_rules.md rulebook in the project."""
    target_path = Path(args.output)
    if target_path.exists() and not args.force:
        print(f"[WARN] Rulebook already exists at: {target_path}. Use --force to overwrite.")
        return 0

    target_path.write_text(DEFAULT_RULEBOOK_TEMPLATE, encoding="utf-8")
    print(f"[OK] Created customizable rulebook at: {target_path}")
    print("[INFO] Developers can add custom rules under ### RULE-... sections.")
    return 0


def cmd_rules(args: argparse.Namespace) -> int:
    """List and validate all active rules loaded from the rulebook."""
    rulebook_path = Path(args.rules)
    if not rulebook_path.exists():
        print(f"[FAIL] Rulebook not found: {rulebook_path}")
        print("[INFO] Run 'python -m enforcer.cli init' to create one.")
        return 2

    try:
        rules = parse_rulebook(rulebook_path)
    except Exception as exc:
        print(f"[FAIL] Error parsing rulebook: {exc}")
        return 2

    print(f"\n================ ACTIVE RULES ({len(rules)}) ================")
    print(f"Source: {rulebook_path.resolve()}\n")

    for rule in rules:
        status_label = f"[{rule.severity}]"
        print(f"{status_label:<12} {rule.id}: {rule.title}")
        print(f"             Scope: {', '.join(rule.file_types)}")
        print(f"             Patterns: {len(rule.compiled_patterns)} active regex(es)")
        print(f"             Fix Action: {rule.fix_action}")
        print(f"             Details: {rule.description}")
        print("-" * 60)

    print(f"\n[OK] All {len(rules)} rules compiled and verified successfully.\n")
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    """Scan files against active rules."""
    from enforcer.scanner import run_scan
    from enforcer.ui import render_scan_results

    rulebook_path = Path(args.rules)
    if not rulebook_path.exists():
        print(f"[FAIL] Rulebook not found: {rulebook_path}. Run 'init' first.")
        return 2

    rules = parse_rulebook(rulebook_path)
    target_path = Path(args.target)
    violations = run_scan(target_path, rules)
    return render_scan_results(violations, rules, target_path)


def cmd_fix(args: argparse.Namespace) -> int:
    """Interactively remediate rule violations with safe backups."""
    from enforcer.remediator import run_remediation

    rulebook_path = Path(args.rules)
    if not rulebook_path.exists():
        print(f"[FAIL] Rulebook not found: {rulebook_path}.")
        return 2

    rules = parse_rulebook(rulebook_path)
    target_path = Path(args.target)
    return run_remediation(target_path, rules, dry_run=args.dry_run, yes=args.yes)


def cmd_rollback(args: argparse.Namespace) -> int:
    """Roll back files to the most recent backup snapshot."""
    from enforcer.backup import run_rollback

    return run_rollback()


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="agentic-rule-enforcer",
        description="Gatekeeper for AI coding agents: validates code against project rules.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: init
    init_parser = subparsers.add_parser("init", help="Bootstrap a standard agent_rules.md file.")
    init_parser.add_argument(
        "--output",
        "-o",
        default="agent_rules.md",
        help="Path where agent_rules.md will be created (default: agent_rules.md).",
    )
    init_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing rulebook file.",
    )
    init_parser.set_defaults(func=cmd_init)

    # Subcommand: rules
    rules_parser = subparsers.add_parser("rules", help="List and validate active rules.")
    rules_parser.add_argument(
        "--rules",
        "-r",
        default="agent_rules.md",
        help="Path to rulebook Markdown file (default: agent_rules.md).",
    )
    rules_parser.set_defaults(func=cmd_rules)

    # Subcommand: scan
    scan_parser = subparsers.add_parser("scan", help="Scan code files against rules.")
    scan_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Directory or file to scan (default: current directory).",
    )
    scan_parser.add_argument(
        "--rules",
        "-r",
        default="agent_rules.md",
        help="Path to rulebook Markdown file (default: agent_rules.md).",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # Subcommand: fix
    fix_parser = subparsers.add_parser("fix", help="Interactively review and apply fixes.")
    fix_parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Directory or file to remediate (default: current directory).",
    )
    fix_parser.add_argument(
        "--rules",
        "-r",
        default="agent_rules.md",
        help="Path to rulebook Markdown file (default: agent_rules.md).",
    )
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show diff without applying changes.",
    )
    fix_parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Apply changes without interactive confirmation prompt.",
    )
    fix_parser.set_defaults(func=cmd_fix)

    # Subcommand: rollback
    rollback_parser = subparsers.add_parser("rollback", help="Revert to last backup snapshot.")
    rollback_parser.set_defaults(func=cmd_rollback)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
