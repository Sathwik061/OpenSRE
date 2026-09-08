"""
sentinel/knowledge/document_parsers.py
=======================================
100% Local, Privacy-Preserving Multi-Format Document Ingestor for OpenSRE.
Extracts operational Standard Operating Procedures (SOPs), headings,
troubleshooting steps, and tables from Adobe PDF (.pdf) and Microsoft Word (.docx/.doc).
Zero document data leaves the local network.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger("sentinel.knowledge.document_parsers")


class SemanticChunk:
    """A coherent chunk of runbook documentation."""
    def __init__(self, heading: str, content: str, chunk_type: str = "procedure"):
        self.heading = heading
        self.content = content
        self.chunk_type = chunk_type  # symptoms | root_cause | actions | verification | reference

    def to_dict(self) -> Dict[str, str]:
        return {
            "heading": self.heading,
            "content": self.content,
            "chunk_type": self.chunk_type,
        }


class PdfRunbookParser:
    """Extracts text, headings, and procedural steps from PDF files using pypdf."""

    @staticmethod
    def extract_text_and_sections(file_path: str) -> Dict[str, Any]:
        try:
            import pypdf
        except ImportError:
            logger.error("pypdf is not installed.")
            return {"title": os.path.basename(file_path), "text": "", "sections": []}

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        full_text_pages: List[str] = []
        try:
            reader = pypdf.PdfReader(file_path)
            title = reader.metadata.title if reader.metadata and reader.metadata.title else None
            for page_idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                full_text_pages.append(page_text.strip())
        except Exception as e:
            logger.error(f"Failed to read PDF {file_path}: {e}")
            return {"title": os.path.basename(file_path), "text": "", "sections": []}

        full_text = "\n\n".join(full_text_pages)
        if not title:
            # First non-empty line as fallback title
            first_lines = [l.strip() for l in full_text.split("\n") if l.strip()]
            title = first_lines[0] if first_lines else os.path.splitext(os.path.basename(file_path))[0]

        sections = SemanticChunker.chunk_text(full_text)
        return {
            "title": title,
            "filename": os.path.basename(file_path),
            "format": "pdf",
            "page_count": len(full_text_pages),
            "full_text": full_text,
            "sections": [s.to_dict() for s in sections],
            "extracted_sop": SemanticChunker.extract_structured_sop(title, full_text, sections),
        }


class DocxRunbookParser:
    """Extracts paragraphs, headings, bullet lists, and tables from Word (.docx) files."""

    @staticmethod
    def extract_text_and_sections(file_path: str) -> Dict[str, Any]:
        try:
            import docx
        except ImportError:
            logger.error("python-docx is not installed.")
            return {"title": os.path.basename(file_path), "text": "", "sections": []}

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"DOCX file not found: {file_path}")

        paragraphs: List[str] = []
        title: Optional[str] = None

        try:
            doc = docx.Document(file_path)
            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                if p.style.name.startswith("Heading 1") or p.style.name.startswith("Title"):
                    if not title:
                        title = text
                    paragraphs.append(f"\n## {text}\n")
                elif p.style.name.startswith("Heading"):
                    paragraphs.append(f"\n### {text}\n")
                else:
                    paragraphs.append(text)

            # Also extract tables
            for t_idx, table in enumerate(doc.tables):
                table_lines = []
                for row in table.rows:
                    row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    if any(row_cells):
                        table_lines.append(" | ".join(row_cells))
                if table_lines:
                    paragraphs.append("\n" + "\n".join(table_lines) + "\n")

        except Exception as e:
            logger.error(f"Failed to read Word document {file_path}: {e}")
            return {"title": os.path.basename(file_path), "text": "", "sections": []}

        full_text = "\n".join(paragraphs)
        if not title:
            first_lines = [l.strip() for l in full_text.split("\n") if l.strip()]
            title = first_lines[0] if first_lines else os.path.splitext(os.path.basename(file_path))[0]

        sections = SemanticChunker.chunk_text(full_text)
        return {
            "title": title,
            "filename": os.path.basename(file_path),
            "format": "docx",
            "full_text": full_text,
            "sections": [s.to_dict() for s in sections],
            "extracted_sop": SemanticChunker.extract_structured_sop(title, full_text, sections),
        }


class SemanticChunker:
    """Splits technical documents into coherent SOP sections while preserving code & steps."""

    @staticmethod
    def chunk_text(text: str) -> List[SemanticChunk]:
        chunks: List[SemanticChunk] = []
        lines = text.split("\n")
        current_heading = "Overview"
        current_lines: List[str] = []

        heading_pattern = re.compile(
            r"^(?:#{1,4}\s+|[0-9]+\.\s+|[A-Z\s]{4,}:|Section\s+[0-9]+|Step\s+[0-9]+:?\s*)(.+)$",
            re.IGNORECASE
        )

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            match = heading_pattern.match(stripped)
            # If line looks like a major section header and current chunk has substance
            if match and len(stripped) < 90 and not stripped.endswith((".", ",", ";")):
                if current_lines:
                    chunk_content = "\n".join(current_lines).strip()
                    c_type = SemanticChunker._classify_chunk_type(current_heading, chunk_content)
                    chunks.append(SemanticChunk(current_heading, chunk_content, c_type))
                    current_lines = []
                current_heading = match.group(1).strip()
            else:
                current_lines.append(line)

        if current_lines:
            chunk_content = "\n".join(current_lines).strip()
            c_type = SemanticChunker._classify_chunk_type(current_heading, chunk_content)
            chunks.append(SemanticChunk(current_heading, chunk_content, c_type))

        return chunks

    @staticmethod
    def _classify_chunk_type(heading: str, content: str) -> str:
        h_low = heading.lower()
        c_low = content.lower()
        if any(k in h_low for k in ["symptom", "error", "trigger", "problem", "alert"]):
            return "symptoms"
        if any(k in h_low for k in ["root cause", "cause", "why", "background", "theory"]):
            return "root_cause"
        if any(k in h_low for k in ["remediation", "action", "how to fix", "resolution", "step", "procedure", "solution"]):
            return "actions"
        if any(k in h_low for k in ["verify", "validation", "confirm", "check"]):
            return "verification"
        return "reference"

    @staticmethod
    def extract_structured_sop(title: str, full_text: str, chunks: List[SemanticChunk]) -> Dict[str, Any]:
        """Synthesizes structured OpenSRE SOP attributes from chunks."""
        symptoms: List[str] = []
        root_causes: List[str] = []
        actions: List[str] = []

        for chunk in chunks:
            lines = [l.strip() for l in chunk.content.split("\n") if l.strip()]
            if chunk.chunk_type == "symptoms":
                symptoms.extend(lines[:4])
            elif chunk.chunk_type == "root_cause":
                root_causes.append(chunk.content)
            elif chunk.chunk_type == "actions":
                # Look for numbered steps or bullet lines
                step_lines = [l for l in lines if re.match(r"^(?:[0-9]+[.)]|[-*•])\s*", l)]
                if step_lines:
                    actions.extend(step_lines)
                else:
                    actions.extend(lines[:5])

        # If no explicit action chunks, search text for numbered lists
        if not actions:
            action_matches = re.findall(r"(?:^|\n)(?:[0-9]+\.|\bStep\s+[0-9]+:?)\s+([^\n]+)", full_text, re.IGNORECASE)
            if action_matches:
                actions = [a.strip() for a in action_matches[:6]]

        # Fallback root cause
        root_cause_summary = "\n".join(root_causes).strip() if root_causes else ""
        if not root_cause_summary:
            for chunk in chunks:
                if "cause" in chunk.content.lower() or "timeout" in chunk.content.lower():
                    root_cause_summary = chunk.content[:400]
                    break

        return {
            "title": title,
            "root_cause": root_cause_summary or f"Operational failure documented in {title}",
            "symptoms": symptoms[:6],
            "recommended_actions": actions[:8] if actions else [
                f"Refer to detailed procedures in uploaded runbook '{title}'.",
                "Verify upstream network and database connectivity before restarting service.",
            ],
        }


def parse_runbook_document(file_path: str) -> Dict[str, Any]:
    """
    Main entrypoint: Auto-detects format (.pdf vs .docx/.doc) and parses runbook.
    Returns unified SOP dictionary.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return PdfRunbookParser.extract_text_and_sections(file_path)
    elif ext in [".docx", ".doc"]:
        return DocxRunbookParser.extract_text_and_sections(file_path)
    elif ext in [".md", ".markdown", ".txt", ".yml", ".yaml"]:
        # Fallback text parser
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        title = os.path.splitext(os.path.basename(file_path))[0].replace("-", " ").title()
        chunks = SemanticChunker.chunk_text(text)
        return {
            "title": title,
            "filename": os.path.basename(file_path),
            "format": ext.lstrip("."),
            "full_text": text,
            "sections": [s.to_dict() for s in chunks],
            "extracted_sop": SemanticChunker.extract_structured_sop(title, text, chunks),
        }
    else:
        raise ValueError(f"Unsupported runbook format: '{ext}'. Supported: .pdf, .docx, .doc, .md, .yml, .txt")
