"""Vertical path patterns: ^@ and @."""
from __future__ import annotations
from typing import Optional
from .base import Pattern
from ..bindings import Bindings, add_binding, get_binding
from ..operators import get_var
from ..expressions import INF


class PointOfAttachment(Pattern):
    """@ — marks point of attachment in vertical path matching."""

    def __init__(self, expr):
        super().__init__()
        self.expr = expr
        # Always bind to key '@' so VerticalPatt can detect the new attachment.
        self.var = '@'
        self.min_width = 1
        self.max_width = 1

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        if len(tree_seq) != 1:
            return None
        return add_binding('@', tree_seq, bindings)


class VerticalPatt(Pattern):
    """(^@ P1 P2 ... Pn) — vertical path matching.

    State tuple: (remaining_pargs, current_tseq, binds, leading_vars)
    """

    def __init__(self, expr: tuple):
        super().__init__()
        self.expr = expr
        self.var = get_var(expr[0]) if isinstance(expr[0], str) else None
        self._raw_args = list(expr[1:])
        self._pos_args: Optional[list] = None
        self.min_width = 1
        self.max_width = 1
        self.keys = []

    def _ensure_compiled(self):
        if self._pos_args is None:
            from ..cache import build_pattern
            self._pos_args = [build_pattern(a) for a in self._raw_args]

    def match(self, tree_seq: list, bindings: Bindings) -> Optional[Bindings]:
        self._ensure_compiled()

        # (^@) with no args: always match seq of exactly one tree
        if not self._raw_args:
            if len(tree_seq) == 1:
                return add_binding(self.var, tree_seq, bindings)
            return None

        if len(tree_seq) != 1:
            return None

        pos_args = self._pos_args
        # State: (remaining_pargs_list, current_tseq, binds, leading_vars)
        stack = [(list(pos_args), tree_seq, bindings, [])]

        while stack:
            pargs, tseq, binds, leading_vars = stack.pop()

            if not pargs:
                # Goal
                return add_binding(self.var, tree_seq, binds)

            leading_patt = pargs[0]
            rest = pargs[1:]

            if leading_patt.min_width == 1 and leading_patt.max_width == 1:
                # Fixed-width: match tseq directly
                result_binds = leading_patt.match(tseq, binds)
                if result_binds is not None:
                    result_binds = add_binding(leading_patt.var, tseq, result_binds)
                    for v in leading_vars:
                        result_binds = add_binding(v, tseq, result_binds)

                    if not rest:
                        # Reject empty non-leaf nodes (Python () = Lisp nil).
                        node = tseq[0]
                        if not node.is_leaf and not node.children:
                            continue
                        return add_binding(self.var, tree_seq, result_binds)

                    at_new = get_binding('@', result_binds)
                    at_old = get_binding('@', binds)
                    if at_new is not None and at_new != at_old:
                        stack.append((rest, at_new, result_binds, []))
                    else:
                        node = tseq[0]
                        if not node.is_leaf:
                            for child in reversed(node.children):
                                stack.append((rest, [child], result_binds, []))
            elif (type(leading_patt).__name__ == 'PermutedSeq'
                  and len(tseq) == 1 and not tseq[0].is_leaf):
                # PermutedSeq in vertical path: match sub-patterns against the
                # children of the current node, not the node-as-sequence.
                from .fpseq import _match_permuted
                node = tseq[0]
                leading_patt._ensure_compiled()
                result_binds = _match_permuted(
                    leading_patt._sub_patts, node.children, binds)
                if result_binds is not None:
                    result_binds = add_binding(leading_patt.var, tseq, result_binds)
                    for v in leading_vars:
                        result_binds = add_binding(v, tseq, result_binds)
                    if not rest:
                        return add_binding(self.var, tree_seq, result_binds)
                    at_new = get_binding('@', result_binds)
                    at_old = get_binding('@', binds)
                    if at_new is not None and at_new != at_old:
                        stack.append((rest, at_new, result_binds, []))
                    else:
                        for child in reversed(node.children):
                            stack.append((rest, [child], result_binds, []))
            else:
                # Variable-width: expand into next states
                for new_state in _next_v_states(pargs, tseq, binds, leading_vars):
                    stack.append(new_state)

        return None


