import json
from pathlib import Path


class KBStore:
    def __init__(
        self,
        upload_dir: Path,
        max_bytes: int = 200_000,
        preferred_default_filename: str = 'AKQA_Work_index.md',
    ) -> None:
        self._upload_dir = upload_dir
        self._max_bytes = max_bytes
        self._preferred_default_filename = preferred_default_filename
        self._active_file = self._upload_dir / '.active_kb.json'
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    def save_markdown(self, filename: str, content: str) -> str:
        if not filename.lower().endswith('.md'):
            raise ValueError('Only markdown (.md) files are supported')
        encoded = content.encode('utf-8')
        if len(encoded) > self._max_bytes:
            raise ValueError('Markdown file is too large')
        path = self._upload_dir / filename
        path.write_text(content, encoding='utf-8')
        self.set_active_filename(filename)
        return filename

    def set_active_filename(self, filename: str) -> str:
        path = self._upload_dir / filename
        if not path.exists() or path.suffix.lower() != '.md':
            raise ValueError('Selected KB file does not exist or is not markdown')
        self._active_file.write_text(json.dumps({'filename': filename}), encoding='utf-8')
        return filename

    def get_active_filename(self) -> str | None:
        if not self._active_file.exists():
            return None
        try:
            data = json.loads(self._active_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return None
        filename = data.get('filename')
        if not isinstance(filename, str):
            return None
        path = self._upload_dir / filename
        if not path.exists() or path.suffix.lower() != '.md':
            return None
        return filename

    def get_content(self) -> str:
        active_filename = self.get_active_filename()
        if active_filename:
            return (self._upload_dir / active_filename).read_text(encoding='utf-8')

        preferred = self._find_preferred_default_file()
        if preferred is not None:
            self.set_active_filename(preferred.name)
            return preferred.read_text(encoding='utf-8')

        files = sorted(self._upload_dir.glob('*.md'))
        if not files:
            return ''
        fallback = files[-1]
        self.set_active_filename(fallback.name)
        return fallback.read_text(encoding='utf-8')

    def _find_preferred_default_file(self) -> Path | None:
        target = self._preferred_default_filename.lower()
        for file in self._upload_dir.glob('*.md'):
            if file.name.lower() == target:
                return file
        return None
