"""Repair one known obsolete local Alembic marker without touching user data.

The removed ``0d9c40325c4d`` migration was an accidental SQLite autogenerate
revision. It changed table types unrelated to clinician summaries, then its
file was correctly removed. A database that already applied it cannot be
upgraded until its marker is reconciled with the clean merge revision.

This script is intentionally narrow: it only handles that marker, validates
the affected schema first, creates a backup, and updates only the Alembic
history row. It refuses all other databases or revision states.
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import settings

OBSOLETE_REVISION = "0d9c40325c4d"
CLEAN_MERGE_REVISION = "c2a7b4e8f901"
REQUIRED_COLUMNS = {
    "analysis_translations": {
        "clinician_summary",
        "doctor_discussion_points",
        "medications_json",
        "schema_version",
    },
    "users": {
        "failed_login_attempts",
        "last_totp_counter",
        "locked_until",
        "session_version",
    },
    "admin_audit_logs": {"actor_subject_id"},
}


def _sqlite_database_path(database_url: str) -> Path:
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        raise SystemExit("This repair supports only a local sqlite+aiosqlite database.")
    path = Path(database_url.removeprefix(prefix)).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def _validate_schema(connection: sqlite3.Connection) -> None:
    for table, required_columns in REQUIRED_COLUMNS.items():
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
        actual_columns = {row[1] for row in rows}
        missing = required_columns - actual_columns
        if missing:
            missing_names = ", ".join(sorted(missing))
            raise SystemExit(
                f"Refusing repair: {table} is missing expected columns: {missing_names}."
            )


def repair() -> Path:
    database_path = _sqlite_database_path(settings.DATABASE_URL)
    if not database_path.is_file():
        raise SystemExit(f"Local database not found: {database_path}")

    backup_path = database_path.with_suffix(database_path.suffix + ".pre-history-repair.bak")
    if backup_path.exists():
        raise SystemExit(
            f"Backup already exists: {backup_path}. Review it before retrying."
        )

    with sqlite3.connect(database_path) as connection:
        version_rows = connection.execute("SELECT version_num FROM alembic_version").fetchall()
        if version_rows != [(OBSOLETE_REVISION,)]:
            raise SystemExit(
                "Refusing repair: this database is not at the known obsolete revision."
            )
        _validate_schema(connection)
        shutil.copy2(database_path, backup_path)
        connection.execute(
            "UPDATE alembic_version SET version_num = ?", (CLEAN_MERGE_REVISION,)
        )
        connection.commit()

    return backup_path


if __name__ == "__main__":
    backup = repair()
    print(
        "Local migration history repaired without deleting data. "
        f"Backup created at: {backup}"
    )
