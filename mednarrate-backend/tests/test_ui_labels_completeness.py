import json
import os
import pytest

from app.api.v1.analysis import REQUIRED_UI_LABEL_KEYS

def test_static_ui_labels():
    labels_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'report_ui_labels.json')
    assert os.path.exists(labels_file), "report_ui_labels.json does not exist"
    
    with open(labels_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    supported_langs = ["en", "hi", "ta", "te", "kn", "ml", "bn", "mr"]
    
    # Verify all languages exist
    for lang in supported_langs:
        assert lang in data, f"Language {lang} is missing from ui_labels dictionary"
        
    expected_keys = set(REQUIRED_UI_LABEL_KEYS)
    assert len(expected_keys) == 78, f"Expected 78 keys, got {len(expected_keys)}"
    
    for lang, lang_dict in data.items():
        if lang not in supported_langs:
            continue
            
        keys = set(lang_dict.keys())
        
        missing = expected_keys - keys
        unexpected = keys - expected_keys
        
        assert not missing, f"[{lang}] Missing keys: {missing}"
        assert not unexpected, f"[{lang}] Unexpected keys: {unexpected}"
        
        for key, value in lang_dict.items():
            assert isinstance(value, str), f"[{lang}] Key {key} must be string"
            assert value.strip() != "", f"[{lang}] Key {key} is empty"
