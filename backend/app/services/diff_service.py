import difflib
import re
from typing import List, Dict, Any, Tuple
from app.models.change import ChangeType, ChangeSeverity
from app.services.ast_parser_service import ast_signature_parser, FunctionASTNode

class DiffService:
    @staticmethod
    def generate_unified_diff(old_text: str, new_text: str, from_tag: str, to_tag: str) -> str:
        """Generates unified diff representation with line markers."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"Version {from_tag}",
            tofile=f"Version {to_tag}",
            lineterm=""
        )
        return "".join(diff)

    @staticmethod
    def extract_explicit_changelog(content: str) -> List[Dict[str, Any]]:
        """Extract explicit changes listed in Changelog / Release Notes sections."""
        changes = []
        changelog_match = re.search(r"(?:##|###)\s*(?:Changelog|Release Notes|Changes|History)(.*?)(?=\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
        if not changelog_match:
            return changes

        changelog_body = changelog_match.group(1)
        # Look for bullet points: `- **[Breaking]**: Removed ...`, `- Added ...`, etc.
        bullet_pattern = r"^[-*]\s+(.+)$"
        for line in changelog_body.splitlines():
            line_clean = line.strip()
            m = re.match(bullet_pattern, line_clean)
            if m:
                raw_text = m.group(1).strip()
                # Extract tag inside **[...]** or [...] or **Tag**:
                tag_match = re.search(r"^\*?\*?\[?([a-zA-Z0-9_-]+)\]?\*?\*?\s*:?\s*(.+)$", raw_text)
                if tag_match:
                    tag = tag_match.group(1).lower()
                    desc = tag_match.group(2).strip()
                else:
                    tag = ""
                    desc = raw_text

                change_type = ChangeType.MODIFIED
                severity = ChangeSeverity.MEDIUM
                is_breaking = False

                if "breaking" in tag or "breaking" in raw_text.lower():
                    change_type = ChangeType.BREAKING
                    severity = ChangeSeverity.CRITICAL
                    is_breaking = True
                elif "deprecat" in tag or "deprecat" in raw_text.lower():
                    change_type = ChangeType.DEPRECATED
                    severity = ChangeSeverity.HIGH
                elif "add" in tag or "new" in tag or "introduced" in raw_text.lower() or "added" in raw_text.lower():
                    change_type = ChangeType.ADDED
                    severity = ChangeSeverity.LOW
                elif "remov" in tag or "delete" in tag or "removed" in raw_text.lower():
                    change_type = ChangeType.REMOVED
                    severity = ChangeSeverity.HIGH
                elif "behavior" in tag or "behavior" in raw_text.lower():
                    change_type = ChangeType.BEHAVIORAL
                    severity = ChangeSeverity.MEDIUM

                changes.append({
                    "location": "Release Notes",
                    "change_type": change_type,
                    "severity": severity,
                    "is_silent": False,
                    "is_breaking": is_breaking,
                    "summary": desc,
                    "source": "explicit_changelog",
                    "confidence": 0.95
                })
        return changes

    @staticmethod
    def _is_mentioned_in_changelog(symbol_name: str, section_title: str, explicit_summaries: List[str]) -> bool:
        """Checks whether a symbol or section title is referenced in any explicit changelog entry."""
        sym_clean = symbol_name.lower().strip("`")
        sec_clean = section_title.lower().strip("`")
        tail_sym = sym_clean.split(".")[-1] if "." in sym_clean else sym_clean

        for summary in explicit_summaries:
            s_low = summary.lower()
            if sym_clean in s_low or sec_clean in s_low:
                return True
            if len(tail_sym) > 3 and tail_sym in s_low:
                return True
        return False

    @classmethod
    def detect_implicit_section_diffs(
        cls,
        old_content: str,
        new_content: str,
        explicit_summaries: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Deep AST & API Signature structural diff between two versions.
        Parses each section into a `FunctionASTNode` (parameters, optionality, defaults,
        return types, exceptions, equality operators, and Python AST bodies) and detects
        silent breaking/behavioral changes omitted from release notes.
        """
        changes = []

        # Split into sections by H2/H3 headings (excluding Changelog section itself)
        def parse_sections(text: str) -> Dict[str, str]:
            secs = {}
            current_title = "General"
            buf = []
            for line in text.splitlines():
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

        old_secs = parse_sections(old_content)
        new_secs = parse_sections(new_content)

        # Parse all sections into FunctionASTNodes keyed by canonical symbol_name
        old_ast_map: Dict[str, Tuple[str, str, FunctionASTNode]] = {}
        for sec_name, body in old_secs.items():
            node = ast_signature_parser.extract_section_ast(sec_name, body)
            old_ast_map[node.symbol_name] = (sec_name, body, node)

        new_ast_map: Dict[str, Tuple[str, str, FunctionASTNode]] = {}
        for sec_name, body in new_secs.items():
            node = ast_signature_parser.extract_section_ast(sec_name, body)
            new_ast_map[node.symbol_name] = (sec_name, body, node)

        category_to_enum = {
            "breaking": ChangeType.BREAKING,
            "deprecated": ChangeType.DEPRECATED,
            "removed": ChangeType.REMOVED,
            "added": ChangeType.ADDED,
            "behavioral": ChangeType.BEHAVIORAL,
            "modified": ChangeType.MODIFIED,
        }
        severity_to_enum = {
            "critical": ChangeSeverity.CRITICAL,
            "high": ChangeSeverity.HIGH,
            "medium": ChangeSeverity.MEDIUM,
            "low": ChangeSeverity.LOW,
        }

        # 1. Added Symbols / Sections
        for sym_name, (sec_name, new_body, new_node) in new_ast_map.items():
            if sym_name not in old_ast_map:
                is_silent = not cls._is_mentioned_in_changelog(sym_name, sec_name, explicit_summaries)
                param_sig = f" ({len(new_node.params)} params)" if new_node.params else ""
                changes.append({
                    "location": sec_name,
                    "change_type": ChangeType.ADDED,
                    "severity": ChangeSeverity.LOW,
                    "is_silent": is_silent,
                    "is_breaking": False,
                    "old_content": None,
                    "new_content": new_body[:500],
                    "summary": f"Added new API symbol/section: '{sec_name}'{param_sig}",
                    "source": "ast_structural_diff",
                    "confidence": 0.94,
                })

        # 2. Removed Symbols / Sections
        for sym_name, (sec_name, old_body, old_node) in old_ast_map.items():
            if sym_name not in new_ast_map:
                is_silent = not cls._is_mentioned_in_changelog(sym_name, sec_name, explicit_summaries)
                changes.append({
                    "location": sec_name,
                    "change_type": ChangeType.REMOVED,
                    "severity": ChangeSeverity.CRITICAL,
                    "is_silent": is_silent,
                    "is_breaking": True,
                    "old_content": old_body[:500],
                    "new_content": None,
                    "summary": f"Removed API symbol/section: '{sec_name}'" + (" (Silent removal - not in changelog)" if is_silent else ""),
                    "source": "ast_structural_diff",
                    "confidence": 0.96,
                })

        # 3. Modified Symbols / Sections (Evaluated via ASTContractDiff)
        for sym_name, (old_sec_name, old_body, old_node) in old_ast_map.items():
            if sym_name in new_ast_map:
                new_sec_name, new_body, new_node = new_ast_map[sym_name]
                if old_body.strip() != new_body.strip() or old_sec_name != new_sec_name:
                    ast_diff = ast_signature_parser.compare_ast_nodes(
                        old_node=old_node,
                        new_node=new_node,
                        old_body=old_body,
                        new_body=new_body,
                    )
                    if ast_diff is None:
                        continue

                    is_silent = not cls._is_mentioned_in_changelog(sym_name, new_sec_name, explicit_summaries)
                    change_type = category_to_enum.get(ast_diff.change_category, ChangeType.MODIFIED)
                    severity = severity_to_enum.get(ast_diff.severity_level, ChangeSeverity.MEDIUM)
                    is_breaking = ast_diff.is_breaking

                    silent_suffix = " (Silent change - not in changelog)" if is_silent else ""
                    changes.append({
                        "location": new_sec_name,
                        "change_type": change_type,
                        "severity": severity,
                        "is_silent": is_silent,
                        "is_breaking": is_breaking,
                        "old_content": old_body[:500],
                        "new_content": new_body[:500],
                        "summary": f"Modified behavior in '{new_sec_name}': {ast_diff.proof_summary}{silent_suffix}",
                        "source": "ast_structural_diff",
                        "confidence": 0.93,
                        "ast_details": ast_diff.details,
                    })

        return changes

    def compute_all_changes(
        self,
        old_content: str,
        new_content: str,
        from_tag: str,
        to_tag: str
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Runs both explicit changelog parsing and implicit deep diffing.
        Returns deduplicated changes list + summary count dictionary.
        """
        explicit = self.extract_explicit_changelog(new_content)
        explicit_texts = [c["summary"] for c in explicit]
        implicit = self.detect_implicit_section_diffs(old_content, new_content, explicit_texts)

        all_changes = explicit + implicit

        summary_counts = {
            "total": len(all_changes),
            "added": sum(1 for c in all_changes if c["change_type"] == ChangeType.ADDED),
            "modified": sum(1 for c in all_changes if c["change_type"] == ChangeType.MODIFIED),
            "removed": sum(1 for c in all_changes if c["change_type"] == ChangeType.REMOVED),
            "deprecated": sum(1 for c in all_changes if c["change_type"] == ChangeType.DEPRECATED),
            "behavioral": sum(1 for c in all_changes if c["change_type"] == ChangeType.BEHAVIORAL),
            "breaking": sum(1 for c in all_changes if c.get("is_breaking")),
            "silent": sum(1 for c in all_changes if c.get("is_silent"))
        }

        return all_changes, summary_counts

    def generate_migration_guide(
        self,
        from_tag: str,
        to_tag: str,
        changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes a production-grade step-by-step migration guide from Version A to Version B.
        Includes code refactor transformation snippets and risk grading.
        """
        breaking = [c for c in changes if c.get("is_breaking")]
        deprecated = [c for c in changes if c.get("change_type") == ChangeType.DEPRECATED or c.get("change_type") == "deprecated"]
        behavioral = [c for c in changes if c.get("change_type") == ChangeType.BEHAVIORAL or c.get("change_type") == "behavioral"]
        added = [c for c in changes if c.get("change_type") == ChangeType.ADDED or c.get("change_type") == "added"]

        # Calculate Migration Risk Score
        risk_score = "LOW"
        risk_color = "emerald"
        if len(breaking) >= 2 or len(deprecated) >= 3:
            risk_score = "CRITICAL"
            risk_color = "rose"
        elif len(breaking) >= 1 or len(behavioral) >= 2:
            risk_score = "HIGH"
            risk_color = "amber"
        elif len(deprecated) >= 1:
            risk_score = "MEDIUM"
            risk_color = "yellow"

        # Generate Actionable Refactoring Steps
        steps = []
        step_num = 1

        if breaking:
            for b in breaking:
                loc = b.get("location", "API")
                steps.append({
                    "step": step_num,
                    "title": f"Refactor Breaking Change in '{loc}'",
                    "severity": "CRITICAL",
                    "description": b.get("summary", "Breaking API signature or behavior change."),
                    "code_before": f"// Legacy code ({from_tag})\n{loc}(...); // Relying on legacy loose equality or implicit conversion",
                    "code_after": f"// Modernized code ({to_tag})\ntry {{\n  {loc}(...); // Explicit error handling with cause inspection\n}} catch (err) {{\n  console.error(err.cause);\n}}"
                })
                step_num += 1

        if deprecated:
            for d in deprecated:
                loc = d.get("location", "API")
                steps.append({
                    "step": step_num,
                    "title": f"Replace Deprecated Feature: '{loc}'",
                    "severity": "HIGH",
                    "description": d.get("summary", "This API is marked deprecated and will be removed in future versions."),
                    "code_before": f"// Deprecated in {from_tag}\nconst tracker = new assert.CallTracker();",
                    "code_after": f"// Recommended replacement in {to_tag}\nconst diagnostics = require('diagnostics_channel');"
                })
                step_num += 1

        if added:
            for a in added[:2]:
                loc = a.get("location", "API")
                steps.append({
                    "step": step_num,
                    "title": f"Leverage New Feature: '{loc}'",
                    "severity": "LOW",
                    "description": a.get("summary", "New functionality available to improve codebase reliability."),
                    "code_before": "// Custom manual check\nconst match = obj.a === 1 && obj.b === 2;",
                    "code_after": f"// Native {to_tag} implementation\nassert.partialDeepStrictEqual(obj, {{ a: 1, b: 2 }});"
                })
                step_num += 1

        # Markdown formatted guide
        md_content = f"# Migration Guide: {from_tag} -> {to_tag}\n\n"
        md_content += f"**Overall Risk Level:** {risk_score}\n\n"
        md_content += "## Summary of Intervening Changes\n"
        md_content += f"- **Breaking Changes:** {len(breaking)}\n"
        md_content += f"- **Deprecated APIs:** {len(deprecated)}\n"
        md_content += f"- **Behavioral Adjustments:** {len(behavioral)}\n"
        md_content += f"- **New Capabilities:** {len(added)}\n\n"
        md_content += "## Step-by-Step Refactoring Instructions\n\n"
        for st in steps:
            md_content += f"### Step {st['step']}: {st['title']}\n"
            md_content += f"{st['description']}\n\n"
            md_content += "```javascript\n" + st['code_before'] + "\n\n" + st['code_after'] + "\n```\n\n"

        return {
            "from_tag": from_tag,
            "to_tag": to_tag,
            "risk_score": risk_score,
            "risk_color": risk_color,
            "breaking_count": len(breaking),
            "deprecated_count": len(deprecated),
            "added_count": len(added),
            "steps": steps,
            "markdown_guide": md_content
        }

    def extract_symbol_history(self, symbol_name: str, versions: List[Any]) -> List[Dict[str, Any]]:
        """Tracks the exact definition and behavior of an API symbol across all releases."""
        history = []
        for v in versions:
            content = v.raw_content or ""
            # Search for section or function definition mentioning the symbol
            matches = []
            for line in content.splitlines():
                if symbol_name.lower() in line.lower() and (line.startswith("#") or "function" in line or "(" in line):
                    matches.append(line.strip().lstrip("#").strip())
            
            snippet = ""
            for sec in content.split("\n\n"):
                if symbol_name.lower() in sec.lower():
                    snippet = sec.strip()
                    break

            status = "Supported"
            if "deprecated" in snippet.lower():
                status = "Deprecated"
            elif "removed" in snippet.lower():
                status = "Removed"
            elif "release candidate" in snippet.lower() or "experimental" in snippet.lower():
                status = "Experimental / RC"
            elif not snippet:
                status = "Not Present"

            history.append({
                "version_tag": v.version_tag,
                "version_order": v.version_order,
                "status": status,
                "signature": matches[0] if matches else symbol_name,
                "documentation_excerpt": snippet[:400] if snippet else f"Symbol '{symbol_name}' was not documented in this release.",
                "has_definition": bool(snippet)
            })
        return history

    def synthesize_release_notes(self, version_tag: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesizes structured release notes and executive summary."""
        breaking = [c for c in changes if c.get("is_breaking")]
        added = [c for c in changes if c.get("change_type") in [ChangeType.ADDED, "added"]]
        deprecated = [c for c in changes if c.get("change_type") in [ChangeType.DEPRECATED, "deprecated"]]
        silent = [c for c in changes if c.get("is_silent")]

        executive_summary = (
            f"Release {version_tag} introduces {len(added)} new features, with {len(breaking)} breaking changes "
            f"and {len(deprecated)} deprecations. Automatic change intelligence flagged {len(silent)} undocumented differences."
        )

        return {
            "version_tag": version_tag,
            "executive_summary": executive_summary,
            "breaking_changes": [b.get("summary") for b in breaking],
            "new_features": [a.get("summary") for a in added],
            "deprecations": [d.get("summary") for d in deprecated],
            "silent_changes": [s.get("summary") for s in silent]
        }

diff_service = DiffService()
