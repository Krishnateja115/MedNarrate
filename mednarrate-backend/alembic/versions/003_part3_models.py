"""part3 models

Revision ID: 003_part3_models
Revises: 002_add_report_analysis_columns
Create Date: 2026-08-08 12:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector

revision: str = '003_part3_models'
down_revision: Union[str, None] = '002_add_report_analysis_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create knowledge_chunks
    op.create_table('knowledge_chunks',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('source', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('content_hash', sa.String(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.Vector(dim=768), nullable=False),
    sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_knowledge_chunks_content_hash'), 'knowledge_chunks', ['content_hash'], unique=True)
    
    # Create analysis_translations
    op.create_table('analysis_translations',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('report_analysis_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('language', sa.String(), nullable=False),
    sa.Column('patient_summary', sa.Text(), nullable=False),
    sa.Column('findings_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['report_analysis_id'], ['report_analyses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('report_analysis_id', 'language', name='_report_lang_uc')
    )

def downgrade() -> None:
    op.drop_table('analysis_translations')
    op.drop_index(op.f('ix_knowledge_chunks_content_hash'), table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
