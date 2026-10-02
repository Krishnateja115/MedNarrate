import os
import re

def patch(file, replacements):
    with open(file, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(file, 'w') as f:
        f.write(content)

patch("app/api/v1/admin_support.py", [
    ("db.get(SupportTicket, uuid.UUID(ticket_id))", "db.get(SupportTicket, ticket_id)"),
    ("SupportTicket.id == uuid.UUID(ticket_id)", "SupportTicket.id == ticket_id")
])

patch("app/api/v1/support.py", [
    ("db.get(SupportTicket, uuid.UUID(ticket_id))", "db.get(SupportTicket, ticket_id)"),
    ("SupportTicket.id == uuid.UUID(ticket_id)", "SupportTicket.id == ticket_id")
])

patch("tests/test_support_diagnostics.py", [
    ("from app.services.support_diagnostics import build_diagnostic_snapshot", "from app.services.support_diagnostics import build_diagnostic_snapshot\nfrom app.models.user import User, UserRole")
])

print("Patched!")
