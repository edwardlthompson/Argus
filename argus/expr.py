"""Safe evaluation of applies_when expressions against signal data."""

from __future__ import annotations

import ast
import builtins
from typing import Any


class ExprError(ValueError):
    """Invalid or unsafe expression."""


_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
    ast.Attribute,
    ast.Subscript,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Call,
    ast.IfExp,
)

_ALLOWED_FUNCS = frozenset({"len", "bool", "any", "all", "min", "max", "get"})


def _validate(node: ast.AST) -> None:
    if not isinstance(node, _ALLOWED_NODES):
        raise ExprError(f"Disallowed expression node: {type(node).__name__}")
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id not in _ALLOWED_FUNCS:
                raise ExprError(f"Function not allowed: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            # Only dict-like .get(...) is permitted
            if node.func.attr != "get":
                raise ExprError(f"Method not allowed: {node.func.attr}")
        else:
            raise ExprError("Only named functions or .get() calls are allowed")
    for child in ast.iter_child_nodes(node):
        _validate(child)


def _get(mapping: Any, key: Any, default: Any = None) -> Any:
    if isinstance(mapping, dict):
        return mapping.get(key, default)
    return default


def evaluate(expression: str, context: dict[str, Any]) -> bool:
    """Evaluate a boolean expression with a restricted AST subset."""
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ExprError(f"Syntax error in expression: {expression}") from exc
    _validate(tree)
    safe_builtins = {name: getattr(builtins, name) for name in _ALLOWED_FUNCS if hasattr(builtins, name)}
    safe_builtins["get"] = _get
    try:
        value = eval(  # noqa: S307 — intentional restricted eval
            compile(tree, "<applies_when>", "eval"),
            {"__builtins__": safe_builtins},
            context,
        )
    except Exception as exc:  # noqa: BLE001
        raise ExprError(f"Evaluation failed for {expression!r}: {exc}") from exc
    return bool(value)
