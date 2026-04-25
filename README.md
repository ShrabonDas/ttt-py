# ttt_py

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

TTT is a pattern matching and rewriting language for s-expression trees, analogous to regex for strings. This is the Python port, originally written in Common Lisp by Adam Purtee / Gene Louis Kim. See the paper [TTT: A tree transduction language for syntactic and semantic processing](http://aclweb.org/anthology/W12-0803).

Trees are Python tuples. Leaves are strings, integers, or floats.

## Branches

- **`reference`** — complete, working Python implementation. Use this if you need a fully functional TTT now.
- **`main`** — clean rebuild in progress, one small commit at a time, with tests and documentation.

## Installation

```bash
pip install -e .
```

## Quick start

```python
from ttt import match_expr, apply_rule, apply_rules, store_pred, mk_pred_ttt

# Match a pattern against a tree
match_expr('_*', ('A', 'B', 'C'))         # True
match_expr(('NP', '_+'), ('NP', 'dog'))   # True
match_expr(('NP', '_+'), ('VP', 'run'))   # False

# Capture with variables
match_expr(('NP', '_+1'), ('NP', 'dog', 'cat'))
# => {'_+1': [['dog', 'cat']]}

# Apply a rewrite rule  (pattern / template)
apply_rule(('/', ('NP', '_+1'), ('NP-moved', '_+1')), ('NP', 'the', 'dog'))
# => ('NP-moved', 'the', 'dog')

# Apply a list of rules until convergence
rules = [
    ('/', ('_*', ('NP', '_+', ('PP', '_+1')), '_*1'),
          ('_*', ('NP', '_+'), ('PP', '_+1'), '_*1')),
]
apply_rules(rules, ('S', ('NP', 'the', 'dog', ('PP', 'in', 'the', 'park'))))
```

## Pattern operators

| Operator | Meaning |
|----------|---------|
| `_*` | zero or more nodes |
| `_+` | one or more nodes |
| `_?` | zero or one node |
| `_*n` / `_+n` / `_?n` | same, bound to variable `n` |
| `_!` | any single node (not a sequence) |
| `(! a b c)` | matches `a`, `b`, or `c` |
| `(~ a b c)` | matches anything except `a`, `b`, `c` |
| `(@  ...)` | matches any permutation of the children |
| `(_** pat)` | matches `pat` anywhere in the subtree (descendant) |

## Predicates

```python
# Register a Python function as a predicate
def noun_phrase?(tree):
    return isinstance(tree, tuple) and tree[0] == 'NP'

store_pred('noun_phrase?', noun_phrase?)
match_expr('noun_phrase?', ('NP', 'dog'))  # True

# Or define a predicate backed by a TTT pattern
mk_pred_ttt('short-np?', ('NP', '_!'))
match_expr('short-np?', ('NP', 'dog'))   # True
match_expr('short-np?', ('NP', 'the', 'dog'))  # False
```

## apply_rule / apply_rules options

```python
apply_rule(rule, tree, shallow=False, max_n=None, trace=False)
apply_rules(rules, tree, shallow=False, max_n=None, trace=False,
            rule_order='slow-forward')
```

`rule_order` options:
- `'slow-forward'` — apply each rule until exhausted, possibly repeating the sequence
- `'earliest-first'` — always apply the first applicable rule, repeat until none apply
- `'fast-forward'` — apply each rule at most once, repeat list until convergence

## Running tests

```bash
export PYTHONPATH=.
pytest
```

## Original Lisp library

The original Common Lisp implementation is maintained at [github.com/genelkim/ttt](https://github.com/genelkim/ttt).
