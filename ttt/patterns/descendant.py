"""Descendant patterns: ^ ^^ ^* ^+ ^[n]
Match a single tree that has a descendant matching one of the pos_args.
"""
from __future__ import annotations
from typing import List, Optional
from .base import Pattern
from ..bindings import Bindings, add_binding
from ..operators import get_op, get_n, get_m, get_var, is_sticky

INF = float('inf')


class DescendantPatt(Pattern):
    """(^[n] P ...) (^* P ...) (^+ P ...) (^^ P ...)"""

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        op_sym = expr[0]
        op = get_op(op_sym)
        n = get_n(op_sym)
        m = get_m(op_sym)
        self.var = get_var(op_sym)
        self._sticky = is_sticky(op_sym) if isinstance(op_sym, str) else False

        raw_pos, raw_neg = _parse_desc_args(expr)
        self._raw_pos = raw_pos
        self._raw_neg = raw_neg
        self._pos_args: Optional[list] = None
        self._neg_args: Optional[list] = None

        if op == '^':
            if n is not None:
                self.min_depth = n
                self.max_depth = n
            else:
                # Count carets
                cnt = op_sym.count('^')
                self.min_depth = cnt
                self.max_depth = cnt
        elif op == '^*':
            if n is not None and m is not None:
                self.min_depth, self.max_depth = n, m
            else:
                self.min_depth, self.max_depth = 0, 10**9
        elif op == '^+':
            if n is not None and m is not None:
                self.min_depth, self.max_depth = n, m
            else:
                self.min_depth, self.max_depth = 1, 10**9
        elif op == '^^':
            self.min_depth = 2
            self.max_depth = 2

        self.min_width = 1
        self.max_width = 1
        self.keys = []

    def _ensure_compiled(self):
        if self._pos_args is None:
            from ..cache import build_pattern
            self._pos_args = [build_pattern(p) for p in self._raw_pos]
            self._neg_args = [build_pattern(p) for p in self._raw_neg]

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()
        if len(tree_seq) != 1:
            return None

        # Sticky check
        if self._sticky and self.var is not None:
            existing = bindings.get(self.var)
            if existing:
                if [t.expr for t in existing[0]] != [t.expr for t in tree_seq]:
                    return None

        root = tree_seq[0]
        # BFS/DFS over descendants
        stack = [(0, root)]
        while stack:
            depth, node = stack.pop()
            if self.min_depth <= depth <= self.max_depth:
                for p in self._pos_args:
                    b = p.match([node], bindings)
                    if b is not None:
                        failed = any(neg.match([node], bindings) is not None
                                     for neg in self._neg_args)
                        if not failed:
                            return add_binding(self.var, tree_seq, b)
            if depth < self.max_depth and not node.is_leaf:
                for child in reversed(node.children):
                    stack.append((depth + 1, child))
        return None


def _parse_desc_args(expr: tuple):
    pos, neg = [], []
    in_neg = False
    for item in expr[1:]:
        if item == '~':
            in_neg = True
        elif in_neg:
            neg.append(item)
        else:
            pos.append(item)
    return pos, neg
