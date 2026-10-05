"""Add admin settings tables missing from the original migration history."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4b2fbde784e8"
down_revision: Union[str, None] = "c2a7b4e8f901"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def _has_index(table: str, index: str) -> bool:
    if not _has_table(table):
        return False
    indexes = sa.inspect(op.get_bind()).get_indexes(table)
    return any(item["name"] == index for item in indexes)


def _create_table(name: str, *args, **kwargs) -> None:
    # Tolerate databases whose tables were already created outside Alembic.
    if not _has_table(name):
        op.create_table(name, *args, **kwargs)


def _create_index(name: str, table: str, columns: list[str], **kwargs) -> None:
    if not _has_index(table, name):
        op.create_index(name, table, columns, **kwargs)


def upgrade() -> None:
    _create_table(
        "announcements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("audience", sa.String(), nullable=False),
        sa.Column("language", sa.String(), nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index("ix_announcements_status", "announcements", ["status"])

    _create_table(
        "feature_flags",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("rollout_percentage", sa.Integer(), nullable=False),
        sa.Column("target_environment", sa.String(), nullable=False),
        sa.Column("target_segment", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index("ix_feature_flags_name", "feature_flags", ["name"], unique=True)

    _create_table(
        "maintenance_mode",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("enabled_by_id", sa.Uuid(), nullable=True),
        sa.Column("enabled_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["enabled_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    _create_table(
        "privacy_data_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("request_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_by_id", sa.Uuid(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index("ix_privacy_data_requests_status", "privacy_data_requests", ["status"])
    _create_index("ix_privacy_data_requests_user_id", "privacy_data_requests", ["user_id"])

    _create_table(
        "system_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("is_sensitive", sa.Boolean(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_index("ix_system_settings_key", "system_settings", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_system_settings_key", table_name="system_settings")
    op.drop_table("system_settings")
    op.drop_index("ix_privacy_data_requests_user_id", table_name="privacy_data_requests")
    op.drop_index("ix_privacy_data_requests_status", table_name="privacy_data_requests")
    op.drop_table("privacy_data_requests")
    op.drop_table("maintenance_mode")
    op.drop_index("ix_feature_flags_name", table_name="feature_flags")
    op.drop_table("feature_flags")
    op.drop_index("ix_announcements_status", table_name="announcements")
    op.drop_table("announcements")
