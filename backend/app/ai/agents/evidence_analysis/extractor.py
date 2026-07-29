"""
Evidence metadata extraction utilities.
Handles: PDFs, images, audio, video, text exports (WhatsApp, email, screenshots).
"""
import os
import re
import hashlib
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any

from app.ai.logging.logger import AILogger

logger = AILogger("evidence.extractor")

# Map MIME type prefixes → evidence category
_CATEGORY_MAP = {
    "application/pdf": "documentary",
    "image/": "digital",
    "audio/": "digital",
    "video/": "digital",
    "text/": "documentary",
    "message/": "documentary",
}

# Patterns to detect timestamps in filenames and text
_TIMESTAMP_PATTERNS = [
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}",          # ISO-like
    r"\d{2}/\d{2}/\d{4}",                            # DD/MM/YYYY
    r"\d{2}-\d{2}-\d{4}",                            # DD-MM-YYYY
    r"\d{4}\d{2}\d{2}_\d{6}",                        # WhatsApp: 20240115_143022
]


def detect_file_type(path: str) -> str:
    """Return a simplified file type label."""
    ext = os.path.splitext(path)[1].lower()
    mapping = {
        ".pdf": "pdf",
        ".png": "image", ".jpg": "image", ".jpeg": "image",
        ".tiff": "image", ".bmp": "image", ".webp": "image",
        ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".m4a": "audio",
        ".mp4": "video", ".avi": "video", ".mov": "video", ".mkv": "video",
        ".txt": "text", ".csv": "text",
        ".eml": "email", ".msg": "email",
    }
    return mapping.get(ext, "unknown")


def detect_category(path: str) -> str:
    """Categorize evidence as documentary / digital / physical / testimonial."""
    mime, _ = mimetypes.guess_type(path)
    if mime:
        for prefix, category in _CATEGORY_MAP.items():
            if mime.startswith(prefix):
                return category
    file_type = detect_file_type(path)
    if file_type in {"audio", "video"}:
        return "digital"
    return "documentary"


def extract_timestamp_from_filename(filename: str) -> Optional[str]:
    """Try to extract a timestamp from the filename."""
    for pattern in _TIMESTAMP_PATTERNS:
        match = re.search(pattern, filename)
        if match:
            return match.group(0)
    return None


def extract_timestamp_from_text(text: str) -> Optional[str]:
    """Extract the first recognizable timestamp from text content."""
    for pattern in _TIMESTAMP_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def file_hash(path: str) -> str:
    """SHA-256 hash for duplicate detection."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except Exception:
        return ""
    return h.hexdigest()


def extract_file_metadata(path: str) -> Dict[str, Any]:
    """Extract all available metadata from a file."""
    stat = os.stat(path) if os.path.exists(path) else None
    filename = os.path.basename(path)
    ts_from_name = extract_timestamp_from_filename(filename)

    meta: Dict[str, Any] = {
        "filename": filename,
        "extension": os.path.splitext(filename)[1].lower(),
        "size_bytes": stat.st_size if stat else 0,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else None,
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat() if stat else None,
        "timestamp_from_filename": ts_from_name,
    }

    # Try to extract EXIF from images
    if detect_file_type(path) == "image":
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            img = Image.open(path)
            exif_data = img._getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag in ("DateTime", "DateTimeOriginal", "DateTimeDigitized"):
                        meta["exif_datetime"] = str(value)
                        break
        except Exception:
            pass

    return meta
