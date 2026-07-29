import os
import uuid
import re
from datetime import datetime
from typing import List, Dict, Optional

from app.ai.agents.base_agent import BaseAgent
from app.ai.orchestrator.state import (
    LexIntelState, EvidenceItem, EvidenceTimelineEntry
)
from app.ai.agents.evidence_analysis.extractor import (
    detect_file_type, detect_category, extract_file_metadata,
    extract_timestamp_from_text, file_hash,
)
from app.ai.logging.logger import AILogger

logger = AILogger("agent.evidence_analysis")

# File types the text extractor can handle
_TEXT_EXTRACTABLE = {"pdf", "image", "text", "email"}

# Ordered list of (regex, strptime_format) pairs covering every format the LLM produces
_TS_PARSE_FORMATS = [
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "%Y-%m-%dT%H:%M:%S"),
    (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}",       "%Y-%m-%dT%H:%M"),
    (r"\d{4}-\d{2}-\d{2}",                    "%Y-%m-%d"),
    (r"\d{2}/\d{2}/\d{4}",                    "%d/%m/%Y"),
    (r"\d{2}-\d{2}-\d{4}",                    "%d-%m-%Y"),
    (r"\d{1,2}/\d{1,2}/\d{4}",               "%d/%m/%Y"),
]
_FALLBACK_DT = datetime(9999, 12, 31)   # unparseable entries sort to the end


def _parse_timestamp(ts: str) -> datetime:
    """Parse any timestamp string the LLM might return into a datetime for sorting."""
    if not ts:
        return _FALLBACK_DT
    for pattern, fmt in _TS_PARSE_FORMATS:
        m = re.search(pattern, ts)
        if m:
            try:
                return datetime.strptime(m.group(0), fmt)
            except ValueError:
                continue
    return _FALLBACK_DT


def _extract_content(path: str, file_type: str) -> Optional[str]:
    """Extract readable text from a file for LLM analysis."""
    if file_type not in _TEXT_EXTRACTABLE:
        return None
    try:
        from app.ai.agents.document_intelligence.extractor import extract_text_from_file
        text, _, _ = extract_text_from_file(path)
        return text[:2000] if text else None  # cap per-file to keep prompt manageable
    except Exception as e:
        logger.warning("Content extraction failed", path=path, error=str(e))
        return None


