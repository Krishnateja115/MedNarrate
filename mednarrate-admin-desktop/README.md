# MedNarrate Admin Desktop

This Tauri wrapper packages the static admin portal. Install dependencies in
`mednarrate-admin` and this directory before building.

Set `NEXT_PUBLIC_API_BASE_URL` to the public HTTPS origin of the deployed
MedNarrate API, then run `npm run build:desktop:mac` or
`npm run build:desktop:win`. The build rejects a missing or non-HTTPS origin.
The API must allow the Tauri origins in its CORS configuration and serve over
HTTPS. Sign and notarize distribution packages before release.

See the root `DESKTOP_BUILD.md` for platform prerequisites and signing steps.
