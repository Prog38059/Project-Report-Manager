"""Logging formatter with sensitive data redaction."""

import logging
import re

# Regex for Indian PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
# Regex for potential bank accounts or long numeric sequences (9 to 18 digits)
BANK_ACCOUNT_PATTERN = re.compile(r"\b\d{9,18}\b")
# Regex for key/token strings
AUTH_TOKEN_PATTERN = re.compile(r"(password|secret|token|api_key|key)=([^\s&]+)", re.IGNORECASE)


def mask_pan(pan: str) -> str:
    """Masks a PAN string revealing only the last 4 characters, e.g. XXXXXX123F."""
    if not pan or len(pan) < 5:
        return "****"
    return "X" * (len(pan) - 4) + pan[-4:]


def redact_sensitive_text(text: str) -> str:
    """Redacts sensitive identifiers and tokens from text."""
    if not text:
        return text

    # Redact PAN
    def replace_pan(match: re.Match) -> str:
        val = match.group(0)
        return mask_pan(val)

    redacted = PAN_PATTERN.sub(replace_pan, text)
    redacted = AUTH_TOKEN_PATTERN.sub(r"\1=********", redacted)
    return redacted


class RedactingFormatter(logging.Formatter):
    """Custom logging formatter that strips sensitive details before writing to log."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        return redact_sensitive_text(original)
