"""Rule application: apply_rule and apply_rules."""
from __future__ import annotations
from typing import List, Optional, Tuple
from .tree import Tree, build_tree, update_dfs_order, update_subtree_index
from .cache import build_pattern
from .bindings import get_binding
from .match_engine import deep_match, deepest_matches
from .template import template_to_tree
from .expressions import INF


def _get_matches(pattern, tree: Tree, rule_depth: str) -> List:
    """Return a list of binding dicts for the given rule_depth mode."""
    if rule_depth == ':shallow':
        b = pattern.match([tree], {})
        return [b] if b is not None else []
    elif rule_depth == ':deepest':
        return deepest_matches(pattern, tree)
    else:  # :default
        b = deep_match(pattern, tree)
        return [b] if b is not None else []


def _do_transduction(tree: Tree, tbind, bindings: dict) -> Tree:
    """Apply one transduction: build new subtree from template and splice it in."""
    raw = template_to_tree(tbind.template_expr, bindings, True)
    if len(raw) != 1:
        raise RuntimeError("Transduction RHS must produce exactly one tree.")
    new_expr = raw[0]
    new_node = build_tree(new_expr, root=True, index_subtrees=True)

    par = tbind.parent
    par_idx = tbind.parent_idx

    if par is None:
        # Replace root
        tree.expr = new_node.expr
        tree.children = new_node.children
        tree.height = new_node.height
        tree.keys = new_node.keys
        tree.parent = None
        tree.parent_idx = None
        for i, c in enumerate(tree.children):
            c.parent = tree
            c.parent_idx = i
    else:
        new_node.parent = par
        new_node.parent_idx = par_idx
        children = list(par.children)
        children[par_idx] = new_node
        par.children = children
        # Update parent-idx for all siblings
        for i, c in enumerate(par.children):
            c.parent_idx = i
        # Rebuild expr up the ancestor chain
        ancestor = par
        while ancestor is not None:
            ancestor.expr = tuple(c.expr for c in ancestor.children)
            from .keys import extract_keys_with_ops
            ancestor.keys = extract_keys_with_ops(ancestor.expr)
            ancestor = ancestor.parent

    update_subtree_index(tree)
    update_dfs_order(tree)
    return tree


def apply_rule(rule_expr, tree_expr,
               shallow: bool = False,
               trace: bool = False,
               max_n: int = 10**9,
               rule_depth: str = ':default') -> any:
    """Apply a single rule to tree_expr until convergence. Returns the result expr."""
    if shallow:
        rule_depth = ':shallow'

    index = rule_depth != ':shallow'
    tr = build_tree(tree_expr, root=True, index_subtrees=index)
    compiled = build_pattern(rule_expr)

    prevs = [tree_expr]
    converged = False
    n = 0

    bs = _get_matches(compiled, tr, rule_depth)
    while not converged and bs and n < max_n:
        b = bs.pop(0)
        tbind = get_binding('/', b)
        tr = _do_transduction(tr, tbind, b)
        n += 1
        if tr.expr not in prevs:
            prevs.append(tr.expr)
            bs = bs + _get_matches(compiled, tr, rule_depth)
        elif rule_depth != ':deepest':
            converged = True

    return prevs[-1]  # last novel state


def apply_rules(rules: list, tree_expr,
                rule_order: str = ':slow-forward',
                trace: bool = False,
                shallow: bool = False,
                deepest: bool = False,
                max_n: int = 10**9,
                rule_depth: str = ':default') -> any:
    """Apply a list of rules to tree_expr. Returns the result expr."""
    if shallow:
        rule_depth = ':shallow'
    if deepest:
        rule_depth = ':deepest'

    index = rule_depth != ':shallow'
    tr = build_tree(tree_expr, root=True, index_subtrees=index)
    compiled_rules = [build_pattern(r) for r in rules]
    prevs = [tree_expr]
    n = 0

    if rule_order == ':slow-forward':
        converged = False
        while not converged:
            converged = True
            for r in compiled_rules:
                bs = _get_matches(r, tr, rule_depth)
                converged2 = False
                while not converged2 and bs and bs[0] is not None and n < max_n:
                    converged2 = True
                    b = bs.pop(0)
                    tbind = get_binding('/', b)
                    tr = _do_transduction(tr, tbind, b)
                    n += 1
                    if tr.expr not in prevs:
                        prevs.append(tr.expr)
                        bs = bs + _get_matches(r, tr, rule_depth)
                        converged = False
                        converged2 = False
                    elif rule_depth == ':deepest':
                        converged = False
                        converged2 = False

    elif rule_order == ':earliest-first':
        converged = False
        while not converged:
            converged = True
            for r in compiled_rules:
                bs = _get_matches(r, tr, rule_depth)
                if bs and bs[0] is not None and n < max_n:
                    b = bs[0]
                    tbind = get_binding('/', b)
                    tr = _do_transduction(tr, tbind, b)
                    n += 1
                    if tr.expr not in prevs:
                        prevs.append(tr.expr)
                        converged = False
                    break

    elif rule_order == ':fast-forward':
        converged = False
        while not converged:
            converged = True
            for r in compiled_rules:
                bs = _get_matches(r, tr, rule_depth)
                if bs and bs[0] is not None and n < max_n:
                    b = bs[0]
                    tbind = get_binding('/', b)
                    tr = _do_transduction(tr, tbind, b)
                    n += 1
                    if tr.expr not in prevs:
                        prevs.append(tr.expr)
                        converged = False
    else:
        raise ValueError(f"Unknown rule_order: {rule_order}")

    return tr.expr
