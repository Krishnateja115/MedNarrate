"""Add job_executions table

Revision ID: 2b6bb0924215
Revises: 94cd56cc96e0
Create Date: 2026-09-23 21:00:22.897995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b6bb0924215'
down_revision: Union[str, None] = '94cd56cc96e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('job_executions',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('job_name', sa.String(length=100), nullable=False),
    sa.Column('status', sa.Enum('running', 'completed', 'failed', name='jobstatus'), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('duration_seconds', sa.Float(), nullable=True),
    sa.Column('failure_category', sa.String(length=100), nullable=True),
    sa.Column('request_id', sa.String(length=50), nullable=True),
    sa.Column('error_details', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_executions_job_name'), 'job_executions', ['job_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_job_executions_job_name'), table_name='job_executions')
    op.drop_table('job_executions')