def _next_v_states(pargs: list, tseq: list, binds: Bindings,
                    leading_vars: list) -> list:
    """Expand variable-width leading pattern into next states.
    Returns list of (new_pargs, tseq, binds, leading_vars) tuples.
    """
    leading_patt = pargs[0]
    rest = pargs[1:]
    result = []
    cls = type(leading_patt).__name__

    if cls == 'UnrestrictedSeq':
        min_i = leading_patt.min_iter
        max_i = leading_patt.max_iter
        # Zero-length match
        if min_i == 0:
            b = add_binding(leading_patt.var, [], binds)
            for v in leading_vars:
                b = add_binding(v, [], b)
            result.append((list(rest), tseq, b, []))
        # One-or-more match: consume one, then continue with reduced pattern
        if max_i > 0:
            one = _make_unrestricted_exact(leading_patt.var)
            if max_i > 1:
                remainder = _make_unrestricted_range(
                    None,
                    max(0, min_i - 1),
                    max_i - 1 if max_i != INF else INF
                )
                new_pargs = [one, remainder] + list(rest)
            else:
                new_pargs = [one] + list(rest)
            result.append((new_pargs, tseq, binds, list(leading_vars)))

    elif cls == 'RestrictedSeq':
        leading_patt._ensure_compiled()
        min_i = leading_patt.min_iter
        max_i = leading_patt.max_iter
        if min_i == 0:
            b = add_binding(leading_patt.var, [], binds)
            result.append((list(rest), tseq, b, []))
        if max_i > 0:
            for parg in (leading_patt._pos_args or []):
                new_lv = ([leading_patt.var] if leading_patt.var else []) + list(leading_vars)
                if max_i > 1:
                    tail = _make_reduced_restricted(leading_patt)
                    new_pargs = [parg, tail] + list(rest)
                else:
                    new_pargs = [parg] + list(rest)
                result.append((new_pargs, tseq, binds, new_lv))

    elif cls == 'FreeSeq':
        leading_patt._ensure_compiled()
        sub = leading_patt._sub_patts or []
        new_lv = ([leading_patt.var] if leading_patt.var else []) + list(leading_vars)
        if sub:
            first = sub[0]
            if len(sub) > 1:
                tail = _make_reduced_free(sub[1:])
                new_pargs = [first, tail] + list(rest)
            else:
                new_pargs = [first] + list(rest)
            result.append((new_pargs, tseq, binds, new_lv))
        else:
            result.append((list(rest), tseq, binds, []))

    elif cls == 'PermutedSeq':
        leading_patt._ensure_compiled()
        sub = leading_patt._sub_patts or []
        new_lv = ([leading_patt.var] if leading_patt.var else []) + list(leading_vars)
        if sub:
            for i, chosen in enumerate(sub):
                remaining_subs = sub[:i] + sub[i+1:]
                if remaining_subs:
                    tail = _make_reduced_permuted(remaining_subs)
                    new_pargs = [chosen, tail] + list(rest)
                else:
                    new_pargs = [chosen] + list(rest)
                result.append((new_pargs, tseq, binds, new_lv))
        else:
            b = add_binding(leading_patt.var, [], binds)
            for v in leading_vars:
                b = add_binding(v, [], b)
            result.append((list(rest), tseq, b, []))
    else:
        pass  # other pattern types not supported as leading variable-width

    return result


# Helpers to create synthetic reduced patterns

def _make_unrestricted_exact(var):
    from .unrestricted import UnrestrictedSeq
    r = UnrestrictedSeq.__new__(UnrestrictedSeq)
    Pattern.__init__(r)
    r.expr = '_!'
    r.min_width = r.max_width = 1
    r.min_iter = r.max_iter = 1
    r.var = var
    r._sticky = False
    r.keys = []
    return r


def _make_unrestricted_range(var, min_i, max_i):
    from .unrestricted import UnrestrictedSeq
    r = UnrestrictedSeq.__new__(UnrestrictedSeq)
    Pattern.__init__(r)
    r.expr = '_*'
    r.min_width = r.min_iter = min_i
    r.max_width = r.max_iter = max_i
    r.var = var
    r._sticky = False
    r.keys = []
    return r


def _make_reduced_restricted(patt):
    from .restricted import RestrictedSeq
    r = RestrictedSeq.__new__(RestrictedSeq)
    Pattern.__init__(r)
    r.expr = patt.expr
    r._raw_pos = patt._raw_pos
    r._raw_neg = patt._raw_neg
    r._pos_args = patt._pos_args
    r._neg_args = patt._neg_args
    r.min_iter = max(0, patt.min_iter - 1)
    r.max_iter = patt.max_iter - 1 if patt.max_iter != INF else INF
    r.var = None
    r._sticky = False
    r.min_width = 0
    r.max_width = INF
    r.keys = []
    return r


def _make_reduced_free(remaining_subs):
    from .fpseq import FreeSeq
    r = FreeSeq.__new__(FreeSeq)
    Pattern.__init__(r)
    r.expr = ('<>',)
    r._raw_args = []
    r._sub_patts = remaining_subs
    r.var = None
    r._sticky = False
    r.min_width = sum(p.min_width for p in remaining_subs)
    r.max_width = (sum(p.max_width for p in remaining_subs)
                   if all(p.max_width != INF for p in remaining_subs) else INF)
    r.keys = []
    return r


def _make_reduced_permuted(remaining_subs):
    from .fpseq import PermutedSeq
    r = PermutedSeq.__new__(PermutedSeq)
    Pattern.__init__(r)
    r.expr = ('{}',)
    r._raw_args = []
    r._sub_patts = remaining_subs
    r.var = None
    r._sticky = False
    r.min_width = sum(p.min_width for p in remaining_subs)
    r.max_width = (sum(p.max_width for p in remaining_subs)
                   if all(p.max_width != INF for p in remaining_subs) else INF)
    r.keys = []
    return r
