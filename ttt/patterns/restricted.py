"""Restricted sequence patterns: ! + * ?
Match sequences by trying alternatives from pos_args, excluding neg_args.
"""
from __future__ import annotations
from typing import List, Optional
from .base import Pattern
from ..bindings import Bindings, add_binding
from ..operators import get_op, get_n, get_m, get_var, is_sticky

INF = float('inf')


def _parse_args(expr: tuple):
    """Split (op P1 ... ~ N1 ...) into pos_args list and neg_args list."""
    # find '~' in the expression (skipping op at index 0)
    pos = []
    neg = []
    in_neg = False
    for item in expr[1:]:
        if item == '~':
            in_neg = True
        elif in_neg:
            neg.append(item)
        else:
            pos.append(item)
    return pos, neg


class RestrictedSeq(Pattern):
    """(![n] P1..Pm ~ N1..Nn)  (+[n] ...)  (*[n-m] ...)  (?[n] ...)"""

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        op_sym = expr[0]
        op = get_op(op_sym)
        n = get_n(op_sym)
        m = get_m(op_sym)
        self.var = get_var(op_sym)
        self._sticky = is_sticky(op_sym) if isinstance(op_sym, str) else False

        # Build pos/neg arg patterns (deferred to avoid circular imports)
        raw_pos, raw_neg = _parse_args(expr)
        self._raw_pos = raw_pos
        self._raw_neg = raw_neg
        self._pos_args: Optional[list] = None  # built lazily
        self._neg_args: Optional[list] = None

        if op == '!':
            self.min_iter = n if n is not None else 1
            self.max_iter = n if n is not None else 1
        elif op == '+':
            self.min_iter = n if n is not None else 1
            self.max_iter = INF
        elif op == '*':
            self.min_iter = n if n is not None else 0
            self.max_iter = m if m is not None else INF
        elif op == '?':
            self.min_iter = 0
            self.max_iter = n if n is not None else 1

        self._compute_widths(op)
        self.keys = []

    def _compute_widths(self, op):
        from ..expressions import patt_min_width, patt_max_width
        self.min_width = patt_min_width(self.expr)
        self.max_width = patt_max_width(self.expr)

    def _ensure_compiled(self):
        if self._pos_args is None:
            from ..cache import build_pattern
            self._pos_args = [build_pattern(p) for p in self._raw_pos]
            self._neg_args = [build_pattern(p) for p in self._raw_neg]

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()

        # Sticky check
        if self._sticky and self.var is not None:
            existing = bindings.get(self.var)
            if existing:
                bound_exprs = [t.expr for t in existing[0]]
                cur_exprs = [t.expr for t in tree_seq]
                if bound_exprs != cur_exprs:
                    return None

        # Special case: only neg args (! ~ N1 ... Nn)
        if not self._pos_args and self._neg_args:
            n = len(tree_seq)
            if n < self.min_iter or (self.max_iter != INF and n > self.max_iter):
                return None
            for t in tree_seq:
                for neg in self._neg_args:
                    if neg.match([t], bindings) is not None:
                        return None
            return add_binding(self.var, tree_seq, bindings)

        # General case: stack-based search
        # State: (n_remaining, m_remaining, binds, tseq_remaining)
        stack = [(self.min_iter, self.max_iter, bindings, tree_seq)]
        while stack:
            n_rem, m_rem, binds, tseq = stack.pop()

            # Goal: n_rem == 0 and tseq empty
            if n_rem == 0 and not tseq:
                return add_binding(self.var, tree_seq, binds)

            if m_rem <= 0:
                continue

            for p in self._pos_args:
                lo = max(1, p.min_width)
                hi = p.max_width if p.max_width != INF else len(tseq)
                hi = min(hi, len(tseq))
                for split in range(lo, hi + 1):
                    prefix = tseq[:split]
                    b = p.match(prefix, binds)
                    if b is not None:
                        # Check neg args
                        blocked = False
                        for neg in self._neg_args:
                            if neg.match(prefix, binds) is not None:
                                blocked = True
                                break
                        if not blocked:
                            new_n = max(0, n_rem - 1)
                            new_m = m_rem - 1 if m_rem != INF else INF
                            stack.append((new_n, new_m, b, tseq[split:]))
        return None
