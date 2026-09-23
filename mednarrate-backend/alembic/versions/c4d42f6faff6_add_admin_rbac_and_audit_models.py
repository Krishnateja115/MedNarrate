"""Add admin RBAC and audit models

Revision ID: c4d42f6faff6
Revises: 7cbdc4385fff
Create Date: 2026-09-23 20:31:18.892835

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4d42f6faff6'
down_revision: Union[str, None] = '7cbdc4385fff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('admin_roles',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_roles_name'), 'admin_roles', ['name'], unique=True)

    op.create_table('admin_permissions',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_permissions_name'), 'admin_permissions', ['name'], unique=True)

    op.create_table('admin_role_permissions',
        sa.Column('role_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('permission_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['admin_permissions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['admin_roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    op.create_table('admin_role_assignments',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('assigned_by_id', sa.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['role_id'], ['admin_roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_role_assignments_role_id'), 'admin_role_assignments', ['role_id'], unique=False)
    op.create_index(op.f('ix_admin_role_assignments_user_id'), 'admin_role_assignments', ['user_id'], unique=False)

    op.create_table('admin_audit_logs',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('actor_admin_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('permission_used', sa.String(), nullable=True),
        sa.Column('result', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('metadata_payload', sa.JSON().with_variant(postgresql.JSONB, 'postgresql'), nullable=False),
        sa.Column('sensitive_access_flag', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['actor_admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_audit_logs_action'), 'admin_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_admin_audit_logs_actor_admin_id'), 'admin_audit_logs', ['actor_admin_id'], unique=False)
    op.create_index(op.f('ix_admin_audit_logs_timestamp'), 'admin_audit_logs', ['timestamp'], unique=False)

    op.create_table('sensitive_access_grants',
        sa.Column('id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('admin_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('approved_by_id', sa.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sensitive_access_grants_admin_id'), 'sensitive_access_grants', ['admin_id'], unique=False)


def downgrade() -> None:
    op.drop_table('sensitive_access_grants')
    op.drop_table('admin_audit_logs')
    op.drop_table('admin_role_assignments')
    op.drop_table('admin_role_permissions')
    op.drop_table('admin_permissions')
    op.drop_table('admin_roles')
