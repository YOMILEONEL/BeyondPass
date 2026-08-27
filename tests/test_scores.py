"""T-2 (Unit), T-3 (Property), T-8 (Regression gegen die Thesis)."""

import random

import pytest

from structcoder.metrics.scores import (
    program_edit_score,
    program_operation_score,
    program_position_score,
    program_sequence_score,
)

ALL_METRIC_FNS = [
    program_operation_score,
    program_position_score,
    program_sequence_score,
    program_edit_score,
]


# --- T-2: Unit-Tests -------------------------------------------------------


@pytest.mark.parametrize("metric_fn", ALL_METRIC_FNS)
def test_identical_programs_score_one(metric_fn):
    tokens = ["FunctionDef", "arg", "Return", "Call:sorted", "Name"]
    assert metric_fn(tokens, tokens) == 1.0


@pytest.mark.parametrize("metric_fn", ALL_METRIC_FNS)
def test_disjoint_programs_score_zero(metric_fn):
    ref = ["FunctionDef", "Return", "Name"]
    cand = ["While", "Break", "Constant:str"]
    assert metric_fn(ref, cand) == 0.0


@pytest.mark.parametrize("metric_fn", ALL_METRIC_FNS)
def test_both_empty_scores_zero(metric_fn):
    assert metric_fn([], []) == 0.0


@pytest.mark.parametrize("metric_fn", ALL_METRIC_FNS)
def test_one_empty_scores_zero(metric_fn):
    assert metric_fn([], ["Name"]) == 0.0
    assert metric_fn(["Name"], []) == 0.0


# --- T-3: Property-Test fuer die Metrik-Invariante (FR-607) ----------------


def test_pos_is_upper_bound_for_random_token_pairs():
    vocab = ["FunctionDef", "Return", "Name", "Call:sorted", "BinOp:Mult", "Constant:2"]
    rng = random.Random(0)

    for _ in range(200):
        ref = [rng.choice(vocab) for _ in range(rng.randint(0, 8))]
        cand = [rng.choice(vocab) for _ in range(rng.randint(0, 8))]

        pos = program_operation_score(ref, cand)
        pps = program_position_score(ref, cand)
        pss = program_sequence_score(ref, cand)
        pes = program_edit_score(ref, cand)

        assert pos >= max(pps, pss, pes) - 1e-9
        for value in (pos, pps, pss, pes):
            assert 0.0 <= value <= 1.0


# --- T-8: Thesis-Konsistenz (Kap. 4.2, "Running Example") ------------------


def test_thesis_running_example_reproduces_reported_scores():
    """Referenzprogramm: Map(*2)(Sort(input)) -> [Map, *2, Sort, INPUT]
    Kandidat:           Sort(Map(+2)(input)) -> [Sort, Map, +2, INPUT]

    Erwartete Werte aus Thesis Kap. 4.2: POS=0.75, PPS=PSS=PES=0.25.
    """
    ref = ["Map", "*2", "Sort", "INPUT"]
    cand = ["Sort", "Map", "+2", "INPUT"]

    assert program_operation_score(ref, cand) == pytest.approx(0.75)
    assert program_position_score(ref, cand) == pytest.approx(0.25)
    assert program_sequence_score(ref, cand) == pytest.approx(0.25)
    assert program_edit_score(ref, cand) == pytest.approx(0.25)
