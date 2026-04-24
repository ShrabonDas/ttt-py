"""Template construction: evaluate the RHS of a transduction rule."""
from __future__ import annotations
from typing import Any, List
from .types import TreeExpr
from .bindings import Bindings, get_binding, bound

# Built-in template functions (names ending with !)
_TEMPLATE_FUNCTIONS: dict = {}

import threading
_subst_counter = 0
_subst_lock = threading.Lock()


def register_template_fn(name: str, fn):
    _TEMPLATE_FUNCTIONS[name] = fn


def template_to_tree(template_expr: TreeExpr, bindings: Bindings,
                     return_expr: bool = True) -> list:
    """Build a new tree expression from a template and bindings.
    Returns a list of tree expressions (usually length 1).
    """
    # Function call: (fn! arg1 arg2 ...)
    if (isinstance(template_expr, tuple) and template_expr
            and isinstance(template_expr[0], str)
            and template_expr[0].endswith('!')
            and _is_callable_fn(template_expr[0])):
        fn = _get_fn(template_expr[0])
        evaled_args = []
        for arg in template_expr[1:]:
            evaled_args.extend(template_to_tree(arg, bindings, True))
        result = fn(*evaled_args)
        if isinstance(result, list):
            return result
        return [result]

    # Compound expression (tuple)
    if isinstance(template_expr, tuple):
        parts = []
        for item in template_expr:
            parts.extend(template_to_tree(item, bindings, return_expr))
        return [tuple(parts)]

    # Bound variable — look up by var name (suffix of the pattern symbol)
    if isinstance(template_expr, str) and not template_expr.startswith('/'):
        from .operators import get_var as _get_var
        lookup_key = _get_var(template_expr) or template_expr
        val = get_binding(lookup_key, bindings)
        if val is None:
            val = get_binding(template_expr, bindings)
        if val is not None:
            from .tree import Tree
            if isinstance(val, list) and val and isinstance(val[0], Tree):
                return [t.expr for t in val]
            return [val] if not isinstance(val, list) else val

    # Literal atom
    return [template_expr]


def _is_callable_fn(name: str) -> bool:
    if name in _TEMPLATE_FUNCTIONS:
        return True
    import builtins
    return hasattr(builtins, name.rstrip('!')) and callable(getattr(builtins, name.rstrip('!')))


def _get_fn(name: str):
    if name in _TEMPLATE_FUNCTIONS:
        return _TEMPLATE_FUNCTIONS[name]
    raise KeyError(f"Template function not found: {name}")


# Built-in template functions

def _join_with_dash(*args) -> list:
    """join-with-dash!: concatenate symbol names with dashes, returns a 1-element tuple."""
    parts = []
    for a in args:
        if not isinstance(a, str):
            raise TypeError(f"join-with-dash! expects symbols, got {a!r}")
        parts.append(a)
    return [('-'.join(parts),)]

def _concatenate_syms(*args) -> list:
    """concatenate-syms!: concatenate symbol names without separator, returns a 1-element tuple."""
    parts = []
    for a in args:
        if not isinstance(a, str):
            raise TypeError(f"concatenate-syms! expects symbols, got {a!r}")
        parts.append(a)
    return [(''.join(parts),)]

def _subst_new(sym, expr) -> list:
    """subst-new!: replace every occurrence of sym in expr with a fresh symbol."""
    global _subst_counter
    if not isinstance(sym, str):
        raise TypeError(f"subst-new! expects a symbol as first arg, got {sym!r}")
    with _subst_lock:
        _subst_counter += 1
        n = _subst_counter
    newsym = f"{sym}.{n}"
    result = _deep_substitute(newsym, sym, expr)
    return [result]

def _deep_substitute(newitem, olditem, seq):
    if isinstance(seq, tuple):
        return tuple(_deep_substitute(newitem, olditem, x) for x in seq)
    return newitem if seq == olditem else seq


register_template_fn('join-with-dash!', _join_with_dash)
register_template_fn('concatenate-syms!', _concatenate_syms)
register_template_fn('subst-new!', _subst_new)
