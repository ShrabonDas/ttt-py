# ttt_py

A Python port of [TTT (Tree-to-Tree Transduction Language)](https://github.com/genelkim/ttt), originally written in Common Lisp by Adam Purtee and maintained by Gene Louis Kim. TTT fills the same role for s-expression trees as regex does for strings.

> **Status**: In Development

## What this repo contains

- `ttt-py/` - the Python port (in progress)
- `repos/ttt/` - the original Lisp source as a git submodule, used as the ground-truth reference for testing

## Setup

**Clone with submodule** (required to get the Lisp reference source):

```bash
git clone --recurse-submodules https://github.com/ShrabonDas/ttt-py
```

Or if already cloned:

```bash
git submodule update --init
```

## Running the Lisp reference (for ground-truth testing)

The Docker setup lets you run the original Lisp TTT to validate Python output against it.

```bash
docker build -t sbcl-quicklisp:1.0 .
docker compose up -d
bash get_shell.bash
```

Inside the container:

```lisp
(ql:quickload :ttt)
(in-package :ttt)
(match-expr '(a b c) '(a b c))
```
