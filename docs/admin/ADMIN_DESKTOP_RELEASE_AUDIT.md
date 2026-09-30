# MedNarrate Admin Desktop - Release Audit

## 1. Dead Template Code Removal
- Removed the unused `src` directory containing the default Tauri `index.html`, `main.js`, `styles.css`, and sample assets.
- Removed the sample `greet` Rust command and its `invoke_handler` from `src-tauri/src/lib.rs`.
- The desktop app now correctly points to the Next.js static output in `../../mednarrate-admin/out` for its frontend bundle.

## 2. Tauri Security & CSP
- Modified `tauri.conf.json` to replace `"csp": null` with a strict Content Security Policy.
- **Remote Content**: `default-src 'none'`, `object-src 'none'`, and `frame-src 'none'` block arbitrary plugin and frame loading.
- **Script Sources**: Restricted to `'self'` along with localhost endpoints for development hot-reloading (`unsafe-inline` and `unsafe-eval` retained for Next.js and React execution requirements).
- **Connect Sources**: Explicitly limited to `https://api.mednarrate.com` and `http://localhost:*`.
- **Window Creation & Navigation**: Restricted by Tauri v2 capabilities (default capabilities do not include `window:create` or unrestricted webview navigation, preventing rogue new windows or redirects).

## 3. Desktop Behavior
- **App Branding & Icons**: Re-generated the complete Tauri icon set (macOS, Windows, iOS, Android) using the official `mednarrate-logo.png` via `tauri icon`. 
- **Window Sizing**: Set to a standard desktop configuration of 1440x900, resizable, non-fullscreen.
- **Login Cookies / Session**: Validated that `tauri://localhost` and `http://tauri.localhost` origins are allowlisted in the MedNarrate backend CORS settings. `credentials: "include"` allows HTTP-only cookies to safely persist in the desktop webview, maintaining session parity with the web version.
- **Logout**: Handled natively by the `/auth/logout` API which successfully clears the webview session cookies.
- **External Link Opening**: Initialized `tauri_plugin_opener` and granted the `opener:default` capability in `capabilities/default.json` so external links safely trigger the system default browser rather than navigating the desktop webview itself.
- **Deep Links**: None currently configured or required for the Admin portal (no custom protocol schemes registered).

## 4. Build Configuration
- Updated the `next.config.ts` in the Admin web project to conditionally set `output: 'export'` when `TAURI_ENV` is present.
- Configured the Tauri `beforeBuildCommand` to execute `cd ../mednarrate-admin && TAURI_ENV=true NEXT_PUBLIC_API_BASE_URL=https://api.mednarrate.com npm run build`.
- This ensures Tauri triggers a proper static export from Next.js and points the API to the correct production domain.
- Verified successful test builds for macOS (`npm run build:desktop:mac`). Windows configuration relies on the standard `x86_64-pc-windows-msvc` target command in `package.json`.
