"""Core type definitions for TTT."""
from __future__ import annotations
from typing import Union

# A tree expression: either an atom (str/int/float) or a tuple of tree expressions.
# We use tuples (not lists) because they are hashable -> cacheable.
TreeExpr = Union[tuple, str, int, float]
