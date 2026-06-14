"""General tree pattern: a list without a TTT operator at the head.
Matches the children of a single tree node.
"""
from __future__ import annotations
from typing import Optional
from .base import Pattern
from ..bindings import Bindings
from ..expressions import INF


class GeneralPatt(Pattern):
    """A compound pattern like (A _* B) that matches against children of a node."""

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        self._raw_args = list(expr)
        self._sub_patts: Optional[list] = None  # built lazily
        self.min_width = 1
        self.max_width = 1
        from ..keys import extract_keys_with_ops
        self.keys = extract_keys_with_ops(expr)

    def _ensure_compiled(self):
        if self._sub_patts is None:
            from ..cache import build_pattern
            self._sub_patts = [build_pattern(a) for a in self._raw_args]

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()
        # Must match exactly one tree whose children match sub_patts in sequence
        if len(tree_seq) != 1:
            return None
        node = tree_seq[0]
        if node.is_leaf:  # atom — has no children to match against
            return None
        children = node.children  # may be [] for empty tuple ()
        result = _match_seq(self._sub_patts, children, bindings)
        return result


def _match_seq(patts: list, tseq: list, bindings: Bindings) -> Optional[Bindings]:
    """Match a sequence of patterns against a sequence of trees (left-to-right)."""
    stack = [(0, 0, bindings)]
    while stack:
        pi, ti, binds = stack.pop()
        if pi == len(patts):
            if ti == len(tseq):
                return binds
            continue
        p = patts[pi]
        lo = p.min_width
        hi = p.max_width if p.max_width != INF else len(tseq) - ti
        hi = min(hi, len(tseq) - ti)
        # Try largest split first so DFS finds answer quickly (like Lisp impl)
        for split in range(int(hi), int(lo) - 1, -1):
            prefix = tseq[ti:ti + split]
            b = p.match(prefix, binds)
            if b is not None:
                stack.append((pi + 1, ti + split, b))
    return None
