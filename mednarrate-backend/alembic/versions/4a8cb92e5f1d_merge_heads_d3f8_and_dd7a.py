"""merge_heads_d3f8_and_dd7a — unify the two divergent migration branches.

Revision ID: 4a8cb92e5f1d
Revises: ("d3f8a1b2c9d4", "dd7a0d153610")
Create Date: 2026-09-27 22:52:00.000000

This is a structural merge only. No schema changes here — both existing heads
are responsible for their own ALTERs:

  - d3f8a1b2c9d4 adds analysis_translations.schema_version (NOT NULL, default 1)
                     and analysis_translations.doctor_discussion_points (JSON)
  - dd7a0d153610 adds analysis_translations.medications_json (JSON)
                   and tightens analysis_translations.ui_labels NOT NULL

After this merge:
  - alembic heads reports exactly ONE head: 4a8cb92e5f1d
  - alembic upgrade head will walk both legs:
      dd7a0d153610 (already in DB) and d3f8a1b2c9d4 (NOT yet applied)
      → only d3f8a1b2c9d4's ALTERs actually run against the current DB.
"""
from alembic import op
import sqlalchemy as sa


revision = "4a8cb92e5f1d"
down_revision = ("d3f8a1b2c9d4", "dd7a0d153610")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Pure merge: no schema operations. Both parents are preserved and responsible
    # for their own ALTERs. For a DB currently at dd7a0d153610, Alembic will
    # independently apply d3f8a1b2c9d4 (since it's a parent of the merge and not
    # yet recorded in alembic_version) before landing at 4a8cb92e5f1d.
    pass


def downgrade() -> None:
    # Pure merge: no schema operations.
    pass
