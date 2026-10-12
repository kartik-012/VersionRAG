"""
Live Codebase Impact & Breaking-Change Scanner (Repo Vulnerability & Upgrade Auditor)
=====================================================================================
Scans developer production code snippets (JavaScript/TypeScript/Node.js, Python, or
REST client code) against the indexed AST Diff Graph between a source version and a
target upgrade version.

Capabilities:
1. Line-by-line AST call-site & symbol matching against `DocumentChange` records and
   live `FunctionASTNode` / `ASTContractDiff` trees between `v_from` and `v_to`.
2. Detects:
   - Explicit breaking API changes & removed symbols
   - Silent behavioral mutations (e.g., `assert.deepEqual` prototype/Symbol checks,
     loose-to-strict equality `==` -> `===`, error cause requirements)
   - Deprecated API usage (e.g., `assert.CallTracker`, `tracker.calls`, `tracker.verify`)
   - Function signature / arity / optional-to-required parameter breaks
   - Exception contract & return-type mutations
3. Synthesizes:
   - Exact 1-indexed line findings with severity, `is_silent` flag, and doc citations
   - Auto-refactored target-version-compliant code
   - Standard unified diff (`difflib.unified_diff`)
   - Compatibility score (0-100%) and risk grade (`CRITICAL`, `HIGH`, `MODERATE`, `SAFE`)
"""

import difflib
import re
from typing import Any, Dict, List, Optional, Tuple
from app.services.ast_parser_service import ast_signature_parser, FunctionASTNode, ASTContractDiff


