# MedNarrate Admin — Testing Matrix & Quality Assurance

## Test Suite Execution

### Backend Test Matrix
Run full backend pytest suite including RBAC, Governance, Analytics, Search, and Alerts:
```bash
cd mednarrate-backend
python -m pytest tests/test_security_governance.py tests/test_admin_rbac.py tests/test_final_release_matrix.py -v
```

### Frontend Build Matrix
Verify production build compilation in Next.js:
```bash
cd mednarrate-admin
npm run build
```

## Security & End-to-End Verification Coverage
1. **Admin Authentication & Token Expiry**
2. **Unauthorized User Access Blocked (HTTP 401/403)**
3. **Role-Based Privilege Boundaries (Support vs SuperAdmin)**
4. **Global Search Resource Resolution**
5. **Real-time Alert Center & Acknowledgment**
6. **Analytics Database Query Aggregations**
7. **PHI / PII Sanitization in Telemetry & Audit Logs**
