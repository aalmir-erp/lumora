import pytest

from app import settings_store


def test_db_set_and_get(monkeypatch):
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    settings_store.set_value("META_ACCESS_TOKEN", "from-db")
    assert settings_store.get("META_ACCESS_TOKEN") == "from-db"


def test_env_takes_precedence_over_db(monkeypatch):
    settings_store.set_value("META_ACCESS_TOKEN", "from-db")
    monkeypatch.setenv("META_ACCESS_TOKEN", "from-env")
    assert settings_store.get("META_ACCESS_TOKEN") == "from-env"


def test_default_when_unset(monkeypatch):
    monkeypatch.delenv("UNSET_KEY", raising=False)
    assert settings_store.get("UNSET_KEY", "fallback") == "fallback"


def test_all_for_admin_marks_provenance(monkeypatch):
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("META_PHONE_NUMBER_ID", "envphoneid")
    settings_store.set_value("HANDOFF_EMAIL", "info@test.com")

    rows = {r["key"]: r for r in settings_store.all_for_admin()}
    assert rows["META_PHONE_NUMBER_ID"]["source"] == "env"
    assert rows["HANDOFF_EMAIL"]["source"] == "db"
    assert rows["META_ACCESS_TOKEN"]["source"] == "unset"


def test_secret_masking():
    settings_store.set_value("ANTHROPIC_API_KEY", "sk-1234567890abcdef")
    rows = {r["key"]: r for r in settings_store.all_for_admin()}
    masked = rows["ANTHROPIC_API_KEY"]["masked"]
    assert masked.startswith("sk-1")
    assert masked.endswith("cdef")
    assert "•" in masked
