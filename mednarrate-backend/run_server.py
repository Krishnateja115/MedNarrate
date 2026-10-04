import os

import uvicorn

if __name__ == "__main__":
    # The desktop development build identifies itself as 1.0.0/dev. Keep the
    # local server launched by this supported entry point aligned with it so a
    # normal restart is never mistaken for an unrelated stale service.
    if os.environ.get("ENVIRONMENT", "development").lower() == "development":
        os.environ.setdefault("MEDNARRATE_VERSION", "1.0.0")
        os.environ.setdefault("MEDNARRATE_COMMIT", "dev")
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run("app.main:app", host=host, port=8000, log_level="info")
