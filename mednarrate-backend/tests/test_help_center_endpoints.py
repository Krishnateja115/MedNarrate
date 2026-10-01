"""
Regression tests for GET /api/v1/admin/help-center and related endpoints.

These tests verify:
- ORM/DB UUID type alignment (the root cause of the 500 error)
- System/seeded articles with zero-UUID created_by work safely
- Real admin UUID as author works
- list, get, versions, create, update flows
- filters: status, category, search
"""
import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.admin import (
    AdminRole,
    AdminPermission,
    AdminRoleAssignment,
    AdminRolePermission,
)
from app.models.help_center import ArticleStatus, HelpArticle, HelpArticleVersion

# The system/seeded zero-UUID that migration inserts
SYSTEM_UUID = uuid.UUID(int=0)


@pytest.fixture
async def help_center_admin(db_session: AsyncSession):
    """Create an admin user with help_center.view and help_center.manage permissions."""
    user = User(
        email=f"hc_admin_{uuid.uuid4()}@example.com",
        hashed_password="hashed_password",
        full_name="HC Admin",
        role=UserRole.admin,
    )
    db_session.add(user)
    await db_session.flush()

    role = AdminRole(name=f"HC Role {uuid.uuid4()}", description="Help Center role")
    db_session.add(role)
    await db_session.flush()

    perms = ["help_center.view", "help_center.manage", "support.manage"]
    for p_name in perms:
        stmt = select(AdminPermission).where(AdminPermission.name == p_name)
        perm = (await db_session.execute(stmt)).scalars().first()
        if not perm:
            perm = AdminPermission(name=p_name, description="Test perm")
            db_session.add(perm)
            await db_session.flush()
        db_session.add(AdminRolePermission(role_id=role.id, permission_id=perm.id))

    db_session.add(AdminRoleAssignment(user_id=user.id, role_id=role.id))
    await db_session.flush()
    await db_session.commit()
    return {"user": user, "token": create_access_token(str(user.id))}


