from pathlib import Path

import typer

from .config import settings
from .indexer import index_vault

app = typer.Typer(help="Akasha — personal knowledge base tools")


@app.command()
def index(
    force: bool = typer.Option(False, "--force", "-f", help="Re-index all notes, even unchanged"),
    vault: Path = typer.Option(None, "--vault", "-v", help="Vault path (overrides config)"),
):
    """Index all markdown files in the vault."""
    vault_path = vault or settings.vault_path
    print(f"Vault: {vault_path}")

    if not vault_path.exists():
        print(f"Error: vault not found at {vault_path}")
        raise typer.Exit(1)

    indexed, skipped = index_vault(vault_path, force=force)
    print(f"\nDone — {indexed} indexed, {skipped} unchanged")


@app.command()
def ingest(
    file: Path = typer.Argument(..., help="Path to .epub or .pdf file"),
    vault: Path = typer.Option(None, "--vault", "-v", help="Vault path (overrides config)"),
    no_index: bool = typer.Option(False, "--no-index", help="Skip re-indexing after ingestion"),
):
    """Ingest an ebook into the vault as structured notes."""
    if not file.exists():
        print(f"Error: file not found: {file}")
        raise typer.Exit(1)

    if not settings.anthropic_api_key:
        print("Error: AKASHA_ANTHROPIC_API_KEY is not set in .env")
        raise typer.Exit(1)

    vault_path = vault or settings.vault_path
    print(f"Ingesting: {file.name}")
    print(f"Vault: {vault_path}")
    print()

    from .ingest import ingest as _ingest

    def on_progress(msg: str):
        print(f"  ✓ {msg}")

    try:
        book_note = _ingest(file, vault_path=vault_path, on_progress=on_progress)
    except Exception as e:
        print(f"\nError: {e}")
        raise typer.Exit(1)

    print(f"\nBook note: {book_note.relative_to(vault_path)}")

    if not no_index:
        print("\nIndexing new notes...")
        indexed, skipped = index_vault(vault_path)
        print(f"Done — {indexed} indexed, {skipped} unchanged")


def main():
    app()


def index_main():
    typer.run(index)


def ingest_main():
    typer.run(ingest)
