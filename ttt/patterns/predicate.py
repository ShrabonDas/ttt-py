"""Predicate patterns: symbols ending in '?' that call Python functions."""
from __future__ import annotations
from typing import Optional, Callable
from .base import Pattern
from ..bindings import Bindings, add_binding

# Global predicate table: sym_str -> callable
_predicate_table: dict = {}


def store_pred(sym: str, fn: Callable) -> None:
    _predicate_table[sym] = fn


def get_pred_fn(sym: str) -> Optional[Callable]:
    """Find the callable for predicate sym."""
    # Direct lookup first
    if sym in _predicate_table:
        return _predicate_table[sym]
    # Try to find function by name (strip digit suffix after ?)
    q = sym.find('?')
    if q < 0:
        return None
    base = sym[:q+1]  # includes the '?'
    if base in _predicate_table:
        return _predicate_table[base]
    # Search builtins / globals
    import builtins
    fn = getattr(builtins, base, None)
    if callable(fn):
        return fn
    return None


class PredicatePatt(Pattern):
    """A predicate pattern — calls a Python function on the tree expression."""

    def __init__(self, sym: str, fn: Optional[Callable] = None, ttt_pred: bool = False):
        super().__init__()
        self.expr = sym
        self.var = sym
        self.min_width = 1
        self.max_width = 1
        self._fn = fn
        self._ttt_pred = ttt_pred   # if True, fn takes a Tree; else takes expr

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        if len(tree_seq) != 1:
            return None
        tree = tree_seq[0]
        fn = self._fn
        if fn is None:
            fn = get_pred_fn(self.expr)
        if fn is None:
            return None
        try:
            if self._ttt_pred:
                result = fn(tree)
            else:
                result = fn(tree.expr)
        except Exception:
            return None
        if result:
            return add_binding(self.var, tree_seq, bindings)
        return None
