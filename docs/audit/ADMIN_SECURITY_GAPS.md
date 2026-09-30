# Admin Security Gaps

1. **Admin Creation Misconfiguration**: New admins receive zero roles upon creation, which is safe, but functionally broken.
2. **Tauri CSP**: The Tauri desktop app has default configuration, but it's a dead starter app.
3. **Prompt Injection Middleware**: (Needs deeper analysis, but likely keyword-based matching is too broad).
