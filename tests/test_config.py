from pathlib import Path

import importlib

import src.config as config_module


def test_get_config_returns_default_paths(monkeypatch):
    monkeypatch.delenv("DOCORGANIZER_INBOX_DIR", raising=False)
    monkeypatch.delenv("DOCORGANIZER_ORGANIZED_DIR", raising=False)
    monkeypatch.delenv("DOCORGANIZER_DB_PATH", raising=False)
    monkeypatch.delenv("DOCORGANIZER_MODEL", raising=False)
    monkeypatch.delenv("DOCORGANIZER_CATEGORIES", raising=False)

    importlib.reload(config_module)
    cfg = config_module.get_config()

    assert cfg["inbox_dir"] == Path("/Users/plmeena/Developer/projects/doc-organizer/inbox")
    assert cfg["organized_dir"] == Path("/Users/plmeena/Developer/projects/doc-organizer/organized")
    assert cfg["db_path"] == Path("/Users/plmeena/Developer/projects/doc-organizer/docorganizer.db")
    assert cfg["model"] == "gemma3:4b"
    assert "Bills" in cfg["categories"]


def test_get_config_respects_env_overrides(monkeypatch):
    monkeypatch.setenv("DOCORGANIZER_INBOX_DIR", "/tmp/custom_inbox")
    monkeypatch.setenv("DOCORGANIZER_ORGANIZED_DIR", "/tmp/custom_organized")
    monkeypatch.setenv("DOCORGANIZER_DB_PATH", "/tmp/custom_db.sqlite")
    monkeypatch.setenv("DOCORGANIZER_MODEL", "custom-model:latest")
    monkeypatch.setenv("DOCORGANIZER_CATEGORIES", "Bills,Travel,Personal")

    importlib.reload(config_module)
    cfg = config_module.get_config()

    assert cfg["inbox_dir"] == Path("/tmp/custom_inbox")
    assert cfg["organized_dir"] == Path("/tmp/custom_organized")
    assert cfg["db_path"] == Path("/tmp/custom_db.sqlite")
    assert cfg["model"] == "custom-model:latest"
    assert cfg["categories"] == ["Bills", "Travel", "Personal"]
