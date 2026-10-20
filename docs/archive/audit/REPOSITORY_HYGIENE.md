# Repository Hygiene

1. **Committed Virtual Environment**: `.backend-venv/` is fully tracked in Git (488 files, 7.3MB). It should be removed and added to `.gitignore`.
2. **Dead Desktop App**: `mednarrate-admin-desktop/` is a completely unmodified Tauri starter app.
3. **Global Lint Disabling**: The `fix_tsx.py` script and the extensive use of `/* eslint-disable */` is poor hygiene.
4. **TODO Placeholders in Prod Config**: Flutter `AppConfig` uses `https://api.mednarrate.com` with a TODO comment to replace with a real deployed backend URL.
