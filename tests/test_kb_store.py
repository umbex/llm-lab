from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.kb_store import KBStore


def test_kb_store_save_and_load_markdown(tmp_path: Path) -> None:
    store = KBStore(tmp_path)
    store.save_markdown('guide.md', '# Title\n\nBody')
    assert store.get_content() == '# Title\n\nBody'


def test_kb_store_rejects_non_markdown_filename(tmp_path: Path) -> None:
    store = KBStore(tmp_path)
    try:
        store.save_markdown('guide.txt', 'nope')
    except ValueError as exc:
        assert 'markdown' in str(exc).lower()
    else:
        raise AssertionError('Expected ValueError for non-markdown file')


def test_kb_store_uses_selected_active_file(tmp_path: Path) -> None:
    store = KBStore(tmp_path)
    store.save_markdown('a.md', 'A')
    store.save_markdown('z.md', 'Z')
    store.set_active_filename('a.md')
    assert store.get_active_filename() == 'a.md'
    assert store.get_content() == 'A'


def test_kb_store_prefers_akqa_default_when_no_active_file(tmp_path: Path) -> None:
    store = KBStore(tmp_path)
    store.save_markdown('other.md', 'Other')
    store.save_markdown('AKQA_Work_Index.md', 'AKQA')
    store._active_file.unlink(missing_ok=True)
    assert store.get_content() == 'AKQA'
    assert store.get_active_filename() == 'AKQA_Work_Index.md'
