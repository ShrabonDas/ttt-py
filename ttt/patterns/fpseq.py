"""Free-standing (<>) and permuted ({}) sequence patterns."""
from __future__ import annotations
from typing import List, Optional
from itertools import permutations
from .base import Pattern
from .general import _match_seq
from ..bindings import Bindings, add_binding
from ..operators import get_var, is_sticky
from ..expressions import patt_min_width, patt_max_width

INF = float('inf')


def _parse_fp_args(expr: tuple):
    # No negation support in <> / {}; args start at index 1
    return list(expr[1:])


class FreeSeq(Pattern):
    """(<> P1 P2 ... Pn) — match the exact sequence P1..Pn in order
    but the operator itself is 'free-standing': the whole thing matches
    the sequence of P1..Pn directly (not children of a node).
    """

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        self.var = get_var(expr[0]) if isinstance(expr[0], str) else None
        self._sticky = is_sticky(expr[0]) if isinstance(expr[0], str) else False
        self._raw_args = _parse_fp_args(expr)
        self._sub_patts: Optional[list] = None
        self.min_width = patt_min_width(expr)
        self.max_width = patt_max_width(expr)
        self.keys = []

    def _ensure_compiled(self):
        if self._sub_patts is None:
            from ..cache import build_pattern
            self._sub_patts = [build_pattern(a) for a in self._raw_args]

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()
        if self._sticky and self.var is not None:
            existing = bindings.get(self.var)
            if existing:
                if [t.expr for t in existing[0]] != [t.expr for t in tree_seq]:
                    return None
        result = _match_seq(self._sub_patts, tree_seq, bindings)
        if result is not None:
            return add_binding(self.var, tree_seq, result)
        return None


class PermutedSeq(Pattern):
    """({} P1 P2 ... Pn) — match P1..Pn in any order."""

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        self.var = get_var(expr[0]) if isinstance(expr[0], str) else None
        self._sticky = is_sticky(expr[0]) if isinstance(expr[0], str) else False
        self._raw_args = _parse_fp_args(expr)
        self._sub_patts: Optional[list] = None
        self.min_width = patt_min_width(expr)
        self.max_width = patt_max_width(expr)
        self.keys = []

    def _ensure_compiled(self):
        if self._sub_patts is None:
            from ..cache import build_pattern
            self._sub_patts = [build_pattern(a) for a in self._raw_args]

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()
        if self._sticky and self.var is not None:
            existing = bindings.get(self.var)
            if existing:
                if [t.expr for t in existing[0]] != [t.expr for t in tree_seq]:
                    return None
        # Try each permutation of sub_patts via stack
        result = _match_permuted(self._sub_patts, tree_seq, bindings)
        if result is not None:
            return add_binding(self.var, tree_seq, result)
        return None



def _match_permuted(patts: list, tseq: list, bindings: Bindings) -> Optional[Bindings]:
    """Match patterns in any order against tseq."""
    # Stack entries: (remaining_patts_list, tseq_remaining, binds)
    stack = [(list(range(len(patts))), tseq, bindings)]
    while stack:
        remaining, seq, binds = stack.pop()
        if not remaining:
            if not seq:
                return binds
            continue
        for i in remaining:
            p = patts[i]
            lo = p.min_width
            hi = p.max_width if p.max_width != INF else len(seq)
            hi = min(hi, len(seq))
            for split in range(int(hi), int(lo) - 1, -1):
                prefix = seq[:split]
                b = p.match(prefix, binds)
                if b is not None:
                    new_remaining = [j for j in remaining if j != i]
                    stack.append((new_remaining, seq[split:], b))
    return None
