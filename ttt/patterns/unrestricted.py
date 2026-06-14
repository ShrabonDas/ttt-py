"""Unrestricted sequence patterns: _! _+ _* _?
These match any sequence of trees without inspecting their content.
"""
from __future__ import annotations
from typing import Optional
from .base import Pattern
from ..bindings import Bindings, add_binding
from ..operators import get_n, get_m, get_var, is_sticky, get_op


class UnrestrictedSeq(Pattern):
    """_![n], _+[n], _*[n-m], _?[n]"""

    def __init__(self, expr: str):
        super().__init__()
        self.expr = expr
        op = get_op(expr)
        n = get_n(expr)
        m = get_m(expr)
        var = get_var(expr)
        self.var = var
        self._sticky = is_sticky(expr)

        if op == '_!':
            self.min_width = n if n is not None else 1
            self.max_width = n if n is not None else 1
        elif op == '_+':
            self.min_width = n if n is not None else 1
            self.max_width = float('inf')
        elif op == '_*':
            self.min_width = n if n is not None else 0
            self.max_width = m if m is not None else float('inf')
        elif op == '_?':
            self.min_width = 0
            self.max_width = n if n is not None else 1

        self.min_iter = self.min_width
        self.max_iter = self.max_width
        self.keys = []

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        n = len(tree_seq)
        if n < self.min_iter:
            return None
        if self.max_iter != float('inf') and n > self.max_iter:
            return None

        # Sticky check
        if self._sticky and self.var is not None:
            existing = bindings.get(self.var)
            if existing:
                bound_exprs = [t.expr for t in existing[0]]
                cur_exprs = [t.expr for t in tree_seq]
                if bound_exprs != cur_exprs:
                    return None

        return add_binding(self.var, tree_seq, bindings)
