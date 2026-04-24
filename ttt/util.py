"""Utility functions: hide/unhide TTT ops, ttt-all-rule-results, etc."""
from __future__ import annotations
from .types import TreeExpr

_TTT_OP_CHARS = set('!+?*@~/') | {'<>', '{}'}


def hide_ttt_ops(expr: TreeExpr, pkg=None) -> TreeExpr:
    """Wrap TTT operator symbols in [...]."""
    if isinstance(expr, str):
        if _should_hide(expr):
            hidden = f'[{expr}]'
            return hidden
        return expr
    if isinstance(expr, tuple):
        return tuple(hide_ttt_ops(item, pkg) for item in expr)
    return expr


def unhide_ttt_ops(expr: TreeExpr, pkg=None) -> TreeExpr:
    """Remove [...] wrapping from hidden TTT operator symbols."""
    if isinstance(expr, str):
        if expr.startswith('[') and expr.endswith(']') and len(expr) > 2:
            inner = expr[1:-1]
            if _should_hide(inner):
                return inner
        return expr
    if isinstance(expr, tuple):
        return tuple(unhide_ttt_ops(item, pkg) for item in expr)
    return expr


def _should_hide(s: str) -> bool:
    if not s:
        return False
    if s[0] in set('!+?*@~/'):
        return True
    if s in ('<>', '{}', '<>...', '{}...'):
        return True
    if len(s) >= 2 and s[:2] in ('<>', '{}'):
        return True
    return False


def ttt_all_rule_results(rule, tree: TreeExpr) -> list:
    """Find all subtrees of tree to which rule applies (returns results, not substitutions)."""
    from .transductions import apply_rule
    results = []
    result = apply_rule(rule, tree, shallow=True, max_n=1)
    if not isinstance(tree, tuple):
        if result is not None and result != tree:
            return [result]
        return []
    if result is not None and result != tree:
        results.append(result)
    for subtree in tree:
        results.extend(ttt_all_rule_results(rule, subtree))
    # Remove duplicates
    seen = []
    for r in results:
        if r not in seen:
            seen.append(r)
    return seen


def ttt_apply_rule_possibilities(rule, tree: TreeExpr,
                                  max_per_tree: int = 1,
                                  min_per_tree: int = 0):
    """Generate all possible results of applying rule to tree with application counts.
    Returns (results_list, counts_list).
    """
    from .transductions import apply_rule

    def helper(tr, apply_count):
        if apply_count >= max_per_tree or tr is None:
            return [(tr, apply_count)]
        if not isinstance(tr, tuple):
            result = apply_rule(rule, tr, shallow=True, max_n=1)
            out = [(tr, apply_count)]
            if result is not None and result != tr:
                out.append((result, apply_count + 1))
            return out
        # Try applying at root
        result = apply_rule(rule, tr, shallow=True, max_n=1)
        cur_rec = loop_rec(tr, apply_count)
        applied_n = []
        applied_rec = []
        if result is not None and result != tr:
            applied_n = [(result, apply_count + 1)]
            if apply_count + 1 < max_per_tree:
                applied_rec = loop_rec(result, apply_count + 1)
        return cur_rec + applied_n + applied_rec

    def loop_rec(tr, apply_count):
        if not isinstance(tr, tuple):
            return [(tuple(), 0)]  # shouldn't happen
        acc = [([], 0)]
        for item in tr:
            item_results = helper(item, apply_count)
            new_acc = []
            for (left, lc) in acc:
                for (ritem, rc) in item_results:
                    combined = lc + rc
                    if combined <= max_per_tree:
                        new_acc.append((left + [ritem], combined))
            acc = new_acc
        return [(tuple(parts), cnt) for parts, cnt in acc]

    raw = helper(tree, 0)
    filtered = [(r, c) for r, c in raw if c >= min_per_tree]
    if not filtered:
        return [], []
    results = [r for r, c in filtered]
    counts = [c for r, c in filtered]
    return results, counts


def lispify_parser_output(char_string: str):
    """Convert a parser output string to a Python nested tuple."""
    import ast
    # Use a simple S-expr parser
    return _parse_sexpr(char_string.strip())


def _parse_sexpr(s: str):
    tokens = _tokenize(s)
    result, _ = _parse_tokens(tokens, 0)
    return result


def _tokenize(s: str):
    tokens = []
    i = 0
    while i < len(s):
        if s[i] in ' \t\n\r':
            i += 1
        elif s[i] == '(':
            tokens.append('(')
            i += 1
        elif s[i] == ')':
            tokens.append(')')
            i += 1
        else:
            j = i
            while j < len(s) and s[j] not in ' \t\n\r()':
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def _parse_tokens(tokens, pos):
    if tokens[pos] == '(':
        items = []
        pos += 1
        while tokens[pos] != ')':
            item, pos = _parse_tokens(tokens, pos)
            items.append(item)
        return tuple(items), pos + 1
    else:
        tok = tokens[pos]
        # Try int/float
        try:
            return int(tok), pos + 1
        except ValueError:
            pass
        try:
            return float(tok), pos + 1
        except ValueError:
            pass
        return tok, pos + 1


def preslash_unsafe_chars(char_string: str) -> str:
    """Prefix backslash before unsafe characters."""
    unsafe = set("#`':;,.\\/|")
    result = []
    for ch in char_string:
        if ch in unsafe:
            result.append('\\')
        result.append(ch)
    return ''.join(result)
