from app.services.diff_service import diff_service
from app.services.ast_parser_service import ast_signature_parser
from app.models.change import ChangeType, ChangeSeverity


def test_explicit_changelog_extraction():
    content = """# Release Notes
## Changelog
- **[Breaking]**: Removed assert.CallTracker
- **[Added]**: Introduced partialDeepStrictEqual
- **[Deprecated]**: Legacy formatting is deprecated
"""
    changes = diff_service.extract_explicit_changelog(content)
    assert len(changes) == 3
    types = [c["change_type"] for c in changes]
    assert ChangeType.BREAKING in types
    assert ChangeType.ADDED in types
    assert ChangeType.DEPRECATED in types


def test_implicit_silent_change_detection():
    old_doc = """# API Doc
## Features
### Function A
This function returns 42.

### Legacy Support
Legacy formatting is active.
"""
    new_doc = """# API Doc
## Features
### Function A
This function throws an error if input is invalid.

### Function B
New function added here.
"""
    # Legacy Support was silently removed, Function A behavior was modified
    changes, summary = diff_service.compute_all_changes(old_doc, new_doc, "v1.0", "v2.0")
    assert summary["total"] >= 2
    assert summary["breaking"] >= 1 or summary["removed"] >= 1
    assert any(c.get("is_silent") for c in changes)


def test_posix_and_typescript_signature_ast_parsing():
    node_posix = ast_signature_parser.extract_section_ast(
        "assert.deepEqual(actual, expected[, message])",
        "Tests for deep equality between actual and expected. Throws AssertionError.",
    )
    assert node_posix.symbol_name == "assert.deepEqual"
    assert len(node_posix.params) == 3
    assert node_posix.required_param_count == 2
    assert node_posix.params[0].name == "actual" and not node_posix.params[0].is_optional
    assert node_posix.params[1].name == "expected" and not node_posix.params[1].is_optional
    assert node_posix.params[2].name == "message" and node_posix.params[2].is_optional
    assert "AssertionError" in node_posix.thrown_exceptions

    node_ts = ast_signature_parser.extract_section_ast(
        "createServer(host: string, port: number = 8080, tls?: boolean): Server",
        "Creates an HTTP server instance.",
    )
    assert node_ts.symbol_name == "createServer"
    assert node_ts.return_type == "Server"
    assert node_ts.required_param_count == 1
    assert node_ts.params[0].type_annotation == "string"
    assert node_ts.params[1].is_optional and node_ts.params[1].default_value == "8080"
    assert node_ts.params[2].is_optional and node_ts.params[2].type_annotation == "boolean"


def test_python_native_ast_code_block_diffing():
    old_sec = """```python
def connect_db(uri: str, timeout: int = 30) -> bool:
    return True
```"""
    new_sec = """```python
def connect_db(uri: str, timeout: int, retries: int) -> bool:
    if not uri:
        raise ValueError("Invalid URI")
    return True
```"""
    old_node = ast_signature_parser.extract_section_ast("connect_db", old_sec)
    new_node = ast_signature_parser.extract_section_ast("connect_db", new_sec)

    assert old_node.required_param_count == 1
    assert new_node.required_param_count == 3
    assert "ValueError" in new_node.thrown_exceptions

    diff = ast_signature_parser.compare_ast_nodes(old_node, new_node, old_sec, new_sec)
    assert diff is not None
    assert diff.is_breaking is True
    assert diff.change_category == "breaking"
    assert "Required parameter arity increased from 1 to 3" in diff.proof_summary


def test_signature_arity_break_across_header_rename():
    """
    Verifies that when a section heading changes its parameter signature
    (e.g. `tracker.calls([fn][, exact])` -> `tracker.calls(fn, exact)`),
    DiffService correlates both headings to the same AST symbol `tracker.calls`
    and flags a breaking parameter contract change rather than separate delete+add.
    """
    old_doc = """# Node Assert
### tracker.calls([fn][, exact])
Wraps a function to track calls. Both fn and exact are optional in v14.
"""
    new_doc = """# Node Assert
### tracker.calls(fn, exact)
Wraps a function to track calls. Both fn and exact are now strictly required.
"""
    changes, summary = diff_service.compute_all_changes(old_doc, new_doc, "v14.0.0", "v15.14.0")
    assert len(changes) == 1
    ch = changes[0]
    assert ch["change_type"] == ChangeType.BREAKING
    assert ch["is_breaking"] is True
    assert ch["is_silent"] is True
    assert "PARAMETER" in ch["summary"]


