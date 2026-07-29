"""
File classification and Case Workspace builder.
Classifies files by extension into legal_document / image / video / audio /
chat / email / spreadsheet / text / unknown.
"""
import os
import uuid
import mimetypes
from typing import List, Tuple, Dict, Any

from app.ai.orchestrator.state import CaseFile, CaseWorkspace, FileClassificationLabel
from app.ai.agents.evidence_analysis.extractor import file_hash

# Extension → classification
_EXT_MAP: Dict[str, FileClassificationLabel] = {
    # Legal documents
    ".pdf": "legal_document",
    ".doc": "legal_document", ".docx": "legal_document",
    ".rtf": "legal_document",
    # Images
    ".jpg": "image", ".jpeg": "image", ".png": "image",
    ".webp": "image", ".bmp": "image", ".tiff": "image", ".tif": "image",
    # Video
    ".mp4": "video", ".mov": "video", ".avi": "video",
    ".mkv": "video", ".webm": "video",
    # Audio
    ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
    ".ogg": "audio",
    # Chat exports
    ".txt": "text",   # refined below for WhatsApp/chat patterns
    # Email
    ".eml": "email", ".msg": "email",
    # Spreadsheets
    ".csv": "spreadsheet", ".xlsx": "spreadsheet", ".xls": "spreadsheet",
}

# Filenames that suggest chat exports
_CHAT_PATTERNS = ("whatsapp", "chat", "telegram", "signal", "messenger")


def classify_file(filename: str) -> FileClassificationLabel:
    ext = os.path.splitext(filename)[1].lower()
    name_lower = filename.lower()

    # Chat heuristic: .txt files with chat-like names
    if ext == ".txt" and any(p in name_lower for p in _CHAT_PATTERNS):
        return "chat"

    return _EXT_MAP.get(ext, "unknown")


def _build_folder_tree(files: List[CaseFile]) -> Dict[str, Any]:
    """Build a nested dict representing the folder structure."""
    tree: Dict[str, Any] = {}
    for f in files:
        parts = f["relative_path"].replace("\\", "/").split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = f["file_id"]
    return tree


# Supported extensions (used for filtering on upload)
SUPPORTED_EXTENSIONS = set(_EXT_MAP.keys())


def build_case_workspace(
    case_name: str,
    file_tuples: List[Tuple[str, str]],  # [(relative_path, absolute_path), ...]
) -> CaseWorkspace:
    """
    Build a CaseWorkspace from a list of (relative_path, absolute_path) pairs.
    Computes classification, hash, and folder structure.
    """
    files: List[CaseFile] = []
    classifications: Dict[str, List[str]] = {}

    for rel_path, abs_path in file_tuples:
        filename = os.path.basename(rel_path)
        ext = os.path.splitext(filename)[1].lower()
        classification = classify_file(filename)
        mime_type, _ = mimetypes.guess_type(filename)
        size = os.path.getsize(abs_path) if os.path.exists(abs_path) else 0
        fhash = file_hash(abs_path) if os.path.exists(abs_path) else None
        fid = str(uuid.uuid4())

        cf = CaseFile(
            file_id=fid,
            original_name=filename,
            relative_path=rel_path.replace("\\", "/"),
            absolute_path=abs_path,
            extension=ext,
            size_bytes=size,
            classification=classification,
            mime_type=mime_type,
            hash=fhash,
        )
        files.append(cf)
        classifications.setdefault(classification, []).append(fid)

    return CaseWorkspace(
        case_name=case_name,
        total_files=len(files),
        files=files,
        folder_structure=_build_folder_tree(files),
        classifications=classifications,
    )
