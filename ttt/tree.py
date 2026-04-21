from __future__ import annotations
from .types import TreeExpr


class Tree:
    __slots__ = ('expr', 'children', 'height', 'keys',
                 'parent', 'parent_idx', 'to_subtrees', 'dfs_order', '_is_atom')
    
    def __init__(self):
        """use build_tree()"""
        self.expr: TreeExpr = None
        self.children: list['Tree'] = []
        self.height: int = 0
        self.keys: list = []
        self.parent: Tree | None = None
        self.parent_idx: int | None = None
        self.to_subtrees: dict | None = None
        self.dfs_order: int = 0
        self._is_atom: bool = True
        
    @property
    def is_leaf(self) -> bool:
        return self._is_atom
    
    
def _dfs(root: Tree):
    """Yield all nodes in DFS left-to-right order using an explicit stack."""
    stack = [root]
    
    while stack:
        node = stack.pop()
        yield node
        if not node.is_leaf:
            for child in reversed(node.children):
                stack.append(child)
    
    
def build_tree(expression: TreeExpr, *, root: bool = True,
               index_subtrees: bool = True) -> Tree:
    """Convert a TreeExpr into a Tree node with parent links and height.
    
    When root=True, also assign dfs_order to every node and builds the 
    subtree index (symbol, depth) -> [Tree, ...] for fast pattern matching."""
    from .keys import extract_keys_with_ops, add_to_index
    
    node = Tree()
    node.expr = expression
    node.keys = extract_keys_with_ops(expression)
    
    if not isinstance(expression, tuple):
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
        update_tree_index(node)
    
    return node
    
    
def update_tree_index(root: Tree) -> None:
    """Rebuild the subtree index and dfs_order for all nodes under root.
    
    Call this after any in-place modifications of the tree structure."""
    from .keys import add_to_index
    subtrees: dict = {}
    
    for dfs, node in enumerate(_dfs(root), start=1):
        node.dfs_order = dfs
        for key in node.keys:
            add_to_index(key, node, subtrees)
    
    root.to_subtrees = subtrees