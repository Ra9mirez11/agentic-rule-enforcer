---
doc: checklist
status: approved
---

# Build Checklist

Build mode: fast

## Slices

- [ ] **1. Core Scaffolding, Extensible Rule Parser, and Init/Rules Commands**
  Becomes usable: CLI can run `init` to bootstrap customizable `agent_rules.md`, `rules` to list and validate all active rules, and the parser compiles custom developer rules from clean Markdown sections.
  Why now: Bootstraps the project scaffold and proves the extensible rule engine before implementing the scanner.
  PRD ref: `prd.md > 1. Rulebook Parsing & Configuration`
  Spec ref: `spec.md > 1. enforcer.parser`, `spec.md > File Structure`
  Build: Scaffold `enforcer/` package, implement `parser.py` supporting human-editable Markdown sections with tags (Pattern, Severity, Message, Fix), implement `cli.py` with `init` and `rules` subcommands, and add unit tests `tests/test_parser.py`.
  Verify (mechanical): Run `python -m unittest tests/test_parser.py` and verify `python -m enforcer.cli init` creates extensible `agent_rules.md`, and `python -m enforcer.cli rules` lists all parsed rules.
  Learner check: Run `python -m enforcer.cli init` and `python -m enforcer.cli rules` to see the parsed rules.
  Commit: `Initialize project scaffolding, extensible rule parser, and CLI init/rules`

- [ ] **2. Core Scanning Engine and High-Contrast Terminal UI**
  Becomes usable: Full `scan` command that inspects files against standard and custom rules (secrets, agent fluff, scope guards), outputting a high-contrast ANSI terminal report with line numbers, code snippets, and exit code 0 or 1.
  Why now: Delivers the unique kernel and the primary verification loop for pre-commit and CI gates.
  PRD ref: `prd.md > 2. Deep Scanning & Accurate Diagnostics`, `prd.md > Screens and Layout`
  Spec ref: `spec.md > 2. enforcer.scanner`, `spec.md > 5. enforcer.ui`
  Build: Implement `scanner.py` evaluating custom and preset rule patterns; implement `ui.py` for colored terminal tables and diagnostics; wire into `cli.py`; add `tests/test_scanner.py`.
  Verify (mechanical): Run `python -m unittest tests/test_scanner.py` and execute scan against sample test file verifying exit code 1 and accurate line reporting.
  Learner check: Run `python -m enforcer.cli scan` on sample code and inspect the formatted failure table.
  Commit: `Implement scanning engine and ANSI terminal report UI`

- [ ] **3. Safe Interactive Remediation, Backups, and Rollback**
  Becomes usable: Running `fix` displays a colored unified diff, prompts for confirmation [Y/n], creates a timestamped backup in `.agentic-enforcer/backups/`, applies remediated code atomically, and enables instant restoration via `rollback`.
  Why now: Completes the end-to-end demo journey (detect -> review diff -> safe backup & fix -> clean scan / rollback).
  PRD ref: `prd.md > 3. Safe Interactive Remediation & Auto-Fix`, `prd.md > 4. Backup & Rollback Engine`
  Spec ref: `spec.md > 3. enforcer.remediator`, `spec.md > 4. enforcer.backup`
  Build: Implement `remediator.py` with unified diff generation, implement `backup.py` with snapshot and restore logic, connect `fix` and `rollback` subcommands to `cli.py`, add `tests/test_remediator.py` and `tests/test_backup.py`.
  Verify (mechanical): Run `python -m unittest discover -s tests`, run fix on a violation file, verify backup creation and clean follow-up scan, then verify rollback restores original file byte-for-byte.
  Learner check: Run `fix`, review diff, approve patch, verify clean scan, and test `rollback`.
  Commit: `Add interactive remediation, automated backups, and rollback`

## Hands-on Checkpoints

- [ ] Early usable behavior explored — Slice 2 (Scanning engine and terminal report on sample code)
- [ ] Final kick-the-tires exploration and feedback completed

## Final Review

- [ ] Final review complete — feedback resolved and learner confirms ready to ship

## Code Tour and App Map

- [ ] Learning activity complete — guided route, focused alternative, prior practice connected, or brief recap
- [ ] Optional edit and transfer reflection addressed — offered/declined/already covered/not applicable as appropriate
- [ ] `devpost/app-map.html` generated from finished code, checked, and shown, including a project-grounded practice to reuse

Activity and evidence: [to be recorded during wrap-up]
Route and stops: [to be recorded during wrap-up]
Edit outcome: [to be recorded during wrap-up]
Reflection: [to be recorded during wrap-up]
Activity mode: [to be recorded during wrap-up]

## Revisions
