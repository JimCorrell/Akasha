from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import settings
from . import indexer


class _VaultHandler(FileSystemEventHandler):
    def _should_handle(self, src_path: str) -> bool:
        path = Path(src_path)
        return (
            path.suffix == ".md"
            and not indexer._is_hidden(path)
        )

    def on_modified(self, event):
        if not event.is_directory and self._should_handle(event.src_path):
            path = Path(event.src_path)
            print(f"Re-indexing: {path.name}")
            indexer.index_note(path)

    def on_created(self, event):
        self.on_modified(event)

    def on_deleted(self, event):
        if not event.is_directory and Path(event.src_path).suffix == ".md":
            path = Path(event.src_path)
            print(f"Removing from index: {path.name}")
            indexer.remove_note(path)


def start_watcher() -> Observer:
    observer = Observer()
    observer.schedule(_VaultHandler(), str(settings.vault_path), recursive=True)
    observer.start()
    print(f"Watching vault: {settings.vault_path}")
    return observer