@pytest.fixture
async def seeded_articles(db_session: AsyncSession, help_center_admin: dict):
    """Seed several articles covering: system UUID, real admin UUID, published, draft."""
    admin_user: User = help_center_admin["user"]
    now = datetime.utcnow()

    # Article authored by the system zero-UUID (migration seed scenario)
    system_article = HelpArticle(
        id=uuid.uuid4(),
        title="System Article",
        slug=f"system-article-{uuid.uuid4().hex[:8]}",
        category="Account",
        summary="A system-seeded help article.",
        content="This is content from the system seeder. Long enough.",
        status=ArticleStatus.published,
        created_by=SYSTEM_UUID,  # zero-UUID sentinel
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    db_session.add(system_article)

    # Article authored by a real admin UUID
    admin_article = HelpArticle(
        id=uuid.uuid4(),
        title="Admin Created Article",
        slug=f"admin-article-{uuid.uuid4().hex[:8]}",
        category="Reports",
        summary="Created by a real admin user with a UUID.",
        content="This is a detailed article about reports. Long enough content.",
        status=ArticleStatus.published,
        created_by=admin_user.id,  # real UUID
        created_at=now,
        updated_at=now,
        published_at=now,
    )
    db_session.add(admin_article)

    # A draft article
    draft_article = HelpArticle(
        id=uuid.uuid4(),
        title="Draft Article Not Published",
        slug=f"draft-article-{uuid.uuid4().hex[:8]}",
        category="Security",
        summary="This is a draft article not yet published.",
        content="This draft contains enough content to be valid for insertion.",
        status=ArticleStatus.draft,
        created_by=admin_user.id,
        created_at=now,
        updated_at=now,
    )
    db_session.add(draft_article)

    await db_session.commit()
    return {
        "system_article": system_article,
        "admin_article": admin_article,
        "draft_article": draft_article,
        "admin_user": admin_user,
    }


# ────────────────────────────────────────────────────────────────────────
# LIST ENDPOINT
# ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_help_center_list_returns_200(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Basic sanity: list endpoint returns 200."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get("/api/v1/admin/help-center", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "articles" in data
    assert "categories" in data


@pytest.mark.asyncio
async def test_help_center_list_contains_seeded_articles(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Seeded articles appear in the list and have correct field shapes."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get("/api/v1/admin/help-center", headers=headers)
    assert response.status_code == 200
    articles = response.json()["articles"]
    article_ids = {a["id"] for a in articles}
    assert str(seeded_articles["system_article"].id) in article_ids
    assert str(seeded_articles["admin_article"].id) in article_ids

    # Verify each article has expected keys
    for article in articles:
        assert "id" in article
        assert "title" in article
        assert "slug" in article
        assert "category" in article
        assert "status" in article
        assert "author" in article
        # id must be a string (UUID serialized to str)
        assert isinstance(article["id"], str)


@pytest.mark.asyncio
async def test_help_center_system_uuid_article_shows_mednarrate_author(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Articles with zero-UUID created_by show 'MedNarrate' as author, not crash."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get("/api/v1/admin/help-center", headers=headers)
    assert response.status_code == 200
    system_id = str(seeded_articles["system_article"].id)
    articles = {a["id"]: a for a in response.json()["articles"]}
    assert system_id in articles
    assert articles[system_id]["author"] == "MedNarrate"


@pytest.mark.asyncio
async def test_help_center_real_admin_uuid_author_shows_name(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Articles with a real admin UUID show the admin's full_name as author."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get("/api/v1/admin/help-center", headers=headers)
    assert response.status_code == 200
    admin_id = str(seeded_articles["admin_article"].id)
    articles = {a["id"]: a for a in response.json()["articles"]}
    assert admin_id in articles
    assert articles[admin_id]["author"] == seeded_articles["admin_user"].full_name


@pytest.mark.asyncio
async def test_help_center_filter_by_status_published(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Filtering by status=published returns only published articles."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get(
        "/api/v1/admin/help-center?status=published", headers=headers
    )
    assert response.status_code == 200
    for article in response.json()["articles"]:
        assert article["status"] == "published"


@pytest.mark.asyncio
async def test_help_center_filter_by_status_draft(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Filtering by status=draft returns only draft articles."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get(
        "/api/v1/admin/help-center?status=draft", headers=headers
    )
    assert response.status_code == 200
    articles = response.json()["articles"]
    assert len(articles) >= 1
    for article in articles:
        assert article["status"] == "draft"
    draft_ids = {a["id"] for a in articles}
    assert str(seeded_articles["draft_article"].id) in draft_ids


@pytest.mark.asyncio
async def test_help_center_filter_by_category(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Filtering by category returns only articles in that category."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get(
        "/api/v1/admin/help-center?category=Reports", headers=headers
    )
    assert response.status_code == 200
    for article in response.json()["articles"]:
        assert article["category"] == "Reports"
    ids = {a["id"] for a in response.json()["articles"]}
    assert str(seeded_articles["admin_article"].id) in ids


@pytest.mark.asyncio
async def test_help_center_search(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """Search by unique title fragment returns the matching article."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get(
        "/api/v1/admin/help-center?search=Draft+Article+Not+Published", headers=headers
    )
    assert response.status_code == 200
    ids = {a["id"] for a in response.json()["articles"]}
    assert str(seeded_articles["draft_article"].id) in ids


# ────────────────────────────────────────────────────────────────────────
# GET SINGLE ARTICLE
# ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_help_center_get_article_by_id(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """GET /{article_id} returns 200 with correct article."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    article_id = str(seeded_articles["admin_article"].id)
    response = await client.get(f"/api/v1/admin/help-center/{article_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["article"]["id"] == article_id
    assert data["article"]["category"] == "Reports"


@pytest.mark.asyncio
async def test_help_center_get_system_article_does_not_crash(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """GET /{system_article_id} where created_by is zero-UUID must return 200."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    article_id = str(seeded_articles["system_article"].id)
    response = await client.get(f"/api/v1/admin/help-center/{article_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["article"]["author"] == "MedNarrate"


@pytest.mark.asyncio
async def test_help_center_get_nonexistent_returns_404(
    client: AsyncClient, help_center_admin: dict
):
    """GET with unknown UUID returns 404, not 500."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get(
        f"/api/v1/admin/help-center/{uuid.uuid4()}", headers=headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_help_center_get_invalid_uuid_returns_404(
    client: AsyncClient, help_center_admin: dict
):
    """GET with non-UUID string returns 404."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    response = await client.get(
        "/api/v1/admin/help-center/not-a-valid-uuid", headers=headers
    )
    assert response.status_code == 404


# ────────────────────────────────────────────────────────────────────────
# VERSIONS ENDPOINT
# ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_help_center_versions_empty_on_new_article(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """GET /{article_id}/versions returns 200 with empty list for new articles."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    article_id = str(seeded_articles["admin_article"].id)
    response = await client.get(
        f"/api/v1/admin/help-center/{article_id}/versions", headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "versions" in data
    assert isinstance(data["versions"], list)


# ────────────────────────────────────────────────────────────────────────
# CREATE ENDPOINT
# ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_help_center_create_article(
    client: AsyncClient, help_center_admin: dict
):
    """POST creates a new article and returns 201 with full article data."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    unique_slug = f"new-test-article-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "New Test Article Title",
        "slug": unique_slug,
        "category": "Troubleshooting",
        "summary": "This is a valid summary for the article.",
        "content": "This is long enough content for a new help center article to be valid.",
        "status": "draft",
    }
    response = await client.post("/api/v1/admin/help-center", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert data["article"]["slug"] == unique_slug
    assert data["article"]["status"] == "draft"
    # id must be a string
    assert isinstance(data["article"]["id"], str)
    # author must be the admin's name
    assert data["article"]["author"] == help_center_admin["user"].full_name


@pytest.mark.asyncio
async def test_help_center_create_published_article(
    client: AsyncClient, help_center_admin: dict
):
    """POST with status=published sets published_at."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    unique_slug = f"published-test-{uuid.uuid4().hex[:8]}"
    payload = {
        "title": "Published Article Title",
        "slug": unique_slug,
        "category": "Account",
        "summary": "This published article has a proper summary.",
        "content": "This is long enough content for a published article to be valid.",
        "status": "published",
    }
    response = await client.post("/api/v1/admin/help-center", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["article"]["status"] == "published"
    assert data["article"]["published_at"] is not None


@pytest.mark.asyncio
async def test_help_center_create_duplicate_slug_returns_409(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """POST with duplicate slug returns 409."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    existing_slug = seeded_articles["admin_article"].slug
    payload = {
        "title": "Duplicate Slug Article",
        "slug": existing_slug,
        "category": "Account",
        "summary": "This article has a duplicate slug that already exists.",
        "content": "This is long enough content for the duplicate slug test.",
        "status": "draft",
    }
    response = await client.post("/api/v1/admin/help-center", json=payload, headers=headers)
    assert response.status_code == 409


# ────────────────────────────────────────────────────────────────────────
# UPDATE ENDPOINT
# ────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_help_center_update_article(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """PATCH updates article fields and creates a version snapshot."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    article_id = str(seeded_articles["draft_article"].id)
    payload = {"title": "Updated Draft Title"}
    response = await client.patch(
        f"/api/v1/admin/help-center/{article_id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["article"]["title"] == "Updated Draft Title"

    # Verify a version was recorded
    versions_response = await client.get(
        f"/api/v1/admin/help-center/{article_id}/versions", headers=headers
    )
    assert versions_response.status_code == 200
    assert len(versions_response.json()["versions"]) >= 1


@pytest.mark.asyncio
async def test_help_center_publish_sets_published_at(
    client: AsyncClient, help_center_admin: dict, seeded_articles: dict
):
    """PATCH status=published on a draft sets published_at."""
    headers = {"Authorization": f"Bearer {help_center_admin['token']}"}
    article_id = str(seeded_articles["draft_article"].id)
    payload = {"status": "published"}
    response = await client.patch(
        f"/api/v1/admin/help-center/{article_id}", json=payload, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["article"]["published_at"] is not None
