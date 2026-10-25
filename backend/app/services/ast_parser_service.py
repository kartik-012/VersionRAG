"""
Real Abstract Syntax Tree (AST) & Formal API Signature Parser Engine.

Provides deterministic structural analysis of:
1. Python code blocks via Python's native `ast` module (`ast.FunctionDef`, `ast.AsyncFunctionDef`, `ast.ClassDef`, `ast.Raise`).
2. JavaScript / TypeScript / Node.js API Signatures (including POSIX/Node bracket optionality `fn(a[, b[, c]])` and TS `fn(a: T, b?: U): Promise<R>`).
3. OpenAPI / REST Endpoint Specifications (`POST /v1/payments/charge`, path/query/body parameters, HTTP response & error status contracts).
4. Semantic Contract Invariants (`FunctionNode`, `ParamNode`, `ReturnTypeNode`, `ExceptionNode`, equality operators `==` vs `===` / `Object.is`).
"""

import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any


@dataclass
class ParamASTNode:
    """Represents a single parsed parameter (`ParamNode`) in a function or OpenAPI endpoint."""
    name: str
    position: int
    is_optional: bool = False
    default_value: Optional[str] = None
    type_annotation: Optional[str] = None
    is_variadic: bool = False
    param_source: str = "argument"  # argument, path, query, body, header

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ParamNode",
            "name": self.name,
            "position": self.position,
            "is_optional": self.is_optional,
            "default_value": self.default_value,
            "type_annotation": self.type_annotation,
            "is_variadic": self.is_variadic,
            "param_source": self.param_source,
        }

    def has_breaking_constraint_against(self, previous: "ParamASTNode") -> bool:
        """Determines if this parameter introduces a breaking constraint relative to a previous version."""
        # 1. Previously optional parameter turned mandatory
        if previous.is_optional and not self.is_optional:
            return True
        # 2. Existing parameter lost its default fallback
        if previous.default_value is not None and self.default_value is None and not self.is_optional:
            return True
        return False


@dataclass
class ReturnTypeNode:
    """Represents a structured return type contract (`ReturnTypeNode`)."""
    raw_type: str
    is_nullable: bool = False
    is_async_promise: bool = False
    inner_type: Optional[str] = None
    http_status_code: Optional[int] = None

    @classmethod
    def from_type_string(cls, raw: Optional[str], is_async_fn: bool = False) -> Optional["ReturnTypeNode"]:
        if not raw or not raw.strip():
            if is_async_fn:
                return cls(raw_type="Promise<void>", is_nullable=False, is_async_promise=True, inner_type="void")
            return None
        clean = raw.strip().strip("`")
        lower = clean.lower()
        is_null = any(tok in lower for tok in ("null", "undefined", "none", "optional[")) or clean.endswith("?")
        is_prom = is_async_fn or lower.startswith("promise<") or lower.startswith("awaitable[") or lower.startswith("future<")
        inner = clean
        m_prom = re.match(r"^(?:Promise|Awaitable|Future)\s*[<\[](.+)[>\]]$", clean, re.IGNORECASE)
        if m_prom:
            inner = m_prom.group(1).strip()
            is_prom = True
        return cls(
            raw_type=clean,
            is_nullable=is_null,
            is_async_promise=is_prom,
            inner_type=inner,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ReturnTypeNode",
            "raw_type": self.raw_type,
            "is_nullable": self.is_nullable,
            "is_async_promise": self.is_async_promise,
            "inner_type": self.inner_type,
            "http_status_code": self.http_status_code,
        }


@dataclass
class ExceptionNode:
    """Represents a structured exception or HTTP error contract (`ExceptionNode`)."""
    error_type: str
    condition: Optional[str] = None
    http_status_code: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "ExceptionNode",
            "error_type": self.error_type,
            "condition": self.condition,
            "http_status_code": self.http_status_code,
        }


