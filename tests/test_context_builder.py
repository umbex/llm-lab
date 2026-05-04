from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import LayerFlags
from app.services.context_builder import build_messages, compose_status


def test_build_messages_respects_full_block_order() -> None:
    messages = build_messages(
        message='current input',
        session_enabled=True,
        session_id='s1',
        history=[
            {'role': 'user', 'content': 'old-user'},
            {'role': 'assistant', 'content': 'old-assistant'},
        ],
        system_enabled=True,
        system_prompt='System role',
        memory_enabled=True,
        memory_summary='Memory summary',
        kb_enabled=True,
        kb_content='KB content',
        max_history_messages=10,
    )

    assert messages == [
        {'role': 'system', 'content': 'System role'},
        {'role': 'system', 'content': 'Persistent memory:\nMemory summary'},
        {'role': 'system', 'content': 'Knowledge base:\nKB content'},
        {'role': 'user', 'content': 'old-user'},
        {'role': 'assistant', 'content': 'old-assistant'},
        {'role': 'user', 'content': 'current input'},
    ]


def test_build_messages_applies_sliding_window_to_history() -> None:
    messages = build_messages(
        message='latest',
        session_enabled=True,
        session_id='s1',
        history=[
            {'role': 'user', 'content': 'u1'},
            {'role': 'assistant', 'content': 'a1'},
            {'role': 'user', 'content': 'u2'},
            {'role': 'assistant', 'content': 'a2'},
        ],
        system_enabled=False,
        system_prompt=None,
        memory_enabled=False,
        memory_summary=None,
        kb_enabled=False,
        kb_content=None,
        max_history_messages=2,
    )

    assert messages == [
        {'role': 'user', 'content': 'u2'},
        {'role': 'assistant', 'content': 'a2'},
        {'role': 'user', 'content': 'latest'},
    ]


def test_compose_status() -> None:
    flags = LayerFlags(session=True, system=False, memory=True, kb=False)
    assert compose_status(flags) == 'session ✓ | system ✗ | memory ✓ | kb ✗'
