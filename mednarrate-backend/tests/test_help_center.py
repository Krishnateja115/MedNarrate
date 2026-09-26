import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.admin import (
    AdminPermission,
    AdminRole,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.help_center import ArticleStatus, HelpArticle
from app.models.support import (
    SupportTicket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)
from app.models.user import User, UserRole
from app.services.help_center_seed import (
    STARTER_HELP_ARTICLES,
    seed_help_center_if_empty,
)


async def _admin_with_permissions(
    db: AsyncSession, permission_names: list[str]
) -> tuple[User, dict[str, str]]:
    user = User(
        email=f"help_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Help Center Admin",
        role=UserRole.admin,
    )
    role = AdminRole(name=f"Help Role {uuid.uuid4()}")
    db.add_all([user, role])
    await db.flush()
    for permission_name in permission_names:
        permission = (
            (
                await db.execute(
                    select(AdminPermission).where(
                        AdminPermission.name == permission_name
                    )
                )
            )
            .scalars()
            .first()
        )
        if not permission:
            permission = AdminPermission(name=permission_name)
            db.add(permission)
            await db.flush()
        db.add(AdminRolePermission(role_id=role.id, permission_id=permission.id))
    db.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db.commit()
    token = create_access_token(subject=str(user.id))
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def help_manager(db_session: AsyncSession):
    return await _admin_with_permissions(
        db_session,
        [
            "help_center.view",
            "help_center.manage",
            "support.view",
            "support.manage",
        ],
    )


@pytest.mark.asyncio
async def test_create_publish_search_archive_and_version_history(
    client: AsyncClient,
    help_manager: tuple[User, dict[str, str]],
):
    _, headers = help_manager
    slug = f"report-processing-{uuid.uuid4().hex[:8]}"
    create_response = await client.post(
        "/api/v1/admin/help-center",
        headers=headers,
        json={
            "title": "Why report processing can take longer",
            "slug": slug,
            "category": "Reports",
            "summary": "Steps for checking a report that remains in the processing state.",
            "content": "Keep the report ID and contact support if processing does not complete after refreshing the report.",
            "status": "draft",
        },
    )
    assert create_response.status_code == 201, create_response.text
    article_id = create_response.json()["article"]["id"]
    assert create_response.json()["article"]["published_at"] is None

    publish_response = await client.patch(
        f"/api/v1/admin/help-center/{article_id}",
        headers=headers,
        json={"status": "published"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["article"]["published_at"] is not None

    search_response = await client.get(
        "/api/v1/admin/help-center?search=processing&status=published",
        headers=headers,
    )
    assert search_response.status_code == 200
    assert any(
        article["id"] == article_id for article in search_response.json()["articles"]
    )

    archive_response = await client.patch(
        f"/api/v1/admin/help-center/{article_id}",
        headers=headers,
        json={"status": "archived"},
    )
    assert archive_response.status_code == 200
    assert archive_response.json()["article"]["status"] == "archived"

    versions_response = await client.get(
        f"/api/v1/admin/help-center/{article_id}/versions", headers=headers
    )
    assert versions_response.status_code == 200
    assert [version["status"] for version in versions_response.json()["versions"]] == [
        "published",
        "draft",
    ]


@pytest.mark.asyncio
async def test_help_center_permissions(
    client: AsyncClient,
    db_session: AsyncSession,
):
    _, viewer_headers = await _admin_with_permissions(db_session, ["help_center.view"])
    list_response = await client.get(
        "/api/v1/admin/help-center", headers=viewer_headers
    )
    assert list_response.status_code == 200

    create_response = await client.post(
        "/api/v1/admin/help-center",
        headers=viewer_headers,
        json={
            "title": "Viewer cannot create this article",
            "slug": f"viewer-cannot-create-{uuid.uuid4().hex[:8]}",
            "category": "Account",
            "summary": "This request must be rejected by the manage permission check.",
            "content": "A read-only Help Center administrator cannot create or edit article content.",
        },
    )
    assert create_response.status_code == 403
    assert (await client.get("/api/v1/admin/help-center")).status_code == 401

    _, support_headers = await _admin_with_permissions(db_session, ["support.manage"])
    support_read_response = await client.get(
        "/api/v1/admin/help-center", headers=support_headers
    )
    assert support_read_response.status_code == 200


@pytest.mark.asyncio
async def test_ticket_suggestions_and_article_linkage_are_content_grounded(
    client: AsyncClient,
    db_session: AsyncSession,
    help_manager: tuple[User, dict[str, str]],
):
    manager, headers = help_manager
    customer = User(
        email=f"customer_{uuid.uuid4()}@test.com",
        hashed_password="hashed",
        full_name="Support Customer",
        role=UserRole.patient,
    )
    db_session.add(customer)
    await db_session.flush()
    article = HelpArticle(
        title="Why is my report still processing?",
        slug=f"ticket-report-processing-{uuid.uuid4().hex[:8]}",
        category="Reports",
        summary="How to investigate report processing that appears stuck.",
        content="Keep the report ID and ask support to inspect report processing diagnostics.",
        status=ArticleStatus.published,
        created_by=str(manager.id),
    )
    unrelated = HelpArticle(
        title="Notification settings",
        slug=f"notification-settings-{uuid.uuid4().hex[:8]}",
        category="Notifications",
        summary="How to review notification permissions on a device.",
        content="Check device notification settings when reminders are not delivered.",
        status=ArticleStatus.published,
        created_by=str(manager.id),
    )
    ticket = SupportTicket(
        user_id=str(customer.id),
        title="My report is stuck processing",
        description="The report processing screen has not completed. I have the report ID.",
        category=TicketCategory.report,
        priority=TicketPriority.p3,
        status=TicketStatus.new,
    )
    db_session.add_all([article, unrelated, ticket])
    await db_session.commit()

    suggestion_response = await client.get(
        f"/api/v1/admin/support/{ticket.id}/article-suggestions", headers=headers
    )
    assert suggestion_response.status_code == 200
    suggestions = suggestion_response.json()["suggestions"]
    assert suggestions[0]["id"] == article.id
    assert "Matches:" in suggestions[0]["reason"]

    attach_response = await client.post(
        f"/api/v1/admin/support/{ticket.id}/articles/{article.id}", headers=headers
    )
    assert attach_response.status_code == 201

    ticket_response = await client.get(
        f"/api/v1/admin/support/{ticket.id}", headers=headers
    )
    assert ticket_response.status_code == 200
    assert ticket_response.json()["attached_articles"][0]["id"] == article.id


@pytest.mark.asyncio
async def test_empty_database_receives_useful_starter_articles(
    db_session: AsyncSession,
):
    await db_session.execute(delete(HelpArticle))
    await db_session.commit()

    created = await seed_help_center_if_empty(db_session)

    articles = (await db_session.execute(select(HelpArticle))).scalars().all()
    assert created == len(STARTER_HELP_ARTICLES)
    assert len(articles) == len(STARTER_HELP_ARTICLES)
    assert all(article.status == ArticleStatus.published for article in articles)
    assert {article.category for article in articles}.issubset(
        {
            "Account",
            "Reports",
            "Report Analysis",
            "AI/Chat",
            "RAG",
            "Notifications",
            "Medication Reminders",
            "Security",
            "Privacy",
            "Troubleshooting",
        }
    )
