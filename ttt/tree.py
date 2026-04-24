from __future__ import annotations
from .types import TreeExpr


class Tree:
    __slots__ = ('expr', 'children', 'height', 'keys',
                 'parent', 'parent_idx', 'to_subtrees', 'dfs_order', '_is_atom')
    
    def __init__(self, expression: TreeExpr, *, root: bool = True):
        from .keys import extract_keys_with_ops
        
        self.expr: TreeExpr = expression
        self.keys: list = extract_keys_with_ops(expression)
        self.parent: Tree | None = None
        self.parent_idx: int | None = None
        self.to_subtrees: dict | None = None
        self.dfs_order: int = 0

        if not isinstance(expression, tuple):
            self._is_atom = True
            self.children: list[Tree] = []
            self.height = 0
        else:
            self._is_atom = False
            children = []
            for i, item in enumerate(expression):
                child = Tree(item, root=False)
                child.parent = self
                child.parent_idx = i
                children.append(child)
            self.children = children
            self.height = 1 + max(c.height for c in children) if children else 1
            
        if root:
            update_tree_index(self)
        
    @property
    def is_leaf(self) -> bool:
        return self._is_atom
    
    def _dfs(self):
        """Yield all nodes in DFS left-to-right order using an explicit stack."""
        stack = [self]
        
        while stack:
            node = stack.pop()
            yield node
            if not node.is_leaf:
                for child in reversed(node.children):
                    stack.append(child)
    
    
def update_tree_index(root: Tree) -> None:
    """Rebuild the subtree index and dfs_order for all nodes under root.
    
    Call this after any in-place modifications of the tree structure."""
    from .keys import add_to_index
    subtrees: dict = {}
    
    for dfs, node in enumerate(root._dfs(), start=1):
        node.dfs_order = dfs
        for key in node.keys:
            add_to_index(key, node, subtrees)
    
    root.to_subtrees = subtrees