# Technical Decisions Log

## Phase 4: Auth & Security Cookie Migration
- **CORS Credentials Configuration**: When migrating to `HttpOnly` cookies, CORS needs `allow_credentials=True`. This necessitates removing wildcard `"*"` origins. I defaulted the admin origin to `ADMIN_APP_ORIGIN` (falling back to `http://localhost:3001` or `http://localhost:3000`), allowing secure cookie exchange without breaking existing setups.
- **FastAPI Auth Header/Cookie Precedence**: Because the mobile application relies on Bearer headers for authorization while the admin app utilizes cookies, I updated `OAuth2PasswordBearer` to gracefully support *both*. I prioritize `Authorization` headers over cookies to prevent test suite failures where test clients persist cookies across isolated assertions.
- **Refresh/Logout Fallback**: `refresh_token` extraction initially prioritizes explicit JSON bodies if sent (`refresh_req.refresh_token`) before falling back to reading from the secure cookie. This provides seamless backwards compatibility for existing mobile clients.
- **Frontend Token Storage**: Stripped out `sessionStorage` tracking within `AuthContext.tsx`. The initial authentication state now completely relies on the backend via the `/api/v1/auth/me` endpoint during load, ensuring absolute protection against token theft through XSS.
- **Sidebar Assumptions**: The `src/components/layout/sidebar.tsx` already appeared to have `hasAnyPermission` logic attached; I confirmed it operates securely by filtering off the `AuthContext`'s user permissions which are safely dictated by the `/me` endpoint. All unknown or unmapped permission structures default safely to checking for highest-tier (super admin) visibility underneath the hood via `hasAnyPermission`.

## Break-Glass Access Model
- **Approver Role Assumption**: The permission `approve_sensitive_access` is required to approve break-glass access grants. If not present on any role, it was automatically added to the highest-privilege "super admin"-equivalent role in the test environments.
- **Default Expiry**: The default break-glass access expiry duration is enforced as a hardcoded 4 hours from the time of approval, non-renewable. This ensures temporal isolation.
- **Atomic Auditing**: The `log_admin_action` method strictly relies on the caller (`admin_breakglass.py`) to commit the database session to ensure both the action state change and the audit log entry succeed or fail atomically.
- **Expiry Model**: The `expires_at` column in `SensitiveAccessGrant` is now nullable to accurately represent that a requested grant does not have an expiry until it is actually approved.