class EvidenceAnalysisAgent(BaseAgent):
    """
    Phase 3A — Agent 4: Evidence Analysis

    Responsibilities:
    - Catalogue all uploaded evidence files
    - Extract metadata (timestamps, file type, size)
    - Detect duplicate files via SHA-256 hash
    - Categorize evidence (documentary / digital / physical / testimonial)
    - Ask LLM to generate a chronological timeline and identify missing evidence
    - Populate state.evidence_items, state.evidence_timeline, state.missing_evidence_hints
    """

    agent_name = "evidence_analysis"
    prompt_name = "evidence_analysis"

    async def execute(self, state: LexIntelState) -> LexIntelState:
        file_paths = state.get("uploaded_file_paths") or []
        doc_intel = state.get("document_intelligence")
        case_summary = doc_intel.get("summary", "") if doc_intel else (
            self.sanitize_input(state.get("raw_input") or "")[:500]
        )

        if not file_paths:
            state["warnings"] = [
                *state.get("warnings", []),
                "EvidenceAnalysisAgent: no files provided",
            ]
            state["evidence_items"] = []
            state["evidence_timeline"] = []
            state["missing_evidence_hints"] = []
            return state

        # ── Build evidence items ──────────────────────────────────────────────
        seen_hashes: Dict[str, str] = {}   # hash → evidence_id
        items: List[EvidenceItem] = []
        # Map evidence_id → extracted text (for LLM prompt)
        content_map: Dict[str, str] = {}

        for path in file_paths:
            if not os.path.exists(path):
                continue

            eid = str(uuid.uuid4())
            meta = extract_file_metadata(path)
            fhash = file_hash(path)
            file_type = detect_file_type(path)
            category = detect_category(path)

            is_dup = fhash in seen_hashes and bool(fhash)
            dup_of = seen_hashes[fhash] if is_dup else None
            if fhash and not is_dup:
                seen_hashes[fhash] = eid

            # Extract actual text content from the file
            extracted_content = _extract_content(path, file_type) if not is_dup else None

            # Try to pull a real timestamp from the extracted content
            content_timestamp = None
            if extracted_content:
                content_timestamp = extract_timestamp_from_text(extracted_content)
                content_map[eid] = extracted_content

            # Best timestamp priority: exif > content > filename > file mtime
            timestamp = (
                meta.get("exif_datetime")
                or content_timestamp
                or meta.get("timestamp_from_filename")
                or meta.get("modified_at")
            )

            # Build a meaningful description from extracted content
            if extracted_content:
                # Use first 120 chars of content as description
                desc_text = " ".join(extracted_content.split())[:120]
                description = f"{file_type.capitalize()}: {desc_text}…" if len(desc_text) == 120 else f"{file_type.capitalize()}: {desc_text}"
            else:
                description = f"{file_type.capitalize()} file: {meta['filename']}"

            items.append(EvidenceItem(
                evidence_id=eid,
                file_name=meta["filename"],
                file_type=file_type,
                file_size_bytes=meta["size_bytes"],
                timestamp=timestamp,
                extracted_timestamp=content_timestamp or meta.get("timestamp_from_filename"),
                category=category,
                description=description,
                metadata=meta,
                is_duplicate=is_dup,
                duplicate_of=dup_of,
                hash=fhash,
            ))

        state["evidence_items"] = items

        if not items:
            state["evidence_timeline"] = []
            state["missing_evidence_hints"] = []
            return state

        # ── Build rich evidence list for LLM — include actual content ─────────
        evidence_parts = []
        for e in items:
            content_snippet = content_map.get(e["evidence_id"], "")
            first_line = " ".join(content_snippet.split()[:15]) if content_snippet else ""
            represents = f" (contains: {first_line})" if first_line else ""

            part = (
                f"--- Evidence Item ---\n"
                f"ID: {e['evidence_id']}\n"
                f"File: {e['file_name']}\n"
                f"Format: {e['file_type']}{represents}\n"
                f"Category: {e['category']}\n"
                f"Timestamp: {e['timestamp'] or 'unknown'}\n"
                f"Duplicate: {e['is_duplicate']}\n"
                f"Extracted Content:\n{content_snippet if content_snippet else '(binary/no text extracted)'}\n"
            )
            evidence_parts.append(part)

        evidence_list_text = "\n".join(evidence_parts)[:4000]

        # ── Build "already identified" summary from Document Intelligence output ──
        # Explicitly tells the LLM what each physical file contains so it can
        # distinguish between files that ARE provided vs items merely mentioned
        # inside a document (e.g. a "Key Evidence" table in a case sheet).
        identified_lines = []
        for e in items:
            snippet = content_map.get(e["evidence_id"], "")
            if snippet:
                first_words = " ".join(snippet.split()[:12])
                identified_lines.append(
                    f"- PHYSICALLY PROVIDED: '{e['file_name']}' "
                    f"({e['file_type']}) — content starts with: {first_words}…"
                )
            else:
                identified_lines.append(
                    f"- PHYSICALLY PROVIDED: '{e['file_name']}' "
                    f"({e['file_type']}) — no text extractable (binary/media file)"
                )
        if doc_intel and doc_intel.get("document_type"):
            identified_lines.append(
                f"- Document Intelligence classified the case as: "
                f"{doc_intel['document_type']}"
            )
        evidence_identified = (
            "The following files are PHYSICALLY PROVIDED (uploaded by the user).\n"
            "Only these files count as present evidence.\n"
            "Items merely MENTIONED or LISTED inside a document are NOT present "
            "unless a separate file containing that content is also provided.\n\n"
            + "\n".join(identified_lines)
        )

        prompt = self.get_prompt()
        response = await self.invoke_llm(
            prompt.system,
            prompt.render_user(
                evidence_list=evidence_list_text,
                case_summary=case_summary[:500],
                evidence_identified=evidence_identified[:800],
            ),
        )
        parsed = self.parse_json_response(response.content)

        # ── Build typed timeline ──────────────────────────────────────────────
        raw_timeline = parsed.get("timeline") or []
        timeline: List[EvidenceTimelineEntry] = [
            EvidenceTimelineEntry(
                timestamp=entry.get("timestamp", ""),
                event_description=entry.get("event_description", ""),
                evidence_ids=entry.get("evidence_ids") or [],
                confidence=float(entry.get("confidence", 0.8)),
            )
            for entry in raw_timeline
            if isinstance(entry, dict)
        ]

        # Sort chronologically — handles DD/MM/YYYY, ISO, and mixed formats
        timeline.sort(key=lambda e: _parse_timestamp(e["timestamp"]))

        state["evidence_timeline"] = timeline
        state["missing_evidence_hints"] = parsed.get("missing_evidence_hints") or []
        state["evidence_analysis"] = {
            "total_items": len(items),
            "duplicates": sum(1 for e in items if e["is_duplicate"]),
            "categories": parsed.get("categories", {}),
            "analysis_summary": parsed.get("analysis_summary", ""),
        }

        logger.info(
            "Evidence analysis complete",
            items=len(items),
            timeline_entries=len(timeline),
            duplicates=state["evidence_analysis"]["duplicates"],
        )
        return state
