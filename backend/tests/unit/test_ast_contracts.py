import pytest
from app.services.ast_parser_service import (
    ParamASTNode,
    ReturnTypeNode,
    ExceptionNode,
    FunctionASTNode,
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
