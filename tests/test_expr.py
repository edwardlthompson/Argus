from __future__ import annotations

import pytest

from argus.expr import ExprError, evaluate


def test_safe_eval_true():
    assert evaluate("hygiene['security_md'] == False", {"hygiene": {"security_md": False}})


def test_dict_get_method():
    assert evaluate("not deps.get('vulnerability_alerts_enabled', False)", {
        "deps": {"vulnerability_alerts_enabled": False},
    })


def test_rejects_imports():
    with pytest.raises(ExprError):
        evaluate("__import__('os').system('echo hi')", {})


def test_rejects_other_methods():
    with pytest.raises(ExprError):
        evaluate("deps.keys()", {"deps": {}})
