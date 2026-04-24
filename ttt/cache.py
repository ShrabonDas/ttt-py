"""Pattern cache: build_pattern with memoization."""
from __future__ import annotations
import threading
from .types import TreeExpr
from .operators import get_op, op_requires_args, is_pred_sym

_built_patterns: dict = {}
_lock = threading.RLock()


def build_pattern(expr: TreeExpr):
    """Build (and cache) a Pattern object for the given expression."""
    # Use expr itself as cache key — tuples and strings are hashable
    try:
        key = expr
        with _lock:
            if key in _built_patterns:
                return _built_patterns[key]
    except TypeError:
        key = None  # unhashable (shouldn't happen)

    patt = _build_uncached(expr)

    if key is not None:
        with _lock:
            _built_patterns[key] = patt
    return patt


def _build_uncached(expr: TreeExpr):
    from .patterns.literal import LiteralPatt
    from .patterns.unrestricted import UnrestrictedSeq
    from .patterns.restricted import RestrictedSeq
    from .patterns.general import GeneralPatt
    from .patterns.fpseq import FreeSeq, PermutedSeq
    from .patterns.descendant import DescendantPatt
    from .patterns.vertical import VerticalPatt, PointOfAttachment
    from .patterns.predicate import PredicatePatt, get_pred_fn
    from .patterns.transduction import TransductionPatt

    # Atomic expressions
    if not isinstance(expr, tuple):
        op = get_op(expr)
        if op in ('_!', '_+', '_*', '_?'):
            return UnrestrictedSeq(expr)
        if op == '@':
            return PointOfAttachment(expr)
        if op == 'pred' or is_pred_sym(str(expr)):
            fn = get_pred_fn(str(expr))
            return PredicatePatt(str(expr), fn)
        # Non-'?' predicate registered via mk_pred_ttt
        from .patterns.predicate import _predicate_table
        if str(expr) in _predicate_table:
            fn = _predicate_table[str(expr)]
            return PredicatePatt(str(expr), fn)
        # Sticky variable without args
        if op in ('!', '+', '*', '?', '<>', '{}', '^', '^*', '^+', '^^', '^@'):
            from .patterns.sticky import StuckPatt
            return StuckPatt(expr)
        # Literal atom
        return LiteralPatt(expr)

    # Tuple (list) expressions
    if not expr:
        return LiteralPatt(expr)   # empty tuple: matches empty list

    head = expr[0]
    op = get_op(head) if isinstance(head, (str, int, float)) else None

    # Note: _! _+ _* _? do NOT require args, so a tuple like ('_!',) or ('_!','X')
    # is a GeneralPatt (matches children of a node), NOT an UnrestrictedSeq.
    # UnrestrictedSeq is only built for bare atoms like '_!', '_*' etc.

    if op in ('!', '+', '*', '?'):
        return RestrictedSeq(expr)

    if op == '<>':
        return FreeSeq(expr)

    if op == '{}':
        return PermutedSeq(expr)

    if op in ('^', '^^', '^*', '^+'):
        return DescendantPatt(expr)

    if op == '^@':
        return VerticalPatt(expr)

    if op == '/':
        return TransductionPatt(expr)

    # General compound pattern (predicate at head treated as first sub-pattern)
    return GeneralPatt(expr)


def clear_cache():
    with _lock:
        _built_patterns.clear()
