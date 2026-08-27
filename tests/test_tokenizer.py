"""T-1: Tokenizer-Tests (Determinismus, alpha-Aequivalenz, SyntaxError)."""

from structcoder.metrics.tokenizer import tokenize

EXAMPLE_SOURCE = """
def solve(lst):
    return sorted([x * 2 for x in lst])
"""

EXPECTED_EXAMPLE_TOKENS = [
    "FunctionDef",
    "arg",
    "Return",
    "Call:sorted",
    "ListComp",
    "BinOp:Mult",
    "Name",
    "Constant:2",
    "comprehension",
    "Name",
]


def test_reproduces_requirements_example():
    """Regressionstest gegen das Beispiel aus Requirements Abschnitt 6.5."""
    assert tokenize(EXAMPLE_SOURCE) == EXPECTED_EXAMPLE_TOKENS


def test_deterministic():
    tokens_a = tokenize(EXAMPLE_SOURCE)
    tokens_b = tokenize(EXAMPLE_SOURCE)
    assert tokens_a == tokens_b


def test_alpha_equivalence_renaming_does_not_change_tokens():
    renamed = """
def solve(values):
    return sorted([y * 2 for y in values])
"""
    assert tokenize(EXAMPLE_SOURCE) == tokenize(renamed)


def test_syntax_error_returns_empty_list():
    assert tokenize("def broken(:\n    pass") == []


def test_docstrings_are_ignored():
    with_docstring = '''
def solve(lst):
    """This is a docstring."""
    return sorted(lst)
'''
    without_docstring = """
def solve(lst):
    return sorted(lst)
"""
    assert tokenize(with_docstring) == tokenize(without_docstring)


def test_small_integer_literal_is_preserved():
    assert "Constant:2" in tokenize("x = 2")


def test_large_integer_literal_is_abstracted_to_type():
    tokens = tokenize("x = 123456789")
    assert "Constant:int" in tokens
    assert "Constant:123456789" not in tokens


def test_string_literal_is_abstracted_to_type():
    assert "Constant:str" in tokenize("x = 'hello'")
