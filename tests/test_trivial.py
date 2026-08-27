"""FR-801/802: Trivial-Solution-Erkennung."""

from beyondpass.feedback.trivial import uses_any_argument


def test_uses_argument_returns_true_when_parameter_is_read():
    code = "def solve(lst):\n    return sorted(lst)\n"
    assert uses_any_argument(code, "solve") is True


def test_uses_argument_returns_false_when_parameter_is_ignored():
    code = "def solve(lst):\n    return []\n"
    assert uses_any_argument(code, "solve") is False


def test_uses_argument_returns_false_for_syntax_error():
    assert uses_any_argument("def solve(:\n    pass", "solve") is False


def test_uses_argument_returns_false_when_function_missing():
    code = "def other():\n    return 1\n"
    assert uses_any_argument(code, "solve") is False


def test_uses_argument_returns_false_for_zero_arg_function():
    code = "def solve():\n    return 42\n"
    assert uses_any_argument(code, "solve") is False
