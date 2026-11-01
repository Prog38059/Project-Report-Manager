"""Integration tests for FileStore attachment management."""

from pathlib import Path
import pytest
import uuid

from app.common.exceptions import StorageError
from app.infrastructure.storage.file_store import FileStore


def test_file_store_lifecycle_and_hash(file_store: FileStore, temp_dir: Path):
    # 1. Create a dummy file
    sample_file = temp_dir / "partnership_deed.pdf"
    sample_file.write_bytes(b"%PDF-1.4 sample partnership deed content for test")

    # 2. Store attachment for an entity (Resolving Gap B-1: no project needed)
    entity_id = uuid.uuid4()
    rel_path, sha_hash, file_size = file_store.store_file(
        source_path=sample_file,
        entity_id=entity_id,
        file_category="LEGAL_DEED",
    )

    assert "entities" in rel_path
    assert str(entity_id) in rel_path
    assert file_size == len(b"%PDF-1.4 sample partnership deed content for test")
    assert len(sha_hash) == 64

    # 3. Verify file on disk matches hash
    assert file_store.verify_file_hash(rel_path, sha_hash) is True
    assert file_store.verify_file_hash(rel_path, "wrong_hash") is False

    # 4. Path traversal guard
    with pytest.raises(StorageError, match="Path traversal detected"):
        file_store.get_absolute_path("../../windows/system32/cmd.exe")


def test_filename_sanitization():
    assert FileStore.sanitize_filename("valid_doc.pdf") == "valid_doc.pdf"
    sanitized = FileStore.sanitize_filename("../../dangerous/file:name*?.pdf")
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert ":" not in sanitized
