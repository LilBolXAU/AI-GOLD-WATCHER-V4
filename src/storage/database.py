"""
SQLite database connection and lifecycle manager for AI GOLD WATCHER V4.
"""

import sqlite3
from pathlib import Path
from typing import Optional
import logging
from src.storage.migrations import apply_migrations

logger = logging.getLogger(__name__)


class Database:
    """Thread-safe SQLite database manager with WAL journal mode."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with row factories and WAL mode."""
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            return conn
        except Exception:
            conn.close()
            raise

    def _init_schema(self) -> None:
        """Initializes tables on startup with integrity recovery."""
        try:
            conn = self.get_connection()
            try:
                # Perform quick integrity check
                cursor = conn.execute("PRAGMA quick_check;")
                res = cursor.fetchone()
                if res and res[0] != "ok":
                    raise sqlite3.DatabaseError(f"Integrity check failed: {res[0]}")
                apply_migrations(conn)
            finally:
                conn.close()
        except (sqlite3.DatabaseError, Exception) as e:
            logger.warning("Corrupted SQLite database detected (%s). Auto-recovering clean database...", e)
            self._recover_corrupted_db()

    def _recover_corrupted_db(self) -> None:
        """Backs up corrupted database and creates a fresh instance."""
        import gc
        import time
        gc.collect()
        ts = int(time.time())
        try:
            if self.db_path.exists():
                corrupted_backup = self.db_path.with_name(f"{self.db_path.stem}_corrupted_{ts}.db")
                try:
                    self.db_path.rename(corrupted_backup)
                    logger.info("Moved corrupted database to %s", corrupted_backup)
                except Exception:
                    self.db_path.unlink(missing_ok=True)
            for ext in ["-wal", "-shm"]:
                sidecar = self.db_path.with_name(self.db_path.name + ext)
                if sidecar.exists():
                    try:
                        sidecar.unlink(missing_ok=True)
                    except Exception:
                        pass
        except Exception as err:
            logger.error("Error cleaning corrupted database files: %s", err)

        # Re-initialize clean schema
        conn = self.get_connection()
        try:
            apply_migrations(conn)
            logger.info("Successfully recreated fresh SQLite database schema at %s", self.db_path)
        finally:
            conn.close()


_DEFAULT_DB: Optional[Database] = None


def init_db(db_path: Path) -> Database:
    """Initialize or get singleton database instance."""
    global _DEFAULT_DB
    if _DEFAULT_DB is None or _DEFAULT_DB.db_path != db_path:
        _DEFAULT_DB = Database(db_path)
    return _DEFAULT_DB
