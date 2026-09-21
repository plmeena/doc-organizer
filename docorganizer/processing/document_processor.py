import json
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

import fitz
from watchdog.events import FileSystemEventHandler

from docorganizer.config import get_config

CONFIG = get_config()
INBOX = CONFIG["inbox_dir"]
ORGANIZED = CONFIG["organized_dir"]
DB_PATH = CONFIG["db_path"]
MODEL = CONFIG["model"]
CATEGORIES = CONFIG["categories"]

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("Tip: pip install pytesseract pillow and brew install tesseract for scanned docs")

import ollama


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        category TEXT,
        vendor TEXT,
        doc_date TEXT,
        expiry_date TEXT,
        amount TEXT,
        status TEXT,
        filepath TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()


def get_text(path: Path) -> str:
    """Extract text with OCR fallback for scanned docs like DL/passport."""
    try:
        if path.suffix.lower() == ".pdf":
            doc = fitz.open(path)
            text = "".join([p.get_text() for p in doc[:2]])
            if len(text.strip()) > 50:
                return text[:2000]

            if OCR_AVAILABLE:
                print(f"  No embedded text in {path.name}, trying OCR...")
                ocr_results = []
                for i in range(min(2, len(doc))):
                    pix = doc[i].get_pixmap(dpi=300)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    txt = pytesseract.image_to_string(img)
                    ocr_results.append(txt)
                    del pix, img
                full = "\n".join(ocr_results)
                print(f"  OCR extracted {len(full)} chars")
                return full[:2000]
            else:
                print("  Install pytesseract for scanned docs")
                return ""

        elif path.suffix.lower() in [".txt", ".md"]:
            return path.read_text()[:2000]
        elif path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
            if OCR_AVAILABLE:
                img = Image.open(path)
                return pytesseract.image_to_string(img)[:2000]
    except Exception as e:
        print(f"Read error: {e}")
    return ""


def extract_attributes(text: str, filename: str) -> dict:
    default = {"category": "Personal", "vendor": "Unknown", "doc_date": "NONE", "expiry_date": "NONE", "amount": "NONE"}
    if not text.strip():
        return default

    prompt = f"""Analyze this document (may be OCR from ID) and return ONLY valid JSON.
Fields:
- category: one of {', '.join(CATEGORIES)}
- vendor: issuer name (e.g. Texas DPS, PG&E)
- doc_date: YYYY-MM-DD or NONE. Look for: Iss, Issued, Issue Date, 4a Iss
- expiry_date: YYYY-MM-DD or NONE. Look for: Exp, Expires, Expiry, Valid until, 4b Exp
- amount: dollar value or NONE

Handle OCR noise. Dates may be MM/DD/YYYY - convert to YYYY-MM-DD.

Filename: {filename}
Content:
{text[:1500]}

JSON:"""
    try:
        res = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        out = res['message']['content'].strip()
        m = re.search(r'\{.*\}', out, re.DOTALL)
        if m:
            out = m.group(0)
        data = json.loads(out)
        for k in default:
            if k not in data:
                data[k] = default[k]
        for k in ["doc_date", "expiry_date"]:
            if not data[k] or str(data[k]).lower() in ["none", "n/a", "unknown"]:
                data[k] = "NONE"
        return data
    except Exception as e:
        print(f"Extract error: {e}")
        return default


def get_status(expiry: str) -> str:
    if not expiry or expiry == "NONE":
        return "No Expiry"
    try:
        exp = datetime.strptime(expiry, "%Y-%m-%d").date()
        today = datetime.now().date()
        delta = (exp - today).days
        if delta < 0:
            return "Expired"
        if delta <= 30:
            return "Expiring Soon"
        return "Valid"
    except Exception:
        return "No Expiry"


class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        time.sleep(1)
        if not path.exists() or path.name.startswith("._"):
            return

        print(f"\nProcessing: {path.name}")
        text = get_text(path)
        attrs = extract_attributes(text, path.name)
        status = get_status(attrs["expiry_date"])

        dest_dir = ORGANIZED / attrs["category"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / path.name
        if dest_path.exists():
            stem = dest_path.stem
            dest_path = dest_dir / f"{stem}_{datetime.now().strftime('%H%M%S')}{dest_path.suffix}"

        import shutil
        shutil.move(str(path), str(dest_path))

        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO documents
            (filename, category, vendor, doc_date, expiry_date, amount, status, filepath, created_at)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (path.name, attrs["category"], attrs["vendor"], attrs["doc_date"],
             attrs["expiry_date"], attrs["amount"], status, str(dest_path),
             datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f" -> {attrs['category']} | Doc: {attrs['doc_date']} | Exp: {attrs['expiry_date']} | {status}")
