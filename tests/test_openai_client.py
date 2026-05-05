from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.openai_client import _parse_unified_completion


def test_parse_unified_completion_valid_json_with_facts() -> None:
    payload = '{"reply_text":"Hello","memory_facts":{"name":"Alice","role":"Engineer"}}'
    parsed = _parse_unified_completion(payload, memory_enabled=True)
    assert parsed == {'reply_text': 'Hello', 'memory_facts': {'name': 'Alice', 'role': 'Engineer'}}


def test_parse_unified_completion_malformed_json_fallback() -> None:
    payload = 'Non JSON assistant response'
    parsed = _parse_unified_completion(payload, memory_enabled=True)
    assert parsed == {'reply_text': 'Non JSON assistant response', 'memory_facts': {}}


def test_parse_unified_completion_empty_facts_and_memory_disabled() -> None:
    payload = '{"reply_text":"Hi","memory_facts":{"name":"Alice"}}'
    parsed = _parse_unified_completion(payload, memory_enabled=False)
    assert parsed == {'reply_text': 'Hi', 'memory_facts': {}}
