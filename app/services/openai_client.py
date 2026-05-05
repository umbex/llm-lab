import os
import json
from typing import Any, TypedDict

from openai import OpenAI


class UnifiedCompletion(TypedDict):
    reply_text: str
    memory_facts: dict[str, str]


def chat_completion(messages: list[dict[str, str]], memory_enabled: bool) -> UnifiedCompletion:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL'),
    )
    model = os.getenv('MODEL', 'gpt-5.4-mini')
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                'role': 'system',
                'content': (
                    'Return only valid JSON with this exact shape: '
                    '{"reply_text":"string","memory_facts":{"key":"value"}}. '
                    'reply_text must contain the full assistant answer for the user. '
                    'memory_facts must include only explicit user-profile facts about identity, '
                    'work/job/role, preferences, or explicit user requests to remember something. '
                    'Never include generic world facts, assistant claims, or unrelated task content. '
                    'If uncertain, use an empty object for memory_facts.'
                ),
            },
            *messages,
        ],
        response_format={'type': 'json_object'},
    )
    return _parse_unified_completion(response.choices[0].message.content or '{}', memory_enabled=memory_enabled)


def _parse_unified_completion(content: str, memory_enabled: bool) -> UnifiedCompletion:
    try:
        payload: dict[str, Any] = json.loads(content)
    except Exception:
        return {
            'reply_text': content.strip(),
            'memory_facts': {},
        }

    reply_text = payload.get('reply_text')
    if not isinstance(reply_text, str):
        reply_text = ''

    facts = payload.get('memory_facts')
    if not isinstance(facts, dict) or not memory_enabled:
        return {'reply_text': reply_text, 'memory_facts': {}}

    clean: dict[str, str] = {}
    for key, value in facts.items():
        if isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip():
            clean[key.strip()] = value.strip()
    return {'reply_text': reply_text, 'memory_facts': clean}
