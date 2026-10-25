"""
VersionRAG Enterprise CLI & CI/CD Pull Request Breaking-Change Auditor
======================================================================
Allows engineering teams and GitHub Actions CI/CD pipelines to audit production source
files against the VersionRAG AST Diff Graph before merging framework or API upgrades.

Usage Examples:
  # Audit a source file against indexed versions (exits 1 if breaking/silent changes found)
  python -m app.cli_audit --file my_service.js --from v14.0.0 --to v16.0.0

  # Audit inline code snippet in JSON mode for CI PR comment bots
  python -m app.cli_audit --code "const t = new assert.CallTracker();" --from v14.0.0 --to v16.0.0 --json

  # Audit code against two local documentation or OpenAPI spec files directly (stateless CI mode)
  python -m app.cli_audit --file client.py --old-doc spec_v1.json --new-doc spec_v2.json --from v1.0.0 --to v2.0.0
"""

import argparse
import json
import os
import sys

# Ensure backend directory is in sys.path
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from typing import Any, Dict, List, Optional, Tuple

from app.services.code_scanner_service import code_scanner_service
from app.services.diff_service import diff_service
from app.services.parser_service import parser_service


_DEFAULT_FALLBACK_DOCS: Dict[str, str] = {
    "v14.0.0": """# Node.js Assert Documentation v14.0.0
## assert.deepEqual(actual, expected[, message])
Tests for deep equality between the actual and expected parameters. Primitive values are compared with the Abstract Equality Comparison (`==`).

## Class: assert.CallTracker
Stability: 1 - Experimental. Tracks function calls during tests.

### tracker.calls([fn][, exact])
Wraps a function to track calls. Both `fn` and `exact` are optional in v14.0.0.
""",
    "v15.14.0": """# Node.js Assert Documentation v15.14.0
## Changelog
- **[Breaking]**: `tracker.calls(fn, exact)` now requires `fn` callback parameter.

## assert.deepEqual(actual, expected[, message])
Tests for deep equality. Primitive values and object prototypes are now compared using `===` strict equality and `Object.is` for NaN/Symbol properties.

## Class: assert.CallTracker
Stability: 1 - Experimental.

### tracker.calls(fn, exact)
Wraps `fn` to track calls. `fn` is now required; calling `tracker.calls(1)` without a function throws `ERR_INVALID_ARG_TYPE`.
""",
    "v16.0.0": """# Node.js Assert Documentation v16.0.0
## Changelog
- **[Deprecated]**: `assert.CallTracker` is deprecated and will be removed in a future release. Migrate to `node:test` `mock.fn()`.
- **[Breaking]**: `assert.ifError(value)` now requires Error cause inspection when wrapping aggregate errors.

## assert.deepEqual(actual, expected[, message])
Tests for deep equality. Primitive values and object prototypes are compared using `===` strict equality and `Object.is` for NaN/Symbol properties.

## Class: assert.CallTracker
**Deprecated**: `assert.CallTracker` is deprecated. Use `mock.fn()` from `node:test` instead.

### tracker.calls(fn, exact)
**Deprecated**: Wraps `fn` to track calls. Both `fn` and `exact` are required.
""",
}


def resolve_docs_and_changes(
    from_tag: str,
    to_tag: str,
    old_doc_path: Optional[str] = None,
    new_doc_path: Optional[str] = None,
) -> Tuple[str, str, List[Dict[str, Any]]]:
    """
    Loads source (`from_tag`) and target (`to_tag`) documentation and change records from:
    1. Explicit `--old-doc` / `--new-doc` file paths (supports Markdown, TXT, PDF, OpenAPI JSON/YAML), OR
    2. Local VersionRAG database (`DocumentVersion` & `DocumentChange`), OR
    3. Built-in reference baseline (for zero-config stateless CI runners).
    """
    if old_doc_path and new_doc_path:
        with open(old_doc_path, "rb") as f_old:
            old_content = parser_service.extract_text_from_file(f_old.read(), os.path.basename(old_doc_path))
        with open(new_doc_path, "rb") as f_new:
            new_content = parser_service.extract_text_from_file(f_new.read(), os.path.basename(new_doc_path))
        computed_changes, _ = diff_service.compute_all_changes(old_content, new_content, from_tag, to_tag)
        return old_content, new_content, computed_changes

    # Try querying local database
    try:
        from app.core.database import SessionLocal
        from app.models.document import DocumentVersion
        from app.models.change import DocumentChange

        db = SessionLocal()
        try:
            v_from = (
                db.query(DocumentVersion)
                .filter(DocumentVersion.version_tag == from_tag)
                .order_by(DocumentVersion.created_at.desc())
                .first()
            )
            v_to = (
                db.query(DocumentVersion)
                .filter(DocumentVersion.version_tag == to_tag)
                .order_by(DocumentVersion.created_at.desc())
                .first()
            )
            if v_from and v_to and v_from.cleaned_text and v_to.cleaned_text:
                db_changes = (
                    db.query(DocumentChange)
                    .filter(DocumentChange.document_id == v_to.document_id)
                    .all()
                )
                stored_list: List[Dict[str, Any]] = [
                    {
                        "location": ch.section_location or "API",
                        "change_type": ch.change_type.value if hasattr(ch.change_type, "value") else str(ch.change_type),
                        "severity": ch.severity.value if hasattr(ch.severity, "value") else str(ch.severity),
                        "is_breaking": bool(ch.is_breaking),
                        "is_silent": bool(ch.is_silent),
                        "summary": ch.summary,
                        "old_content": ch.old_snippet,
                        "new_content": ch.new_snippet,
                    }
                    for ch in db_changes
                ]
                return v_from.cleaned_text, v_to.cleaned_text, stored_list
        finally:
            db.close()
    except Exception:
        pass

    # Fallback to stateless reference docs
    old_content = _DEFAULT_FALLBACK_DOCS.get(from_tag, _DEFAULT_FALLBACK_DOCS["v14.0.0"])
    new_content = _DEFAULT_FALLBACK_DOCS.get(to_tag, _DEFAULT_FALLBACK_DOCS["v16.0.0"])
    computed_changes, _ = diff_service.compute_all_changes(old_content, new_content, from_tag, to_tag)
    return old_content, new_content, computed_changes


