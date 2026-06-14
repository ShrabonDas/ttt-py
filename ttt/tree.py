"""Tree node class and builder for TTT."""
from __future__ import annotations
from typing import Optional, List
from .types import TreeExpr


class Tree:
    """A compiled tree node with parent links, height, and subtree index."""
    __slots__ = ('expr', 'children', 'height', 'keys',
                 'parent', 'parent_idx', 'to_subtrees', 'dfs_order', '_is_atom')

    def __init__(self):
        self.expr: TreeExpr = None
        self.children: List['Tree'] = []   # empty list = leaf
        self.height: int = 0
        self.keys: list = []
        self.parent: Optional['Tree'] = None
        self.parent_idx: Optional[int] = None
        self.to_subtrees: Optional[dict] = None   # key -> [Tree, ...]
        self.dfs_order: int = 0
        self._is_atom: bool = True  # True for non-tuple expressions

    @property
    def is_leaf(self) -> bool:
        # Atoms are leaves; empty tuples () are NOT (they're empty lists)
        return self._is_atom


def build_tree(expression: TreeExpr, *, root: bool = True,
               index_subtrees: bool = True) -> Tree:
    """Convert a Python expression (tuple/atom) into a Tree node."""
    from .keys import extract_keys_with_ops, add_to_index

    node = Tree()
    node.expr = expression
    node.keys = extract_keys_with_ops(expression)

    if not isinstance(expression, tuple):
        # Atom leaf node
        node._is_atom = True
        node.children = []
        node.height = 0
    else:
        node._is_atom = False
        children = []
        for i, item in enumerate(expression):
            child = build_tree(item, root=False, index_subtrees=False)
            child.parent = node
            child.parent_idx = i
            children.append(child)
        node.children = children
        node.height = 1 + max(c.height for c in children) if children else 1

    if root:
        # Build subtree index and assign DFS order
        subtrees: dict = {}  # (sym, depth) -> [Tree, ...]
        dfs = [0]
        stack = [node]
        while stack:
            current = stack.pop()
            dfs[0] += 1
            current.dfs_order = dfs[0]
            if index_subtrees:
                for key in current.keys:
                    add_to_index(key, current, subtrees)
            if not current.is_leaf:
                for child in reversed(current.children):
                    stack.append(child)
        if index_subtrees:
            node.to_subtrees = subtrees
    return node


def update_dfs_order(root: Tree) -> None:
    count = [0]
    stack = [root]
    while stack:
        node = stack.pop()
        count[0] += 1
        node.dfs_order = count[0]
        if not node.is_leaf:
            for child in reversed(node.children):
                stack.append(child)


def update_subtree_index(root: Tree) -> None:
    from .keys import add_to_index
    subtrees: dict = {}
    stack = [root]
    while stack:
        node = stack.pop()
        for key in node.keys:
            add_to_index(key, node, subtrees)
        if not node.is_leaf:
            for child in reversed(node.children):
                stack.append(child)
    root.to_subtrees = subtrees