class CodeScannerService:
    """
    Audits production code snippets against the versioned AST Diff Graph and generates
    line-level vulnerability diagnostics + auto-refactored target-version code.
    """

    @staticmethod
    def _parse_doc_sections(content: str) -> Dict[str, str]:
        secs: Dict[str, str] = {}
        current_title = "General"
        buf: List[str] = []
        for line in (content or "").splitlines():
            if line.startswith("## ") or line.startswith("### "):
                if buf and current_title.lower() not in ("changelog", "release notes", "changes", "history"):
                    secs[current_title] = "\n".join(buf).strip()
                current_title = line.lstrip("#").strip()
                buf = []
            else:
                buf.append(line)
        if buf and current_title.lower() not in ("changelog", "release notes", "changes", "history"):
            secs[current_title] = "\n".join(buf).strip()
        return secs

    @staticmethod
    def _extract_call_arity(line: str, symbol: str) -> Optional[int]:
        """
        If `symbol(...)` is invoked on `line`, returns the number of arguments passed
        at the call site. Returns None if no call invocation is matched.
        """
        short_sym = symbol.split(".")[-1]
        for candidate in (symbol, short_sym):
            if not candidate:
                continue
            pattern = re.escape(candidate) + r"\s*\(([^)]*)\)"
            m = re.search(pattern, line)
            if m:
                args_str = m.group(1).strip()
                if not args_str:
                    return 0
                return len([a.strip() for a in args_str.split(",") if a.strip()])
        return None

    @staticmethod
    def _auto_refactor_line(
        line: str,
        symbol: str,
        change_type: str,
        is_silent: bool,
        summary: str,
        to_tag: str,
        ast_diff: Optional[ASTContractDiff] = None,
        new_node: Optional[FunctionASTNode] = None,
    ) -> Tuple[str, str]:
        """
        Generates a target-version-compliant refactored line (preserving indentation)
        and a human-readable explanation of the code transformation.
        """
        indent_match = re.match(r"^(\s*)", line)
        indent = indent_match.group(1) if indent_match else ""
        stripped = line.strip()
        low_line = stripped.lower()
        low_sym = symbol.lower()
        low_sum = summary.lower()

        # 1. Node.js assert.CallTracker deprecation -> node:test mock.fn()
        if "calltracker" in low_line or "calltracker" in low_sym:
            var_match = re.match(r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*new\s+assert\.CallTracker\s*\(\s*\)\s*;?", stripped)
            var_name = var_match.group(1) if var_match else "tracker"
            refactored = (
                f"{indent}const {{ mock }} = require('node:test'); "
                f"// [{to_tag} Refactor] Replaced deprecated assert.CallTracker ({var_name})"
            )
            return refactored, f"Replaced deprecated `new assert.CallTracker()` with `node:test` `mock` runner API in {to_tag}."

        # 2. tracker.calls(...) arity / deprecation refactor
        if ".calls(" in low_line:
            m_calls = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)\.calls\s*\(\s*([^)]*)\)", stripped)
            if m_calls:
                args_raw = m_calls.group(2).strip()
                # If called with only a number like tracker.calls(1) without fn
                if re.match(r"^\d+$", args_raw):
                    refactored = re.sub(
                        r"\.calls\s*\(\s*(\d+)\s*\)",
                        r".calls(() => {}, \1)",
                        line,
                    ) + f" // [{to_tag} Fix] Supplied required callback fn parameter"
                    return refactored, f"Added required `fn` callback parameter to `.calls(fn, exact)` (calling `.calls({args_raw})` without `fn` throws `ERR_INVALID_ARG_TYPE` in {to_tag})."
                refactored = (
                    f"{indent}// [{to_tag} Refactor] Migrate tracker.calls({args_raw}) to mock.fn()\n"
                    f"{line.rstrip()} // Verify via mockFn.mock.callCount()"
                )
                return refactored, f"Flagged `tracker.calls()` for `mock.fn()` call-count verification in {to_tag}."

        # 3. tracker.verify() deprecation refactor
        if ".verify(" in low_line:
            refactored = (
                f"{indent}assert.strictEqual(mock.calls?.length ?? 1, 1); "
                f"// [{to_tag} Refactor] Replaced deprecated tracker.verify()"
            )
            return refactored, f"Replaced deprecated `tracker.verify()` with explicit `assert.strictEqual` assertion in {to_tag}."

        # 4. Silent behavioral change in assert.deepEqual -> assert.deepStrictEqual
        if "assert.deepequal(" in low_line or ("deepequal" in low_sym and "deepequal(" in low_line):
            refactored = re.sub(r"\bassert\.deepEqual\s*\(", "assert.deepStrictEqual(", line)
            refactored = f"{refactored.rstrip()} // [{to_tag} Silent-Break Fix] Enforced explicit deepStrictEqual"
            return (
                refactored,
                f"Upgraded `assert.deepEqual()` to `assert.deepStrictEqual()` because {to_tag} silently alters prototype and own enumerable Symbol comparison semantics.",
            )

        # 5. Loose equality assert.equal -> assert.strictEqual
        if "assert.equal(" in low_line:
            refactored = re.sub(r"\bassert\.equal\s*\(", "assert.strictEqual(", line)
            refactored = f"{refactored.rstrip()} // [{to_tag} Refactor] Enforced strict equality"
            return refactored, f"Upgraded legacy `assert.equal()` to `assert.strictEqual()` for {to_tag} strict comparison compliance."

        # 6. AST Contract Diff: Newly required parameters (optional -> required or added required param)
        if ast_diff and ast_diff.details:
            newly_req = ast_diff.details.get("newly_required_params", [])
            added_req = [
                p for p in ast_diff.details.get("added_params", [])
                if not p.get("is_optional", True)
            ]
            missing_params = newly_req + [p.get("name") for p in added_req if p.get("name")]
            if missing_params:
                short_sym = symbol.split(".")[-1]
                call_pat = re.compile(r"(" + re.escape(short_sym) + r"\s*\()([^)]*)(\))")
                m_call = call_pat.search(line)
                if m_call:
                    existing_args = m_call.group(2).strip()
                    placeholder_args = ", ".join(f"{p}=None" if "def " in summary else f"/* {p} */ undefined" for p in missing_params)
                    joined_args = f"{existing_args}, {placeholder_args}" if existing_args else placeholder_args
                    refactored = (
                        line[:m_call.start()]
                        + f"{m_call.group(1)}{joined_args}{m_call.group(3)}"
                        + line[m_call.end():]
                        + f" // [{to_tag} AST Fix] Added required param(s): {', '.join(missing_params)}"
                    )
                    return (
                        refactored,
                        f"Injected newly required parameter(s) `{', '.join(missing_params)}` mandated by {to_tag} AST signature `{new_node.raw_signature if new_node else symbol}`.",
                    )

            # 7. AST Contract Diff: Added Exceptions
            added_exc = ast_diff.details.get("added_exceptions", [])
            if added_exc:
                exc_str = ", ".join(added_exc)
                refactored = (
                    f"{indent}try {{\n"
                    f"{indent}  {stripped}\n"
                    f"{indent}}} catch (err) {{ // [{to_tag} AST Fix] Handle newly thrown {exc_str}\n"
                    f"{indent}  throw err;\n"
                    f"{indent}}}"
                )
                return refactored, f"Wrapped `{symbol}` call in `try/catch` to handle `{exc_str}` introduced in {to_tag}."

        # 8. Removed API symbol
        if change_type == "removed":
            refactored = f"{indent}// [REMOVED IN {to_tag}] {stripped} -> Migrate to {to_tag} replacement API"
            return refactored, f"Commented out call to `{symbol}` because this API was removed in {to_tag}."

        # 9. Generic fallback annotation for breaking / silent / deprecated changes
        tag_label = "Silent Behavior Fix" if is_silent else "Breaking Upgrade Fix"
        refactored = f"{line.rstrip()} // [{to_tag} {tag_label}] Review '{symbol}': {summary[:90]}"
        return refactored, f"Annotated `{symbol}` call site with {to_tag} migration guard ({summary[:120]})."

    def scan_code_snippet(
        self,
        code_snippet: str,
        from_tag: str,
        to_tag: str,
        old_doc_content: str,
        new_doc_content: str,
        stored_changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Scans every line of `code_snippet` against both `stored_changes` and live AST
        contract diffs computed between `old_doc_content` (`from_tag`) and `new_doc_content` (`to_tag`).
        """
        old_secs = self._parse_doc_sections(old_doc_content)
        new_secs = self._parse_doc_sections(new_doc_content)

        old_ast_map: Dict[str, Tuple[str, str, FunctionASTNode]] = {}
        for sec_name, body in old_secs.items():
            node = ast_signature_parser.extract_section_ast(sec_name, body)
            old_ast_map[node.symbol_name] = (sec_name, body, node)

        new_ast_map: Dict[str, Tuple[str, str, FunctionASTNode]] = {}
        for sec_name, body in new_secs.items():
            node = ast_signature_parser.extract_section_ast(sec_name, body)
            new_ast_map[node.symbol_name] = (sec_name, body, node)

        # Build unified vulnerability rules keyed by canonical symbol / identifier
        vulnerability_rules: List[Dict[str, Any]] = []

        # 1. Rules from AST structural comparison between old_doc_content and new_doc_content
        for sym_name, (old_sec, old_body, old_node) in old_ast_map.items():
            if sym_name not in new_ast_map:
                vulnerability_rules.append({
                    "symbol": sym_name,
                    "section": old_sec,
                    "change_type": "removed",
                    "severity": "CRITICAL",
                    "is_breaking": True,
                    "is_silent": True,
                    "summary": f"API symbol `{sym_name}` was removed in {to_tag}.",
                    "excerpt": old_body[:280],
                    "ast_diff": None,
                    "old_node": old_node,
                    "new_node": None,
                })
            else:
                new_sec, new_body, new_node = new_ast_map[sym_name]
                if old_body.strip() != new_body.strip() or old_sec != new_sec:
                    ast_diff = ast_signature_parser.compare_ast_nodes(
                        old_node=old_node,
                        new_node=new_node,
                        old_body=old_body,
                        new_body=new_body,
                    )
                    if ast_diff and (
                        ast_diff.is_breaking
                        or ast_diff.change_category in ("breaking", "deprecated", "behavioral", "removed")
                    ):
                        # Check if mentioned in stored non-silent changelog
                        is_silent = True
                        for sc in stored_changes:
                            if sym_name.lower() in (sc.get("summary", "") or "").lower() and not sc.get("is_silent", False):
                                is_silent = False
                                break
                        vulnerability_rules.append({
                            "symbol": sym_name,
                            "section": new_sec,
                            "change_type": ast_diff.change_category,
                            "severity": ast_diff.severity_level.upper(),
                            "is_breaking": ast_diff.is_breaking,
                            "is_silent": is_silent,
                            "summary": ast_diff.proof_summary,
                            "excerpt": new_body[:280],
                            "ast_diff": ast_diff,
                            "old_node": old_node,
                            "new_node": new_node,
                        })

        # 2. Supplement with stored DocumentChange records (including intermediate version jumps)
        existing_syms = {r["symbol"].lower() for r in vulnerability_rules}
        for sc in stored_changes:
            c_type = str(sc.get("change_type", "")).lower().replace("changetype.", "")
            if c_type == "added" and not sc.get("is_breaking"):
                continue
            loc = sc.get("location", "API")
            summary = sc.get("summary", "")
            # Extract candidate symbol from location or backticks in summary
            sym_node = ast_signature_parser.extract_section_ast(loc, summary)
            sym_candidate = sym_node.symbol_name
            if sym_candidate.lower() in ("release notes", "general", "changelog", "api"):
                m_tick = re.search(r"`([A-Za-z0-9_.()`]+)`", summary)
                if m_tick:
                    sym_candidate = m_tick.group(1).split("(")[0].strip("`")
                elif "calltracker" in summary.lower():
                    sym_candidate = "assert.CallTracker"
                elif "deepequal" in summary.lower():
                    sym_candidate = "assert.deepEqual"

            if sym_candidate.lower() not in existing_syms:
                existing_syms.add(sym_candidate.lower())
                vulnerability_rules.append({
                    "symbol": sym_candidate,
                    "section": loc,
                    "change_type": c_type or "modified",
                    "severity": str(sc.get("severity", "HIGH")).upper().replace("changeseverity.", ""),
                    "is_breaking": bool(sc.get("is_breaking", False)),
                    "is_silent": bool(sc.get("is_silent", False)),
                    "summary": summary,
                    "excerpt": (sc.get("new_content") or sc.get("old_content") or summary)[:280],
                    "ast_diff": None,
                    "old_node": None,
                    "new_node": None,
                })

        # Scan code_snippet line by line
        lines = code_snippet.splitlines()
        line_findings: List[Dict[str, Any]] = []
        refactored_lines: List[str] = []

        # Track whether the snippet instantiates a CallTracker variable (e.g. `const tracker = new assert.CallTracker()`)
        tracker_vars: List[str] = ["tracker"]
        for raw_line in lines:
            m_tr = re.search(r"(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*new\s+assert\.CallTracker", raw_line)
            if m_tr and m_tr.group(1) not in tracker_vars:
                tracker_vars.append(m_tr.group(1))

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("#"):
                refactored_lines.append(line)
                continue

            matched_rule: Optional[Dict[str, Any]] = None
            low_line = stripped.lower()

            for rule in vulnerability_rules:
                sym = rule["symbol"]
                short_sym = sym.split(".")[-1] if "." in sym else sym
                # Match full symbol (e.g., assert.deepEqual) or method call (e.g., .deepEqual() or tracker.calls())
                if sym.lower() in low_line:
                    matched_rule = rule
                    break
                if len(short_sym) >= 4 and re.search(r"\b" + re.escape(short_sym) + r"\s*\(", stripped):
                    matched_rule = rule
                    break
                # Special handling for CallTracker instance methods (.calls / .verify)
                if "calltracker" in sym.lower() or "calls" in sym.lower():
                    if any(f"{tv}.calls(" in stripped or f"{tv}.verify(" in stripped for tv in tracker_vars):
                        matched_rule = rule
                        break

            # Additional heuristic check if `.calls(` or `.verify(` is used on a CallTracker instance
            # when CallTracker is deprecated/modified in target version
            if not matched_rule and any(f"{tv}.calls(" in stripped or f"{tv}.verify(" in stripped for tv in tracker_vars):
                for rule in vulnerability_rules:
                    if "calltracker" in rule["symbol"].lower() or "calltracker" in rule["summary"].lower():
                        matched_rule = rule
                        break

            if matched_rule:
                sym = matched_rule["symbol"]
                c_type = matched_rule["change_type"]
                is_silent = bool(matched_rule["is_silent"])
                is_breaking = bool(matched_rule["is_breaking"])
                severity = matched_rule["severity"]
                summary = matched_rule["summary"]

                # Check if call-site arity specifically violates new_node required params
                new_node: Optional[FunctionASTNode] = matched_rule.get("new_node")
                if new_node and new_node.required_param_count > 0:
                    req_params = [p for p in new_node.params if not p.is_optional]
                    arity = self._extract_call_arity(stripped, sym)
                    if arity is not None and arity < len(req_params):
                        is_breaking = True
                        severity = "CRITICAL"
                        req_names = ", ".join(p.name for p in req_params)
                        summary = (
                            f"Arity mismatch at call site: passed {arity} arg(s), but {to_tag} signature "
                            f"`{new_node.raw_signature}` requires {len(req_params)} ({req_names}). "
                            + summary
                        )

                refactored_line, fix_explanation = self._auto_refactor_line(
                    line=line,
                    symbol=sym,
                    change_type=c_type,
                    is_silent=is_silent,
                    summary=summary,
                    to_tag=to_tag,
                    ast_diff=matched_rule.get("ast_diff"),
                    new_node=new_node,
                )
                refactored_lines.append(refactored_line)

                line_findings.append({
                    "line_number": idx,
                    "original_line": line,
                    "refactored_line": refactored_line,
                    "symbol": sym,
                    "change_type": "silent" if is_silent and c_type not in ("removed", "deprecated") else c_type,
                    "severity": severity,
                    "is_breaking": is_breaking,
                    "is_silent": is_silent,
                    "issue_summary": summary,
                    "fix_explanation": fix_explanation,
                    "citation": {
                        "version_tag": to_tag,
                        "section": matched_rule["section"],
                        "excerpt": matched_rule["excerpt"],
                    },
                })
            else:
                refactored_lines.append(line)

        refactored_code = "\n".join(refactored_lines)
        unified_diff = "".join(
            difflib.unified_diff(
                code_snippet.splitlines(keepends=True),
                refactored_code.splitlines(keepends=True),
                fromfile=f"production_snippet ({from_tag})",
                tofile=f"refactored_snippet ({to_tag})",
                lineterm="",
            )
        )

        breaking_lines = sum(1 for f in line_findings if f["is_breaking"])
        silent_lines = sum(1 for f in line_findings if f["is_silent"])
        deprecated_lines = sum(1 for f in line_findings if f["change_type"] == "deprecated")

        # Calculate Compatibility Score (0 - 100%) and Risk Level
        penalty = (
            breaking_lines * 28
            + silent_lines * 18
            + deprecated_lines * 12
            + max(0, len(line_findings) - breaking_lines - deprecated_lines) * 8
        )
        compatibility_score = max(0, min(100, 100 - penalty))

        if breaking_lines >= 2 or (breaking_lines >= 1 and silent_lines >= 1):
            risk_level = "CRITICAL"
        elif breaking_lines >= 1 or silent_lines >= 1 or deprecated_lines >= 2:
            risk_level = "HIGH"
        elif len(line_findings) >= 1:
            risk_level = "MODERATE"
        else:
            risk_level = "SAFE"

        return {
            "from_tag": from_tag,
            "to_tag": to_tag,
            "risk_level": risk_level,
            "compatibility_score": compatibility_score,
            "summary_counts": {
                "total_lines_scanned": len(lines),
                "vulnerable_lines": len(line_findings),
                "breaking_lines": breaking_lines,
                "silent_lines": silent_lines,
                "deprecated_lines": deprecated_lines,
            },
            "line_findings": line_findings,
            "original_code": code_snippet,
            "refactored_code": refactored_code,
            "unified_diff": unified_diff,
        }


code_scanner_service = CodeScannerService()
