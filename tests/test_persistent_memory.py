from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.persistent_memory import DEFAULT_MEMORY_FACTS, PersistentMemoryStore


def test_memory_store_initializes_missing_file(tmp_path: Path) -> None:
    store = PersistentMemoryStore(tmp_path / 'memory.json')
    assert store.get_facts() == DEFAULT_MEMORY_FACTS


def test_memory_store_persists_summary(tmp_path: Path) -> None:
    path = tmp_path / 'memory.json'
    store = PersistentMemoryStore(path)
    store.set_facts({'preference': 'concise answers'})

    reloaded = PersistentMemoryStore(path)
    assert reloaded.get_facts() == {'preference': 'concise answers'}
