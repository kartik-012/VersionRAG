import pytest
from app.services.ast_parser_service import (
    ParamASTNode,
    ReturnTypeNode,
    ExceptionNode,
    FunctionASTNode,
    ASTContractDiff,
    ast_signature_parser,
)


def test_param_ast_node_constraint_detection():
    # Previous: optional param with default
    old_p = ParamASTNode(name="timeout", position=1, is_optional=True, default_value="30")
    # New: mandatory param without default (BREAKING)
    new_p_breaking = ParamASTNode(name="timeout", position=1, is_optional=False, default_value=None)
    assert new_p_breaking.has_breaking_constraint_against(old_p) is True

    # New: optional param with default preserved (NON-BREAKING)
    new_p_safe = ParamASTNode(name="timeout", position=1, is_optional=True, default_value="60")
    assert new_p_safe.has_breaking_constraint_against(old_p) is False


def test_function_ast_node_get_param():
    fn = FunctionASTNode(
        symbol_name="authenticate",
        raw_signature="authenticate(user: str, password: str, token: Optional[str] = None)",
        section_title="Authentication Module",
        params=[
            ParamASTNode(name="user", position=0, is_optional=False),
            ParamASTNode(name="password", position=1, is_optional=False),
            ParamASTNode(name="token", position=2, is_optional=True, default_value="None"),
        ],
    )

    assert fn.required_param_count == 2
    assert fn.total_param_count == 3
    assert fn.get_param_by_name("USER") is not None
    assert fn.get_param_by_name("user").position == 0
    assert fn.get_param_by_name("token").is_optional is True
    assert fn.get_param_by_name("non_existent") is None


def test_return_type_node_promise_parsing():
    ret = ReturnTypeNode.from_type_string("Promise<UserResponse>", is_async_fn=True)
    assert ret is not None
    assert ret.is_async_promise is True
    assert ret.inner_type == "UserResponse"


def test_ast_contract_diff_markdown_table():
    diff1 = ASTContractDiff(
        symbol_name="assert.deepEqual",
        ast_diff_type="operator_change",
        is_breaking=True,
        severity_level="critical",
        change_category="breaking",
        old_signature="assert.deepEqual(a, b)",
        new_signature="assert.deepEqual(a, b)",
        proof_summary="Prototype comparison changed to strict equality",
    )
    diff2 = ASTContractDiff(
        symbol_name="assert.CallTracker",
        ast_diff_type="lifecycle_deprecation",
        is_breaking=False,
        severity_level="medium",
        change_category="deprecated",
        old_signature="class assert.CallTracker",
        new_signature=None,
        proof_summary="Deprecated in favor of diagnostics_channel",
    )

    table = ASTContractDiff.format_markdown_table([diff1, diff2])
    assert "| `assert.deepEqual` |" in table
    assert "💥 BREAKING" in table
    assert "✅ COMPATIBLE" in table
    assert "| Symbol | Category | Severity |" in table

    # Empty diff list handling
    assert ASTContractDiff.format_markdown_table([]) == "_No contract mutations detected._"
