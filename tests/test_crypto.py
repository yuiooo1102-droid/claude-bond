import pytest

from claude_bond.utils.crypto import decrypt_bytes, encrypt_bytes


def test_encrypt_decrypt_roundtrip():
    data = b"Hello, this is a test of bond encryption!"
    password = "test-password-123"
    encrypted = encrypt_bytes(data, password)
    decrypted = decrypt_bytes(encrypted, password)
    assert decrypted == data


def test_encrypted_starts_with_magic():
    encrypted = encrypt_bytes(b"test", "pass")
    assert encrypted[:4] == b"BOND"


def test_wrong_password_fails():
    encrypted = encrypt_bytes(b"secret data", "correct-password")
    with pytest.raises(ValueError, match="Invalid password"):
        decrypt_bytes(encrypted, "wrong-password")


def test_corrupted_data_fails():
    encrypted = encrypt_bytes(b"test", "pass")
    corrupted = encrypted[:20] + b"\x00" * 10 + encrypted[30:]
    with pytest.raises(ValueError, match="Invalid password"):
        decrypt_bytes(corrupted, "pass")


def test_not_encrypted_file_fails():
    with pytest.raises(ValueError, match="Not an encrypted"):
        decrypt_bytes(b"PK\x03\x04 regular zip data", "pass")
