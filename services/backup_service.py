"""
ParkSmart Pro — Database Backup & Disaster Recovery Service
TQM Principle: Risk Mitigation & Business Continuity (ISO/IEC 25010)
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import config
from database.connection import get_db_connection
from database.migrations import check_integrity
from services.audit_service import audit_service
from utils.logger import get_logger

logger = get_logger("backup_service")

class BackupService:
    def create_backup(self, user_id: Optional[int] = None,
                      username: Optional[str] = None) -> Tuple[bool, Optional[Path], str]:
        """
        Create a live, atomic, non-locking SQLite backup using the online backup API.
        Verifies integrity before declaring success.
        """
        config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"parksmart_backup_{timestamp}.db"
        backup_path = config.BACKUP_DIR / backup_filename

        src_conn = get_db_connection()
        try:
            dest_conn = sqlite3.connect(str(backup_path))
            try:
                # Online backup API
                src_conn.backup(dest_conn, pages=100)
            finally:
                dest_conn.close()

            # Verify integrity of backup
            is_valid, msgs = check_integrity(backup_path)
            if not is_valid:
                backup_path.unlink(missing_ok=True)
                return False, None, f"Backup created but failed integrity check: {'; '.join(msgs)}"

            file_size_kb = round(backup_path.stat().st_size / 1024, 2)
            audit_service.log(
                action="BACKUP_DATABASE", entity_type="SYSTEM", entity_id=backup_filename,
                details=f"Backup created successfully ({file_size_kb} KB)",
                user_id=user_id, username=username
            )
            logger.info(f"Database backed up to {backup_filename} ({file_size_kb} KB)")
            return True, backup_path, f"Database backup created: {backup_filename} ({file_size_kb} KB)"

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            if backup_path.exists():
                backup_path.unlink(missing_ok=True)
            return False, None, f"Backup failed: {str(e)}"
        finally:
            src_conn.close()

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files sorted newest first."""
        config.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        files = sorted(config.BACKUP_DIR.glob("*.db"), key=lambda f: f.stat().st_mtime, reverse=True)
        backups = []
        for f in files:
            stat = f.stat()
            backups.append({
                "filename": f.name,
                "filepath": f,
                "size_kb": round(stat.st_size / 1024, 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_safety": f.name.startswith("pre_restore_safety")
            })
        return backups

    def restore_backup(self, backup_path: Path, user_id: Optional[int] = None,
                       username: Optional[str] = None) -> Tuple[bool, str]:
        """
        Restore database from backup.
        TQM Failsafe:
        1. Verifies the backup file exists and passes integrity check.
        2. Automatically creates an emergency snapshot of current DB before replacing.
        3. Restores database.
        4. Verifies newly restored DB integrity.
        """
        backup_path = Path(backup_path)
        if not backup_path.exists():
            return False, "Selected backup file does not exist."

        # 1. Pre-validation of target backup
        is_valid, msgs = check_integrity(backup_path)
        if not is_valid:
            return False, f"Selected backup is corrupted: {'; '.join(msgs)}"

        # 2. Safety snapshot of current database
        safety_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        safety_backup = config.BACKUP_DIR / f"pre_restore_safety_backup_{safety_time}.db"
        try:
            if config.DB_PATH.exists():
                shutil.copy2(config.DB_PATH, safety_backup)
                logger.info(f"Safety snapshot created at {safety_backup.name}")
        except Exception as e:
            return False, f"Failed to create safety snapshot before restore: {str(e)}"

        # 3. Restore using SQLite backup API (destination is active DB)
        try:
            src_conn = sqlite3.connect(str(backup_path))
            dest_conn = get_db_connection()
            try:
                src_conn.backup(dest_conn, pages=100)
            finally:
                src_conn.close()
                dest_conn.close()

            # 4. Verify restored DB
            restored_ok, restored_msgs = check_integrity(config.DB_PATH)
            if not restored_ok:
                # Emergency rollback to safety backup!
                shutil.copy2(safety_backup, config.DB_PATH)
                return False, f"Restored DB failed integrity check! Rolled back to safety backup. Details: {'; '.join(restored_msgs)}"

            audit_service.log(
                action="RESTORE_DATABASE", entity_type="SYSTEM", entity_id=backup_path.name,
                details=f"Database restored from {backup_path.name}. Safety snapshot: {safety_backup.name}",
                user_id=user_id, username=username
            )
            logger.info(f"Database successfully restored from {backup_path.name}")
            return True, f"Database restored successfully from {backup_path.name}. (Safety snapshot preserved)"

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            if safety_backup.exists():
                shutil.copy2(safety_backup, config.DB_PATH)
            return False, f"Restore failed (rolled back to safety snapshot): {str(e)}"

backup_service = BackupService()
