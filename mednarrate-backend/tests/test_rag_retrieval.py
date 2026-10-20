"""Retrieval quality and robustness of the RAG pipeline (embeddings, backfill, keyword fallback,
knowledge-base notes in chat). Embedders here are fakes: no network is used."""
import asyncio
import sys
import types
from unittest.mock import patch

import pytest
from sqlalchemy import select

from app.api.v1 import chat as chat_api
from app.core.config import settings
from app.models.rag_chunk import RagChunk
from app.services import embedding_provider as ep
from app.services import rag
from tests.pdf_fixtures import VALID_PDF
from tests.test_rag_privacy_boundary import _make_report

TOPICS = [
    ("hemoglobin", "haemoglobin", "anemia"),
    ("glucose", "sugar", "diabetes"),
    ("cholesterol", "lipid", "ldl"),
    ("thyroid", "tsh"),
]

REPORT = "\n---\n".join(
    [
        "Hemoglobin 9.1 g/dL (12.0-15.5) low, anemia pattern",
        "Glucose fasting 200 mg/dL (70-99) high",
        "Cholesterol LDL 190 mg/dL lipid panel",
        "TSH thyroid 2.5 mIU/L normal",
    ]
)


def topic_embed(text, task_type="retrieval_document"):
    """A 'meaning' embedder: sugar and glucose land on the same axis."""
    lowered = text.lower()
    return [float(sum(lowered.count(w) for w in group)) + 0.01 for group in TOPICS]


@pytest.fixture
def four_chunks(monkeypatch):
    monkeypatch.setattr(rag, "chunk_text", lambda text, *a, **k: text.split("\n---\n"))


async def _chunks(db, report_id):
    return (
        await db.execute(select(RagChunk).where(RagChunk.report_id == report_id).order_by(RagChunk.chunk_index))
    ).scalars().all()


# ---------------------------------------------------------------- dense retrieval

@pytest.mark.asyncio
async def test_dense_retrieval_finds_the_chunk_by_meaning(db_session, monkeypatch, four_chunks):
    monkeypatch.setattr(rag, "get_embedder", lambda: topic_embed)
    _, report = await _make_report(db_session, "dense@example.com")
    await rag.process_report_for_rag(report.id, REPORT, db_session)

    out = await rag.retrieve_chunks("how is my sugar level", report.id, db_session, top_k=1)

    # "sugar" never appears in the report, so keyword search could not find this chunk.
    assert "Glucose fasting 200" in out
    assert "Hemoglobin" not in out
    assert out.startswith("[Chunk 2/4]")


@pytest.mark.asyncio
async def test_chunks_come_back_in_document_order(db_session, monkeypatch, four_chunks):
    monkeypatch.setattr(rag, "get_embedder", lambda: topic_embed)
    _, report = await _make_report(db_session, "order@example.com")
    await rag.process_report_for_rag(report.id, REPORT, db_session)

    out = await rag.retrieve_chunks("sugar and hemoglobin", report.id, db_session, top_k=2)

    assert out.index("Hemoglobin") < out.index("Glucose")


@pytest.mark.asyncio
async def test_reports_stored_without_vectors_are_backfilled_on_first_question(db_session, monkeypatch, four_chunks):
    _, report = await _make_report(db_session, "backfill@example.com")
    monkeypatch.setattr(rag, "get_embedder", lambda: None)
    await rag.process_report_for_rag(report.id, REPORT, db_session)
    assert all(c.embedding_json is None for c in await _chunks(db_session, report.id))

    monkeypatch.setattr(rag, "get_embedder", lambda: topic_embed)
    out = await rag.retrieve_chunks("sugar level please", report.id, db_session, top_k=1)

    assert "Glucose fasting 200" in out
    assert all(c.embedding_json is not None for c in await _chunks(db_session, report.id))


