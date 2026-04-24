"""Binding system for TTT pattern matching.

Bindings map variable names to lists of matched tree-expressions (LIFO).
We store them as plain dicts: var -> [most_recent, ...older...].
add_binding is non-destructive (returns a new dict).
"""
from __future__ import annotations
from typing import Any, Optional

Bindings = dict  # var_name -> list[TreeExpr]  (most-recent first)

EMPTY: Bindings = {}   # sentinel for "no bindings yet / just True"


def make_bindings() -> Bindings:
    return {}


def add_binding(var, seq, bindings: Bindings) -> Bindings:
    """Non-destructively add var->seq to bindings. Returns new dict."""
    if var is None:
        return bindings
    new = dict(bindings)
    lst = list(new.get(var, []))
    lst.insert(0, seq)   # LIFO: most recent first
    new[var] = lst
    return new


def get_binding(var, bindings: Bindings):
    """Return most-recent value for var, or None."""
    lst = bindings.get(var)
    if lst:
        return lst[0]
    return None


def bound(var, bindings: Bindings) -> bool:
    return bool(bindings.get(var))