def test_operator_semantic_shift_silent_detection():
    old_doc = """# Node Assert
### assert.deepEqual(actual, expected[, message])
Primitive values are compared with the `==` coercive operator.
"""
    new_doc = """# Node Assert
### assert.deepEqual(actual, expected[, message])
Primitive values and prototypes are now compared using `===` strict equality and `Object.is`.
"""
    changes, _ = diff_service.compute_all_changes(old_doc, new_doc, "v14.0.0", "v15.14.0")
    assert len(changes) == 1
    ch = changes[0]
    assert ch["is_breaking"] is True
    assert ch["is_silent"] is True
    assert "OPERATOR_SEMANTIC_SHIFT" in ch["summary"]
    assert "===" in ch["ast_details"]["new_operators"]


def test_return_type_and_exception_ast_nodes_breaking_proof():
    """
    Verifies Part 2 Item 1:
    - Parses TypeScript/JavaScript functions into FunctionNode, ParamNode, ReturnTypeNode, and ExceptionNode.
    - Mathematically proves breaking changes when ReturnTypeNode expands to nullable (`User` -> `User | null`)
      or a new ExceptionNode (`throw new TypeError`) is introduced in the code block.
    """
    old_body = """```typescript
function getUserProfile(userId: string): UserProfile {
    return db.find(userId);
}
```"""
    new_body = """```typescript
function getUserProfile(userId: string): UserProfile | null {
    if (!userId) {
        throw new TypeError("Invalid userId");
    }
    return db.find(userId);
}
```"""
    old_node = ast_signature_parser.extract_section_ast("getUserProfile(userId: string): UserProfile", old_body)
    new_node = ast_signature_parser.extract_section_ast("getUserProfile(userId: string): UserProfile | null", new_body)

    assert old_node.return_node is not None
    assert old_node.return_node.raw_type == "UserProfile"
    assert old_node.return_node.is_nullable is False

    assert new_node.return_node is not None
    assert new_node.return_node.is_nullable is True
    assert any(e.error_type == "TypeError" for e in new_node.exception_nodes)

    diff = ast_signature_parser.compare_ast_nodes(old_node, new_node, old_body, new_body)
    assert diff is not None
    assert diff.is_breaking is True
    assert "RETURN_TYPE_NULLABLE_EXPANSION" in diff.proof_summary
    assert "TypeError" in diff.proof_summary
    assert diff.details["new_ast"]["return_node"]["node_type"] == "ReturnTypeNode"
    assert diff.details["new_ast"]["exception_nodes"][0]["node_type"] == "ExceptionNode"


def test_openapi_endpoint_ast_parsing_and_contract_break():
    """
    Verifies OpenAPI / REST Endpoint AST parsing into FunctionNode, ParamNode, ReturnTypeNode, and ExceptionNode.
    """
    old_openapi = """
Parameters:
- `amount` (number, required)
- `currency` (string, required)
- `idempotency_key` (string, optional)

Responses:
- 200: `ChargeReceipt`
- 400: Bad Request
"""
    new_openapi = """
Parameters:
- `amount` (number, required)
- `currency` (string, required)
- `idempotency_key` (string, required)

Responses:
- 200: `ChargeReceipt`
- 400: Bad Request
- 422: Unprocessable Idempotency Key
"""
    old_node = ast_signature_parser.extract_section_ast("POST /v1/payments/charge", old_openapi)
    new_node = ast_signature_parser.extract_section_ast("POST /v1/payments/charge", new_openapi)

    assert old_node.http_method == "POST"
    assert old_node.endpoint_path == "/v1/payments/charge"
    assert old_node.required_param_count == 2
    assert new_node.required_param_count == 3
    assert old_node.return_node is not None and old_node.return_node.raw_type == "ChargeReceipt"
    assert any(e.http_status_code == 422 for e in new_node.exception_nodes)

    diff = ast_signature_parser.compare_ast_nodes(old_node, new_node, old_openapi, new_openapi)
    assert diff is not None
    assert diff.is_breaking is True
    assert "idempotency_key" in diff.proof_summary
    assert "HTTP_422" in diff.proof_summary


def test_non_breaking_optional_parameter_extension_proof():
    """
    Mathematically proves that adding an optional parameter with a default value at the end
    of a function signature is classified as NON-BREAKING (`is_breaking == False`).
    """
    old_node = ast_signature_parser.extract_section_ast(
        "fetchMetrics(projectId: string): MetricsReport",
        "Fetches metrics report.",
    )
    new_node = ast_signature_parser.extract_section_ast(
        "fetchMetrics(projectId: string, includeHistogram: boolean = false): MetricsReport",
        "Fetches metrics report with optional histogram.",
    )
    diff = ast_signature_parser.compare_ast_nodes(
        old_node, new_node, "Fetches metrics report.", "Fetches metrics report with optional histogram."
    )
    assert diff is not None
    assert diff.is_breaking is False
    assert diff.ast_diff_type == "PARAMETER_EXTENDED"
    assert "includeHistogram" in diff.proof_summary

