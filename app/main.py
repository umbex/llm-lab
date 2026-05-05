from pathlib import Path
import threading
import re
import json
import os
from urllib.parse import urlparse

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.schemas import ChatRequest, ChatResponse, MemoryPayload
from app.services.context_builder import build_messages, compose_status
from app.services.kb_store import KBStore
from app.services.openai_client import chat_completion, extract_memory_facts
from app.services.persistent_memory import PersistentMemoryStore
from app.services.session_store import SessionStore

app = FastAPI()
session_store = SessionStore()
memory_store = PersistentMemoryStore(Path('data/memory.json'))
kb_store = KBStore(Path('data/uploads'))
MAX_HISTORY_MESSAGES = 12
STATIC_DIR = Path(__file__).parent / 'static'
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


@app.get('/')
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / 'index.html')


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/runtime')
def runtime_info() -> dict[str, str]:
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    host = urlparse(base_url).hostname or 'openai'
    provider = 'openai' if host.endswith('openai.com') else (host.split('.')[0] if host else 'openai')
    model = os.getenv('MODEL', 'gpt-5.4-mini')
    return {'provider': provider, 'model': model}


@app.post('/chat', response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    history = []
    if payload.flags.session and payload.session_id:
        history = session_store.get_history(payload.session_id)
    messages = build_messages(
        message=payload.message,
        session_enabled=payload.flags.session,
        session_id=payload.session_id,
        history=history,
        system_enabled=payload.flags.system,
        system_prompt=payload.system_prompt,
        memory_enabled=payload.flags.memory,
        memory_summary=memory_store.get_summary(),
        kb_enabled=payload.flags.kb,
        kb_content=kb_store.get_content(),
        max_history_messages=MAX_HISTORY_MESSAGES,
    )
    prompt_bytes = len(json.dumps(messages, ensure_ascii=False).encode('utf-8'))
    reply = chat_completion(messages)
    if payload.flags.memory:
        threading.Thread(
            target=_update_memory_in_background,
            args=(payload.message, reply),
            daemon=True,
        ).start()
    if payload.flags.session and payload.session_id:
        session_store.append_turn(payload.session_id, payload.message, reply)
    return ChatResponse(reply=reply, status=compose_status(payload.flags), prompt_bytes=prompt_bytes)


def _update_memory_in_background(user_message: str, assistant_reply: str) -> None:
    if not _should_extract_memory(user_message):
        return
    try:
        facts = extract_memory_facts(user_message, assistant_reply)
    except Exception:
        return
    if facts:
        memory_store.upsert_facts(facts)


def _should_extract_memory(user_message: str) -> bool:
    text = user_message.lower()
    explicit_patterns = [
        r'\bmy name is\b',
        r'\bi am\b',
        r'\bi work\b',
        r'\bmy work\b',
        r'\bmy role\b',
        r'\bi prefer\b',
        r'\bremember this\b',
        r'\bremember that\b',
        r'\bmemorizz',
        r'\bricord',
        r'\bplease remember\b',
        r'\bstore this\b',
        r'\bmi chiamo\b',
        r'\bsono\b',
        r'\blavoro\b',
        r'\bil mio lavoro\b',
        r'\bil mio ruolo\b',
        r'\bpreferisco\b',
        r'\bricorda questo\b',
        r'\bmemorizza questo\b',
        r'\bsalva questo\b',
        r'\btienilo a mente\b',
    ]
    return any(re.search(pattern, text) for pattern in explicit_patterns)


@app.get('/memory', response_model=MemoryPayload)
def get_memory() -> MemoryPayload:
    return MemoryPayload(facts=memory_store.get_facts())


@app.delete('/memory', response_model=MemoryPayload)
def clear_memory() -> MemoryPayload:
    return MemoryPayload(facts=memory_store.clear())


@app.post('/kb/upload')
async def upload_kb(file: UploadFile = File(...)) -> dict[str, str]:
    content = (await file.read()).decode('utf-8')
    try:
        filename = kb_store.save_markdown(file.filename or 'uploaded.md', content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'filename': filename}


@app.put('/kb/select')
def select_kb(payload: dict[str, str]) -> dict[str, str]:
    filename = payload.get('filename', '')
    try:
        selected = kb_store.set_active_filename(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {'filename': selected}


@app.get('/kb')
def get_kb() -> dict[str, str | None]:
    return {'filename': kb_store.get_active_filename(), 'content': kb_store.get_content()}
