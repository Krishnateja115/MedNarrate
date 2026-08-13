"""add report analysis columns

Revision ID: 002_add_report_analysis_columns
Revises: 001_initial
Create Date: 2026-08-08 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002_add_report_analysis_columns'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('report_analyses', sa.Column('structured_lab_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('report_analyses', sa.Column('entities', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('report_analyses', sa.Column('abnormal_findings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('report_analyses', sa.Column('clinician_summary', sa.Text(), nullable=True))
    op.add_column('report_analyses', sa.Column('patient_summary', sa.Text(), nullable=True))
    op.add_column('report_analyses', sa.Column('error_reason', sa.Text(), nullable=True))
    op.add_column('report_analyses', sa.Column('model_versions', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('report_analyses', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('report_analyses', 'processed_at')
    op.drop_column('report_analyses', 'model_versions')
    op.drop_column('report_analyses', 'error_reason')
    op.drop_column('report_analyses', 'patient_summary')
    op.drop_column('report_analyses', 'clinician_summary')
    op.drop_column('report_analyses', 'abnormal_findings')
    op.drop_column('report_analyses', 'entities')
    op.drop_column('report_analyses', 'structured_lab_values')
