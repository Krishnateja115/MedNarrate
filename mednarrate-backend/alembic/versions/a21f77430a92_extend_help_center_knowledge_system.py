"""extend help center knowledge system

Revision ID: a21f77430a92
Revises: 715e4f09cea7
Create Date: 2026-09-26 12:57:02.936936

"""

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a21f77430a92"
down_revision: Union[str, None] = "715e4f09cea7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # `init_db()` is intentionally useful for a fresh local development
    # database and can create model tables before Alembic has recorded this
    # revision. Make the upgrade safe for that supported bootstrap path.
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    article_columns = {
        column["name"] for column in inspector.get_columns("help_articles")
    }
    if "summary" not in article_columns or "published_at" not in article_columns:
        with op.batch_alter_table("help_articles", schema=None) as batch_op:
            if "summary" not in article_columns:
                batch_op.add_column(
                    sa.Column("summary", sa.Text(), server_default="", nullable=False)
                )
            if "published_at" not in article_columns:
                batch_op.add_column(
                    sa.Column("published_at", sa.DateTime(), nullable=True)
                )

    table_names = set(sa.inspect(connection).get_table_names())
    if "help_article_versions" not in table_names:
        op.create_table(
            "help_article_versions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("article_id", sa.String(length=36), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("slug", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=9), nullable=False),
            sa.Column("created_by", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"], ["help_articles.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "article_id", "version", name="uq_help_article_version"
            ),
        )
    if "support_ticket_help_articles" not in table_names:
        op.create_table(
            "support_ticket_help_articles",
            sa.Column("ticket_id", sa.String(length=36), nullable=False),
            sa.Column("article_id", sa.String(length=36), nullable=False),
            sa.Column("attached_by", sa.String(length=36), nullable=False),
            sa.Column("attached_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(
                ["article_id"], ["help_articles.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["ticket_id"], ["support_tickets.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("ticket_id", "article_id"),
        )
    permissions = (
        (
            "20000000-0000-0000-0000-000000000001",
            "support.view",
            "View support tickets and grounded article suggestions",
        ),
        (
            "20000000-0000-0000-0000-000000000002",
            "support.escalate",
            "Escalate support tickets to incidents",
        ),
        (
            "20000000-0000-0000-0000-000000000003",
            "help_center.view",
            "View and preview Help Center articles",
        ),
        (
            "20000000-0000-0000-0000-000000000004",
            "help_center.manage",
            "Create, publish, archive, and edit Help Center articles",
        ),
    )
    for permission_id, name, description in permissions:
        exists = connection.execute(
            sa.text("SELECT 1 FROM admin_permissions WHERE name = :name"),
            {"name": name},
        ).first()
        if not exists:
            connection.execute(
                sa.text(
                    "INSERT INTO admin_permissions "
                    "(id, name, description, created_at) "
                    "VALUES (:id, :name, :description, :created_at)"
                ),
                {
                    "id": permission_id,
                    "name": name,
                    "description": description,
                    "created_at": "2026-09-26 00:00:00",
                },
            )

    article_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM help_articles")
    ).scalar_one()
    if article_count == 0:
        help_articles = sa.table(
            "help_articles",
            sa.column("id", sa.String),
            sa.column("title", sa.String),
            sa.column("slug", sa.String),
            sa.column("category", sa.String),
            sa.column("summary", sa.Text),
            sa.column("content", sa.Text),
            sa.column("status", sa.String),
            sa.column("created_by", sa.String),
            sa.column("created_at", sa.DateTime),
            sa.column("updated_at", sa.DateTime),
            sa.column("published_at", sa.DateTime),
        )
        published_at = datetime(2026, 9, 26)
        op.bulk_insert(
            help_articles,
            [
                {
                    "id": "10000000-0000-0000-0000-000000000001",
                    "title": "Why is my report still processing?",
                    "slug": "why-is-my-report-still-processing",
                    "category": "Reports",
                    "summary": "What the processing state means and what to include when asking support for help.",
                    "content": "MedNarrate processes an uploaded report before its analysis is available. Keep the report ID shown in the app and refresh after a short wait. If processing does not finish, open a support ticket with the report ID. Do not paste private medical text into the ticket.",
                    "status": "published",
                    "created_by": "system",
                    "created_at": published_at,
                    "updated_at": published_at,
                    "published_at": published_at,
                },
                {
                    "id": "10000000-0000-0000-0000-000000000002",
                    "title": "Understanding a MedNarrate report analysis",
                    "slug": "understanding-report-analysis",
                    "category": "Report Analysis",
                    "summary": "How to review extracted findings without treating them as a diagnosis.",
                    "content": "MedNarrate can extract text and generate plain-language summaries from supported reports. Check important values against the original report. The analysis does not replace the source report or advice from a qualified clinician.",
                    "status": "published",
                    "created_by": "system",
                    "created_at": published_at,
                    "updated_at": published_at,
                    "published_at": published_at,
                },
                {
                    "id": "10000000-0000-0000-0000-000000000003",
                    "title": "Using AI chat with your report",
                    "slug": "using-ai-chat-with-your-report",
                    "category": "AI/Chat",
                    "summary": "How to ask focused questions and check AI-generated answers.",
                    "content": "Ask focused questions about information available in your MedNarrate report. AI responses can be incomplete or incorrect, so verify important details against the original report and consult a clinician before making medical decisions.",
                    "status": "published",
                    "created_by": "system",
                    "created_at": published_at,
                    "updated_at": published_at,
                    "published_at": published_at,
                },
                {
                    "id": "10000000-0000-0000-0000-000000000004",
                    "title": "Managing medication reminders",
                    "slug": "managing-medication-reminders",
                    "category": "Medication Reminders",
                    "summary": "Check schedules and notification settings when a reminder is missing.",
                    "content": "Medication reminders use schedules saved in MedNarrate and notification settings on your device. Confirm that the schedule and active state are correct, then check app and device notification permissions.",
                    "status": "published",
                    "created_by": "system",
                    "created_at": published_at,
                    "updated_at": published_at,
                    "published_at": published_at,
                },
                {
                    "id": "10000000-0000-0000-0000-000000000005",
                    "title": "Protecting privacy when contacting support",
                    "slug": "protecting-privacy-when-contacting-support",
                    "category": "Privacy",
                    "summary": "Share useful identifiers without including unnecessary medical details.",
                    "content": "Share the report ID, ticket ID, or request ID shown by MedNarrate. Avoid copying full report text, passwords, access tokens, or sensitive medical information into a support ticket.",
                    "status": "published",
                    "created_by": "system",
                    "created_at": published_at,
                    "updated_at": published_at,
                    "published_at": published_at,
                },
            ],
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "DELETE FROM help_articles WHERE id IN ("
            "'10000000-0000-0000-0000-000000000001',"
            "'10000000-0000-0000-0000-000000000002',"
            "'10000000-0000-0000-0000-000000000003',"
            "'10000000-0000-0000-0000-000000000004',"
            "'10000000-0000-0000-0000-000000000005')"
        )
    )
    connection.execute(
        sa.text(
            "DELETE FROM admin_permissions WHERE id IN ("
            "'20000000-0000-0000-0000-000000000001',"
            "'20000000-0000-0000-0000-000000000002',"
            "'20000000-0000-0000-0000-000000000003',"
            "'20000000-0000-0000-0000-000000000004')"
        )
    )
    op.drop_table("support_ticket_help_articles")
    op.drop_table("help_article_versions")
    with op.batch_alter_table("help_articles", schema=None) as batch_op:
        batch_op.drop_column("published_at")
        batch_op.drop_column("summary")
