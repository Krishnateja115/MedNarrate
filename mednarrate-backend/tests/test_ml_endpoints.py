"""Model-performance and XAI endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.admin import AdminAuditLog

pytestmark = pytest.mark.asyncio


async def test_user_endpoint_requires_login(client: AsyncClient):
    assert (await client.get("/api/v1/ml/model-performance")).status_code == 401


async def test_user_sees_every_model_without_server_details(client: AsyncClient, token_headers):
    resp = await client.get("/api/v1/ml/model-performance", headers=token_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["models"]) == 9
    assert body["summary"]["deep_learning_total"] >= 5
    assert {"lime", "linear_attribution", "occlusion", "rule_trace"} <= {m["id"] for m in body["xai_methods"]}
    assert "environment" not in body and "how_to_refresh" not in body
    for model in body["models"]:
        assert model["status"] in {"evaluated", "not_evaluated", "failed"}
        if model["status"] != "evaluated":
            assert model["metrics"] == []  # never an invented number


async def test_admin_endpoint_is_admin_only(client: AsyncClient, token_headers, admin_token_and_user):
    assert (await client.get("/api/v1/admin/ml/model-performance", headers=token_headers)).status_code == 403
    client.cookies.clear()  # the login in token_headers left a session cookie behind
    assert (await client.get("/api/v1/admin/ml/model-performance")).status_code == 401
    admin_headers, _ = admin_token_and_user
    resp = await client.get("/api/v1/admin/ml/model-performance", headers=admin_headers)
    assert resp.status_code == 200
    assert "how_to_refresh" in resp.json()


async def test_explain_report_type_returns_lime_and_linear_attribution(
    client: AsyncClient, admin_token_and_user, db_session
):
    headers, admin = admin_token_and_user
    text = "Histopathology: invasive ductal carcinoma, tumor size 2.1 cm, lymph nodes negative"
    resp = await client.post("/api/v1/admin/ml/explain/report-type", headers=headers, json={"text": text})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["predicted"] == "TCGA"
    assert body["lime"]["method"] == "lime" and body["linear"]["method"] == "linear_attribution"
    assert body["linear"]["features"]

    logs = (await db_session.execute(select(AdminAuditLog).where(AdminAuditLog.action == "XAI_EXPLAIN_REPORT_TYPE"))).scalars().all()
    assert logs, "explanation should be audited"
    assert logs[0].metadata_payload == {"characters": len(text)}  # size only, never the text


async def test_explain_rejects_blank_oversized_and_non_admin(client: AsyncClient, admin_token_and_user, token_headers):
    headers, _ = admin_token_and_user
    url = "/api/v1/admin/ml/explain/report-type"
    assert (await client.post(url, headers=headers, json={"text": "   "})).status_code == 422
    assert (await client.post(url, headers=headers, json={"text": "x" * 3001})).status_code == 422
    assert (await client.post(url, headers=token_headers, json={"text": "hello"})).status_code == 403
    client.cookies.clear()
    assert (await client.post(url, json={"text": "hello"})).status_code == 401


async def test_explain_entities_uses_the_ner_model(client: AsyncClient, admin_token_and_user, monkeypatch):
    headers, _ = admin_token_and_user
    text = "patient takes metformin for diabetes"

    def fake_pipeline(t):
        if "diabetes" not in t:
            return []
        start = t.index("diabetes")
        score = 0.9 if "metformin" in t else 0.5
        return [{"start": start, "end": start + 8, "entity_group": "Disease_disorder", "score": score}]

    from app.services import model_registry

    monkeypatch.setattr(model_registry, "get_ner_pipeline", lambda: fake_pipeline)
    resp = await client.post("/api/v1/admin/ml/explain/entities", headers=headers, json={"text": text})
    assert resp.status_code == 200, resp.text
    entity = resp.json()["entities"][0]
    assert entity["entity"] == "diabetes"
    assert entity["evidence"][0]["word"] == "metformin"


async def test_explain_entities_limits_and_missing_model(client: AsyncClient, admin_token_and_user, monkeypatch):
    headers, _ = admin_token_and_user
    url = "/api/v1/admin/ml/explain/entities"
    too_long = " ".join(["word"] * 61)
    assert (await client.post(url, headers=headers, json={"text": too_long})).status_code == 422

    from app.services import model_registry

    def boom():
        raise OSError("no network")

    monkeypatch.setattr(model_registry, "get_ner_pipeline", boom)
    resp = await client.post(url, headers=headers, json={"text": "patient has fever"})
    assert resp.status_code == 503
