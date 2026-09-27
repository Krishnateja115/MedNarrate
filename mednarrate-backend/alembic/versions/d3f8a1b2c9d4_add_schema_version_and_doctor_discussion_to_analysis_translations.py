"""add_schema_version_and_doctor_discussion_to_analysis_translations

Revision ID: d3f8a1b2c9d4
Revises: f675d1a74b2d
Create Date: 2026-09-27 00:00:00.000000

Adds:
  - analysis_translations.schema_version  (Integer, nullable=False, default=1)
    Old translation rows (pre-structured-doctor-discussion) will read as version 1
    and are automatically treated as stale (cache miss) by the backend that now
    requires version >= TRANSLATION_SCHEMA_VERSION (= 2).
  - analysis_translations.doctor_discussion_points (JSONB / JSON, nullable, default=list)
    Persists the fully-translated doctor discussion bullet-point array so the
    Flutter UI never constructs patient-facing sentences from English templates.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d3f8a1b2c9d4"
# Revises the latest existing migration in the tree
down_revision = "f675d1a74b2d"
branch_labels = None
depends_on = None


def _is_postgres(connection) -> bool:
    dialect_name = connection.dialect.name.lower()
    return dialect_name.startswith("postgres")


def upgrade() -> None:
    bind = op.get_bind()
    if _is_postgres(bind):
        from sqlalchemy.dialects.postgresql import JSONB
        json_type = JSONB()
        json_impl = "JSONB"
    else:
        json_type = sa.JSON()
        json_impl = "JSON"

    # 1. Add schema_version column with default=1 so existing rows immediately
    #    carry the legacy version marker. Use server_default so both new
    #    inserts via migration and the ORM default are aligned.
    with op.batch_alter_table("analysis_translations", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "schema_version",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
                default=1,
            )
        )
        batch_op.add_column(
            sa.Column(
                "doctor_discussion_points",
                json_type,
                nullable=True,
                default=list,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("analysis_translations", schema=None) as batch_op:
        batch_op.drop_column("doctor_discussion_points")
        batch_op.drop_column("schema_version")
