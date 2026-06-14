"""Deep-match engine: search a tree for a pattern match."""
from __future__ import annotations
from typing import Optional, List
from .bindings import Bindings, get_binding
from .tree import Tree
from .keys import fastmap


def deep_match(pattern, tree: Tree) -> Optional[Bindings]:
    """Search tree for first subtree matching pattern. Uses key index if available."""
    if pattern.keys and tree.to_subtrees is not None:
        for key in pattern.keys:
            for subtree in fastmap(key, tree.to_subtrees):
                if (subtree.height >= pattern.min_height and
                        subtree.height <= pattern.max_height):
                    b = pattern.match([subtree], {})
                    if b is not None:
                        return b
        return None
    return _deep_match_brute(pattern, tree)


def _deep_match_brute(pattern, tree: Tree) -> Optional[Bindings]:
    b = pattern.match([tree], {})
    if b is not None:
        return b
    if not tree.is_leaf:
        for child in tree.children:
            b = _deep_match_brute(pattern, child)
            if b is not None:
                return b
    return None


def deepest_matches(pattern, tree: Tree) -> List[Bindings]:
    """Return all subtree matches (deepest first)."""
    if pattern.keys and tree.to_subtrees is not None:
        result = []
        for key in pattern.keys:
            for subtree in fastmap(key, tree.to_subtrees):
                if (subtree.height >= pattern.min_height and
                        subtree.height <= pattern.max_height):
                    b = pattern.match([subtree], {})
                    if b is not None:
                        result.append(b)
        return result
    return _deepest_matches_brute(pattern, tree)


def _deepest_matches_brute(pattern, tree: Tree) -> List[Bindings]:
    b = pattern.match([tree], {})
    if tree.is_leaf:
        return [b] if b is not None else []
    child_results = []
    for child in tree.children:
        child_results.extend(_deepest_matches_brute(pattern, child))
    if b is not None:
        return [b] + child_results
    return child_results
