import os
from typing import Any

from openai import OpenAI


def chat_completion(messages: list[dict[str, str]]) -> str:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        base_url=os.getenv('OPENAI_BASE_URL'),
    )
    model = os.getenv('MODEL', 'gpt-5.4-mini')
    response = client.chat.completions.create(model=model, messages=messages)

    content = response.choices[0].message.content
    return content or ''


def extract_memory_facts(user_message: str, assistant_reply: str) -> dict[str, str]:
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
                    'Extract ONLY explicit user-profile facts from the conversation. '
                    'Allowed facts are strictly about: user identity, user work/job/role, '
                    'user preferences, or explicit user requests to remember information. '
                    'Do NOT store generic world facts, assistant claims, or task content not about the user. '
                    'If uncertain or not explicit, return empty facts. '
                    'Return only JSON object with string key:value pairs under "facts". '
                    'If no useful facts, return {"facts":{}}.'
                ),
            },
            {
                'role': 'user',
                'content': f'User: {user_message}\nAssistant: {assistant_reply}',
            },
        ],
        response_format={'type': 'json_object'},
    )
    content = response.choices[0].message.content or '{}'
    try:
        import json

        payload: dict[str, Any] = json.loads(content)
    except Exception:
        return {}
    facts = payload.get('facts')
    if not isinstance(facts, dict):
        return {}
    clean: dict[str, str] = {}
    for key, value in facts.items():
        if isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip():
            clean[key.strip()] = value.strip()
    return clean
