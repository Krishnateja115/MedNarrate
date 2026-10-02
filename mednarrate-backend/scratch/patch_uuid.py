import os
import re

def patch(file, replacements):
    with open(file, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(file, 'w') as f:
        f.write(content)

patch("app/api/v1/admin_admins.py", [
    ("SupportTicket.assigned_admin_id == str(admin_uuid)", "SupportTicket.assigned_admin_id == admin_uuid")
])

patch("app/api/v1/support.py", [
    ("ticket_id: str", "ticket_id: uuid.UUID"),
    ("user_id=str(current_user.id)", "user_id=current_user.id"),
    ("sender_id=str(current_user.id)", "sender_id=current_user.id"),
    ("SupportTicket.user_id == str(current_user.id)", "SupportTicket.user_id == current_user.id")
])

with open("app/api/v1/support.py", 'r') as f:
    if "import uuid" not in f.read():
        patch("app/api/v1/support.py", [("from typing import", "import uuid\nfrom typing import")])

patch("app/api/v1/admin_support.py", [
    ("ticket_id: str", "ticket_id: uuid.UUID"),
    ("resource_id=ticket_id", "resource_id=str(ticket_id)"),
    ("resource_id=ticket.id", "resource_id=str(ticket.id)"),
    ("attached_by=admin_ctx.user.id", "attached_by=str(admin_ctx.user.id)"),
    ("sender_id=admin_ctx.user.id", "sender_id=str(admin_ctx.user.id)")
])

patch("tests/test_support_diagnostics.py", [
    ("related_report_id=str(report.id)", "related_report_id=report.id"),
    ("user_id=user.id", "user_id=u.id")
])

print("Patched!")
