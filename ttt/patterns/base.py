"""Abstract Pattern base class."""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List, TYPE_CHECKING
from ..bindings import Bindings

if TYPE_CHECKING:
    from ..tree import Tree


class Pattern(ABC):
    """Abstract base for all TTT patterns."""

    def __init__(self):
        self.expr = None           # original expression
        self.min_width: int = 1
        self.max_width: int = 1    # use float('inf') for unbounded
        self.min_height: int = 0
        self.max_height: int = 10**9
        self.keys: list = []
        self.var: Optional[str] = None

    @abstractmethod
    def match(self, tree_seq: List['Tree'], bindings: Bindings) -> Optional[Bindings]:
        """Try to match this pattern against tree_seq.
        Returns updated bindings on success, None on failure.
        """
        ...
