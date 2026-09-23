---
doc: prd
status: approved
---

# Agentic Rule Enforcer — Product Requirements

A developer-first CLI guardrail system that monitors, validates, and remediates code created by AI coding assistants against local project guidelines and security policies before commits are finalized.

Source: `scope.md > The Unique Kernel` and `scope.md > The Core Loop`.

## The Core Journey
1. **Initialization (`init`)**: If the user runs the tool in a new repository, running `agentic-rule-enforcer init` bootstraps a standard `agent_rules.md` template containing security, code style, and scope policies.
2. **Pre-Commit Scan (`scan`)**: The developer or automated git hook runs `agentic-rule-enforcer scan`. The tool parses `agent_rules.md` and inspects staged changes or targeted directories.
3. **Structured Review**: The user receives a high-contrast, structured terminal report with color-coded badges (`[PASS]`, `[FAIL]`, `[WARN]`), exact file paths, line numbers, code snippets with highlights, and violation explanations.
4. **Remediation Review (`fix --dry-run` / `fix`)**: The user invokes `agentic-rule-enforcer fix`. The tool displays an interactive unified color diff showing the exact proposed modifications.
5. **Safe Confirmation & Backup**: The user explicitly confirms applying the patch (Y/n). Before touching any source file, the tool creates an automatic timestamped backup under `.agentic-enforcer/backups/`.
6. **Execution & Rollback**: Files are safely updated using atomic writes. If needed, the developer can run `agentic-rule-enforcer rollback` to instantly restore the previous state.
7. **Verification**: Re-running `scan` confirms a clean state (`[PASS]`), exiting with return code 0.

## Screens and Layout (CLI Interaction Surfaces)
- **Dashboard / Report View**:
  - Top header: project name, active rulebook path, number of rules loaded, scanned files count.
  - Results Table: Rule ID, Severity (CRITICAL, HIGH, MEDIUM), File:Line, Status, and Rule Summary.
  - Detailed Violation Card: Collapsible/indented code snippet showing the offending line with contextual lines before and after.
  - Bottom summary bar: Total Violations, Auto-fixable count, Manual review count, and Exit Code (0 clean, 1 violations).
- **Interactive Remediation View**:
  - File-by-file Git-style colored diff (red for removals, green for additions).
  - Explicit confirmation prompt: `Apply this patch? [Y/n/q/details]`.
  - Backup creation acknowledgement with exact backup directory path.
- **Rollback View**:
  - List of available backup snapshots with timestamps and modified file counts.
  - Single-command restoration confirmation.

## Look and Feel
- **Terminal Aesthetics**: Professional, high-contrast CLI typography (ANSI colors, bold labels, UTF-8 status glyphs with graceful ASCII fallback for legacy consoles).
- **Color Palette**:
  - `[PASS]` / Clean: Bright Green
  - `[FAIL]` / Critical: Bold Red
  - `[WARN]` / Notice: Amber / Yellow
  - Information / Headers: Cyan and Bold White
  - Diffs: Standard red (- deletion) and green (+ addition)
- **Tone**: Objective, technical, and actionable. No conversational fluff or emojis; precise line numbers and exact remediation instructions.

## Features and Behavior

### 1. Rulebook Parsing & Configuration
- Supports Markdown rule definitions (e.g. `agent_rules.md`) structured by headers or bullet points.
- Pre-packaged checks for core agent mistakes:
  - **Secrets Leakage**: Detection of hardcoded API keys, private keys, JWTs, and passwords.
  - **Rulebook Fluff & Log Dumps**: Detection of disallowed terminal spam, excessive debug logs, or banned conversational patterns in committed assets.
  - **Protected Scope Guard**: Detection of unauthorized edits to sensitive configuration files (e.g. `.env`, CI workflows, root build scripts).
- Acceptance Criteria:
  - [x] Correctly identifies and extracts rules from `agent_rules.md`.
  - [x] Gracefully handles missing rulebook by printing guidance to run `init`.

### 2. Deep Scanning & Accurate Diagnostics
- Analyzes either single files, git staged diffs, or entire project directories.
- Acceptance Criteria:
  - [x] Output reports exact 1-indexed file lines where violations occur.
  - [x] Returns standard exit code `0` when all checks pass.
  - [x] Returns exit code `1` when blocking violations are discovered (enabling pre-commit blocking).

### 3. Safe Interactive Remediation & Auto-Fix
- Generates precise unified diffs replacing violated lines with rule-compliant code (e.g. replacing hardcoded secrets with `os.environ.get(...)` / `process.env...`, removing disallowed statements).
- Acceptance Criteria:
  - [x] Displays unified diff before applying changes.
  - [x] Requires explicit user confirmation before writing changes to disk.
  - [x] Supports `--dry-run` to preview changes without filesystem modification.

### 4. Backup & Rollback Engine
- Creates snapshot copies of all modified files in `.agentic-enforcer/backups/<timestamp>/` prior to any disk write.
- Provides `agentic-rule-enforcer rollback` command to revert the latest patch.
- Acceptance Criteria:
  - [x] Backup directory created automatically with original file contents.
  - [x] Rollback restores exact original files byte-for-byte.

## States and Boundaries
- **Uninitialized State**: No `agent_rules.md` present -> CLI notifies the user with instructions to run `init` or specify custom `--rules <path>`.
- **Clean State (Zero Violations)**: CLI outputs green summary with metrics and exits code 0.
- **Violation State (Non-zero violations)**: Displays formatted failure table, lists auto-fix availability, and exits code 1.
- **Pre-Fix State**: Displays colored unified diff and halts for user confirmation.
- **Rollback State**: Identifies prior backup metadata and prompts to confirm restoration.

## Product Decisions
- **Interactive Confirmation Over Silent Auto-Write**: To prevent destructive edits by AI or auto-tools, developer consent is mandatory before modifying source code.
- **Automatic Backups by Default**: Any mutating action must be reversible via `rollback`.
- **Standalone Zero-Dependency Engine**: For reliability and speed in terminal environments, core scanning runs fast and locally without requiring cloud network roundtrips.

## What We're Building (POC Scope)
- Complete CLI executable with commands: `init`, `scan`, `fix`, `rollback`.
- Rule scanner with built-in regex & pattern analyzers for secrets, agent fluff, and file scope constraints.
- Unified diff viewer and interactive CLI prompt.
- Backup snapshot engine and one-command rollback.

## Deferred From the POC
- Custom Web UI dashboard (CLI gives 100% developer control and integrates directly into git hooks).
- Multi-language abstract syntax tree (AST) deep static analysis beyond regex/heuristics.

## Possible Later Enhancements
- Pre-commit git hook automated installer script (`agentic-rule-enforcer install-hook`).
- GitHub Action companion for pull request automated reviews.

## Non-Goals
- Replacing full-fledged compiler analyzers like ESLint or Rust compiler; this tool focuses specifically on enforcing AI agent behavioral guidelines, security constraints, and project policies.

## Open Questions
- None blocking. All core behaviors, safety guarantees, and UI layout are specified.