@pytest.mark.asyncio
async def test_backfill_stops_cleanly_when_the_provider_fails(db_session, monkeypatch, four_chunks):
    _, report = await _make_report(db_session, "backfill2@example.com")
    monkeypatch.setattr(rag, "get_embedder", lambda: None)
    await rag.process_report_for_rag(report.id, REPORT, db_session)

    def down(text, task_type="retrieval_document"):
        raise RuntimeError("quota")

    monkeypatch.setattr(rag, "get_embedder", lambda: down)
    monkeypatch.setattr(rag.asyncio, "sleep", _no_sleep)
    out = await rag.retrieve_chunks("glucose", report.id, db_session, top_k=1)

    assert "Glucose fasting 200" in out  # keyword search answered


async def _no_sleep(_seconds):
    return None


@pytest.mark.asyncio
async def test_ingestion_stops_calling_a_failing_provider(db_session, monkeypatch, four_chunks):
    calls = []

    def flaky(text, task_type="retrieval_document"):
        calls.append(text)
        raise RuntimeError("down")

    monkeypatch.setattr(rag, "get_embedder", lambda: flaky)
    monkeypatch.setattr(rag.asyncio, "sleep", _no_sleep)
    _, report = await _make_report(db_session, "flaky@example.com")
    await rag.process_report_for_rag(report.id, REPORT, db_session)

    assert len(calls) == 2  # one chunk, tried twice; the other three were not attempted
    assert len(await _chunks(db_session, report.id)) == 4


@pytest.mark.asyncio
async def test_query_embedding_failure_uses_keyword_search(db_session, monkeypatch, four_chunks):
    def embed(text, task_type="retrieval_document"):
        if task_type == "retrieval_query":
            raise RuntimeError("down")
        return topic_embed(text, task_type)

    monkeypatch.setattr(rag, "get_embedder", lambda: embed)
    monkeypatch.setattr(rag.asyncio, "sleep", _no_sleep)
    _, report = await _make_report(db_session, "qfail@example.com")
    await rag.process_report_for_rag(report.id, REPORT, db_session)

    out = await rag.retrieve_chunks("cholesterol", report.id, db_session, top_k=1)

    assert "Cholesterol LDL 190" in out


@pytest.mark.asyncio
async def test_an_empty_report_returns_no_context(db_session, monkeypatch):
    monkeypatch.setattr(rag, "get_embedder", lambda: topic_embed)
    _, report = await _make_report(db_session, "empty@example.com")
    assert await rag.retrieve_chunks("anything", report.id, db_session) == ""


# ---------------------------------------------------------------- helpers

def test_vectors_of_the_wrong_size_are_never_stored_on_postgres(monkeypatch):
    monkeypatch.setattr(rag, "_is_postgres", lambda: True)
    assert rag._storable_embedding([0.1] * 3072) is None
    assert rag._storable_embedding([0.1] * ep.EMBEDDING_DIM) == [0.1] * ep.EMBEDDING_DIM
    assert rag._storable_embedding([]) is None
    assert rag._storable_embedding(None) is None
    assert rag._storable_embedding([float("nan")] * ep.EMBEDDING_DIM) is None


def test_other_sizes_are_accepted_on_sqlite(monkeypatch):
    monkeypatch.setattr(rag, "_is_postgres", lambda: False)
    assert rag._storable_embedding([0.5, 0.25]) == [0.5, 0.25]


def test_numpy_vectors_from_pgvector_are_understood():
    import numpy as np

    assert rag._as_vector(np.array([1, 2, 3], dtype=np.float32)).tolist() == [1.0, 2.0, 3.0]


def test_tokens_keep_decimals_and_indian_script_words_whole():
    assert rag._tokens("Hemoglobin: 12.5 g/dL (13.0-17.0).") == ["hemoglobin", "12.5", "g", "dl", "13.0", "17.0"]
    assert rag._tokens("हीमोग्लोबिन कम है") == ["हीमोग्लोबिन", "कम", "है"]


