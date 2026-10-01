"""Encrypt legacy AI API keys

Revision ID: 9858814da870
Revises: 4a8cb92e5f1d
Create Date: 2026-10-01 19:09:36.543899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9858814da870'
down_revision: Union[str, None] = '4a8cb92e5f1d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from app.core.encryption import encrypt_value, get_fernet

def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "system_settings" not in inspector.get_table_names():
        return
    res = conn.execute(sa.text("SELECT id, value FROM system_settings WHERE key = 'ai_api_key'"))
    for row in res:
        id, value = row
        if not value:
            continue
        try:
            # check if it's already encrypted
            f = get_fernet()
            f.decrypt(value.encode())
        except Exception:
            # It's not encrypted, so encrypt it
            encrypted = encrypt_value(value)
            conn.execute(sa.text("UPDATE system_settings SET value = :val WHERE id = :id"), {"val": encrypted, "id": id})


def downgrade() -> None:
    pass
