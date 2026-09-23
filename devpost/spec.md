---
doc: spec
status: approved
---

# Agentic Rule Enforcer — Technical Spec

## How This Works, In Plain Language
Agentic Rule Enforcer is a local command-line gatekeeper written in pure Python. When run, it reads project rule definitions written in Markdown (`agent_rules.md`), extracts rules into deterministic detection patterns, and inspects files or git diffs for violations.

When violations are found (such as hardcoded API secrets, terminal dump logs, or unauthorized edits):
1. It reports them with exact line numbers and code snippets in a high-contrast terminal UI.
2. If the user invokes `fix`, it computes the exact changes, presents an interactive colored diff, and pauses for explicit user approval.
3. Upon approval, it creates a timestamped backup of the target files before applying changes atomically to disk.
4. If anything goes wrong, a single `rollback` command restores the original files.

We chose this zero-external-dependency architecture so that anyone reviewing or cloning the repository can run it immediately without package managers or setup friction.

## The Core Journey Through the System
1. The user executes `python -m enforcer.cli scan` (or CLI alias).
2. `parser.py` parses `agent_rules.md`, compiling regex patterns and scope paths into active rule definitions.
3. `scanner.py` walks target files, applies rule patterns line by line, and generates structured `Violation` objects.
4. `ui.py` displays the results table and exits with code 1 if violations exist (blocking CI / git commit).
5. The user runs `python -m enforcer.cli fix`.
6. `remediator.py` generates unified diffs showing exact line replacements and prints them via `ui.py`.
7. `ui.py` requests confirmation `[Y/n]`.
8. On confirmation, `backup.py` creates a snapshot under `.agentic-enforcer/backups/<timestamp>/` and writes modified files.
9. Subsequent scan exits with code 0 (`[PASS]`).
PRD ref: `prd.md > The Core Journey`.

## Stack
- **Language**: Python 3.10+
- **Standard Library Modules**:
  - `argparse`: Command-line interface parsing and subcommands (`init`, `scan`, `fix`, `rollback`).
  - `difflib`: Computing standard unified diffs for terminal preview and safe patching.
  - `re`: High-performance regular expression matching for secrets, fluff, and code patterns.
  - `pathlib` & `shutil`: Safe filesystem traversal, atomic file writes, and directory backup snapshotting.
  - `json`: Persisting backup metadata and machine-readable output.
- **Tradeoff**: Pure Python standard library means zero external `pip` dependencies, ensuring immediate reproducibility across Windows, macOS, and Linux without virtual environment overhead.

## Where It Runs and How Someone Tries It
- **Runtime**: Local terminal execution in Windows PowerShell, Bash, or zsh with Python 3.10+.
- **Start Command**:
  ```bash
  python -m enforcer.cli scan
  python -m enforcer.cli fix
  python -m enforcer.cli rollback
  ```
- **Demo Recording Flow**:
  1. Show `sample_violations.py` containing hardcoded secrets and debug noise.
  2. Run `python -m enforcer.cli scan` -> displays failure table with colored badges and line numbers (exit code 1).
  3. Run `python -m enforcer.cli fix` -> shows colored diff and prompts for confirmation.
  4. Confirm -> files updated and backup created.
  5. Run `python -m enforcer.cli scan` -> displays all checks passing green (exit code 0).

## Look and Feel
- **Terminal Aesthetics**: Crisp, high-contrast typography using ANSI color codes (`\033[92m` green, `\033[91m` red, `\033[93m` yellow, `\033[96m` cyan, `\033[0m` reset).
- **Badge Indicators**: `[PASS]` in green, `[FAIL]` in bold red, `[INFO]` in cyan.
- **Diff Display**: Git standard color diff highlighting deletions in red and additions in green.
- **Voice/Tone**: Strictly objective, technical diagnostic output without emojis or conversational filler.

## Components

### 1. `enforcer.parser` (Rule Parser)
Reads and tokenizes Markdown rulebooks (`agent_rules.md`). Extracts rules based on numbered items or markdown sections, mapping rule IDs to pattern definitions (e.g. `RULE-01-SECRETS`, `RULE-02-FLUFF`, `RULE-03-SCOPE`).
PRD ref: `prd.md > 1. Rulebook Parsing & Configuration`.

