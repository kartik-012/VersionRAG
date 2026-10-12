import re
import os
import json
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
    def _resolve_schema_name(schema: Dict[str, Any]) -> str:
        """Extracts a clean type or schema identifier from an OpenAPI schema object."""
        if not isinstance(schema, dict):
            return "object"
        if "$ref" in schema:
            ref = str(schema["$ref"])
            return ref.split("/")[-1]
        if "title" in schema:
            return str(schema["title"]).replace(" ", "")
        schema_type = str(schema.get("type", "object"))
        if schema_type == "array" and isinstance(schema.get("items"), dict):
            inner = ParserService._resolve_schema_name(schema["items"])
            return f"Array<{inner}>"
        return schema_type

    @staticmethod
    def normalize_openapi_spec(spec: Dict[str, Any]) -> Optional[str]:
        """
        Detects OpenAPI 3.x (`openapi`) or Swagger 2.0 (`swagger`) dictionary specs and
        normalizes every `(path, method)` operation into structured Markdown AST sections
        compatible with `ChunkingService`, `ASTSignatureParserService`, and `DiffService`.
        """
        if not isinstance(spec, dict):
            return None
        if not (("openapi" in spec or "swagger" in spec) and isinstance(spec.get("paths"), dict)):
            return None

        info = spec.get("info") if isinstance(spec.get("info"), dict) else {}
        title = str(info.get("title") or "OpenAPI Specification").strip()
        raw_version = str(info.get("version") or "1.0.0").strip()
        v_tag = raw_version if raw_version.lower().startswith("v") else f"v{raw_version}"
        description = str(info.get("description") or "").strip()

        lines: List[str] = [f"# {title} {v_tag}", f"Version: {v_tag}"]
        if description:
            lines.append(description)
        lines.append("")

        paths: Dict[str, Any] = spec.get("paths", {})
        http_methods = ("get", "post", "put", "patch", "delete", "head", "options")

        for path_str, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
            path_level_params = path_item.get("parameters") if isinstance(path_item.get("parameters"), list) else []

            for method in http_methods:
                op = path_item.get(method)
                if not isinstance(op, dict):
                    continue

                lines.append(f"## {method.upper()} {path_str}")
                summary = str(op.get("summary") or op.get("operationId") or "").strip()
                op_desc = str(op.get("description") or "").strip()
                if summary:
                    lines.append(summary)
                if op_desc and op_desc != summary:
                    lines.append(op_desc)
                if op.get("deprecated") is True:
                    lines.append("**Deprecated**: This endpoint is deprecated and scheduled for removal.")

                # Collect parameters from path-level, operation-level, and requestBody
                param_bullets: List[str] = []
                seen_params = set()

                combined_params = list(path_level_params) + (
                    op.get("parameters") if isinstance(op.get("parameters"), list) else []
                )
                for p in combined_params:
                    if not isinstance(p, dict):
                        continue
                    p_name = str(p.get("name") or "").strip()
                    if not p_name or p_name in seen_params:
                        continue
                    seen_params.add(p_name)

                    p_in = str(p.get("in") or "query").lower()
                    is_req = bool(p.get("required", False)) or p_in == "path"
                    p_schema = p.get("schema") if isinstance(p.get("schema"), dict) else p
                    # Swagger 2.0 body parameter with properties
                    if p_in == "body" and isinstance(p_schema.get("properties"), dict):
                        req_props = set(p_schema.get("required") or [])
                        for prop_name, prop_schema in p_schema["properties"].items():
                            if prop_name in seen_params or not isinstance(prop_schema, dict):
                                continue
                            seen_params.add(prop_name)
                            prop_type = ParserService._resolve_schema_name(prop_schema)
                            req_label = "required" if prop_name in req_props else "optional"
                            prop_desc = str(prop_schema.get("description") or "").strip()
                            suffix = f": {prop_desc}" if prop_desc else ""
                            param_bullets.append(f"- `{prop_name}` ({prop_type}, {req_label}){suffix}")
                        continue

                    p_type = ParserService._resolve_schema_name(p_schema)
                    req_label = "required" if is_req else "optional"
                    p_desc = str(p.get("description") or "").strip()
                    suffix = f": {p_desc}" if p_desc else ""
                    param_bullets.append(f"- `{p_name}` ({p_type}, {req_label}){suffix}")

                # OpenAPI 3.x requestBody
                req_body = op.get("requestBody")
                if isinstance(req_body, dict):
                    content_map = req_body.get("content") if isinstance(req_body.get("content"), dict) else {}
                    for media_obj in content_map.values():
                        if not isinstance(media_obj, dict):
                            continue
                        b_schema = media_obj.get("schema")
                        if not isinstance(b_schema, dict):
                            continue
                        req_props = set(b_schema.get("required") or [])
                        props = b_schema.get("properties")
                        if isinstance(props, dict):
                            for prop_name, prop_schema in props.items():
                                if prop_name in seen_params or not isinstance(prop_schema, dict):
                                    continue
                                seen_params.add(prop_name)
                                prop_type = ParserService._resolve_schema_name(prop_schema)
                                req_label = "required" if prop_name in req_props else "optional"
                                prop_desc = str(prop_schema.get("description") or "").strip()
                                suffix = f": {prop_desc}" if prop_desc else ""
                                param_bullets.append(f"- `{prop_name}` ({prop_type}, {req_label}){suffix}")

                if param_bullets:
                    lines.append("")
                    lines.append("Parameters:")
                    lines.extend(param_bullets)

                # Collect responses
                responses = op.get("responses")
                if isinstance(responses, dict) and responses:
                    lines.append("")
                    lines.append("Responses:")
                    for status_code, resp_obj in responses.items():
                        if not isinstance(resp_obj, dict):
                            continue
                        code_str = str(status_code).strip()
                        resp_desc = str(resp_obj.get("description") or "").strip()
                        schema_label = None
                        # OpenAPI 3.x response content schema
                        resp_content = resp_obj.get("content")
                        if isinstance(resp_content, dict):
                            for media_obj in resp_content.values():
                                if isinstance(media_obj, dict) and isinstance(media_obj.get("schema"), dict):
                                    schema_label = ParserService._resolve_schema_name(media_obj["schema"])
                                    break
                        # Swagger 2.0 response schema
                        if not schema_label and isinstance(resp_obj.get("schema"), dict):
                            schema_label = ParserService._resolve_schema_name(resp_obj["schema"])

                        if code_str.startswith("2"):
                            target_schema = schema_label or (resp_desc.replace(" ", "") if resp_desc else "SuccessResponse")
                            lines.append(f"- {code_str}: `{target_schema}`")
                        else:
                            err_label = resp_desc or schema_label or f"HTTP_{code_str}"
                            lines.append(f"- {code_str}: {err_label}")

                lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
        """Extracts clean text content from PDF, Markdown, TXT, JSON/YAML (including OpenAPI specs), HTML, DOCX."""
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

        elif ext in ["json", "yaml", "yml"]:
            raw_text = file_bytes.decode("utf-8", errors="ignore")
            parsed_spec = None
            try:
                parsed_spec = json.loads(raw_text)
            except Exception:
                try:
                    import yaml  # type: ignore
                    parsed_spec = yaml.safe_load(raw_text)
                except Exception:
                    parsed_spec = None

            if isinstance(parsed_spec, dict):
                normalized_md = ParserService.normalize_openapi_spec(parsed_spec)
                if normalized_md:
                    return normalized_md
            return raw_text

        elif ext in ["md", "markdown", "txt"]:
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
