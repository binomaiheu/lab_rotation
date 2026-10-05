# lab_rotation

Builds a lab rotation schedule with the [OR-Tools](https://developers.google.com/optimization) CP-SAT solver.

There are **G** groups and **E** experiments, run over **E** weeks. Every group does every experiment exactly once. Every experiment runs every week, and a bench holds at most 2 groups. With more groups than experiments, some benches are shared each week. The solver spreads that sharing as evenly as possible.

## Constraints

- Each group does one experiment per week and every experiment exactly once.
- Each experiment has 1 or 2 groups every week.
- No group shares a bench more often than necessary. The cap is the pigeonhole bound, `ceil(shared slots / G)`.
- Two groups share a bench at most once.
- Optionally, no group shares a bench in two consecutive weeks.
- Secondary objective: as few groups as possible reach the cap.

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```sh
git clone <repo-url>
cd lab_rotation
uv sync
```

## Usage

```sh
uv run lab-rotation
# or
uv run python lab_rotation.py
```

Set the parameters at the top of `lab_rotation.py`:

| Variable         | Default | Meaning                                         |
|------------------|---------|-------------------------------------------------|
| `G`              | 10      | number of groups                                |
| `E`              | 8       | number of experiments (= number of weeks)       |
| `CAP`            | 2       | maximum groups per experiment per week          |
| `NO_CONSECUTIVE` | `True`  | forbid sharing a bench in two consecutive weeks |

The solver has a time limit of 60 s and uses 8 workers.

## Output

The output is a table with one row per group and one column per week. Each cell holds the experiment letter. A `*` marks a week in which the group shares its bench. The last column gives each group's number of shared weeks. Below the table is a list of the shared benches per week, followed by a final check of the schedule.

```
Group | W1  W2  W3  ... | doubles
G1    | A   C*  F   ... | 3
...
Shared benches per week:
  W1: A: G1+G9,  B: G2+G10
  ...
verified OK
```