def test_keyword_search_ranks_by_overlap_and_falls_back_to_document_order():
    rows = [
        (0, "hemoglobin 9.1 low", None),
        (1, "glucose 200 high", None),
        (2, "cholesterol ldl 190", None),
    ]
    assert rag._bm25_top(rows, "glucose result", 1)[0][0] == 1
    # Nothing in common (or nothing to search for): first chunks, in order.
    assert [r[0] for r in rag._bm25_top(rows, "zzz qqq", 2)] == [0, 1]
    assert [r[0] for r in rag._bm25_top(rows, "", 2)] == [0, 1]


def test_dense_search_gives_up_if_a_vector_is_missing_or_the_wrong_size():
    import numpy as np

    q = np.array([1.0, 0.0])
    good = [(0, "a", np.array([1.0, 0.0])), (1, "b", np.array([0.0, 1.0]))]
    assert [r[0] for r in rag._dense_top(good, q, 1)] == [0]
    assert rag._dense_top(good + [(2, "c", None)], q, 1) == []
    assert rag._dense_top(good + [(2, "c", np.array([1.0, 0.0, 0.0]))], q, 1) == []


# ---------------------------------------------------------------- embedding provider

def test_gemini_embeddings_are_requested_at_the_size_the_database_column_holds(monkeypatch):
    seen = {}
    fake = types.ModuleType("google.generativeai")
    fake.configure = lambda api_key=None: seen.setdefault("key", api_key)

    def embed_content(**kwargs):
        seen["kwargs"] = kwargs
        return {"embedding": [0.0] * kwargs["output_dimensionality"]}

    fake.embed_content = embed_content
    monkeypatch.setitem(sys.modules, "google.generativeai", fake)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key", raising=False)

    embed = ep._gemini_embedder()
    vector = embed("some text", "retrieval_query")

    assert seen["kwargs"]["output_dimensionality"] == 768 == ep.EMBEDDING_DIM
    assert seen["kwargs"]["model"] == "models/gemini-embedding-001"
    assert seen["kwargs"]["task_type"] == "retrieval_query"
    assert len(vector) == 768


@pytest.fixture
def sentinel_gemini(monkeypatch):
    sentinel = object()
    monkeypatch.setitem(ep._PROVIDERS, "gemini", lambda: sentinel)
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", None, raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
    return sentinel


def test_groq_as_answering_model_still_gets_gemini_embeddings_when_a_key_exists(monkeypatch, sentinel_gemini):
    monkeypatch.setattr(settings, "PRIMARY_LLM_PROVIDER", "groq", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "key", raising=False)
    assert ep.get_embedder() is sentinel_gemini


def test_no_gemini_key_means_no_embeddings_not_an_error(monkeypatch, sentinel_gemini):
    monkeypatch.setattr(settings, "PRIMARY_LLM_PROVIDER", "groq", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None, raising=False)
    assert ep.get_embedder() is None


def test_production_needs_the_explicit_gemini_opt_in(monkeypatch, sentinel_gemini):
    monkeypatch.setattr(settings, "PRIMARY_LLM_PROVIDER", "groq", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "key", raising=False)
    monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)
    monkeypatch.setattr(settings, "ALLOW_GEMINI_API_KEY_IN_PRODUCTION", False, raising=False)
    assert ep.get_embedder() is None
    monkeypatch.setattr(settings, "ALLOW_GEMINI_API_KEY_IN_PRODUCTION", True, raising=False)
    assert ep.get_embedder() is sentinel_gemini


def test_an_explicit_unknown_embedding_provider_still_disables_embeddings(monkeypatch, sentinel_gemini):
    monkeypatch.setattr(settings, "PRIMARY_LLM_PROVIDER", "groq", raising=False)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "key", raising=False)
    monkeypatch.setattr(settings, "EMBEDDING_PROVIDER", "nope", raising=False)
    assert ep.get_embedder() is None


# ---------------------------------------------------------------- chat wiring

