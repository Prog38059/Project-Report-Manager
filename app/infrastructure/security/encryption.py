"""Local encryption provider implementing ADR-022.

Protects sensitive identifiers (such as PAN and statutory registration values)
at rest using authenticated Fernet encryption, with master key protected by
Windows Data Protection API (DPAPI).
"""

import base64
import hashlib
import os
import sys
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet

from app.common.exceptions import SecurityError


def _dpapi_protect(data: bytes) -> bytes:
    """Encrypt data using Windows DPAPI (CryptProtectData)."""
    if sys.platform != "win32":
        return data

    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    in_blob = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
    out_blob = DATA_BLOB()

    # CRYPTPROTECT_UI_FORBIDDEN = 0x1
    success = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        "PRM_MasterKey",
        None,
        None,
        None,
        0x1,
        ctypes.byref(out_blob),
    )
    if not success:
        raise SecurityError("Failed to protect master key using Windows DPAPI.")

    encrypted_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    kernel32.LocalFree(out_blob.pbData)
    return encrypted_bytes


def _dpapi_unprotect(data: bytes) -> bytes:
    """Decrypt data using Windows DPAPI (CryptUnprotectData)."""
    if sys.platform != "win32":
        return data

    import ctypes
    from ctypes import wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    in_blob = DATA_BLOB(len(data), ctypes.create_string_buffer(data, len(data)))
    out_blob = DATA_BLOB()

    success = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        None,
        None,
        None,
        0x1,
        ctypes.byref(out_blob),
    )
    if not success:
        raise SecurityError("Failed to unprotect master key using Windows DPAPI.")

    decrypted_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
    kernel32.LocalFree(out_blob.pbData)
    return decrypted_bytes


class EncryptionService:
    """Handles field-level encryption, decryption, and secure hashing."""

    def __init__(self, key_file_path: Optional[Path] = None, fixed_key: Optional[bytes] = None) -> None:
        if fixed_key:
            self._fernet = Fernet(fixed_key)
        elif key_file_path:
            self._fernet = Fernet(self._load_or_create_key(key_file_path))
        else:
            # Ephemeral fallback for test stubs
            self._fernet = Fernet(Fernet.generate_key())

    @staticmethod
    def _load_or_create_key(key_file_path: Path) -> bytes:
        """Load protected key from disk or generate a new one protected via DPAPI."""
        key_file_path.parent.mkdir(parents=True, exist_ok=True)
        if key_file_path.exists():
            protected_key = key_file_path.read_bytes()
            raw_key = _dpapi_unprotect(protected_key)
            return raw_key
        else:
            raw_key = Fernet.generate_key()
            protected_key = _dpapi_protect(raw_key)
            key_file_path.write_bytes(protected_key)
            return raw_key

    def encrypt(self, plaintext: str) -> str:
        """Encrypts a plaintext string into a safe base64 URL-encoded token."""
        if plaintext is None:
            return ""
        encrypted_bytes = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted_bytes.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypts a base64 ciphertext back to plaintext."""
        if not ciphertext:
            return ""
        decrypted_bytes = self._fernet.decrypt(ciphertext.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")

    @staticmethod
    def compute_search_hash(value: str) -> str:
        """Computes a normalized SHA-256 hash for searchable duplicate detection."""
        if not value:
            return ""
        normalized = value.strip().upper()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
