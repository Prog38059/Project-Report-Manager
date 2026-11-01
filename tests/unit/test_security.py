"""Unit tests for encryption, search hashes, and log redaction."""

from app.infrastructure.security.encryption import EncryptionService
from app.infrastructure.security.redaction import redact_sensitive_text, mask_pan


def test_encryption_roundtrip(encryption_service: EncryptionService):
    original_pan = "ABCDE1234F"
    encrypted = encryption_service.encrypt(original_pan)
    assert encrypted != original_pan

    decrypted = encryption_service.decrypt(encrypted)
    assert decrypted == original_pan


def test_search_hash(encryption_service: EncryptionService):
    pan1 = "abcde1234f"
    pan2 = "ABCDE1234F"
    # Case insensitive normalized hash
    assert encryption_service.compute_search_hash(pan1) == encryption_service.compute_search_hash(pan2)
    assert len(encryption_service.compute_search_hash(pan1)) == 64


def test_mask_pan():
    assert mask_pan("ABCDE1234F") == "XXXXXX234F"
    assert mask_pan("A") == "****"


def test_redact_sensitive_text():
    sample_log = "Saving entity member with PAN ABCDE1234F and password=secret123 to database."
    redacted = redact_sensitive_text(sample_log)
    assert "ABCDE1234F" not in redacted
    assert "secret123" not in redacted
    assert "XXXXXX234F" in redacted
    assert "password=********" in redacted
