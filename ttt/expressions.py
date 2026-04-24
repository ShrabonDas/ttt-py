"""Utilities for analysing pattern expressions (min/max width etc.)."""
from __future__ import annotations
from .types import TreeExpr
from .operators import get_op, op_requires_args, get_n, get_m, is_sticky

INF = float('inf')


def patt_min_width(expr: TreeExpr) -> int:
    op = get_op(expr[0]) if isinstance(expr, tuple) and expr else get_op(expr)

    if isinstance(expr, tuple) and op and op_requires_args(op):
        n = get_n(expr[0])
        m = get_m(expr[0])
        pos_args = _pos_args(expr)
        if op in ('!', '+'):
            if pos_args:
                recmin = min(patt_min_width(a) for a in pos_args)
                if n is not None:
                    return n * recmin
                return recmin
            return 1
        elif op == '*':
            if n is not None and m is not None and pos_args:
                recmin = min(patt_min_width(a) for a in pos_args)
                return n * recmin
            return 0
        elif op == '?':
            return 0
        elif op in ('<>', '{}'):
            return sum(patt_min_width(a) for a in pos_args)
        elif op in ('^', '^^', '^*', '^+', '^@', '/', 'literal', 'general'):
            return 1
        return 1

    if isinstance(expr, str):
        op2 = get_op(expr)
        n = get_n(expr)
        if op2 == '_!':
            return n if n is not None else 1
        elif op2 == '_+':
            return n if n is not None else 1
        elif op2 == '_?':
            return 0
        elif op2 == '_*':
            return n if n is not None else 0
        elif op2 == '@':
            return 1
        elif op2 == 'literal':
            return 1
        if is_sticky(expr):
            return 0
        return 1

    if isinstance(expr, (int, float)):
        return 1
    return 1


def patt_max_width(expr: TreeExpr) -> float:
    op = get_op(expr[0]) if isinstance(expr, tuple) and expr else get_op(expr)

    if isinstance(expr, tuple) and op and op_requires_args(op):
        n = get_n(expr[0])
        m = get_m(expr[0])
        pos_args = _pos_args(expr)
        if op == '!':
            if pos_args:
                recmax = max(patt_max_width(a) for a in pos_args)
                if n is not None:
                    return n * recmax if recmax != INF else INF
                return recmax
            return 1
        elif op == '?':
            if pos_args:
                locmax = max(1, max(patt_max_width(a) for a in pos_args))
                if n is not None:
                    return n * locmax if locmax != INF else INF
                return locmax
            return 1
        elif op == '*':
            if pos_args:
                recmax = max(patt_max_width(a) for a in pos_args)
                if m is not None and recmax != INF:
                    return m * recmax
            return INF
        elif op == '+':
            return INF
        elif op in ('<>', '{}'):
            parts = [patt_max_width(a) for a in pos_args]
            if any(p == INF for p in parts):
                return INF
            return sum(parts)
        elif op in ('^', '^^', '^*', '^+', '^@', '/', 'literal', 'general'):
            return 1
        return 1

    if isinstance(expr, str):
        op2 = get_op(expr)
        n = get_n(expr)
        m = get_m(expr)
        if op2 == '_!':
            return n if n is not None else 1
        elif op2 == '_?':
            return n if n is not None else 1
        elif op2 == '_+':
            return INF
        elif op2 == '_*':
            return m if m is not None else INF
        elif op2 == '@':
            return 1
        elif op2 == 'literal':
            return 1
        if is_sticky(expr):
            return INF
        return 1

    if isinstance(expr, (int, float)):
        return 1
    return 1


def _pos_args(expr: tuple) -> list:
    """Return the positive args of a compound pattern (skipping op and negated args)."""
    result, in_neg = [], False
    for item in expr[1:]:
        if item == '~':
            in_neg = True
        elif not in_neg:
            result.append(item)
    return result
