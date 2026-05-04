# Agent Evolution Lab

Minimal Dockerized FastAPI app to demonstrate progressive LLM context layers.

## Quick Start (GitHub)

Clone the repository:

```bash
git clone https://github.com/umbex/llm-lab.git
cd llm-lab
```

Create environment file:

```bash
cp .env.example .env
```

Edit `.env` and set at least:
- `OPENAI_API_KEY`
- (optional) `MODEL`
- (optional) `OPENAI_BASE_URL`

Run with Docker:

```bash
docker-compose up --build
```

Open the app:
- `http://localhost:3000`

How to use:
- Enable one or more context layers from the sidebar (`Session`, `System`, `Persistent Memory`, `Knowledge Base`)
- Send the same prompt with different layer combinations
- Compare `Prompt size (bytes)` to see context growth

## What it shows

Layer toggles in the UI:
- Layer 0: Stateless LLM
- Layer 1: Session Memory
- Layer 2: System Prompt
- Layer 3: Persistent Memory
- Layer 4: Knowledge Base (.md)

Prompt block order in backend:
1. System Prompt
2. Persistent Memory Summary
3. Knowledge Base Content
4. Session History (sliding window)
5. Current User Input

## Environment

Copy and edit `.env.example`:

```bash
cp .env.example .env
```

Required vars:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (default OpenAI API base)
- `MODEL`

## Local Run

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 3000
```

Open:
- `http://localhost:3000`
- Health check: `http://localhost:3000/health`

## Docker Run

Preferred command:

```bash
docker compose up --build
```

Fallback if compose plugin is missing:

```bash
docker-compose up --build
```

Service details:
- app port: `3000`
- volume mount: `./data:/app/data`

## API Reference

### `POST /chat`

Request body:

```json
{
  "message": "User input",
  "flags": {
    "session": true,
    "system": true,
    "memory": true,
    "kb": true
  },
  "session_id": "optional-session-id",
  "system_prompt": "optional system prompt"
}
```

Response:

```json
{
  "reply": "Assistant output",
  "status": "session ✓ | system ✓ | memory ✓ | kb ✓"
}
```

### `GET /memory`
Reads persistent memory summary.

### `PUT /memory`
Updates persistent memory summary.

### `POST /kb/upload`
Uploads a markdown file (`.md`) into `data/uploads`.

### `GET /kb`
Returns current KB content.

## Layer-by-layer sample payloads

Layer 0 only (stateless):

```json
{
  "message": "Explain this app in one sentence.",
  "flags": {"session": false, "system": false, "memory": false, "kb": false}
}
```

Layer 1 (session on):

```json
{
  "message": "What did I ask before?",
  "session_id": "demo-session",
  "flags": {"session": true, "system": false, "memory": false, "kb": false}
}
```

Layer 2 (system on):

```json
{
  "message": "Teach me this simply.",
  "system_prompt": "You are a strict tutor. Be concise.",
  "flags": {"session": false, "system": true, "memory": false, "kb": false}
}
```

Layer 3 (persistent memory on):

```json
{
  "message": "Use what you know about me.",
  "flags": {"session": false, "system": false, "memory": true, "kb": false}
}
```

Layer 4 (kb on):

```json
{
  "message": "Answer from the uploaded notes.",
  "flags": {"session": false, "system": false, "memory": false, "kb": true}
}
```

## Troubleshooting

- `ModuleNotFoundError` / missing packages:
  - Re-run `./.venv/bin/pip install -r requirements.txt`
- `Form data requires "python-multipart"`:
  - Ensure `python-multipart` is installed via requirements
- Empty memory in UI:
  - Check `data/memory.json` exists and is writable
- KB not applied:
  - Upload a `.md` file via UI or `POST /kb/upload`, then verify `GET /kb`
- `docker compose` not found:
  - Use `docker-compose` fallback command
- No model replies:
  - Validate `.env` contains a valid `OPENAI_API_KEY` and reachable `OPENAI_BASE_URL`

## Test

```bash
./.venv/bin/pytest tests/test_context_builder.py tests/test_chat_api.py tests/test_kb_store.py tests/test_persistent_memory.py tests/test_smoke.py -q
```
