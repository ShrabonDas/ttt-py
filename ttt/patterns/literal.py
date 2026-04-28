"""Literal pattern: matches exactly one specific atom or tree."""
from __future__ import annotations
from typing import List, Optional
from .base import Pattern
from ..bindings import Bindings
from ..keys import extract_keys_with_ops


class LiteralPatt(Pattern):
    """Matches exactly one tree whose expression equals self.expr."""

    def __init__(self, expr):
        super().__init__()
        self.expr = expr
        self.min_width = 1
        self.max_width = 1
        from ..tree import build_tree as _bt
        # compute height from expression
        self.min_height = self.max_height = _expr_height(expr)
        self.keys = extract_keys_with_ops(expr)

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        if len(tree_seq) != 1:
            return None
        t = tree_seq[0]
        if t.height != self.min_height:
            return None
        if t.expr == self.expr:
            return bindings
        return None


def _expr_height(expr) -> int:
    if not isinstance(expr, tuple):
        return 0
    if not expr:
        return 1
    return 1 + max(_expr_height(c) for c in expr)