### 2. `enforcer.scanner` (Scan Engine)
Iterates over targeted code files, applying rule patterns. Produces structured `Violation` objects recording file path, 1-indexed line number, violated rule name, snippet, and suggested remediation replacement.
PRD ref: `prd.md > 2. Deep Scanning & Accurate Diagnostics`.

### 3. `enforcer.remediator` (Remediation & Diff Engine)
Takes violations and builds replacement content. Uses `difflib.unified_diff` to generate unified patch representations for user inspection.
PRD ref: `prd.md > 3. Safe Interactive Remediation & Auto-Fix`.

### 4. `enforcer.backup` (Backup & Rollback Engine)
Maintains `.agentic-enforcer/backups/`. Saves timestamped snapshots before executing writes and restores files on `rollback`.
PRD ref: `prd.md > 4. Backup & Rollback Engine`.

### 5. `enforcer.ui` (Terminal Formatter)
Renders tables, diffs, metrics, and prompts with ANSI color formatting.
PRD ref: `prd.md > Screens and Layout`.

## Data Model
- **`Rule`**: `{ id: str, title: str, description: str, severity: str, patterns: list[str], fix_template: str | None }`
- **`Violation`**: `{ rule_id: str, rule_title: str, file_path: Path, line_number: int, line_content: str, fix_replacement: str | None }`
- **`BackupManifest`**: `{ timestamp: str, files: list[str], backup_dir: str }` stored in `.agentic-enforcer/backups/<timestamp>/manifest.json`.

## File Structure
```
F:\Devpost hackatano\
├── enforcer/
│   ├── __init__.py          # Package initialization
│   ├── cli.py               # Main CLI entrypoint and command router
│   ├── parser.py            # Markdown rulebook parser
│   ├── scanner.py           # Core scanning patterns and violation collector
│   ├── remediator.py        # Unified diff generator and patch applicator
│   ├── backup.py            # Snapshot backup and rollback manager
│   └── ui.py                # ANSI terminal presentation and interactive prompts
├── tests/
│   ├── __init__.py
│   ├── test_parser.py       # Rule parsing tests
│   ├── test_scanner.py      # Violation detection tests
│   ├── test_remediator.py   # Diff and fix tests
│   └── test_backup.py       # Backup and rollback tests
├── agent_rules.md           # Default rules template
├── devpost/
│   ├── learner-profile.md   # Devpost learning context
│   ├── scope.md             # Approved Scope
│   ├── prd.md               # Approved PRD
│   └── spec.md              # Approved Technical Spec
└── README.md                # Hackathon presentation documentation
```

## External Services and Dependencies
- **External Dependencies**: None. Uses 100% Python Standard Library.
- **External APIs / Databases**: None. Runs completely offline and locally.

## Important Failure Modes
- **Missing Rulebook**: If `agent_rules.md` is absent, CLI displays instructions to run `python -m enforcer.cli init` and exits with code 2.
- **Corrupted / Invalid File Encoding**: Falls back to UTF-8 with `errors='replace'` to prevent crashes on non-standard binary or foreign character files.
- **Failed Rollback**: If backup directory is missing or empty, CLI reports `No restore point found` without altering project files.

## What Was Simplified and Why
- **Regex & Pattern Engine instead of full AST parsing**: Standard ASTs are language-specific (Python AST cannot parse Solidity or TypeScript). Pattern-based rule evaluation allows the enforcer to monitor multi-language repositories and plain configuration files uniformly.
- **Zero-Dependency CLI instead of rich/curses**: Avoids installation hurdles during review and ensures reliable execution in any terminal.

## Decisions and Open Issues
- **Decision**: Zero external dependencies confirmed for maximum portability and instant verification during hackathon judging.
- **Decision**: Interactive review required for `fix` to guarantee complete developer control and prevent destructive edits.
- **Open Issues**: None. Architecture is verified and ready for implementation.
