"""Trivial-Solution-Erkennung (FR-800).

Adressiert den in der Thesis (Kap. 6.3.5) dokumentierten Fall, dass ein
Programm die Beispiele erfuellt, ohne die intendierte Regel umzusetzen.

Eigenstaendige, kleine AST-Analyse -- unabhaengig vom Tokenizer aus AP2,
der Identifier bewusst wegnormalisiert und daher hierfuer nicht geeignet ist.
"""

from __future__ import annotations

import ast


def uses_any_argument(candidate_code: str, entry_point: str) -> bool:
    """True, wenn der Funktionskoerper von `entry_point` mindestens einen
    seiner Parameter liest (FR-801). Liefert konservativ False bei
    SyntaxError, fehlender Funktion oder wenn die Funktion keine Parameter
    hat (FR-802)."""
    try:
        tree = ast.parse(candidate_code)
    except SyntaxError:
        return False

    func = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == entry_point
        ),
        None,
    )
    if func is None:
        return False

    args = func.args
    param_names = {a.arg for a in (*args.posonlyargs, *args.args, *args.kwonlyargs)}
    if args.vararg:
        param_names.add(args.vararg.arg)
    if args.kwarg:
        param_names.add(args.kwarg.arg)

    if not param_names:
        return False

    return any(
        isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id in param_names
        for node in ast.walk(func)
    )
