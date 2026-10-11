"""The translation prompt must request every label enforced by the API."""

from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS
from app.services.prompts import TRANSLATION_PROMPT


def test_translation_prompt_contains_every_required_ui_label() -> None:
    assert len(REQUIRED_UI_LABEL_KEYS) == 78
    assert len(REQUIRED_UI_LABEL_KEYS) == len(set(REQUIRED_UI_LABEL_KEYS))
    for key in REQUIRED_UI_LABEL_KEYS:
        assert f'"{key}"' in TRANSLATION_PROMPT