@pytest.mark.asyncio
async def test_knowledge_notes_are_skipped_for_non_english_and_never_raise(monkeypatch):
    calls = []

    async def kb(query, top_k=3):
        calls.append(query)
        return "note"

    monkeypatch.setattr(chat_api, "retrieve_kb_context", kb)
    assert await chat_api._knowledge_context("मेरा शुगर कितना है") == ""
    assert await chat_api._knowledge_context("   ") == ""
    assert calls == []
    assert await chat_api._knowledge_context("what is hemoglobin") == "note"

    async def broken(query, top_k=3):
        raise RuntimeError("chroma down")

    monkeypatch.setattr(chat_api, "retrieve_kb_context", broken)
    assert await chat_api._knowledge_context("what is hemoglobin") == ""

    async def slow(query, top_k=3):
        await asyncio.sleep(5)
        return "late"

    monkeypatch.setattr(chat_api, "retrieve_kb_context", slow)
    monkeypatch.setattr(chat_api, "_KB_TIMEOUT_SECONDS", 0.05)
    assert await chat_api._knowledge_context("what is hemoglobin") == ""


@pytest.mark.asyncio
async def test_general_chat_prompt_carries_the_knowledge_notes(client, token_headers, monkeypatch):
    async def kb(query, top_k=3):
        return "Hemoglobin carries oxygen in red blood cells."

    monkeypatch.setattr(chat_api, "retrieve_kb_context", kb)
    created = await client.post("/api/v1/chat/sessions", json={"title": "General"}, headers=token_headers)
    sid = created.json()["id"]
    captured = {}

    async def fake_generate(prompt, system_instruction=None, **kwargs):
        captured["prompt"] = prompt
        return "Hemoglobin carries oxygen."

    with patch("app.api.v1.chat.generate", side_effect=fake_generate):
        resp = await client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            json={"content": "What does hemoglobin do in the body"},
            headers=token_headers,
        )

    assert resp.status_code == 200
    assert "<HEALTH_NOTES>" in captured["prompt"]
    assert "carries oxygen in red blood cells" in captured["prompt"]


@pytest.mark.asyncio
async def test_report_chat_uses_report_chunks_and_notes_and_searches_follow_ups_with_context(
    client, token_headers, monkeypatch
):
    upload = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        files={"file": ("test.pdf", VALID_PDF, "application/pdf")},
        data={"title": "T", "report_date": "2024-01-01", "report_type": "blood"},
    )
    report_id = upload.json()["id"]
    created = await client.post(
        "/api/v1/chat/sessions", headers=token_headers, json={"report_id": report_id, "title": "Chat"}
    )
    sid = created.json()["id"]

    searches = []

    async def fake_retrieve(query, rid, db, top_k=5):
        searches.append(query)
        return "[Chunk 1/1]: Glucose fasting 200 mg/dL"

    async def kb(query, top_k=3):
        return "Fasting glucose is measured after 8 hours without food."

    monkeypatch.setattr(chat_api, "retrieve_chunks", fake_retrieve)
    monkeypatch.setattr(chat_api, "retrieve_kb_context", kb)
    prompts = []

    async def fake_generate(prompt, system_instruction=None, **kwargs):
        prompts.append(prompt)
        return "Your fasting glucose is 200 mg/dL."

    with patch("app.api.v1.chat.generate", side_effect=fake_generate):
        first = await client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            json={"content": "What is my glucose result in this report"},
            headers=token_headers,
        )
        second = await client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            json={"content": "what does that mean"},
            headers=token_headers,
        )

    assert first.status_code == 200 and second.status_code == 200
    assert "<GENERAL_KNOWLEDGE>" in prompts[0]
    assert "Glucose fasting 200 mg/dL" in prompts[0]
    assert "measured after 8 hours without food" in prompts[0]
    # A long question is searched as written; the short follow-up is searched with the question before it.
    assert searches[0] == "What is my glucose result in this report"
    assert searches[1].startswith("What is my glucose result in this report")
    assert searches[1].endswith("what does that mean")


