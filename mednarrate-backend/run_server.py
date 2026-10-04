import os
from pathlib import Path

import uvicorn


def _upgrade_development_database() -> None:
    """Apply the checked-in migration history before a local server starts.

    Development users run the desktop app and the admin portal against the
    same local database. Updating it here prevents an application update from
    leaving login code ahead of the database schema. Production deployments
    retain their explicit migration step.
    """
    if os.environ.get("ENVIRONMENT", "development").lower() != "development":
        return

    from alembic import command
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parent
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("prepend_sys_path", str(backend_root))
    command.upgrade(config, "head")


if __name__ == "__main__":
    # The desktop development build identifies itself as 1.0.0/dev. Keep the
    # local server launched by this supported entry point aligned with it so a
    # normal restart is never mistaken for an unrelated stale service.
    if os.environ.get("ENVIRONMENT", "development").lower() == "development":
        os.environ.setdefault("MEDNARRATE_VERSION", "1.0.0")
        os.environ.setdefault("MEDNARRATE_COMMIT", "dev")
    _upgrade_development_database()
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("app.main:app", host=host, port=8000, log_level="info")
