import importlib.util
import sqlite3
from pathlib import Path

import pytest


def _load_repair_module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "repair_local_sqlite_history.py"
    )
    spec = importlib.util.spec_from_file_location("repair_history_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_known_obsolete_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num VARCHAR(32))")
        connection.execute("INSERT INTO alembic_version VALUES ('0d9c40325c4d')")
        connection.execute(
            "CREATE TABLE analysis_translations (clinician_summary TEXT, "
            "doctor_discussion_points JSON, medications_json JSON, schema_version INTEGER)"
        )
        connection.execute(
            "CREATE TABLE users (failed_login_attempts INTEGER, last_totp_counter INTEGER, "
            "locked_until DATETIME, session_version INTEGER)"
        )
        connection.execute("CREATE TABLE admin_audit_logs (actor_subject_id VARCHAR)")


def test_repair_replaces_only_the_known_obsolete_history_marker(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_repair_module()
    database = tmp_path / "mednarrate.db"
    _make_known_obsolete_database(database)
    monkeypatch.setattr(module.settings, "DATABASE_URL", f"sqlite+aiosqlite:///{database}")

    backup = module.repair()

    assert backup.is_file()
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT version_num FROM alembic_version").fetchall() == [
            ("c2a7b4e8f901",)
        ]


def test_repair_refuses_unknown_history(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_repair_module()
    database = tmp_path / "mednarrate.db"
    _make_known_obsolete_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE alembic_version SET version_num = 'unknown'")
    monkeypatch.setattr(module.settings, "DATABASE_URL", f"sqlite+aiosqlite:///{database}")

    with pytest.raises(SystemExit, match="known obsolete revision"):
        module.repair()
