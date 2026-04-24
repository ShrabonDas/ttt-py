"""Operator registry and symbol parsing for TTT.

Maps operator symbols (strings) to their metadata and Python pattern classes.
"""
from __future__ import annotations
import re
from typing import Optional, Tuple

# Set of all TTT operator names
OPERATORS = {
    '_!', '_?', '_*', '_+',
    '*', '+', '!', '?',
    '<>', '{}',
    '^', '^*', '^+', '^^', '^@',
    '@', '/',
}

# Operators that require arguments (list form)
REQUIRES_ARGS = {'*', '+', '!', '?', '<>', '{}', '^', '^*', '^+', '^^', '^@', '/'}

# Pattern: op chars that cannot appear in suffixes
_INVALID_SUFFIX_CHARS = set('!*+_?^<>{}@ ')

# Pre-compiled regex for bounded iteration: e.g. _![3] or _*[2-5]
_BOUNDED_RE = re.compile(r'^(\[(\d+)(?:-(\d+))?\])$')


def parse_sym(sym: str) -> Tuple[Optional[str], Optional[str], Optional[int], Optional[int]]:
    """Parse a TTT symbol string.
    Returns (op, var, n, m) where:
      op  — operator name (e.g. '_!', '!', '^*') or 'literal'
      var — variable name if present, else None
      n   — first bound integer if present
      m   — second bound integer if present
    """
    if not sym:
        return ('literal', None, None, None)

    # Try each possible operator prefix (longest first)
    for op in sorted(OPERATORS, key=len, reverse=True):
        if sym.startswith(op):
            suffix = sym[len(op):]
            if _valid_suffix(suffix):
                n, m = _parse_bounds(suffix)
                var = _parse_var(suffix)
                return (op, var, n, m)

    # Check if it's a predicate: name ending in '?' optionally followed by digits
    q = sym.find('?')
    if q >= 0:
        rest = sym[q+1:]
        if rest == '' or rest.isdigit():
            return ('pred', sym, None, None)

    return ('literal', None, None, None)


def _valid_suffix(suffix: str) -> bool:
    """A suffix is valid if it contains no operator-start characters."""
    # Allow: digits, letters, '.', '[', ']', '-' (for bounds)
    for ch in suffix:
        if ch in _INVALID_SUFFIX_CHARS:
            return False
    return True


def _parse_bounds(suffix: str) -> Tuple[Optional[int], Optional[int]]:
    lb = suffix.find('[')
    rb = suffix.find(']')
    if lb == -1 or rb == -1:
        return None, None
    inner = suffix[lb+1:rb]
    if '-' in inner:
        parts = inner.split('-', 1)
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None, None
    else:
        try:
            n = int(inner)
            return n, None
        except ValueError:
            return None, None


def _parse_var(suffix: str) -> Optional[str]:
    """Extract variable name from suffix (stripping bounds)."""
    lb = suffix.find('[')
    rb = suffix.find(']')
    if lb >= 0 and rb >= 0:
        # Remove [n] or [n-m] part
        suffix = suffix[:lb] + suffix[rb+1:]
    return suffix if suffix else None


# Cache for parsed symbols
_parse_cache: dict = {}


def get_op(sym) -> str:
    """Return the operator string for a symbol, or 'literal'."""
    if isinstance(sym, (int, float)):
        return 'literal'
    if not isinstance(sym, str):
        return 'literal'
    cached = _parse_cache.get(sym)
    if cached is not None:
        return cached[0]
    result = parse_sym(sym)
    _parse_cache[sym] = result
    return result[0]


def get_var(sym) -> Optional[str]:
    if not isinstance(sym, str):
        return None
    cached = _parse_cache.get(sym)
    if cached is None:
        cached = parse_sym(sym)
        _parse_cache[sym] = cached
    return cached[1]


def get_n(sym) -> Optional[int]:
    if not isinstance(sym, str):
        return None
    cached = _parse_cache.get(sym)
    if cached is None:
        cached = parse_sym(sym)
        _parse_cache[sym] = cached
    return cached[2]


def get_m(sym) -> Optional[int]:
    if not isinstance(sym, str):
        return None
    cached = _parse_cache.get(sym)
    if cached is None:
        cached = parse_sym(sym)
        _parse_cache[sym] = cached
    return cached[3]


def op_requires_args(op: str) -> bool:
    return op in REQUIRES_ARGS


def is_sticky(sym: str) -> bool:
    """Return True if sym is a sticky variable (contains '.')."""
    if not isinstance(sym, str):
        return False
    op = get_op(sym)
    if op == 'literal':
        return False
    # Has a dot in suffix
    cached = _parse_cache.get(sym)
    if cached is None:
        cached = parse_sym(sym)
        _parse_cache[sym] = cached
    var = cached[1]
    return var is not None and '.' in var


def is_pred_sym(sym: str) -> bool:
    """Return True if sym looks like a predicate (ends with ?)."""
    if not isinstance(sym, str):
        return False
    # Must not be a known TTT operator
    op = get_op(sym)
    if op != 'literal' and op != 'pred':
        # It resolved to a known operator — not a predicate
        if op in OPERATORS:
            return False
    q = sym.find('?')
    if q < 0:
        return False
    # The '?' must come from a function name, not an operator suffix
    # Known operators ending in ?: _? and ?
    if sym in ('_?', '?'):
        return False
    rest = sym[q+1:]
    return rest == '' or rest.isdigit()
