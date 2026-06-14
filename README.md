# ttt-py

Python port of [TTT (Tree-to-Tree Transduction Language)](https://github.com/genelkim/ttt),
originally written in Common Lisp by Adam Purtee and maintained by Gene Louis Kim.
TTT fills the same role for s-expression trees as regex does for strings.

## Setup

Install with uv:

```bash
uv sync
```

## Running tests

```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

## Usage

```python
from ttt import apply_rule
result = apply_rule("(a _! b)", "(c d e)", "(a (c d) b)")
```

## License

See LICENSE.
