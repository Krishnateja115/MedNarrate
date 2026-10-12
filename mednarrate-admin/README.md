# MedNarrate Admin Portal

The admin portal is a Next.js application for MedNarrate staff. It uses
HTTP-only session cookies and the FastAPI admin endpoints.

## Development

Run `npm ci`, then `npm run dev`. The default development API proxy points to
`http://127.0.0.1:8000`; set `MEDNARRATE_API_PROXY_URL` if the API runs
elsewhere. Open `http://localhost:3001`.

## Production web deployment

Set `MEDNARRATE_API_PROXY_URL` to the internal HTTPS API origin before running
`npm run build` and `npm run start`. The build fails if it is missing. The browser uses the same-origin `/api/v1`
proxy, so secure cookies stay first-party. Configure the backend's
`ADMIN_APP_ORIGIN` and `CORS_ORIGINS` for the deployed portal origin.

## Desktop package

The Tauri wrapper in `../mednarrate-admin-desktop` exports this portal as
static assets. Its build requires `NEXT_PUBLIC_API_BASE_URL` to be the public
HTTPS API origin.

## Checks

Run `npm run lint`, `npm run typecheck`, `npm test -- --ci`, and
`npm run build` before release.
