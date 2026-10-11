import asyncio

import pytest

from app.services import analysis_pipeline


@pytest.mark.asyncio
async def test_core_summaries_start_concurrently(monkeypatch) -> None:
    started = set()
    both_started = asyncio.Event()
    release = asyncio.Event()

    async def fake_generate(prompt: str, **kwargs: object) -> dict:
        started.add(prompt)
        if len(started) == 2:
            both_started.set()
        await release.wait()
        return {"content": prompt}

    monkeypatch.setattr(
        analysis_pipeline, "generate_with_timeout_metadata", fake_generate
    )

    task = asyncio.create_task(
        analysis_pipeline.generate_core_summaries(
            "clinician", "patient", "clinician system", "patient system", "req-1"
        )
    )
    try:
        await asyncio.wait_for(both_started.wait(), timeout=1)
    finally:
        release.set()
    clinician, patient = await task

    assert clinician["content"] == "clinician"
    assert patient["content"] == "patient"
