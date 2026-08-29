"""AST-Tokenizer: Python-Quellcode -> flache, normalisierte Token-Sequenz.

Portiert die DSL-Tokenisierung der Bachelorarbeit (Kap. 4.1/4.2) auf
Python-AST (FR-501 bis FR-507). Traversierung ist Pre-Order-DFS ueber die
Kindfelder in der von `ast._fields` vorgegebenen Reihenfolge (FR-506).

Normalisierungsregeln:
- `Name`-Knoten erzeugen nur im Lese-Kontext (`ast.Load`) einen Token
  ("Name", ohne Identifier -- FR-503, alpha-Aequivalenz). Bindungen
  (`ast.Store`/`ast.Del`, z.B. Zuweisungsziele oder Comprehension-Targets)
  erzeugen keinen Token, ihre Funktion ist bereits durch den umgebenden
  Knoten (z.B. `Assign`, `comprehension`) sichtbar.
- `Constant`-Werte werden auf Typ-Ebene abstrahiert, ausser bei kleinen
  Ganzzahlen, die als Literal erhalten bleiben (FR-504).
- `Call` und `Attribute` betten das Ziel (Funktions-/Attributname) in den
  Token ein (z.B. "Call:sorted", "Attribute:value") statt es separat zu
  traversieren -- sonst wuerde z.B. `sorted(...)` zusaetzlich einen eigenen
  "Name"-Token fuer "sorted" erzeugen.
- `BinOp`/`UnaryOp`/`BoolOp` betten den Operatortyp ein (z.B. "BinOp:Mult").
- `Module` und `arguments` erzeugen selbst keinen Token, nur ihre Kinder.
- Docstrings (erstes Statement in Module/Function/Class-Body als reines
  String-Literal) werden uebersprungen (FR-507).

Nicht-parsbarer Code liefert eine leere Sequenz (FR-505).
"""

from __future__ import annotations

import ast

SMALL_INT_ABS_MAX = 256

_DOCSTRING_OWNERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_NO_SELF_TOKEN = (ast.Module, ast.arguments)


def tokenize(source: str) -> list[str]:
    """Wandelt Python-Quellcode in eine normalisierte Token-Sequenz um.

    Gibt bei SyntaxError eine leere Liste zurueck (FR-505).
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    tokens: list[str] = []
    _tokenize_node(tree, tokens)
    return tokens


def _is_docstring_stmt(stmt: ast.stmt) -> bool:
    return (
        isinstance(stmt, ast.Expr)
        and isinstance(stmt.value, ast.Constant)
        and isinstance(stmt.value.value, str)
    )


def _call_target_name(func: ast.expr) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return "<expr>"


def _constant_token(value: object) -> str:
    if isinstance(value, bool):
        return "Constant:bool"
    if value is None:
        return "Constant:NoneType"
    if value is Ellipsis:
        return "Constant:ellipsis"
    if isinstance(value, int) and abs(value) <= SMALL_INT_ABS_MAX:
        return f"Constant:{value}"
    return f"Constant:{type(value).__name__}"


def _tokenize_field(value: object, tokens: list[str]) -> None:
    if isinstance(value, ast.AST):
        _tokenize_node(value, tokens)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, ast.AST):
                _tokenize_node(item, tokens)


def _tokenize_node(node: ast.AST, tokens: list[str]) -> None:
    if isinstance(node, ast.Name):
        if isinstance(node.ctx, ast.Load):
            tokens.append("Name")
        return

    if isinstance(node, ast.Constant):
        tokens.append(_constant_token(node.value))
        return

    if isinstance(node, ast.Attribute):
        tokens.append(f"Attribute:{node.attr}")
        _tokenize_node(node.value, tokens)
        return

    if isinstance(node, ast.Call):
        tokens.append(f"Call:{_call_target_name(node.func)}")
        for arg in node.args:
            _tokenize_node(arg, tokens)
        for keyword in node.keywords:
            _tokenize_node(keyword.value, tokens)
        return

    if isinstance(node, ast.BinOp):
        tokens.append(f"BinOp:{type(node.op).__name__}")
        _tokenize_node(node.left, tokens)
        _tokenize_node(node.right, tokens)
        return

    if isinstance(node, ast.UnaryOp):
        tokens.append(f"UnaryOp:{type(node.op).__name__}")
        _tokenize_node(node.operand, tokens)
        return

    if isinstance(node, ast.BoolOp):
        tokens.append(f"BoolOp:{type(node.op).__name__}")
        for value in node.values:
            _tokenize_node(value, tokens)
        return

    if not isinstance(node, _NO_SELF_TOKEN):
        tokens.append(type(node).__name__)

    body = node.body if isinstance(node, _DOCSTRING_OWNERS) else None
    for field_name, value in ast.iter_fields(node):
        if body is not None and field_name == "body":
            stmts = body[1:] if body and _is_docstring_stmt(body[0]) else body
            for stmt in stmts:
                _tokenize_node(stmt, tokens)
            continue
        _tokenize_field(value, tokens)
