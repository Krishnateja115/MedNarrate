"""initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-08 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    op.create_table('users',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('role', sa.Enum('patient', 'clinician', name='userrole'), nullable=False),
    sa.Column('preferred_language', sa.String(), nullable=False),
    sa.Column('date_of_birth', sa.String(), nullable=True),
    sa.Column('gender', sa.String(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    op.create_table('medical_profiles',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('blood_group', sa.String(), nullable=True),
    sa.Column('known_allergies', sa.Text(), nullable=True),
    sa.Column('chronic_conditions', sa.Text(), nullable=True),
    sa.Column('emergency_contact_name', sa.String(), nullable=True),
    sa.Column('emergency_contact_phone', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id')
    )
    
    op.create_table('refresh_tokens',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('token_hash', sa.String(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=False)
    
    op.create_table('reports',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('hospital', sa.String(), nullable=True),
    sa.Column('report_date', sa.Date(), nullable=False),
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('file_path', sa.String(), nullable=False),
    sa.Column('file_type', sa.Enum('pdf', 'image', name='filetype'), nullable=False),
    sa.Column('report_type', sa.Enum('blood', 'pathology', 'health', 'other', name='reporttype'), nullable=False),
    sa.Column('extracted_text', sa.Text(), nullable=True),
    sa.Column('processing_status', sa.Enum('uploaded', 'processing', 'completed', 'failed', name='processingstatus'), nullable=False),
    sa.Column('is_favourite', sa.Boolean(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'], unique=False)
    
    op.create_table('report_analyses',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('report_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('report_id')
    )
    
    op.create_table('chat_sessions',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('report_id', sa.UUID(as_uuid=True), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('chat_messages',
    sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('chat_session_id', sa.UUID(as_uuid=True), nullable=False),
    sa.Column('role', sa.Enum('user', 'assistant', name='chatrole'), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['chat_session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('report_analyses')
    op.drop_index(op.f('ix_reports_user_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_table('medical_profiles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    sa.Enum(name='chatrole').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='processingstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='reporttype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='filetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