@dataclass
class FunctionASTNode:
    """Represents a structured AST node (`FunctionNode`) for an API symbol, function, method, class, or OpenAPI endpoint."""
    symbol_name: str
    raw_signature: str
    section_title: str
    params: List[ParamASTNode] = field(default_factory=list)
    return_type: Optional[str] = None
    return_node: Optional[ReturnTypeNode] = None
    thrown_exceptions: Set[str] = field(default_factory=set)
    exception_nodes: List[ExceptionNode] = field(default_factory=list)
    operators_used: Set[str] = field(default_factory=set)
    lifecycle_state: str = "stable"  # stable, experimental, deprecated, removed
    is_async: bool = False
    http_method: Optional[str] = None
    endpoint_path: Optional[str] = None
    code_ast_dump: Optional[str] = None

    @property
    def required_param_count(self) -> int:
        return sum(1 for p in self.params if not p.is_optional and not p.is_variadic)

    @property
    def total_param_count(self) -> int:
        return len(self.params)

    def get_param_by_name(self, name: str) -> Optional[ParamASTNode]:
        """Look up a parameter node by its variable or argument name."""
        for p in self.params:
            if p.name.strip().lower() == name.strip().lower():
                return p
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_type": "FunctionNode",
            "symbol_name": self.symbol_name,
            "raw_signature": self.raw_signature,
            "section_title": self.section_title,
            "is_async": self.is_async,
            "http_method": self.http_method,
            "endpoint_path": self.endpoint_path,
            "lifecycle_state": self.lifecycle_state,
            "required_param_count": self.required_param_count,
            "total_param_count": self.total_param_count,
            "params": [p.to_dict() for p in self.params],
            "return_node": self.return_node.to_dict() if self.return_node else None,
            "exception_nodes": [e.to_dict() for e in self.exception_nodes],
            "operators_used": sorted(self.operators_used),
        }


# Canonical aliases matching Part 2 specification
ParamNode = ParamASTNode
FunctionNode = FunctionASTNode


@dataclass
class ASTContractDiff:
    """Represents a mathematically verified AST / Contract mutation between two versions."""
    symbol_name: str
    ast_diff_type: str
    is_breaking: bool
    severity_level: str  # critical, high, medium, low
    change_category: str  # breaking, deprecated, removed, added, behavioral, modified
    old_signature: Optional[str]
    new_signature: Optional[str]
    proof_summary: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol_name": self.symbol_name,
            "ast_diff_type": self.ast_diff_type,
            "is_breaking": self.is_breaking,
            "severity_level": self.severity_level,
            "change_category": self.change_category,
            "old_signature": self.old_signature,
            "new_signature": self.new_signature,
            "proof_summary": self.proof_summary,
            "details": self.details,
        }


