"""Bond file encryption using PBKDF2 key derivation and HMAC-SHA256 stream cipher."""
from __future__ import annotations

import hashlib
import hmac
import os
import struct


_SALT_SIZE = 16
_KEY_SIZE = 32
_NONCE_SIZE = 16
_TAG_SIZE = 32
_ITERATIONS = 600_000
_MAGIC = b"BOND"  # file header


def _derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=_KEY_SIZE)


def _xor_stream(data: bytes, key: bytes, nonce: bytes) -> bytes:
    """XOR-based stream cipher using HMAC-SHA256 as CSPRNG."""
    result = bytearray(len(data))
    block_size = 32
    for i in range(0, len(data), block_size):
        counter = struct.pack(">Q", i // block_size)
        keystream = hmac.new(key, nonce + counter, hashlib.sha256).digest()
        chunk = data[i : i + block_size]
        for j, byte in enumerate(chunk):
            result[i + j] = byte ^ keystream[j]
    return bytes(result)


def encrypt_bytes(data: bytes, password: str) -> bytes:
    salt = os.urandom(_SALT_SIZE)
    nonce = os.urandom(_NONCE_SIZE)
    key = _derive_key(password, salt)

    ciphertext = _xor_stream(data, key, nonce)

    # HMAC for authentication
    tag = hmac.new(key, salt + nonce + ciphertext, hashlib.sha256).digest()

    return _MAGIC + salt + nonce + tag + ciphertext


def decrypt_bytes(encrypted: bytes, password: str) -> bytes:
    if not encrypted.startswith(_MAGIC):
        raise ValueError("Not an encrypted bond file")

    offset = len(_MAGIC)
    salt = encrypted[offset : offset + _SALT_SIZE]
    offset += _SALT_SIZE
    nonce = encrypted[offset : offset + _NONCE_SIZE]
    offset += _NONCE_SIZE
    tag = encrypted[offset : offset + _TAG_SIZE]
    offset += _TAG_SIZE
    ciphertext = encrypted[offset:]

    key = _derive_key(password, salt)

    # Verify authentication
    expected_tag = hmac.new(key, salt + nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected_tag):
        raise ValueError("Invalid password or corrupted file")

    return _xor_stream(ciphertext, key, nonce)
