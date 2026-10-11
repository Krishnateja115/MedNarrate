import os

import pytest

from app.services import report_text_loader


@pytest.mark.asyncio
async def test_cloud_report_is_staged_only_during_extraction(monkeypatch) -> None:
    class FakeStorage:
        async def download_file(self, key: str) -> bytes:
            assert key == "user/report.pdf"
            return b"%PDF-fake"

    def fake_extract(path: str, file_type: str) -> str:
        assert file_type == "pdf"
        assert os.path.exists(path)
        with open(path, "rb") as report_file:
            assert report_file.read() == b"%PDF-fake"
        staged_paths.append(path)
        return "Medical report text"

    staged_paths: list[str] = []
    monkeypatch.setattr(report_text_loader.settings, "STORAGE_BACKEND", "gcs")
    monkeypatch.setattr(report_text_loader, "get_storage_backend", FakeStorage)
    monkeypatch.setattr(report_text_loader, "extract_text_from_file", fake_extract)

    text = await report_text_loader.extract_report_text("user/report.pdf", "pdf")
    assert text == "Medical report text"
    assert not os.path.exists(staged_paths[0])
