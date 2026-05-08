import pytest

from app import auth


def test_password_hash_roundtrip():
    encoded = auth.hash_password("supersecret")
    assert auth.verify_password("supersecret", encoded) is True
    assert auth.verify_password("wrong", encoded) is False


def test_set_and_check_login():
    auth.set_password("anothersecret")
    assert auth.is_password_set() is True
    assert auth.check_login("anothersecret") is True
    assert auth.check_login("nope") is False


def test_short_password_rejected():
    with pytest.raises(ValueError):
        auth.set_password("short")


def test_corrupted_hash_returns_false():
    assert auth.verify_password("x", "garbage") is False