class ASTSignatureParserService:
    """
    Parses Python AST code blocks, JS/TS/API formal signatures, and OpenAPI REST specifications
    into `FunctionNode`, `ParamNode`, `ReturnTypeNode`, and `ExceptionNode` trees,
    and computes deterministic mathematical breaking vs. non-breaking proofs.
    """

    # Matches signatures like `assert.deepEqual(actual, expected[, message])`, `async function fetchUser(id: string): Promise<User>`, or `def foo(a, b=1) -> int:`
    _SIGNATURE_RE = re.compile(
        r"^(?:Class:\s*)?(async\s+)?(?:function\s+|def\s+)?([a-zA-Z_$][a-zA-Z0-9_$.]*)\s*\(([^)]*)\)(?:\s*(?:->|:)\s*([a-zA-Z0-9_<>\[\]|?\s,]+?))?\s*:?$"
    )
    _OPENAPI_HEADER_RE = re.compile(
        r"^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+(/[a-zA-Z0-9_/\-{}:.]*)",
        re.IGNORECASE,
    )
    _CLASS_HEADER_RE = re.compile(r"^Class:\s*([a-zA-Z_$][a-zA-Z0-9_$.]*)")
    _FENCED_CODE_RE = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)
    _EXCEPTION_RE = re.compile(
        r"\b(AssertionError|TypeError|RangeError|SyntaxError|ReferenceError|ValueError|KeyError|RuntimeError|PermissionError|TimeoutError|AuthenticationError|ValidationError|ERR_[A-Z0-9_]+)\b"
    )
    _JS_THROW_RE = re.compile(r"throw\s+new\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(")
    _HTTP_ERROR_STATUS_RE = re.compile(
        r"(?:status|response|code|error|returns?|\bhttp)?\s*\b(400|401|403|404|409|422|429|500|502|503)\b(?:\s*[:\-]\s*([A-Za-z0-9_ ]+))?",
        re.IGNORECASE,
    )
    _RETURN_CONTRACT_RE = re.compile(
        r"(?:Returns|Return type|@returns?)\s*:?\s*`?\{?<?([a-zA-Z0-9_\[\]|<>?\s]+?)>?\}?`?(?:\n|$|\.)",
        re.IGNORECASE,
    )

    @classmethod
    def parse_parameter_list(cls, raw_params: str) -> List[ParamASTNode]:
        """
        Parses parameter strings supporting:
        - POSIX/Node bracket optionality: `actual, expected[, message]` or `[fn][, exact]`
        - TypeScript/Python defaults & types: `options?: ServerOptions, port: number = 8080`
        """
        if not raw_params or not raw_params.strip():
            return []

        s = raw_params.strip()
        params: List[ParamASTNode] = []

        # Detect which parameters appear inside `[...]` optional brackets
        optional_names: Set[str] = set()
        for bracket_match in re.finditer(r"\[([^\[\]]+)\]", s):
            inner = bracket_match.group(1)
            for tok in re.findall(r"[a-zA-Z_$][a-zA-Z0-9_$]*", inner):
                optional_names.add(tok)

        # Strip brackets to split cleanly by comma
        flat = s.replace("[", "").replace("]", "")
        parts = [p.strip() for p in flat.split(",") if p.strip()]

        for idx, part in enumerate(parts):
            is_var = part.startswith("...") or part.startswith("*")
            clean_part = part.lstrip(".*").strip()

            default_val: Optional[str] = None
            type_ann: Optional[str] = None
            is_opt = False

            # Check default value `param = val`
            if "=" in clean_part:
                lhs, rhs = clean_part.split("=", 1)
                clean_part = lhs.strip()
                default_val = rhs.strip()
                is_opt = True

            # Check TypeScript / Python type annotation `param?: Type` or `param: Type`
            if ":" in clean_part:
                lhs, rhs = clean_part.split(":", 1)
                clean_part = lhs.strip()
                type_ann = rhs.strip()
                if "optional[" in type_ann.lower() or "null" in type_ann.lower() or "undefined" in type_ann.lower():
                    is_opt = True

            if clean_part.endswith("?"):
                clean_part = clean_part[:-1].strip()
                is_opt = True

            name_match = re.match(r"^([a-zA-Z_$][a-zA-Z0-9_$]*)", clean_part)
            param_name = name_match.group(1) if name_match else clean_part

            if param_name in optional_names:
                is_opt = True

            if param_name and param_name not in ("self", "cls"):
                params.append(
                    ParamASTNode(
                        name=param_name,
                        position=len(params),
                        is_optional=is_opt,
                        default_value=default_val,
                        type_annotation=type_ann,
                        is_variadic=is_var,
                    )
                )

        return params

    @classmethod
    def _parse_openapi_parameters_and_responses(
        cls,
        endpoint_path: str,
        section_body: str
    ) -> Tuple[List[ParamASTNode], Optional[ReturnTypeNode], List[ExceptionNode]]:
        """
        Parses OpenAPI / REST endpoint parameters (path `{id}`, YAML/JSON/table parameters)
        and response / error status codes into `ParamNode`, `ReturnTypeNode`, and `ExceptionNode`.
        """
        params: List[ParamASTNode] = []
        seen_names: Set[str] = set()

        # 1. Path parameters like `/v1/users/{user_id}`
        for path_param in re.findall(r"\{([a-zA-Z0-9_]+)\}", endpoint_path):
            if path_param not in seen_names:
                seen_names.add(path_param)
                params.append(
                    ParamASTNode(
                        name=path_param,
                        position=len(params),
                        is_optional=False,
                        type_annotation="string",
                        param_source="path",
                    )
                )

        # 2. YAML / Markdown parameter definitions:
        # e.g. `- name: amount\n  in: body\n  required: true\n  type: number`
        # or bullet points `- \`amount\` (number, required): ...`
        yaml_param_blocks = re.finditer(
            r"-\s*name:\s*([a-zA-Z0-9_]+)(.*?)(?=\n\s*-\s*name:|\n\s*responses:|\Z)",
            section_body,
            re.DOTALL | re.IGNORECASE,
        )
        for m in yaml_param_blocks:
            p_name = m.group(1).strip()
            block = m.group(2)
            if p_name in seen_names:
                continue
            seen_names.add(p_name)
            is_req = bool(re.search(r"required:\s*true", block, re.IGNORECASE))
            in_match = re.search(r"in:\s*(query|path|body|header)", block, re.IGNORECASE)
            type_match = re.search(r"type:\s*([a-zA-Z0-9_]+)", block, re.IGNORECASE)
            params.append(
                ParamASTNode(
                    name=p_name,
                    position=len(params),
                    is_optional=not is_req,
                    type_annotation=type_match.group(1) if type_match else "string",
                    param_source=in_match.group(1).lower() if in_match else "query",
                )
            )

        # Bullet parameter syntax: `- `currency` (string, required)` or `- `idempotency_key` (string, optional)`
        bullet_params = re.finditer(
            r"[-*]\s*`([a-zA-Z0-9_]+)`\s*\(([^)]+)\)",
            section_body,
        )
        for m in bullet_params:
            p_name = m.group(1).strip()
            meta_str = m.group(2).lower()
            if p_name in seen_names:
                continue
            seen_names.add(p_name)
            is_opt = "optional" in meta_str or "default" in meta_str
            type_tok = meta_str.split(",")[0].strip()
            params.append(
                ParamASTNode(
                    name=p_name,
                    position=len(params),
                    is_optional=is_opt,
                    type_annotation=type_tok,
                    param_source="body",
                )
            )

        # 3. Extract 200/201 success response schema -> ReturnTypeNode
        return_node: Optional[ReturnTypeNode] = None
        resp_200 = re.search(
            r"\b(200|201)\b\s*[:\-]?\s*`?([A-Za-z0-9_<>\[\]|]+)`?",
            section_body,
        )
        if resp_200:
            status_code = int(resp_200.group(1))
            schema_name = resp_200.group(2)
            return_node = ReturnTypeNode(
                raw_type=schema_name,
                is_nullable=False,
                is_async_promise=True,
                inner_type=schema_name,
                http_status_code=status_code,
            )

        # 4. Extract 4xx/5xx HTTP error contracts -> ExceptionNode
        exception_nodes: List[ExceptionNode] = []
        seen_codes: Set[int] = set()
        for err_m in cls._HTTP_ERROR_STATUS_RE.finditer(section_body):
            code = int(err_m.group(1))
            desc = (err_m.group(2) or f"HTTP_{code}").strip()
            if code not in seen_codes:
                seen_codes.add(code)
                exception_nodes.append(
                    ExceptionNode(
                        error_type=f"HTTP_{code}",
                        condition=desc,
                        http_status_code=code,
                    )
                )

        return params, return_node, exception_nodes

    @classmethod
    def _parse_python_code_ast(cls, code_str: str, section_title: str) -> List[FunctionASTNode]:
        """Uses Python's native `ast` module to parse Python code blocks into FunctionASTNodes."""
        nodes: List[FunctionASTNode] = []
        try:
            tree = ast.parse(code_str)
        except SyntaxError:
            return nodes

        for item in ast.walk(tree):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_async_fn = isinstance(item, ast.AsyncFunctionDef)
                params: List[ParamASTNode] = []
                total_args = item.args.args
                num_defaults = len(item.args.defaults)
                default_start_idx = len(total_args) - num_defaults

                for idx, arg in enumerate(total_args):
                    if arg.arg in ("self", "cls"):
                        continue
                    has_default = idx >= default_start_idx
                    def_val = None
                    if has_default:
                        def_node = item.args.defaults[idx - default_start_idx]
                        try:
                            def_val = ast.unparse(def_node)
                        except Exception:
                            def_val = "default"

                    ann_str = None
                    if arg.annotation:
                        try:
                            ann_str = ast.unparse(arg.annotation)
                        except Exception:
                            ann_str = "Any"

                    params.append(
                        ParamASTNode(
                            name=arg.arg,
                            position=len(params),
                            is_optional=has_default or (ann_str is not None and "Optional[" in ann_str),
                            default_value=def_val,
                            type_annotation=ann_str,
                        )
                    )

                ret_type = None
                if item.returns:
                    try:
                        ret_type = ast.unparse(item.returns)
                    except Exception:
                        ret_type = None

                return_node = ReturnTypeNode.from_type_string(ret_type, is_async_fn=is_async_fn)

                # Walk function body to extract raised exceptions and comparison operators
                raised: Set[str] = set()
                exc_nodes: List[ExceptionNode] = []
                ops: Set[str] = set()
                for sub in ast.walk(item):
                    if isinstance(sub, ast.Raise) and sub.exc:
                        exc_name = None
                        if isinstance(sub.exc, ast.Call) and isinstance(sub.exc.func, ast.Name):
                            exc_name = sub.exc.func.id
                        elif isinstance(sub.exc, ast.Name):
                            exc_name = sub.exc.id
                        if exc_name and exc_name not in raised:
                            raised.add(exc_name)
                            exc_nodes.append(ExceptionNode(error_type=exc_name, condition="ast.Raise"))
                    elif isinstance(sub, ast.Eq):
                        ops.add("==")
                    elif isinstance(sub, ast.Is):
                        ops.add("is")

                param_sig = ", ".join(
                    f"{p.name}={p.default_value}" if p.default_value else p.name for p in params
                )
                raw_sig = f"{'async ' if is_async_fn else ''}{item.name}({param_sig})" + (f" -> {ret_type}" if ret_type else "")

                nodes.append(
                    FunctionASTNode(
                        symbol_name=item.name,
                        raw_signature=raw_sig,
                        section_title=section_title,
                        params=params,
                        return_type=ret_type,
                        return_node=return_node,
                        thrown_exceptions=raised,
                        exception_nodes=exc_nodes,
                        operators_used=ops,
                        is_async=is_async_fn,
                        code_ast_dump=ast.dump(item),
                    )
                )
        return nodes

    @classmethod
    def extract_section_ast(cls, section_title: str, section_body: str) -> FunctionASTNode:
        """
        Extracts a unified `FunctionASTNode` (`FunctionNode`) with nested `ParamNode`,
        `ReturnTypeNode`, and `ExceptionNode` children from a documentation section title + body.
        Supports Python AST, TypeScript/JavaScript signatures, and OpenAPI REST specifications.
        """
        clean_title = section_title.strip().strip("`")
        symbol_name = clean_title
        params: List[ParamASTNode] = []
        return_type: Optional[str] = None
        return_node: Optional[ReturnTypeNode] = None
        is_async = clean_title.lower().startswith("async ")
        http_method: Optional[str] = None
        endpoint_path: Optional[str] = None
        openapi_exc_nodes: List[ExceptionNode] = []

        openapi_match = cls._OPENAPI_HEADER_RE.match(clean_title)
        sig_match = cls._SIGNATURE_RE.match(clean_title)
        class_match = cls._CLASS_HEADER_RE.match(clean_title)

        if openapi_match:
            http_method = openapi_match.group(1).upper()
            endpoint_path = openapi_match.group(2).strip()
            symbol_name = f"{http_method} {endpoint_path}"
            params, return_node, openapi_exc_nodes = cls._parse_openapi_parameters_and_responses(
                endpoint_path, section_body
            )
            if return_node:
                return_type = return_node.raw_type
        elif sig_match:
            if sig_match.group(1):
                is_async = True
            symbol_name = sig_match.group(2)
            params = cls.parse_parameter_list(sig_match.group(3))
            return_type = sig_match.group(4).strip() if sig_match.group(4) else None
        elif class_match:
            symbol_name = class_match.group(1)

        # Also inspect any fenced code blocks in the section body
        code_ast_dump = None
        js_thrown: Set[str] = set()
        for fence_match in cls._FENCED_CODE_RE.finditer(section_body):
            lang = (fence_match.group(1) or "").lower()
            code_text = fence_match.group(2)
            if lang in ("py", "python", ""):
                py_nodes = cls._parse_python_code_ast(code_text, clean_title)
                if py_nodes:
                    first_py = py_nodes[0]
                    if symbol_name == clean_title:
                        symbol_name = first_py.symbol_name
                    if not params and first_py.params:
                        params = first_py.params
                    if not return_type and first_py.return_type:
                        return_type = first_py.return_type
                        return_node = first_py.return_node
                    if first_py.is_async:
                        is_async = True
                    js_thrown.update(first_py.thrown_exceptions)
                    code_ast_dump = first_py.code_ast_dump

            if lang in ("yaml", "yml", "json", "openapi") and not http_method:
                # Check for OpenAPI path inside fenced YAML/JSON
                path_m = re.search(r"(/[a-zA-Z0-9_/\-{}:]+):\s*\n\s*(get|post|put|patch|delete):", code_text, re.IGNORECASE)
                if path_m:
                    endpoint_path = path_m.group(1)
                    http_method = path_m.group(2).upper()
                    symbol_name = f"{http_method} {endpoint_path}"
                    oa_params, oa_ret, oa_excs = cls._parse_openapi_parameters_and_responses(
                        endpoint_path, code_text + "\n" + section_body
                    )
                    if oa_params:
                        params = oa_params
                    if oa_ret:
                        return_node = oa_ret
                        return_type = oa_ret.raw_type
                    openapi_exc_nodes.extend(oa_excs)

            # Inspect JS/TS code blocks for signature definitions and `throw new ErrorType()`
            for js_exc in cls._JS_THROW_RE.findall(code_text):
                js_thrown.add(js_exc)

            if not params:
                for line in code_text.splitlines():
                    line_s = line.strip().rstrip("{")
                    m = cls._SIGNATURE_RE.match(line_s)
                    if m:
                        if m.group(1):
                            is_async = True
                        if symbol_name == clean_title:
                            symbol_name = m.group(2)
                        params = cls.parse_parameter_list(m.group(3))
                        if not return_type and m.group(4):
                            return_type = m.group(4).strip()
                        break

        # Extract thrown exceptions & error codes from prose + code
        exceptions = set(cls._EXCEPTION_RE.findall(section_body)) | js_thrown
        if "throws" in section_body.lower() and not exceptions:
            exceptions.add("Error")

        exception_nodes: List[ExceptionNode] = list(openapi_exc_nodes)
        existing_exc_names = {e.error_type for e in exception_nodes}
        for exc_name in sorted(exceptions):
            if exc_name not in existing_exc_names:
                exception_nodes.append(ExceptionNode(error_type=exc_name, condition="thrown"))
                existing_exc_names.add(exc_name)
        for e_node in openapi_exc_nodes:
            exceptions.add(e_node.error_type)

        # Extract return type contract if mentioned in prose
        if not return_type:
            ret_match = cls._RETURN_CONTRACT_RE.search(section_body)
            if ret_match:
                return_type = ret_match.group(1).strip()

        if not return_node and (return_type or is_async):
            return_node = ReturnTypeNode.from_type_string(return_type, is_async_fn=is_async)

        # Extract equality & comparison operator semantics
        operators: Set[str] = set()
        body_lower = section_body.lower()
        if "===" in section_body or "strict equality" in body_lower:
            operators.add("===")
        if "object.is" in body_lower:
            operators.add("Object.is")
        if ("==" in section_body and "===" not in section_body.replace("===", "")) or "coercive" in body_lower or "abstract equality" in body_lower:
            operators.add("==")
        if "prototype" in body_lower or "__proto__" in body_lower:
            if "not" in body_lower and "prototype" in body_lower:
                operators.add("no_prototype_check")
            else:
                operators.add("prototype_check")

        # Determine lifecycle state
        lifecycle = "stable"
        if "removed" in body_lower or "no longer supported" in body_lower:
            lifecycle = "removed"
        elif "deprecate" in body_lower or "stability: 0" in body_lower:
            lifecycle = "deprecated"
        elif "experimental" in body_lower or "stability: 1" in body_lower:
            lifecycle = "experimental"

        return FunctionASTNode(
            symbol_name=symbol_name,
            raw_signature=clean_title,
            section_title=section_title,
            params=params,
            return_type=return_type,
            return_node=return_node,
            thrown_exceptions=exceptions,
            exception_nodes=exception_nodes,
            operators_used=operators,
            lifecycle_state=lifecycle,
            is_async=is_async,
            http_method=http_method,
            endpoint_path=endpoint_path,
            code_ast_dump=code_ast_dump,
        )

    @classmethod
    def compare_ast_nodes(
        cls,
        old_node: FunctionASTNode,
        new_node: FunctionASTNode,
        old_body: str,
        new_body: str,
    ) -> Optional[ASTContractDiff]:
        """
        Mathematically compares two FunctionASTNodes (V_old vs V_new) to classify
        structural signature changes, parameter arity breaks, exception shifts,
        and operator semantic mutations.
        """
        diffs_detected: List[str] = []
        ast_diff_type = "CONTENT_REFINEMENT"
        is_breaking = False
        severity = "medium"
        category = "modified"

        # 1. Lifecycle Transition Check (Active/Experimental -> Deprecated/Removed)
        if old_node.lifecycle_state != new_node.lifecycle_state:
            if new_node.lifecycle_state == "removed":
                is_breaking = True
                severity = "critical"
                category = "removed"
                ast_diff_type = "LIFECYCLE_REMOVAL"
                diffs_detected.append(
                    f"Symbol lifecycle transitioned from '{old_node.lifecycle_state}' to 'removed'"
                )
            elif new_node.lifecycle_state == "deprecated":
                severity = "high"
                category = "deprecated"
                ast_diff_type = "LIFECYCLE_DEPRECATION"
                diffs_detected.append(
                    f"Symbol '{new_node.symbol_name}' marked as deprecated (previously '{old_node.lifecycle_state}')"
                )
            elif old_node.lifecycle_state == "experimental" and new_node.lifecycle_state == "stable":
                severity = "low"
                category = "modified"
                ast_diff_type = "LIFECYCLE_STABILIZATION"
                diffs_detected.append(
                    f"Symbol '{new_node.symbol_name}' promoted from 'experimental' to 'stable'"
                )

        # 2. Parameter Arity & Optionality Contract Check
        old_param_map = {p.name: p for p in old_node.params}
        new_param_map = {p.name: p for p in new_node.params}

        if old_node.params or new_node.params:
            # Check if required parameters increased
            if new_node.required_param_count > old_node.required_param_count:
                is_breaking = True
                severity = "critical"
                category = "breaking"
                ast_diff_type = "PARAMETER_REQUIRED_ARITY_INCREASE"
                diffs_detected.append(
                    f"Required parameter arity increased from {old_node.required_param_count} to {new_node.required_param_count}"
                )

            # Check removed parameters
            removed_params = [p.name for p in old_node.params if p.name not in new_param_map]
            if removed_params:
                is_breaking = True
                severity = "critical"
                category = "breaking"
                ast_diff_type = "PARAMETER_REMOVED"
                diffs_detected.append(f"Removed parameter(s): {', '.join(removed_params)}")

            # Check added optional parameters
            added_params = [p.name for p in new_node.params if p.name not in old_param_map]
            if added_params and not is_breaking:
                ast_diff_type = "PARAMETER_EXTENDED"
                diffs_detected.append(f"Added parameter(s): {', '.join(added_params)}")

            # Check default value or type annotation changes on existing parameters
            for p_name, old_p in old_param_map.items():
                if p_name in new_param_map:
                    new_p = new_param_map[p_name]
                    if old_p.is_optional and not new_p.is_optional:
                        is_breaking = True
                        severity = "critical"
                        category = "breaking"
                        ast_diff_type = "PARAMETER_OPTIONAL_TO_REQUIRED"
                        diffs_detected.append(f"Parameter '{p_name}' changed from optional to required")
                    elif old_p.default_value != new_p.default_value:
                        severity = "high"
                        category = "behavioral"
                        ast_diff_type = "PARAMETER_DEFAULT_MUTATION"
                        diffs_detected.append(
                            f"Parameter '{p_name}' default mutated from {old_p.default_value} to {new_p.default_value}"
                        )
                    elif old_p.type_annotation != new_p.type_annotation and (old_p.type_annotation or new_p.type_annotation):
                        is_breaking = True
                        severity = "high"
                        category = "breaking"
                        ast_diff_type = "PARAMETER_TYPE_MUTATION"
                        diffs_detected.append(
                            f"Parameter '{p_name}' type changed from '{old_p.type_annotation}' to '{new_p.type_annotation}'"
                        )

        # 3. Operator & Prototype Semantic Shift Check
        if old_node.operators_used != new_node.operators_used:
            added_ops = new_node.operators_used - old_node.operators_used
            removed_ops = old_node.operators_used - new_node.operators_used
            if added_ops or removed_ops:
                if category not in ("removed", "deprecated", "breaking"):
                    category = "behavioral"
                    severity = "high"
                if "===" in added_ops or "Object.is" in added_ops:
                    is_breaking = True
                    severity = "critical"
                    category = "breaking"
                ast_diff_type = "OPERATOR_SEMANTIC_SHIFT"
                diffs_detected.append(
                    f"Operator semantics shifted (added: {sorted(added_ops)}, removed: {sorted(removed_ops)})"
                )

        # 4. Thrown Exception (`ExceptionNode`) & Return Type (`ReturnTypeNode`) Contract Check
        if old_node.thrown_exceptions != new_node.thrown_exceptions:
            new_exc = new_node.thrown_exceptions - old_node.thrown_exceptions
            if new_exc:
                is_breaking = True
                severity = "critical"
                category = "breaking"
                ast_diff_type = "EXCEPTION_CONTRACT_CHANGE"
                diffs_detected.append(f"New exception contract introduced: {', '.join(sorted(new_exc))}")

        if old_node.is_async != new_node.is_async:
            is_breaking = True
            severity = "critical"
            category = "breaking"
            ast_diff_type = "ASYNC_SYNC_CONTRACT_BREAK"
            diffs_detected.append(
                f"Execution model shifted from {'async' if old_node.is_async else 'sync'} to {'async' if new_node.is_async else 'sync'}"
            )

        if old_node.return_node and new_node.return_node:
            if not old_node.return_node.is_nullable and new_node.return_node.is_nullable:
                is_breaking = True
                severity = "critical"
                category = "breaking"
                ast_diff_type = "RETURN_TYPE_NULLABLE_EXPANSION"
                diffs_detected.append(
                    f"Return contract expanded to nullable ('{old_node.return_node.raw_type}' -> '{new_node.return_node.raw_type}')"
                )
            elif old_node.return_node.raw_type != new_node.return_node.raw_type:
                is_breaking = True
                severity = "critical"
                category = "breaking"
                ast_diff_type = "RETURN_TYPE_MUTATION"
                diffs_detected.append(
                    f"Return contract changed from '{old_node.return_node.raw_type}' to '{new_node.return_node.raw_type}'"
                )
        elif old_node.return_type != new_node.return_type and (old_node.return_type or new_node.return_type):
            is_breaking = True
            severity = "critical"
            category = "breaking"
            ast_diff_type = "RETURN_TYPE_MUTATION"
            diffs_detected.append(
                f"Return contract changed from '{old_node.return_type}' to '{new_node.return_type}'"
            )

        # 5. Python AST Structural Dump Check
        if old_node.code_ast_dump and new_node.code_ast_dump and old_node.code_ast_dump != new_node.code_ast_dump:
            if not diffs_detected:
                category = "behavioral"
                severity = "high"
                ast_diff_type = "CODE_AST_BODY_MUTATION"
                diffs_detected.append("Underlying function implementation AST mutated")

        # 6. Fallback behavioral prose analysis if bodies differ
        if not diffs_detected and old_body.strip() != new_body.strip():
            if "behavior" in new_body.lower() or "returns" in new_body.lower() or "legacy" in new_body.lower():
                category = "behavioral"
                severity = "high"
                ast_diff_type = "BEHAVIORAL_SPEC_CHANGE"
                diffs_detected.append(f"Behavioral specification modified in '{new_node.section_title}'")
            else:
                diffs_detected.append(f"Documentation specification updated in '{new_node.section_title}'")

        if not diffs_detected:
            return None

        proof_str = f"[{ast_diff_type}] " + "; ".join(diffs_detected)
        return ASTContractDiff(
            symbol_name=new_node.symbol_name,
            ast_diff_type=ast_diff_type,
            is_breaking=is_breaking,
            severity_level=severity,
            change_category=category,
            old_signature=old_node.raw_signature,
            new_signature=new_node.raw_signature,
            proof_summary=proof_str,
            details={
                "old_required_params": old_node.required_param_count,
                "new_required_params": new_node.required_param_count,
                "old_lifecycle": old_node.lifecycle_state,
                "new_lifecycle": new_node.lifecycle_state,
                "old_operators": sorted(old_node.operators_used),
                "new_operators": sorted(new_node.operators_used),
                "old_exceptions": sorted(old_node.thrown_exceptions),
                "new_exceptions": sorted(new_node.thrown_exceptions),
                "old_return_type": old_node.return_type,
                "new_return_type": new_node.return_type,
                "old_ast": old_node.to_dict(),
                "new_ast": new_node.to_dict(),
            },
        )


ast_signature_parser = ASTSignatureParserService()

