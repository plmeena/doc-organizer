"""Processing package for DocOrganizer."""

from .document_processor import Handler, extract_attributes, get_status, get_text, init_db

__all__ = [
    "Handler",
    "extract_attributes",
    "get_status",
    "get_text",
    "init_db",
]
