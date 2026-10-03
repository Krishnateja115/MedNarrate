"""Add OrphanFile model

Revision ID: ce57d53d74af
Revises: cebe80380c15
Create Date: 2026-10-02 17:05:46.375916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce57d53d74af'
down_revision: Union[str, None] = 'cebe80380c15'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('orphan_files',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('file_path', sa.String(length=512), nullable=False),
    sa.Column('storage_backend', sa.String(length=50), nullable=False, server_default='local'),
    sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
    sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('last_error_code', sa.String(length=50), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('last_attempt_at', sa.DateTime(), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('orphan_files', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_orphan_files_file_path'), ['file_path'], unique=False)
        batch_op.create_index(batch_op.f('ix_orphan_files_status'), ['status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('orphan_files', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_orphan_files_status'))
        batch_op.drop_index(batch_op.f('ix_orphan_files_file_path'))
    op.drop_table('orphan_files')
