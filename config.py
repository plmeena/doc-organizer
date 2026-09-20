import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def _read_config_file() -> dict:
    if not CONFIG_PATH.exists():
        return {}

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _resolve_path(value, default: Path) -> Path:
    if value is None:
        return default
    value = str(value).strip()
    if not value:
        return default
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    return path


def get_config() -> dict:
    defaults = {
        "base_dir": BASE_DIR,
        "inbox_dir": _resolve_path("inbox", BASE_DIR / "inbox"),
        "organized_dir": _resolve_path("organized", BASE_DIR / "organized"),
        "db_path": _resolve_path("docorganizer.db", BASE_DIR / "docorganizer.db"),
        "model": "gemma3:4b",
        "categories": [
            "Bills", "Tax", "Work", "Identity", "Financial", "Legal", "Health",
            "Immigration", "Education", "Travel", "Medical", "Contracts", "Receipts",
            "Personal"
        ],
    }

    file_config = _read_config_file()
    merged = defaults.copy()
    merged.update({
        "inbox_dir": file_config.get("inbox_dir", defaults["inbox_dir"]),
        "organized_dir": file_config.get("organized_dir", defaults["organized_dir"]),
        "db_path": file_config.get("db_path", defaults["db_path"]),
        "model": file_config.get("model", defaults["model"]),
        "categories": file_config.get("categories", defaults["categories"]),
    })

    env_overrides = {
        "inbox_dir": os.getenv("DOCORGANIZER_INBOX_DIR"),
        "organized_dir": os.getenv("DOCORGANIZER_ORGANIZED_DIR"),
        "db_path": os.getenv("DOCORGANIZER_DB_PATH"),
        "model": os.getenv("DOCORGANIZER_MODEL"),
        "categories": os.getenv("DOCORGANIZER_CATEGORIES"),
    }

    for key, value in env_overrides.items():
        if value not in (None, ""):
            if key == "categories":
                merged[key] = [item.strip() for item in value.split(",") if item.strip()]
            else:
                merged[key] = value

    merged["base_dir"] = BASE_DIR
    merged["inbox_dir"] = _resolve_path(merged["inbox_dir"], defaults["inbox_dir"])
    merged["organized_dir"] = _resolve_path(merged["organized_dir"], defaults["organized_dir"])
    merged["db_path"] = _resolve_path(merged["db_path"], defaults["db_path"])
    if not isinstance(merged["categories"], list) or not merged["categories"]:
        merged["categories"] = defaults["categories"]

    return merged
