"""Database migrations for Pensieve."""

# This package contains all database migrations.
# Each migration file should define:
# - VERSION: int - the migration version number
# - NAME: str - human-readable migration name
# - upgrade(conn: sqlite3.Connection) -> None - applies the migration
# - checksum() -> str - returns SHA256 checksum for integrity verification
