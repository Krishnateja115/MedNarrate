"""Add requested duration hours to break glass

Revision ID: cebe80380c15
Revises: 7b7135d1f49f
Create Date: 2026-10-02 09:58:28.679326

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'cebe80380c15'
down_revision: Union[str, None] = '7b7135d1f49f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('sensitive_access_grants', schema=None) as batch_op:
        batch_op.add_column(sa.Column('requested_duration_hours', sa.Integer(), nullable=True))
    with op.batch_alter_table('admin_audit_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('actor_subject_id', sa.String(), nullable=True))
        batch_op.create_index(batch_op.f('ix_admin_audit_logs_actor_subject_id'), ['actor_subject_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('admin_audit_logs', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_admin_audit_logs_actor_subject_id'))
        batch_op.drop_column('actor_subject_id')
    with op.batch_alter_table('sensitive_access_grants', schema=None) as batch_op:
        batch_op.drop_column('requested_duration_hours')
