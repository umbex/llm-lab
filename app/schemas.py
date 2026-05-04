from pydantic import BaseModel, ConfigDict


class LayerFlags(BaseModel):
    session: bool
    system: bool
    memory: bool
    kb: bool


class ChatRequest(BaseModel):
    message: str
    flags: LayerFlags

    # Placeholders for next layers.
    session_id: str | None = None
    system_prompt: str | None = None
    memory_hint: str | None = None
    kb_hint: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    reply: str
    status: str
    prompt_bytes: int


class MemoryPayload(BaseModel):
    facts: dict[str, str]
