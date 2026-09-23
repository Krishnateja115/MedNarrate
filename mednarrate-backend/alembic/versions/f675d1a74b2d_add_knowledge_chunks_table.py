"""Add knowledge_chunks table

Revision ID: f675d1a74b2d
Revises: 003_part3_models
Create Date: 2026-08-12 19:30:39.777004

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'f675d1a74b2d'
down_revision: Union[str, None] = '003_part3_models'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
