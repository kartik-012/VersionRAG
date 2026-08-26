import re
import os
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime
import io

class ParserService:
    @staticmethod
    def parse_version_string(raw_version: str) -> Tuple[str, Optional[str], int]:
        """
        Parses raw version strings (semver, non-semver, date-based).
        Returns: (cleaned_version_tag, normalized_version, sort_order_integer)
        """
        raw = raw_version.strip()
        if not raw:
            return "v1.0", "1.0.0", 1000

        # Pattern 1: Semver e.g. v15.14.0 or 2.1.0
        semver_match = re.search(r"v?(\d+)(?:\.(\d+))?(?:\.(\d+))?", raw, re.IGNORECASE)
        if semver_match:
            major = int(semver_match.group(1) or 0)
            minor = int(semver_match.group(2) or 0)
            patch = int(semver_match.group(3) or 0)
            normalized = f"{major}.{minor}.{patch}"
            order = major * 10000 + minor * 100 + patch
            tag = raw if raw.startswith("v") or raw.startswith("V") else f"v{raw}"
            return tag, normalized, order

        # Pattern 2: Year/Quarter or Date e.g. 2025.01, 2025-Q1
        date_match = re.search(r"(\d{4})[-.](Q\d|\d{1,2})", raw, re.IGNORECASE)
        if date_match:
            year = int(date_match.group(1))
            sub = date_match.group(2).upper()
            if sub.startswith("Q"):
                q_num = int(sub[1])
                order = year * 100 + q_num * 25
            else:
                order = year * 100 + int(sub)
            return raw, f"{year}-{sub}", order

        # Fallback to string hash sort order
        return raw, raw, 500

    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
        """Extracts clean text content from PDF, Markdown, TXT, HTML, DOCX."""
        ext = filename.split(".")[-1].lower() if "." in filename else "txt"

        if ext == "pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text_parts = []
                for i, page in enumerate(reader.pages):
                    extracted = page.extract_text() or ""
                    text_parts.append(f"--- Page {i+1} ---\n{extracted}")
                return "\n\n".join(text_parts)
            except Exception:
                return file_bytes.decode("utf-8", errors="ignore")

        elif ext in ["md", "markdown", "txt", "json"]:
            return file_bytes.decode("utf-8", errors="ignore")

        elif ext in ["html", "htm"]:
            raw_html = file_bytes.decode("utf-8", errors="ignore")
            # Strip html tags cleanly
            clean_text = re.sub(r"<style.*?</style>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<script.*?</script>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<[^>]+>", " ", clean_text)
            clean_text = re.sub(r"\s+", " ", clean_text)
            return clean_text.strip()

        elif ext == "docx":
            try:
                import docx
                doc = docx.Document(io.BytesIO(file_bytes))
                return "\n\n".join([p.text for p in doc.paragraphs if p.text])
            except Exception:
                return file_bytes.decode("utf-8", errors="ignore")

        return file_bytes.decode("utf-8", errors="ignore")

    @staticmethod
    def extract_metadata_and_version(content: str, filename: str) -> Dict[str, Any]:
        """
        Deterministic + heuristic metadata extraction.
        Extracts title, version tag, release date, and document family hints.
        """
        meta = {
            "title": "",
            "version_tag": "v1.0",
            "release_date": None,
            "doc_family": "",
            "confidence": 0.85,
            "source": "heuristic_parser"
        }

        # 1. Look for version tag in filename e.g. "assert_v15.md", "node-v16.0.0.pdf", "api-spec-2025.1.txt"
        v_match = re.search(r"v?(\d+(?:\.\d+)*(?:-[a-zA-Z0-9]+)?)", filename, re.IGNORECASE)
        if v_match:
            tag, norm, order = ParserService.parse_version_string(v_match.group(0))
            meta["version_tag"] = tag
            meta["version_order"] = order
            meta["normalized_version"] = norm

        # 2. Look for title in first 1000 characters
        first_chunk = content[:2000]
        # Markdown title: `# Title`
        h1_match = re.search(r"^#\s+(.+)$", first_chunk, re.MULTILINE)
        if h1_match:
            meta["title"] = h1_match.group(1).strip()
        else:
            # Fallback title from filename
            base_name = os.path.splitext(filename)[0]
            clean_title = re.sub(r"[-_v\d.]+", " ", base_name).strip().title()
            meta["title"] = clean_title if clean_title else "Documentation"

        # 3. Document family hint
        # Remove version numbers from title to get family name
        family_name = re.sub(r"v?\d+(\.\d+)*", "", meta["title"], flags=re.IGNORECASE).strip()
        family_name = re.sub(r"\s+", " ", family_name).strip()
        meta["doc_family"] = family_name or meta["title"]

        # 4. Check for version tags inside content headers
        content_v_match = re.search(r"(?:version|release|v)\s*[:=]?\s*([v\d.]+)", first_chunk, re.IGNORECASE)
        if content_v_match and meta["version_tag"] == "v1.0":
            tag, norm, order = ParserService.parse_version_string(content_v_match.group(1))
            meta["version_tag"] = tag
            meta["version_order"] = order
            meta["normalized_version"] = norm

        return meta

parser_service = ParserService()
