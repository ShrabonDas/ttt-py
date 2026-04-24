"""TTT: Tree-to-Tree Transduction — Python port."""
from __future__ import annotations
from .types import TreeExpr
from .cache import build_pattern, clear_cache
from .tree import build_tree
from .bindings import get_binding
from .match_engine import deep_match
from .transductions import apply_rule, apply_rules
from .util import hide_ttt_ops, unhide_ttt_ops, ttt_all_rule_results, ttt_apply_rule_possibilities
from .patterns.predicate import store_pred, PredicatePatt, _predicate_table
from .template import register_template_fn


def match_expr(pattern_expr: TreeExpr, tree_expr: TreeExpr) -> object:
    """Match a pattern expression against a tree expression.
    Returns True (or a bindings dict) on success, False on failure.
    """
    patt = build_pattern(pattern_expr)
    tree = build_tree(tree_expr, root=True, index_subtrees=True)
    b = patt.match([tree], {})
    if b is None:
        return False
    # Filter out internal '/' binding
    user_binds = {k: v for k, v in b.items() if k != '/'}
    if not user_binds:
        return True
    # Return simplified bindings: var -> list_of_exprs (most recent)
    result = {}
    for k, v_list in user_binds.items():
        result[k] = [[t.expr for t in seq] if isinstance(seq, list) else seq
                     for seq in v_list]
    return result


def mk_pred_ttt(pred_op: str, patt_expr: TreeExpr) -> None:
    """Define a TTT predicate backed by a pattern."""
    from .cache import build_pattern as bp
    patt = bp(patt_expr)

    def pred_fn(tree_expr):
        from .tree import build_tree as bt
        t = bt(tree_expr, root=True, index_subtrees=False)
        return patt.match([t], {}) is not None

    store_pred(pred_op, pred_fn)
    # Also register the pattern-backed predicate
    pp = PredicatePatt(pred_op, pred_fn, ttt_pred=False)
    _predicate_table[pred_op] = pp._fn
    clear_cache()


__all__ = [
    'match_expr', 'apply_rule', 'apply_rules', 'store_pred', 'mk_pred_ttt',
    'hide_ttt_ops', 'unhide_ttt_ops',
    'ttt_all_rule_results', 'ttt_apply_rule_possibilities',
    'register_template_fn', 'build_pattern',
]