@pytest.mark.asyncio
async def test_report_chat_still_answers_when_the_knowledge_base_is_broken(client, token_headers, monkeypatch):
    upload = await client.post(
        "/api/v1/reports/upload",
        headers=token_headers,
        files={"file": ("test.pdf", VALID_PDF, "application/pdf")},
        data={"title": "T", "report_date": "2024-01-01", "report_type": "blood"},
    )
    created = await client.post(
        "/api/v1/chat/sessions", headers=token_headers, json={"report_id": upload.json()["id"], "title": "Chat"}
    )
    sid = created.json()["id"]

    async def fake_retrieve(query, rid, db, top_k=5):
        return "[Chunk 1/1]: Glucose fasting 200 mg/dL"

    async def broken_kb(query, top_k=3):
        raise RuntimeError("chroma down")

    monkeypatch.setattr(chat_api, "retrieve_chunks", fake_retrieve)
    monkeypatch.setattr(chat_api, "retrieve_kb_context", broken_kb)

    async def fake_generate(prompt, system_instruction=None, **kwargs):
        assert "<GENERAL_KNOWLEDGE>\nNone\n</GENERAL_KNOWLEDGE>" in prompt
        return "Your glucose is 200 mg/dL."

    with patch("app.api.v1.chat.generate", side_effect=fake_generate):
        resp = await client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            json={"content": "What is my glucose result in this report"},
            headers=token_headers,
        )

    assert resp.status_code == 200
    assert "200" in resp.json()["message"]["content"]


# ---------------------------------------------------------------- knowledge base lookup

class _FakeCollection:
    def __init__(self, documents):
        self.documents = documents
        self.asked = None

    def count(self):
        return len(self.documents)

    def query(self, query_texts, n_results):
        self.asked = (query_texts, n_results)
        return {"documents": [self.documents[:n_results]]}


@pytest.mark.asyncio
async def test_knowledge_base_lookup_returns_notes_and_never_asks_for_more_than_exist(monkeypatch):
    fake = _FakeCollection(["Note A", "Note B"])
    monkeypatch.setattr(rag, "kb_collection", fake)

    assert await rag.retrieve_kb_context("what is hemoglobin", top_k=5) == "Note A\n\nNote B"
    assert fake.asked[1] == 2


@pytest.mark.asyncio
async def test_knowledge_base_lookup_is_empty_when_unbuilt_or_broken(monkeypatch):
    monkeypatch.setattr(rag, "kb_collection", _FakeCollection([]))
    assert await rag.retrieve_kb_context("anything") == ""

    monkeypatch.setattr(rag, "kb_collection", None)
    assert await rag.retrieve_kb_context("anything") == ""

    class Broken(_FakeCollection):
        def query(self, query_texts, n_results):
            raise RuntimeError("model could not be downloaded")

    monkeypatch.setattr(rag, "kb_collection", Broken(["x"]))
    assert await rag.retrieve_kb_context("anything") == ""


def test_chat_verifier_does_not_compare_numbers_with_the_question():
    """A good answer quotes numbers the question never contained (report values).

    The chat check once compared question numbers with answer numbers, so every such answer
    failed, was regenerated, and got a stray "Translation note" appended."""
    from app.services.translation_validation import TranslationVerifier

    question = "What does my hemoglobin mean?"
    answer = "Your hemoglobin is 10.2 g/dL, below the 12.0 to 15.5 range in your report."
    verifier = TranslationVerifier()
    assert verifier.verify({"content": question}, {"content": answer}, "en", preserve_numeric=False)["ok"]
    assert not verifier.verify({"content": question}, {"content": answer}, "en")["ok"]
    import inspect
    from app.api.v1 import chat
    assert inspect.getsource(chat._generate_rag_answer).count("preserve_numeric=False") == 2
