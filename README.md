# DocOrganizer

DocOrganizer is a local, offline document organizer that watches an inbox folder, extracts document details, and routes files into categorized folders using a local Ollama model.

## Features

- Watches a local inbox folder for new files
- Extracts text with PyMuPDF and OCR fallback
- Uses Ollama to infer category, vendor, dates, and amount
- Moves files into organized category directories
- Stores metadata in SQLite
- Includes a Streamlit viewer for browsing documents

## Project structure

```text
.
├── config.json
├── config.py
├── docorganizer/
│   ├── __init__.py
│   ├── app.py
│   ├── config.py
│   ├── core/
│   ├── processing/
│   └── ui/
├── inbox/
├── organized/
├── main.py
├── requirements.txt
├── viewer.py
└── tests/
```

## Setup

1. Create a Python virtual environment if desired.
2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Start Ollama and ensure the model is available. The default model is `gemma3:4b`.

## Configuration

The app reads configuration from [config.json](config.json) and supports environment overrides:

- `DOCORGANIZER_INBOX_DIR`
- `DOCORGANIZER_ORGANIZED_DIR`
- `DOCORGANIZER_DB_PATH`
- `DOCORGANIZER_MODEL`
- `DOCORGANIZER_CATEGORIES`

Example:

```bash
export DOCORGANIZER_MODEL=gemma3:1b
export DOCORGANIZER_CATEGORIES="Bills,Tax,Identity,Travel,Personal"
```

## Run the organizer

```bash
python3 main.py
```

This starts the file watcher and processes files dropped into the inbox folder.

## Run the UI

```bash
streamlit run viewer.py
```

## Test

```bash
python3 -m pytest -q
```
