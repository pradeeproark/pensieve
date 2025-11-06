"""Migration system for database schema evolution."""

import hashlib
import importlib
import pkgutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from pensieve import migrations


class MigrationModule(Protocol):
    """Protocol for migration modules."""

    VERSION: int
    NAME: str

    def upgrade(self, conn: sqlite3.Connection) -> None:
        """Apply the migration."""
        ...

    def checksum(self) -> str:
        """Return SHA256 checksum of migration."""
        ...


class MigrationRunner:
    """Manages database migrations."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        """Initialize migration runner.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn
        self._ensure_migrations_table()

    def _ensure_migrations_table(self) -> None:
        """Create schema_migrations table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL,
                checksum TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def get_current_version(self) -> int:
        """Get current schema version.

        Returns:
            Current version number, 0 if no migrations applied
        """
        cursor = self.conn.execute(
            "SELECT MAX(version) FROM schema_migrations"
        )
        result = cursor.fetchone()[0]
        return result if result is not None else 0

    def get_applied_migrations(self) -> list[tuple[int, str, str, str]]:
        """Get list of applied migrations.

        Returns:
            List of (version, name, applied_at, checksum) tuples
        """
        cursor = self.conn.execute("""
            SELECT version, name, applied_at, checksum
            FROM schema_migrations
            ORDER BY version
        """)
        return cursor.fetchall()

    def _load_migration_modules(self) -> list[MigrationModule]:
        """Load all migration modules from the migrations package.

        Returns:
            List of migration modules sorted by version
        """
        migration_modules: list[MigrationModule] = []

        # Get the migrations package path
        migrations_path = Path(migrations.__file__).parent

        # Import all modules in the migrations package
        for importer, modname, ispkg in pkgutil.iter_modules([str(migrations_path)]):
            if modname.startswith("_"):
                continue

            # Import the module
            module = importlib.import_module(f"pensieve.migrations.{modname}")

            # Verify it has required attributes
            if not all(hasattr(module, attr) for attr in ["VERSION", "NAME", "upgrade", "checksum"]):
                continue

            migration_modules.append(module)  # type: ignore[arg-type]

        # Sort by version
        return sorted(migration_modules, key=lambda m: m.VERSION)

    def get_pending_migrations(self) -> list[MigrationModule]:
        """Get list of pending migrations.

        Returns:
            List of migration modules that haven't been applied
        """
        current_version = self.get_current_version()
        all_migrations = self._load_migration_modules()
        return [m for m in all_migrations if m.VERSION > current_version]

    def verify_migration_integrity(self, migration: MigrationModule) -> bool:
        """Verify migration hasn't been tampered with.

        Args:
            migration: Migration module to verify

        Returns:
            True if migration is valid, False otherwise
        """
        cursor = self.conn.execute(
            "SELECT checksum FROM schema_migrations WHERE version = ?",
            (migration.VERSION,)
        )
        result = cursor.fetchone()

        if result is None:
            # Migration not applied yet, can't verify
            return True

        stored_checksum = result[0]
        current_checksum = migration.checksum()

        return stored_checksum == current_checksum

    def apply_migration(self, migration: MigrationModule) -> None:
        """Apply a single migration.

        Args:
            migration: Migration module to apply

        Raises:
            RuntimeError: If migration fails or checksum mismatch
        """
        # Verify integrity if already applied
        if not self.verify_migration_integrity(migration):
            raise RuntimeError(
                f"Migration {migration.VERSION} checksum mismatch! "
                "Database may be corrupted or migration was modified."
            )

        # Check if already applied
        current_version = self.get_current_version()
        if migration.VERSION <= current_version:
            raise RuntimeError(
                f"Migration {migration.VERSION} already applied (current version: {current_version})"
            )

        try:
            # Apply the migration
            migration.upgrade(self.conn)

            # Record the migration
            self.conn.execute("""
                INSERT INTO schema_migrations (version, name, applied_at, checksum)
                VALUES (?, ?, ?, ?)
            """, (
                migration.VERSION,
                migration.NAME,
                datetime.utcnow().isoformat(),
                migration.checksum()
            ))

            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to apply migration {migration.VERSION}: {e}") from e

    def apply_all_pending(self) -> int:
        """Apply all pending migrations.

        Returns:
            Number of migrations applied

        Raises:
            RuntimeError: If any migration fails
        """
        pending = self.get_pending_migrations()

        for migration in pending:
            self.apply_migration(migration)

        return len(pending)

    def get_status(self) -> dict[str, Any]:
        """Get migration status information.

        Returns:
            Dictionary with current version, applied migrations, and pending migrations
        """
        current_version = self.get_current_version()
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        return {
            "current_version": current_version,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_migrations": [
                {
                    "version": v,
                    "name": n,
                    "applied_at": a,
                    "checksum": c
                }
                for v, n, a, c in applied
            ],
            "pending_migrations": [
                {
                    "version": m.VERSION,
                    "name": m.NAME,
                    "checksum": m.checksum()
                }
                for m in pending
            ]
        }


def create_migration_checksum(content: str) -> str:
    """Create SHA256 checksum for migration content.

    Args:
        content: String content to hash (typically the upgrade function source)

    Returns:
        Hexadecimal SHA256 checksum
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
