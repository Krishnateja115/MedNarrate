"""Add the admin value to the userrole enum.

Revision ID: 110ba6a7df09
Revises: 4b2fbde784e8
Create Date: 2026-10-05 22:22:21.891060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '110ba6a7df09'
down_revision: Union[str, None] = '4b2fbde784e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'admin'")


def downgrade() -> None:
    # PostgreSQL cannot remove an enum value in place.  The value is retained
    # on downgrade so existing admin rows remain readable and safe.
    pass
