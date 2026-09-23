"""Unit tests for backup and rollback module."""

import tempfile
import unittest
from pathlib import Path

from enforcer.backup import create_backup, get_latest_backup, run_rollback


class TestBackup(unittest.TestCase):
    """Test suite for backup snapshotting and rollback restoration."""

    def test_backup_and_rollback(self):
        with tempfile.TemporaryDirectory() as temp_dir_str:
            temp_dir = Path(temp_dir_str)
            test_file = temp_dir / "target.py"
            test_file.write_text("original_content = 42\n", encoding="utf-8")

            # 1. Create backup
            backup_dir = create_backup([test_file], project_root=temp_dir)
            self.assertTrue(backup_dir.exists())

            # 2. Modify target file
            test_file.write_text("mutated_content = 99\n", encoding="utf-8")
            self.assertEqual(test_file.read_text(encoding="utf-8"), "mutated_content = 99\n")

            # 3. Verify latest backup detected
            latest = get_latest_backup(project_root=temp_dir)
            self.assertIsNotNone(latest)

            # 4. Perform rollback
            res = run_rollback(project_root=temp_dir)
            self.assertEqual(res, 0)

            # 5. Confirm original content restored
            self.assertEqual(test_file.read_text(encoding="utf-8"), "original_content = 42\n")


if __name__ == "__main__":
    unittest.main()
