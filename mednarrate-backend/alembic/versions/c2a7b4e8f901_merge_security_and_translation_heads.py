"""Merge security-hardening and clinician-translation histories.

Revision ID: c2a7b4e8f901
Revises: 75dbea6aaf06, 96f33db29794
Create Date: 2026-10-04
"""

from typing import Sequence, Union


revision: str = "c2a7b4e8f901"
down_revision: Union[str, Sequence[str], None] = (
    "75dbea6aaf06",
    "96f33db29794",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Join the two legitimate heads; schema changes live in their revisions."""


def downgrade() -> None:
    """Split the graph back to the two parent heads."""
