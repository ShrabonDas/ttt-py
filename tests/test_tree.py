from ttt.tree import Tree, build_tree, update_dfs_order, update_subtree_index


# ---------------------------------------------------------------------------
# Leaf nodes
# ---------------------------------------------------------------------------

def test_string_leaf():
    t = build_tree('dog')
    assert t.expr == 'dog'
    assert t.is_leaf
    assert t.children == []
    assert t.height == 0
    assert t.parent is None
    assert t.parent_idx is None

def test_int_leaf():
    t = build_tree(42)
    assert t.expr == 42
    assert t.is_leaf

def test_float_leaf():
    t = build_tree(3.14)
    assert t.expr == 3.14
    assert t.is_leaf

def test_empty_tuple():
    t = build_tree(())
    assert not t.is_leaf
    assert t.children == []
    assert t.height == 1


# ---------------------------------------------------------------------------
# Tuple nodes
# ---------------------------------------------------------------------------

def test_single_child():
    t = build_tree(('NP',))
    assert not t.is_leaf
    assert len(t.children) == 1
    assert t.children[0].expr == 'NP'
    assert t.height == 1

def test_flat_tuple():
    t = build_tree(('NP', 'the', 'dog'))
    assert not t.is_leaf
    assert len(t.children) == 3
    assert t.height == 1

def test_nested_tuple():
    t = build_tree(('S', ('NP', 'the', 'dog'), ('VP', 'runs')))
    assert t.height == 2
    assert len(t.children) == 3

def test_deeply_nested():
    t = build_tree(('A', ('B', ('C', 'leaf'))))
    assert t.height == 3


# ---------------------------------------------------------------------------
# Parent links
# ---------------------------------------------------------------------------

def test_parent_link():
    t = build_tree(('NP', 'the', 'dog'))
    for i, child in enumerate(t.children):
        assert child.parent is t
        assert child.parent_idx == i

def test_nested_parent_link():
    t = build_tree(('S', ('NP', 'dog'), ('VP', 'runs')))
    np = t.children[1]  # children[0]='S', [1]=('NP','dog'), [2]=('VP','runs')
    assert np.parent is t
    assert np.children[0].parent is np  # 'NP' leaf


# ---------------------------------------------------------------------------
# DFS order
# ---------------------------------------------------------------------------

def test_dfs_order_root():
    t = build_tree('x')
    assert t.dfs_order == 1

def test_dfs_order_flat():
    t = build_tree(('A', 'B', 'C'))
    assert t.dfs_order == 1
    assert t.children[0].dfs_order == 2
    assert t.children[1].dfs_order == 3
    assert t.children[2].dfs_order == 4

def test_dfs_order_nested():
    t = build_tree(('S', ('NP', 'dog'), ('VP', 'runs')))
    # tuple=1, 'S'=2, ('NP','dog')=3, 'NP'=4, 'dog'=5, ('VP','runs')=6, 'VP'=7, 'runs'=8
    assert t.dfs_order == 1
    assert t.children[0].dfs_order == 2       # 'S' leaf
    assert t.children[1].dfs_order == 3       # ('NP', 'dog')
    assert t.children[1].children[0].dfs_order == 4  # 'NP'
    assert t.children[1].children[1].dfs_order == 5  # 'dog'
    assert t.children[2].dfs_order == 6       # ('VP', 'runs')

def test_update_dfs_order():
    t = build_tree(('A', 'B'))
    t.children[0].dfs_order = 999
    update_dfs_order(t)
    assert t.children[0].dfs_order == 2


# ---------------------------------------------------------------------------
# Subtree index
# ---------------------------------------------------------------------------

def test_to_subtrees_built_at_root():
    t = build_tree(('NP', 'dog'))
    assert t.to_subtrees is not None

def test_to_subtrees_none_for_non_root():
    t = build_tree(('NP', 'dog'))
    assert t.children[0].to_subtrees is None

def test_index_subtrees_false():
    t = build_tree(('NP', 'dog'), index_subtrees=False)
    assert t.to_subtrees is None

def test_update_subtree_index_rebuilds():
    t = build_tree(('NP', 'dog'), index_subtrees=False)
    assert t.to_subtrees is None
    update_subtree_index(t)
    assert t.to_subtrees is not None
