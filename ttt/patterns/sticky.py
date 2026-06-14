"""StuckPatt: sticky variable without args (e.g. bare !. or *.)."""
from __future__ import annotations
from typing import Optional
from .base import Pattern
from ..bindings import Bindings, get_binding
from ..operators import get_var


class StuckPatt(Pattern):
    """A sticky variable that requires args but appears without them.
    When matched, it checks that the current tree_seq equals the previously
    bound value.
    """

    def __init__(self, expr):
        super().__init__()
        self.expr = expr
        self.var = get_var(str(expr)) if isinstance(expr, str) else None
        self.min_width = 0
        self.max_width = float('inf')

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        if self.var is None:
            return None
        existing = bindings.get(self.var)
        if not existing:
            raise RuntimeError(
                f"Cannot match unbound sticky pattern without args: {self.expr}")
        bound_seq = existing[0]
        if [t.expr for t in bound_seq] == [t.expr for t in tree_seq]:
            return bindings
        return None
