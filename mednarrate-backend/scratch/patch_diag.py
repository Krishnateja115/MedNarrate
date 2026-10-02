import re
with open("tests/test_support_diagnostics.py", "r") as f:
    c = f.read()

c = c.replace("user_id = uuid.uuid4()", """
    u = User(
        email="diag@test.com",
        password_hash="...",
        role=UserRole.user,
        is_active=True
    )
    db_session.add(u)
    await db_session.commit()
    user_id = u.id
""")
c = c.replace("user_id=user.id", "user_id=user_id")

with open("tests/test_support_diagnostics.py", "w") as f:
    f.write(c)
