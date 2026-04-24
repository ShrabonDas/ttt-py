"""Key extraction and index for TTT pattern matching optimization.

A key is a (symbol, depth) pair. The index maps keys to lists of Tree nodes,
enabling fast pruning: if a pattern requires a key not in a tree, skip it.
"""
from __future__ import annotations
from typing import List, Tuple, Any
from .types import TreeExpr

Key = Tuple[Any, int]  # (symbol, depth)


# ---------------------------------------------------------------------------
# Key extraction
# ---------------------------------------------------------------------------

def _filter_ops(expression, maxdepth: int = 2):
    """Mirror of Lisp filter-ops: return the 'required symbol sets' of a pattern."""
    from .operators import get_op, op_requires_args, OPERATORS
    if maxdepth < 0:
        return []
    if not isinstance(expression, tuple):
        op = get_op(expression)
        if op == 'literal' or isinstance(expression, (int, float)):
            return [expression]
        # predicate or variable — return keys from pred-keys if any
        return []
    op = get_op(expression[0]) if expression else None
    if op in ('!', '+'):
        # union of all arg filter-ops
        parts = [_filter_ops(a, maxdepth - 1) for a in expression[1:] if not isinstance(a, str) or a != '~']
        if any(p is None for p in parts):
            return []
        result = []
        for p in parts:
            result.extend(p)
        return result if result else []
    elif op in ('^@', '/'):
        return _filter_ops(expression[1], maxdepth - 1) if len(expression) > 1 else []
    elif op in ('*', '?', '^', '^*'):
        return []
    elif op in ('<>', '{}'):
        result = []
        for a in expression:
            result.extend(_filter_ops(a, maxdepth - 1))
        return result
    else:
        # general pattern (list without special operator at head)
        result = []
        for a in expression:
            sub = _filter_ops(a, maxdepth - 1)
            if sub:
                result.extend(sub)
        return [tuple(result)] if result else []


def extract_keys(pattern: TreeExpr, maxdepth: int = 2) -> List[Key]:
    """Extract (symbol, depth) keys from a pattern expression."""
    filtered = _filter_ops(pattern, maxdepth)
    return _rechelper(filtered if isinstance(filtered, tuple) or (isinstance(filtered, list) and filtered) else [pattern], 0, maxdepth)


def extract_keys_with_ops(pattern: TreeExpr, maxdepth: int = 2) -> List[Key]:
    """Extract keys directly from a tree expression (with_ops=True path)."""
    return _rechelper([pattern], 0, maxdepth)


def _rechelper(pat, depth: int, maxdepth: int) -> List[Key]:
    if depth > maxdepth:
        return []
    if not isinstance(pat, (tuple, list)):
        return []
    result = []
    seen = set()
    # atoms at this level
    for item in pat:
        if not isinstance(item, (tuple, list)) and item is not None:
            key = (item, depth)
            if key not in seen:
                seen.add(key)
                result.append(key)
    # recurse into sublists
    for item in pat:
        if isinstance(item, (tuple, list)):
            for k in _rechelper(item, depth + 1, maxdepth):
                if k not in seen:
                    seen.add(k)
                    result.append(k)
    return result


# ---------------------------------------------------------------------------
# Index (key -> [Tree])
# ---------------------------------------------------------------------------

def add_to_index(key: Key, value, index: dict) -> None:
    lst = index.get(key)
    if lst is None:
        index[key] = [value]
    else:
        lst.append(value)


def fastmap(key: Key, index: dict) -> list:
    return index.get(key, [])