def run_cli_audit(
    code_snippet: str,
    from_tag: str = "v14.0.0",
    to_tag: str = "v16.0.0",
    old_doc_path: Optional[str] = None,
    new_doc_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the VersionRAG Codebase Impact & Breaking-Change Scanner and returns the full report.
    """
    old_content, new_content, stored_changes = resolve_docs_and_changes(
        from_tag=from_tag,
        to_tag=to_tag,
        old_doc_path=old_doc_path,
        new_doc_path=new_doc_path,
    )
    return code_scanner_service.scan_code_snippet(
        code_snippet=code_snippet,
        from_tag=from_tag,
        to_tag=to_tag,
        old_doc_content=old_content,
        new_doc_content=new_content,
        stored_changes=stored_changes,
    )


def format_terminal_report(report: Dict[str, Any], source_label: str) -> str:
    """Formats a human-readable CI/CD console report."""
    counts = report.get("summary_counts", {})
    from_v = report.get("from_tag", "v14.0.0")
    to_v = report.get("to_tag", "v16.0.0")
    lines: List[str] = [
        "=" * 78,
        "VersionRAG CI/CD Breaking-Change & Upgrade Auditor",
        f"Target: {source_label} | Migration: {from_v} -> {to_v}",
        "=" * 78,
        f"Compatibility Score : {report.get('compatibility_score', 100)}%",
        f"Risk Grade          : {report.get('risk_level', 'SAFE')}",
        f"Lines Scanned       : {counts.get('total_lines_scanned', 0)} | Vulnerable Lines: {counts.get('vulnerable_lines', 0)}",
        f"Breaking Lines      : {counts.get('breaking_lines', 0)} | Silent Behavioral Lines: {counts.get('silent_lines', 0)}",
        "-" * 78,
    ]

    findings = report.get("line_findings", [])
    if not findings:
        lines.append("[PASS] Zero breaking or silent behavioral vulnerabilities detected.")
    else:
        lines.append("Line-by-Line Findings:")
        for f in findings:
            silent_badge = " [SILENT BREAK]" if f.get("is_silent") else ""
            cite = f.get("citation") or {}
            lines.append(
                f"  Line {f['line_number']:>3} [{f['severity']}/{str(f['change_type']).upper()}]{silent_badge} "
                f"Symbol: `{f.get('symbol', 'API')}`"
            )

            lines.append(f"           Issue : {f.get('issue_summary', '')}")
            lines.append(f"           Fix   : {f.get('fix_explanation', '')}")
            lines.append(f"           Cite  : [{cite.get('section', 'Documentation')}] ({cite.get('version_tag', to_v)})")

    if report.get("unified_diff"):
        lines.extend([
            "-" * 78,
            f"Auto-Refactored Unified Diff ({from_v} -> {to_v}):",
            report["unified_diff"],
        ])

    lines.append("=" * 78)
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli_audit",
        description="VersionRAG CLI & CI/CD Pull Request Breaking-Change Auditor",
    )
    parser.add_argument("--file", "-f", type=str, help="Path to production source code file to audit")
    parser.add_argument("--code", "-c", type=str, help="Inline source code snippet to audit")
    parser.add_argument("--from", dest="from_version", default="v14.0.0", help="Source version tag (default: v14.0.0)")
    parser.add_argument("--to", dest="to_version", default="v16.0.0", help="Target version tag (default: v16.0.0)")
    parser.add_argument("--old-doc", type=str, default=None, help="Optional path to baseline doc/OpenAPI file")
    parser.add_argument("--new-doc", type=str, default=None, help="Optional path to target doc/OpenAPI file")
    parser.add_argument("--json", action="store_true", help="Output structured JSON report for CI bots")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Optional file path to write audit report (useful for CI artifacts)",
    )
    parser.add_argument(
        "--no-fail",
        action="store_true",
        help="Always exit 0 even when breaking/silent changes are detected (advisory mode)",
    )

    args = parser.parse_args(argv)

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 2
        with open(args.file, "r", encoding="utf-8", errors="ignore") as f_in:
            code_snippet = f_in.read()
        source_label = args.file
    elif args.code:
        code_snippet = args.code
        source_label = "<inline-snippet>"
    else:
        print("Error: Provide either --file <path> or --code <snippet>", file=sys.stderr)
        return 2

    report = run_cli_audit(
        code_snippet=code_snippet,
        from_tag=args.from_version,
        to_tag=args.to_version,
        old_doc_path=args.old_doc,
        new_doc_path=args.new_doc,
    )

    if args.json:
        output_text = json.dumps(report, indent=2)
    else:
        output_text = format_terminal_report(report, source_label)

    print(output_text)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as out_f:
                out_f.write(output_text)
        except Exception as e:
            print(f"Warning: Failed to write output file {args.output}: {e}", file=sys.stderr)

    counts = report.get("summary_counts", {})
    has_failures = (
        counts.get("breaking_lines", 0) > 0
        or counts.get("silent_lines", 0) > 0
        or counts.get("vulnerable_lines", 0) > 0
    )
    if has_failures and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

