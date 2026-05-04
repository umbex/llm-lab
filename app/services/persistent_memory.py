import json
import threading
from pathlib import Path

DEFAULT_MEMORY_FACTS = {'name': 'Mario Kart'}


class PersistentMemoryStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._path.write_text(json.dumps({'facts': DEFAULT_MEMORY_FACTS}), encoding='utf-8')

    def _read_facts_unlocked(self) -> dict[str, str]:
        try:
            data = json.loads(self._path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return dict(DEFAULT_MEMORY_FACTS)
        facts = data.get('facts')
        if not isinstance(facts, dict):
            return dict(DEFAULT_MEMORY_FACTS)
        clean: dict[str, str] = {}
        for key, value in facts.items():
            if not isinstance(key, str) or not isinstance(value, str):
                continue
            key_clean = key.strip().lower().replace(' ', '_')
            value_clean = value.strip()
            if key_clean and value_clean:
                clean[key_clean] = value_clean
        return clean

    def get_facts(self) -> dict[str, str]:
        with self._lock:
            return self._read_facts_unlocked()

    def get_summary(self) -> str:
        facts = self.get_facts()
        return '\n'.join(f'{key}: {value}' for key, value in facts.items())

    def upsert_facts(self, new_facts: dict[str, str]) -> dict[str, str]:
        with self._lock:
            current = self._read_facts_unlocked()
            for key, value in new_facts.items():
                if not key or not value:
                    continue
                normalized_key = key.strip().lower().replace(' ', '_')
                normalized_value = value.strip()
                if normalized_key and normalized_value:
                    current[normalized_key] = normalized_value
            self._path.write_text(json.dumps({'facts': current}), encoding='utf-8')
            return current

    def clear(self) -> dict[str, str]:
        with self._lock:
            self._path.write_text(json.dumps({'facts': {}}), encoding='utf-8')
            return {}

    def set_facts(self, facts: dict[str, str]) -> dict[str, str]:
        with self._lock:
            self._path.write_text(json.dumps({'facts': facts}), encoding='utf-8')
            return facts
