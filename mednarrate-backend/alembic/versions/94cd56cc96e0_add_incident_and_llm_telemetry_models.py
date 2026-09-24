"""Add incident and llm telemetry models

Revision ID: 94cd56cc96e0
Revises: c4d42f6faff6
Create Date: 2026-09-23 20:37:29.801729

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "94cd56cc96e0"
down_revision: Union[str, None] = "c4d42f6faff6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "incidents",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column(
            "severity",
            sa.Enum("sev1", "sev2", "sev3", "sev4", name="incidentseverity"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "open",
                "investigating",
                "identified",
                "resolved",
                "closed",
                name="incidentstatus",
            ),
            nullable=False,
        ),
        sa.Column("affected_service", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_to_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "incident_events",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_incident_events_incident_id"),
        "incident_events",
        ["incident_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_incident_events_timestamp"),
        "incident_events",
        ["timestamp"],
        unique=False,
    )

    op.create_table(
        "llm_diagnostic_events",
        sa.Column("id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model_name", sa.String(), nullable=True),
        sa.Column("feature", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("error_category", sa.String(), nullable=True),
        sa.Column("fallback_used", sa.Boolean(), nullable=False),
        sa.Column(
            "timestamp", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_llm_diagnostic_events_provider"),
        "llm_diagnostic_events",
        ["provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_llm_diagnostic_events_request_id"),
        "llm_diagnostic_events",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_llm_diagnostic_events_timestamp"),
        "llm_diagnostic_events",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("llm_diagnostic_events")
    op.drop_table("incident_events")
    op.drop_table("incidents")
