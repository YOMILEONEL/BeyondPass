# BeyondPass

**Multi-Agent Code Synthesis with Structurally-Grounded Feedback**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-in%20development-orange.svg)]()

BeyondPass is a multi-agent system that solves programming tasks through iterative code generation — but instead of relying on a plain pass/fail signal, it diagnoses *why* a candidate solution is wrong using structural program metrics, and turns that diagnosis into targeted feedback for the next attempt.

It is a direct continuation of my Bachelor thesis, [*"Beyond Accuracy: Measuring Intelligence in Programming by Example"*](docs/Thesis.pdf) (TU Clausthal, 2026), which introduced four token-based metrics to compare a generated program against a reference program rather than only comparing outputs. This project asks the natural next question the thesis leaves open: **can those same metrics be used not just to measure a solution, but to actively guide an agent toward a better one?**

---

## Table of Contents

- [Project Status](#project-status)
- [The Problem](#the-problem)
- [The Approach](#the-approach)
- [Architecture](#architecture)
- [What's Being Measured](#whats-being-measured)
- [Results](#results)
- [Key Design Constraints](#key-design-constraints)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Testing](#testing)
- [Limitations](#limitations)
- [Relation to the Thesis](#relation-to-the-thesis)
- [License](#license)

---

## Project Status

The system is being built in four work packages. **Foundation and metrics are done and tested; the agent loop is next.**

- [x] **Foundation** — typed config, HumanEval loader, Docker sandbox (isolated, no network, resource-limited) for candidate execution
- [x] **Metrics** — AST tokenizer and the four POS/PPS/PSS/PES scores, verified to reproduce the exact worked example from the thesis (Ch. 4.2)
- [ ] **Agents & feedback loop** — Planner/Coder/Tester/Critic agents, diagnosis logic, orchestrator (baseline vs. structural modes)
- [ ] **Evaluation & results** — full HumanEval runs across seeds, comparison report, results filled into this README

34 tests currently pass (`pytest tests/`). The `run`/`report` CLI commands shown under [Usage](#usage) describe the target interface and are not implemented yet — see [Project Structure](#project-structure) for what exists today versus what's planned.

## The Problem

A standard code-generation feedback loop tells an LLM agent only whether its solution passed or failed the given tests. This binary signal says nothing about *how close* a failing solution actually is, or *what kind* of mistake was made. An agent that found the right building blocks but combined them in the wrong order receives the exact same feedback as one that got everything wrong.

## The Approach

BeyondPass runs four cooperating agents — **Planner**, **Coder**, **Tester**, and **Critic** — in a loop over benchmark tasks (HumanEval). The Critic agent tokenizes both the candidate solution and the canonical reference solution via Python's `ast` module and computes four structural similarity scores, ported from the thesis' DSL-based metrics to Python AST:

| Metric | What it captures |
|---|---|
| **POS** — Program Operation Score | Are the right building blocks present at all? |
| **PPS** — Program Position Score | Are they in the exact right position? |
| **PSS** — Program Sequence Score | Do related operations stay contiguous? |
| **PES** — Program Edit Score | How many edits separate candidate and reference overall? |

The resulting metric pattern is translated into a concrete diagnosis — e.g. *"right operations, wrong order"* vs. *"fundamentally wrong approach"* — which becomes the feedback the Coder agent receives for its next attempt, instead of a generic "tests failed."

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Orchestrator                        │
└───────┬──────────┬───────────┬────────────┬─────────────┘
        │          │           │            │
        ▼          ▼           ▼            ▼
   ┌─────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
   │ Planner │ │ Coder  │ │ Tester  │ │  Critic  │
   │  Agent  │ │ Agent  │ │  Agent  │ │  Agent   │
   └─────────┘ └────────┘ └────┬────┘ └────┬─────┘
                                │           │
                                ▼           ▼
                          ┌──────────┐ ┌──────────┐
                          │  Docker  │ │  AST +   │
                          │ Sandbox  │ │ Metrics  │
                          └──────────┘ └──────────┘
```

**Loop per task:** Planner drafts a solution plan → Coder writes code → Tester executes it in an isolated sandbox → Critic compares it structurally against the reference → a diagnosis-driven feedback message is sent back to the Coder for the next iteration, until the tests pass or the iteration budget is exhausted.

## What's Being Measured

The project runs a controlled comparison: the same model, the same task subset, and the same iteration budget, once with plain pass/fail feedback (**baseline**) and once with structural, diagnosis-driven feedback (**structural**). It reports:

- **Solve rate** and **average iterations to solution**
- The four thesis metrics, averaged both over *all* tasks and over *solved* tasks only — following the same reporting convention used in the thesis
- Flagged trivial/suspicious solutions (see [Limitations](#limitations))

## Results

> To be filled in after evaluation runs.

| Condition | Solve Rate | Avg. Iterations | POS (solved) | PPS (solved) | PSS (solved) | PES (solved) |
|---|---|---|---|---|---|---|
| Baseline (pass/fail only) | — | — | — | — | — | — |
| Structural (diagnosis-driven) | — | — | — | — | — | — |

*Mean ± standard deviation over 3 seeds, evaluated on a HumanEval subset (n ≥ 50).*

## Key Design Constraints

- The **Planner and Coder agents never see the reference solution** — only the Critic does, purely for comparison purposes. This will be enforced by an automated test, not just by convention.
- All LLM-generated code runs in an **isolated, network-disabled Docker sandbox** with resource limits before it is ever evaluated.
- Following a finding from the original thesis (a program can pass all tests while ignoring its input entirely), solutions that pass without meaningfully using their input are **flagged separately** as potential trivial/false positives rather than silently counted as successes.

## Getting Started

### Prerequisites

- Python 3.10+
- Docker (running and accessible from the CLI)
- An Anthropic or OpenAI API key

### Installation

```bash
git clone https://github.com/YOMILEONEL/BeyondPass.git
cd BeyondPass
pip install -e ".[dev]"
```

### Configuration

```bash
cp .env.example .env
# add your API key to .env
export ANTHROPIC_API_KEY="your-key-here"
```

Adjust `config/default.yaml` if needed (model, task limit, budget cap, iteration count).

## Usage

```bash
# Run the structural-feedback condition
python -m beyondpass run \
    --mode structural \
    --benchmark humaneval \
    --limit 50 \
    --seed 0 \
    --out results/run_structural_seed0.jsonl

# Run the baseline (pass/fail only) condition for comparison
python -m beyondpass run \
    --mode baseline \
    --benchmark humaneval \
    --limit 50 \
    --seed 0 \
    --out results/run_baseline_seed0.jsonl

# Generate a comparison report
python -m beyondpass report \
    --runs results/*.jsonl \
    --out results/summary.md
```

## Project Structure

```
beyondpass/
├── src/beyondpass/
│   ├── config.py         # Typed, validated settings (Pydantic)          ✓
│   ├── benchmarks/       # Task loaders (HumanEval; MBPP planned)        ✓
│   ├── metrics/          # AST tokenizer + POS/PPS/PSS/PES               ✓
│   ├── sandbox/          # Docker-based isolated execution               ✓
│   ├── agents/           # Planner, Coder, Tester, Critic                planned
│   ├── feedback/         # Diagnosis logic and feedback templates        planned
│   ├── orchestrator.py   # Iteration loop                                planned
│   └── reporting/        # Aggregation and plots                         planned
├── tests/
├── config/
├── docs/                 # Requirements spec + thesis PDF
└── results/
```

## Tech Stack

Python · Anthropic/OpenAI API (function calling) · Docker · `ast` · `pytest` · pandas / matplotlib

## Testing

```bash
pytest tests/
```

Notably includes:
- **Thesis-consistency test** — verifies the ported metrics reproduce the exact example values from the thesis (POS = 0.75, PPS = PSS = PES = 0.25 on the running example)
- **Metric-invariance property test** — verifies POS ≥ max(PPS, PSS, PES) holds for arbitrary token sequences
- **Sandbox tests** — timeout handling, no network access, exceptions don't crash the host, correct solutions pass

A **no-reference-leak test** (asserting the reference solution never appears in Planner/Coder prompts) is planned alongside the agent implementation.

## Limitations

These are inherited directly from the thesis and stated openly rather than glossed over:

- **Structural closeness is not semantic equivalence.** Two very different programs can compute the same function; the metrics only measure similarity to one specific reference, not functional correctness beyond the given tests.
- **A canonical reference is only one of many valid solutions.** A low structural score does not necessarily mean "worse code" — only "different from this particular reference."
- **Evaluated on a single domain and benchmark** (Python functions via HumanEval); generalization to other domains or longer programs is untested.
- **A clean negative result is a valid outcome.** If structural feedback shows no measurable advantage over plain pass/fail feedback, that is reported as such — not hidden.

## Relation to the Thesis

| Thesis element | Used here as |
|---|---|
| POS / PPS / PSS / PES (Ch. 4.2) | Core of the Critic agent, ported to Python AST |
| Convention: empty sequences → 0 (Ch. 4.2) | Same convention applied |
| Metric invariance POS ≥ others (Ch. 6.3.1) | Enforced via property-based test |
| "All tasks" vs. "solved only" reporting (Ch. 5.4) | Same reporting convention |
| Trivial-solution case (Ch. 6.3.5) | Dedicated flagging mechanism |
| Compute-matching critique (Ch. 2.2) | Baseline and structural runs share model, subset, and budget |
| Future Work: combining structural + functional evaluation (Ch. 7.1) | The core motivation for this project |

Thesis code this project builds on:
- [DeepCoder fork with thesis extensions](https://github.com/YOMILEONEL/deepcoder)
- [DreamCoder fork with thesis extensions](https://github.com/YOMILEONEL/ec)

## License

MIT — see [LICENSE](LICENSE) for details. Benchmark datasets (HumanEval) retain their original licenses; see their respective sources.

---

Built by [Steve Leonel Yomi Mbiakop](https://steveyomiportfolio.vercel.app/) — [LinkedIn](https://www.linkedin.com/in/steve-leonel-yomi-mbiakop-8690a52b8/) · [GitHub](https://github.com/YOMILEONEL)
