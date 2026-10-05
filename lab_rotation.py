"""
Lab rotation scheduler (CP-SAT).

G groups, E experiments, E weeks. Every group does every experiment exactly once.
Each experiment has capacity 2, and every experiment runs every week, so each week
G - E experiments are "doubled". Goal: spread the doubling as evenly as possible.

Hard constraints
  - each group: one experiment per week, each experiment exactly once
  - each (week, experiment): 1..2 groups
  - each group doubled at most ceil(total_double_slots / G) times  (the pigeonhole optimum)
  - no two groups share a bench more than once
  - (optional) no group doubled in two consecutive weeks
Objective
  - secondary: minimise the number of groups that hit the maximum double count
"""
import math
import itertools
import string
from ortools.sat.python import cp_model

G, E = 10, 8              # groups, experiments (= weeks)
W = E
CAP = 2
NO_CONSECUTIVE = True


def main():
    n_doubled_exp_per_week = G - E                        # 2
    double_slots = CAP * n_doubled_exp_per_week * W       # 32 group-weeks in a shared bench
    max_per_group = math.ceil(double_slots / G)           # 4 (lower bound, provably optimal)

    m = cp_model.CpModel()
    x = {(g, w, e): m.NewBoolVar(f"x{g}_{w}_{e}")
         for g in range(G) for w in range(W) for e in range(E)}

    for g in range(G):
        for w in range(W):
            m.AddExactlyOne(x[g, w, e] for e in range(E))
        for e in range(E):
            m.AddExactlyOne(x[g, w, e] for w in range(W))

    # d[w,e] = 1 if experiment e has 2 groups in week w
    d = {}
    for w in range(W):
        for e in range(E):
            occ = sum(x[g, w, e] for g in range(G))
            d[w, e] = m.NewBoolVar(f"d{w}_{e}")
            m.Add(occ == 1 + d[w, e])          # forces 1 <= occ <= 2

    # y[g,w] = group g is on a doubled bench in week w
    y = {}
    for g in range(G):
        for w in range(W):
            y[g, w] = m.NewBoolVar(f"y{g}_{w}")
            z = []
            for e in range(E):
                ze = m.NewBoolVar("")
                m.AddBoolAnd([x[g, w, e], d[w, e]]).OnlyEnforceIf(ze)
                m.AddBoolOr([x[g, w, e].Not(), d[w, e].Not()]).OnlyEnforceIf(ze.Not())
                z.append(ze)
            m.Add(y[g, w] == sum(z))

    cnt = [sum(y[g, w] for w in range(W)) for g in range(G)]
    for g in range(G):
        m.Add(cnt[g] <= max_per_group)
        if NO_CONSECUTIVE:
            for w in range(W - 1):
                m.AddBoolOr([y[g, w].Not(), y[g, w + 1].Not()])

    # each pair of groups shares a bench at most once
    for g, h in itertools.combinations(range(G), 2):
        meets = []
        for w in range(W):
            for e in range(E):
                b = m.NewBoolVar("")
                m.AddBoolAnd([x[g, w, e], x[h, w, e]]).OnlyEnforceIf(b)
                m.AddBoolOr([x[g, w, e].Not(), x[h, w, e].Not()]).OnlyEnforceIf(b.Not())
                meets.append(b)
        m.Add(sum(meets) <= 1)

    # symmetry breaking: week 1, groups 1..E do experiments A..E in order
    for g in range(E):
        m.Add(x[g, 0, g] == 1)

    # secondary objective: as few groups as possible at the max (pigeonhole gives G*max - slots)
    at_max = [m.NewBoolVar("") for _ in range(G)]
    for g in range(G):
        m.Add(cnt[g] <= max_per_group - 1).OnlyEnforceIf(at_max[g].Not())
    # pigeonhole: k*max + (G-k)*(max-1) >= slots  ->  k >= slots - G*(max-1)
    m.Add(sum(at_max) >= max(0, double_slots - G * (max_per_group - 1)))
    m.Minimize(sum(at_max))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 60
    solver.parameters.num_workers = 8
    status = solver.Solve(m)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE), solver.StatusName(status)

    L = string.ascii_uppercase
    sched = [[next(e for e in range(E) if solver.Value(x[g, w, e])) for w in range(W)]
             for g in range(G)]

    print(f"status: {solver.StatusName(status)}\n")
    print("Group | " + " ".join(f"W{w+1:<3}" for w in range(W)) + "| doubles")
    for g in range(G):
        cells = [L[sched[g][w]] + ("*" if solver.Value(y[g, w]) else " ") for w in range(W)]
        print(f"G{g+1:<4} | " + " ".join(f"{c:<4}" for c in cells)
              + f"| {solver.Value(cnt[g])}")

    print("\nShared benches per week:")
    for w in range(W):
        pairs = []
        for e in range(E):
            gs = [g + 1 for g in range(G) if sched[g][w] == e]
            if len(gs) == 2:
                pairs.append(f"{L[e]}: G{gs[0]}+G{gs[1]}")
        print(f"  W{w+1}: " + ",  ".join(pairs))

    # independent sanity check
    for g in range(G):
        assert sorted(sched[g]) == list(range(E))
    for w in range(W):
        occ = [sum(sched[g][w] == e for g in range(G)) for e in range(E)]
        assert min(occ) >= 1 and max(occ) <= CAP
    print("\nverified OK")


if __name__ == "__main__":
    main()
