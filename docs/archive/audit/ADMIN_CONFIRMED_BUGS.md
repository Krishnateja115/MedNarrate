# Admin Confirmed Bugs

## P0 Bugs
1. **Admin Notification Enum Crash**: Dispatching notifications to audiences "doctors", "patients", "caregivers" crashes the backend because `admin_notifications.py` uses `UserRole.DOCTOR` which is invalid (the enum uses lower-case members like `UserRole.clinician`).
2. **Feature Flag Update Bug**: `update_feature_flag` in `admin_feature_flags.py` raises `ValueError` when passing a name (e.g. `enable_ocr`) to `uuid.UUID`, making name lookup completely unreachable.

## P1 Bugs
1. **Fake Notification Dispatch**: Admin notification dispatch simulates success without actually calling a push notification service (FCM/APNS). Retry also just flips the DB status.
2. **Admin Creation without Roles**: Creating a new Admin from the UI sends `role_ids: []`. The newly created Admin is effectively unusable until roles are manually assigned.

## P2 Bugs
1. **ESLint Disable Abuse**: Almost every file in `mednarrate-admin/src` begins with `/* eslint-disable */`, masking potential frontend issues.
