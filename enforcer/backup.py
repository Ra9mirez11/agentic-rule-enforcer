"""Backup and rollback engine for Agentic Rule Enforcer.

Provides safe, timestamped snapshots of files before any remediation is applied,
allowing instant, byte-for-byte rollbacks.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BACKUP_ROOT = Path(".agentic-enforcer") / "backups"


def create_backup(files: List[Path], project_root: Optional[Path] = None) -> Path:
    """Create a timestamped backup snapshot of the specified files."""
    if project_root is None:
        project_root = Path.cwd()

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_dir = project_root / BACKUP_ROOT / timestamp_str
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    manifest_files: List[Dict[str, str]] = []

    for file_path in files:
        if not file_path.exists():
            continue

        try:
            rel_path = file_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            rel_path = Path(file_path.name)

        dest_path = snapshot_dir / "files" / rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, dest_path)

        manifest_files.append(
            {
                "original_path": str(file_path.resolve()),
                "relative_path": str(rel_path),
                "backup_path": str(dest_path.resolve()),
            }
        )

    manifest_path = snapshot_dir / "manifest.json"
    manifest_data = {
        "timestamp": timestamp_str,
        "files_count": len(manifest_files),
        "files": manifest_files,
    }
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    return snapshot_dir


def get_latest_backup(project_root: Optional[Path] = None) -> Optional[Tuple[Path, dict]]:
    """Retrieve the most recent backup snapshot directory and manifest data."""
    if project_root is None:
        project_root = Path.cwd()

    backup_dir = project_root / BACKUP_ROOT
    if not backup_dir.exists():
        return None

    snapshots = sorted([d for d in backup_dir.iterdir() if d.is_dir()], reverse=True)
    for snapshot in snapshots:
        manifest_file = snapshot / "manifest.json"
        if manifest_file.exists():
            try:
                data = json.loads(manifest_file.read_text(encoding="utf-8"))
                return snapshot, data
            except Exception:
                continue

    return None


def run_rollback(project_root: Optional[Path] = None) -> int:
    """Roll back files from the latest snapshot."""
    if project_root is None:
        project_root = Path.cwd()

    latest = get_latest_backup(project_root)
    if not latest:
        print("\n[FAIL] No backup restore points found in .agentic-enforcer/backups/")
        return 1

    snapshot_dir, manifest = latest
    timestamp = manifest.get("timestamp", "unknown")
    files_list = manifest.get("files", [])

    print("\n" + "=" * 70)
    print(f" AGENTIC RULE ENFORCER -- ROLLBACK TO SNAPSHOT [{timestamp}]")
    print("=" * 70)
    print(f"Restore Point: {snapshot_dir.resolve()}")
    print(f"Files to Restore: {len(files_list)}\n")

    restored_count = 0
    for item in files_list:
        orig = Path(item["original_path"])
        bkp = Path(item["backup_path"])

        if bkp.exists():
            orig.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bkp, orig)
            print(f" [OK] Restored: {orig}")
            restored_count += 1
        else:
            print(f" [WARN] Backup file missing: {bkp}")

    print("-" * 70)
    print(f"[OK] Successfully restored {restored_count} file(s) to state at {timestamp}.\n")
    return 0
