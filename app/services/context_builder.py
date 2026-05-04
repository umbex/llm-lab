from app.schemas import LayerFlags


def compose_status(flags: LayerFlags) -> str:
    return (
        f"session {'✓' if flags.session else '✗'} | "
        f"system {'✓' if flags.system else '✗'} | "
        f"memory {'✓' if flags.memory else '✗'} | "
        f"kb {'✓' if flags.kb else '✗'}"
    )


def _window_history(history: list[dict[str, str]], max_history_messages: int) -> list[dict[str, str]]:
    if max_history_messages <= 0:
        return []
    return history[-max_history_messages:]


def build_messages(
    message: str,
    session_enabled: bool,
    session_id: str | None,
    history: list[dict[str, str]],
    system_enabled: bool,
    system_prompt: str | None,
    memory_enabled: bool,
    memory_summary: str | None,
    kb_enabled: bool,
    kb_content: str | None,
    max_history_messages: int,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    if system_enabled and system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    if memory_enabled and memory_summary:
        messages.append({'role': 'system', 'content': f'Persistent memory:\n{memory_summary}'})
    if kb_enabled and kb_content:
        messages.append({'role': 'system', 'content': f'Knowledge base:\n{kb_content}'})

    if session_enabled and session_id:
        history_window = _window_history(history, max_history_messages)
        return [*messages, *history_window, {'role': 'user', 'content': message}]
    return [*messages, {'role': 'user', 'content': message}]
