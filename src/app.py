import time
from pathlib import Path

from watchdog.observers import Observer

from src.config import get_config
from src.processing.document_processor import Handler, init_db

CONFIG = get_config()
BASE_DIR = CONFIG["base_dir"]
INBOX = CONFIG["inbox_dir"]
ORGANIZED = CONFIG["organized_dir"]
DB_PATH = CONFIG["db_path"]
MODEL = CONFIG["model"]


def main() -> None:
    init_db()
    INBOX.mkdir(parents=True, exist_ok=True)
    ORGANIZED.mkdir(parents=True, exist_ok=True)
    print(f"DocOrganizer v2.1 watching {INBOX}")
    print(f"DB: {DB_PATH}")
    print(f"Model: {MODEL} | OCR: {'enabled' if True else 'install pytesseract for scans'}")
    print("Make sure: ollama serve is running in another terminal\n")

    observer = Observer()
    observer.schedule(Handler(), str(INBOX), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
