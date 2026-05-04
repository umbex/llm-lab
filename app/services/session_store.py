from collections import defaultdict


class SessionStore:
    def __init__(self) -> None:
        self._history: dict[str, list[dict[str, str]]] = defaultdict(list)

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        return list(self._history.get(session_id, []))

    def append_turn(self, session_id: str, user_message: str, assistant_message: str) -> None:
        self._history[session_id].append({'role': 'user', 'content': user_message})
        self._history[session_id].append({'role': 'assistant', 'content': assistant_message})
