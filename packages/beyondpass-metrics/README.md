# beyondpass-metrics

Four token-based structural similarity scores for comparing a Python
program against a reference program - **POS**, **PPS**, **PSS**, and
**PES** - plus the AST tokenizer they run on.

Extracted from [BeyondPass](https://github.com/YOMILEONEL/BeyondPass), a
multi-agent code-synthesis project built on top of the metrics introduced in
the Bachelor thesis *"Beyond Accuracy: Measuring Intelligence in Programming
by Example"* (TU Clausthal, 2026). Unlike a plain pass/fail signal, these
metrics tell you *how close* a candidate program is to a reference, and in
what specific way it differs - presence of the right operations, position,
contiguity, or overall edit distance.

## Status

**Not yet published to PyPI.** This package currently exists as a
self-contained, independently buildable snapshot of BeyondPass's internal
`beyondpass.metrics` module (same logic, own package name and tests) -
prepared for eventual publication, not a live dependency of the main
project yet. If you found this in the `packages/` folder of the BeyondPass
repo, this is that snapshot.

## Install (local / editable, for now)

```bash
pip install -e .
```

## Usage

```python
from beyondpass_metrics import all_metrics, tokenize

reference = "def add(a, b):\n    return a + b\n"
candidate = "def add(x, y):\n    return x + y\n"

result = all_metrics(reference, candidate)
print(result.pos, result.pps, result.pss, result.pes)
# 1.0 1.0 1.0 1.0 -- identical up to variable renaming (alpha-equivalence)

tokenize(reference)
# ['FunctionDef', 'arg', 'arg', 'Return', 'BinOp:Add', 'Name', 'Name']
```

| Metric | What it captures |
|---|---|
| **POS** - Program Operation Score | Are the right building blocks present at all? (multiset overlap) |
| **PPS** - Program Position Score | Are they in the exact right position? |
| **PSS** - Program Sequence Score | Do related operations stay contiguous? |
| **PES** - Program Edit Score | How many edits separate candidate and reference overall? |

By convention (matching the thesis), all four metrics are `0.0` if either
token sequence is empty, and `POS >= max(PPS, PSS, PES)` always holds.

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check src/ tests/
mypy src/beyondpass_metrics
```

`tests/test_scores.py` includes a regression test reproducing the exact
worked example from the thesis (Ch. 4.2): POS = 0.75, PPS = PSS = PES = 0.25.

## Publishing (not done yet)

If you want to actually push this to PyPI:

```bash
pip install build twine
python -m build                          # writes dist/*.whl and dist/*.tar.gz
twine upload dist/*                      # asks for your PyPI credentials/token
```

This requires your own PyPI account and is a public, hard-to-reverse action
- nobody has done this on your behalf.

## License

MIT - see [LICENSE](LICENSE).
