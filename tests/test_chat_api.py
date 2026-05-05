from pathlib import Path
import sys

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app



def test_chat_endpoint_returns_reply_and_status_shape(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        captured['messages'] = messages
        captured['memory_enabled'] = memory_enabled
        return {'reply_text': 'Echo: ciao', 'memory_facts': {}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)

    client = TestClient(app)
    payload = {
        'message': 'ciao',
        'flags': {'session': True, 'system': False, 'memory': False, 'kb': False},
    }

    response = client.post('/chat', json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data['reply'] == 'Echo: ciao'
    assert data['status'] == 'session ✓ | system ✗ | memory ✗ | kb ✗'
    assert isinstance(data['prompt_bytes'], int)
    assert data['prompt_bytes'] > 0
    assert captured['memory_enabled'] is False
    assert captured['messages'] == [{'role': 'user', 'content': 'ciao'}]


def test_chat_endpoint_accepts_optional_placeholders(monkeypatch) -> None:
    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        return {'reply_text': 'ok', 'memory_facts': {'role': 'developer'}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)

    client = TestClient(app)
    payload = {
        'message': 'domanda',
        'flags': {'session': False, 'system': True, 'memory': True, 'kb': True},
        'session_id': 'abc123',
        'system_prompt': 'be concise',
        'memory_hint': 'user likes python',
        'kb_hint': 'docs snippet',
    }

    response = client.post('/chat', json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body['reply'] == 'ok'
    assert body['status'] == 'session ✗ | system ✓ | memory ✓ | kb ✓'
    assert isinstance(body['prompt_bytes'], int)


def test_chat_endpoint_validates_required_fields() -> None:
    client = TestClient(app)
    response = client.post('/chat', json={'flags': {'session': False, 'system': False, 'memory': False, 'kb': False}})

    assert response.status_code == 422


def test_chat_endpoint_includes_session_history_when_enabled(monkeypatch) -> None:
    captured_calls: list[list[dict[str, str]]] = []

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        captured_calls.append(messages)
        return {'reply_text': f"reply-{len(captured_calls)}", 'memory_facts': {}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)

    client = TestClient(app)
    payload_1 = {
        'message': 'first question',
        'session_id': 'sess-1',
        'flags': {'session': True, 'system': False, 'memory': False, 'kb': False},
    }
    payload_2 = {
        'message': 'second question',
        'session_id': 'sess-1',
        'flags': {'session': True, 'system': False, 'memory': False, 'kb': False},
    }

    response_1 = client.post('/chat', json=payload_1)
    response_2 = client.post('/chat', json=payload_2)

    assert response_1.status_code == 200
    assert response_2.status_code == 200
    assert captured_calls[0] == [{'role': 'user', 'content': 'first question'}]
    assert captured_calls[1] == [
        {'role': 'user', 'content': 'first question'},
        {'role': 'assistant', 'content': 'reply-1'},
        {'role': 'user', 'content': 'second question'},
    ]


def test_chat_endpoint_injects_system_prompt_first_when_enabled(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        captured['messages'] = messages
        return {'reply_text': 'ok-system', 'memory_facts': {}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)

    client = TestClient(app)
    payload = {
        'message': 'what is this app?',
        'system_prompt': 'You are a strict tutor.',
        'flags': {'session': False, 'system': True, 'memory': False, 'kb': False},
    }

    response = client.post('/chat', json=payload)

    assert response.status_code == 200
    assert captured['messages'] == [
        {'role': 'system', 'content': 'You are a strict tutor.'},
        {'role': 'user', 'content': 'what is this app?'},
    ]


def test_chat_endpoint_ignores_system_prompt_when_flag_is_disabled(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        captured['messages'] = messages
        return {'reply_text': 'ok-no-system', 'memory_facts': {}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)

    client = TestClient(app)
    payload = {
        'message': 'hello',
        'system_prompt': 'Do not include me',
        'flags': {'session': False, 'system': False, 'memory': False, 'kb': False},
    }

    response = client.post('/chat', json=payload)
    assert response.status_code == 200
    assert captured['messages'] == [{'role': 'user', 'content': 'hello'}]


def test_chat_endpoint_injects_persistent_memory_when_enabled(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        captured['messages'] = messages
        captured['memory_enabled'] = memory_enabled
        return {'reply_text': 'ok-memory', 'memory_facts': {'name': 'Mario'}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)
    monkeypatch.setattr('app.main.memory_store.get_summary', lambda: 'Known fact: user is in Rome.')

    client = TestClient(app)
    payload = {
        'message': 'where am i?',
        'flags': {'session': False, 'system': False, 'memory': True, 'kb': False},
    }

    response = client.post('/chat', json=payload)

    assert response.status_code == 200
    assert captured['messages'] == [
        {'role': 'system', 'content': 'Persistent memory:\nKnown fact: user is in Rome.'},
        {'role': 'user', 'content': 'where am i?'},
    ]
    assert captured['memory_enabled'] is True


def test_memory_inspector_read_and_clear() -> None:
    client = TestClient(app)

    get_response = client.get('/memory')
    assert get_response.status_code == 200
    assert 'facts' in get_response.json()

    clear_response = client.delete('/memory')
    assert clear_response.status_code == 200
    assert clear_response.json() == {'facts': {}}

    get_response_after = client.get('/memory')
    assert get_response_after.status_code == 200
    assert get_response_after.json() == {'facts': {}}


def test_chat_endpoint_injects_kb_when_enabled(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        captured['messages'] = messages
        return {'reply_text': 'ok-kb', 'memory_facts': {}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)
    monkeypatch.setattr('app.main.kb_store.get_content', lambda: '# KB\nUse this information.')

    client = TestClient(app)
    payload = {
        'message': 'answer from docs',
        'flags': {'session': False, 'system': False, 'memory': False, 'kb': True},
    }

    response = client.post('/chat', json=payload)
    assert response.status_code == 200
    assert captured['messages'] == [
        {'role': 'system', 'content': 'Knowledge base:\n# KB\nUse this information.'},
        {'role': 'user', 'content': 'answer from docs'},
    ]


def test_kb_upload_and_read() -> None:
    client = TestClient(app)
    files = {'file': ('notes.md', b'# Notes\n\nHello KB', 'text/markdown')}
    upload_response = client.post('/kb/upload', files=files)
    assert upload_response.status_code == 200
    assert upload_response.json() == {'filename': 'notes.md'}

    read_response = client.get('/kb')
    assert read_response.status_code == 200
    assert read_response.json() == {'filename': 'notes.md', 'content': '# Notes\n\nHello KB'}


def test_kb_upload_rejects_non_markdown_file() -> None:
    client = TestClient(app)
    files = {'file': ('notes.txt', b'no markdown', 'text/plain')}
    response = client.post('/kb/upload', files=files)
    assert response.status_code == 400


def test_kb_select_binds_specific_file() -> None:
    client = TestClient(app)
    client.post('/kb/upload', files={'file': ('a.md', b'A content', 'text/markdown')})
    client.post('/kb/upload', files={'file': ('z.md', b'Z content', 'text/markdown')})

    select_response = client.put('/kb/select', json={'filename': 'a.md'})
    assert select_response.status_code == 200
    assert select_response.json() == {'filename': 'a.md'}

    read_response = client.get('/kb')
    assert read_response.status_code == 200
    assert read_response.json() == {'filename': 'a.md', 'content': 'A content'}


def test_health_endpoint_still_returns_ok_payload() -> None:
    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_chat_memory_not_persisted_when_flag_disabled(monkeypatch) -> None:
    monkeypatch.setattr('app.main.memory_store.clear', lambda: {})
    monkeypatch.setattr('app.main.memory_store.get_summary', lambda: None)

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        return {'reply_text': 'ok', 'memory_facts': {'name': 'Luca'}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)
    monkeypatch.setattr('app.main.memory_store.upsert_facts', lambda facts: (_ for _ in ()).throw(AssertionError('must not persist')))

    client = TestClient(app)
    response = client.post(
        '/chat',
        json={'message': 'my name is Luca', 'flags': {'session': False, 'system': False, 'memory': False, 'kb': False}},
    )
    assert response.status_code == 200
    assert response.json()['reply'] == 'ok'


def test_chat_memory_persisted_when_enabled_and_explicit(monkeypatch) -> None:
    persisted: dict[str, str] = {}
    monkeypatch.setattr('app.main.memory_store.clear', lambda: {})
    monkeypatch.setattr('app.main.memory_store.get_summary', lambda: None)

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        return {'reply_text': 'ok', 'memory_facts': {'Name': 'Alice', 'irrelevant': 'x'}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)
    monkeypatch.setattr('app.main.memory_store.upsert_facts', lambda facts: persisted.update(facts) or facts)

    client = TestClient(app)
    response = client.post(
        '/chat',
        json={'message': 'my name is Alice', 'flags': {'session': False, 'system': False, 'memory': True, 'kb': False}},
    )
    assert response.status_code == 200
    assert persisted == {'name': 'Alice'}


def test_chat_memory_not_persisted_for_non_user_message(monkeypatch) -> None:
    monkeypatch.setattr('app.main.memory_store.clear', lambda: {})
    monkeypatch.setattr('app.main.memory_store.get_summary', lambda: None)

    def fake_chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> dict[str, object]:
        return {'reply_text': 'ok', 'memory_facts': {'name': 'Alice'}}

    monkeypatch.setattr('app.main.chat_completion', fake_chat_completion)
    monkeypatch.setattr('app.main.memory_store.upsert_facts', lambda facts: (_ for _ in ()).throw(AssertionError('must not persist')))

    client = TestClient(app)
    response = client.post(
        '/chat',
        json={'message': 'What is the weather today?', 'flags': {'session': False, 'system': False, 'memory': True, 'kb': False}},
    )
    assert response.status_code == 200
