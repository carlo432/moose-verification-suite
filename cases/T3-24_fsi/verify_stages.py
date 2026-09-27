#!/usr/bin/env python3
"""Check the CFD1 / CSM1 staged sub-benchmarks against Turek & Hron.

These are GATES on the FSI1 coupling, not scored suite rows: reference values
were declared before running but numeric tolerances were not, so this script
deliberately reports no PASS/FAIL verdict on an error magnitude. What it does
check is the criterion that was declared -- that the error decreases
monotonically under refinement -- which cannot be satisfied by a lucky coarse
mesh the way a bare error threshold can.
"""
import csv, json, pathlib, sys

CASE = pathlib.Path(__file__).parent
REF = json.loads((CASE / 'reference.json').read_text())
SV = REF['staged_validation_results']


def last_row(name):
    rows = list(csv.DictReader((CASE / 'out' / name).open()))
    if not rows:
        raise SystemExit(f'{name}: empty')
    return rows[-1]


def monotone(errs):
    return all(b < a for a, b in zip(errs, errs[1:]))


def report(tag, ref_map, levels, size_key):
    print(f'\n=== {tag} vs {SV[tag]["reference"].get("table", "")} ===')
    head = f'{"level":>5} {"cells":>7}'
    for q in ref_map:
        head += f' {q:>13} {"err%":>7}'
    print(head)
    errs = {q: [] for q in ref_map}
    for lv in levels:
        line = f'{lv["level"]:5} {lv[size_key]:7d}'
        for q, key in ref_map.items():
            v, r = lv[key], SV[tag]['reference'][q]
            e = abs((v - r) / r)
            errs[q].append(e)
            line += f' {v:13.5g} {e*100:7.2f}'
        print(line)
    line = f'{"paper":>5} {"":7}'
    for q in ref_map:
        line += f' {SV[tag]["reference"][q]:13.5g} {"":7}'
    print(line)
    ok = {}
    for q in ref_map:
        ok[q] = monotone(errs[q])
        print(f'  monotone in {q:5}: {ok[q]}'
              + ('' if ok[q] else '   <-- see cfd1_lift_caveat in reference.json'))
    return ok


# The CSV columns are the raw NodalSum of the saved momentum residual, which is
# the force the BODY exerts on the FLUID; the force ON the body is its negation.
# The sign is fixed by physics before any comparison with Table 5: drag on a body
# in channel flow must act downstream (+x), and the cylinder sits at y = 0.2 while
# the channel centreline is at 0.205, so the flow is faster above it and lift must
# act upward (+y). Both published values are positive, and this negation is what
# makes the computed pair positive too -- it is not tuned to match them.
cfd = []
for i in range(3):
    r = last_row(f'cfd1_L{i}.csv')
    cfd.append(dict(level=i, n_elem=int(float(r['n_elem'])),
                    drag=-float(r['drag']), lift=-float(r['lift'])))
if not all(c['drag'] > 0 and c['lift'] > 0 for c in cfd):
    raise SystemExit('CFD1: drag or lift is not positive after the documented sign '
                     'convention -- the flow, not the post-processing, is wrong.')
cfd_ok = report('CFD1', {'drag': 'drag', 'lift': 'lift'}, cfd, 'n_elem')

csm = []
for i in range(3):
    r = last_row(f'csm1_L{i}.csv')
    csm.append(dict(level=i, n_elem=int(float(r['n_elem'])),
                    ux=float(r['ux_A']), uy=float(r['uy_A'])))
csm_ok = report('CSM1', {'ux_of_A_e-3': 'ux', 'uy_of_A_e-3': 'uy'}, csm, 'n_elem')

print('\nGate on the FSI1 coupling:')
print(f'  fluid half (CFD1 drag) : {"MET" if cfd_ok["drag"] else "NOT MET"}')
print(f'  solid half (CSM1 both) : {"MET" if all(csm_ok.values()) else "NOT MET"}')
print('\nNo verdict is emitted for these stages by design -- no tolerance was '
      'pre-declared,\nand T3-24 is scored on FSI1 against its 10% tip-displacement '
      'tolerance alone.')
sys.exit(0 if cfd_ok['drag'] and all(csm_ok.values()) else 1)
