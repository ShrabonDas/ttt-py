"""Transduction pattern: (/ lhs rhs)
Matches like lhs, then stores rhs template for application.
"""
from __future__ import annotations
from typing import Optional
from .base import Pattern
from ..bindings import Bindings, add_binding
from ..types import TreeExpr


class TBind:
    """Binding payload for a transduction match."""
    __slots__ = ('parent', 'parent_idx', 'template_expr')

    def __init__(self, parent, parent_idx, template_expr):
        self.parent = parent
        self.parent_idx = parent_idx
        self.template_expr = template_expr


class TransductionPatt(Pattern):
    """(/ lhs rhs) — apply lhs pattern, store rhs for template construction."""

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        if len(expr) != 3:
            raise ValueError(f"Transduction requires exactly 3 elements: {expr}")
        self._raw_lhs = expr[1]
        self.rhs: TreeExpr = expr[2]
        self._lhs: Optional[Pattern] = None
        self.var = '/'
        self.min_width = 1
        self.max_width = 1
        self.keys = []

    def _ensure_compiled(self):
        if self._lhs is None:
            from ..cache import build_pattern
            self._lhs = build_pattern(self._raw_lhs)

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()
        if len(tree_seq) != 1:
            return None
        b = self._lhs.match(tree_seq, bindings)
        if b is None:
            return None
        node = tree_seq[0]
        tbind = TBind(
            parent=node.parent,
            parent_idx=node.parent_idx,
            template_expr=self.rhs,
        )
        return add_binding('/', tbind, b)
