#!/usr/bin/env python3
"""Score T3-24 (Turek & Hron FSI1) against Table 13.

The scored quantity is the one declared in reference.json before the case was
built: relative tip displacement error at point A, tolerance 0.1. Both
components must satisfy it; the reported error is the worse of the two.

Steadiness and interface slip are reported as GUARDS, not as scored criteria --
they were not part of the pre-declared tolerance. They exist so the verifier
cannot score an unconverged transient or a coupling that is quietly leaking, and
both are stated numerically so a reader can judge them independently.
"""
import csv, json, math, pathlib, sys

CASE = pathlib.Path(__file__).parent
REF = json.loads((CASE / 'reference.json').read_text())
A = REF['reference']['value']            # [ux, uy] from Table 13
TOL = REF['tolerance']['value']
DRAG_REF, LIFT_REF = 14.295, 0.7638      # Table 13, reported not scored

# Declared before the runs: the tip must have stopped moving, and the penalty
# must actually be enforcing no-slip. Loose by design -- these reject garbage,
# they do not decide the verdict.
STEADY_MAX = 1e-6                        # |change in uy per step| at the end
SLIP_MAX = 1e-5                          # |mean vel_x on the interface|, vs Ubar = 0.2

levels = []
for L in range(3):
    f = CASE / 'out' / f'fsi1_L{L}.csv'
    if not f.exists():
        print(json.dumps({"verdict": "BLOCKED", "reason": f"missing {f.name}"}, indent=2))
        sys.exit(1)
    r = list(csv.DictReader(f.open()))[-1]
    ux, uy = float(r['ux_A']), float(r['uy_A'])
    drag = -(float(r['cyl_fx']) + float(r['weld_fx']))
    lift = -(float(r['cyl_fy']) + float(r['weld_fy']))
    levels.append({
        "level": L, "elements": int(float(r['n_elem'])), "end_time": float(r['time']),
        "ux": ux, "uy": uy,
        "ux_rel_err": abs((ux - A[0]) / A[0]), "uy_rel_err": abs((uy - A[1]) / A[1]),
        "drag": drag, "lift": lift,
        "drag_rel_err": abs((drag - DRAG_REF) / DRAG_REF),
        "lift_rel_err": abs((lift - LIFT_REF) / LIFT_REF),
        "uy_change_per_step": abs(float(r['uy_A_rate'])),
        "interface_slip": abs(float(r['interface_slip'])),
    })

fin = levels[-1]
worst = max(fin['ux_rel_err'], fin['uy_rel_err'])
mono_ux = all(b['ux_rel_err'] < a['ux_rel_err'] for a, b in zip(levels, levels[1:]))
mono_uy = all(b['uy_rel_err'] < a['uy_rel_err'] for a, b in zip(levels, levels[1:]))

checks = {
    "tip_displacement_within_tolerance": bool(worst <= TOL),
    "all_levels_reached_end_time": all(abs(l['end_time'] - 12.0) < 1e-9 for l in levels),
    "steady_at_final_step": bool(fin['uy_change_per_step'] <= STEADY_MAX),
    "interface_not_leaking": bool(fin['interface_slip'] <= SLIP_MAX),
    "error_decreases_under_refinement": bool(mono_ux and mono_uy),
}
verdict = "PASS" if all(checks.values()) else "FAIL"

out = {
    "case_id": REF['case_id'], "capability": REF['capability'],
    "validation_class": REF['validation_class'],
    "reference_value": A, "moose_value": [fin['ux'], fin['uy']], "units": "m",
    "error": {"absolute": max(abs(fin['ux'] - A[0]), abs(fin['uy'] - A[1])),
              "relative": worst},
    "tolerance": REF['tolerance'],
    "convergence": {"levels": levels, "observed_order": None, "expected_order": None},
    "forces_reported_not_scored": {
        "drag": fin['drag'], "drag_reference": DRAG_REF, "drag_rel_err": fin['drag_rel_err'],
        "lift": fin['lift'], "lift_reference": LIFT_REF, "lift_rel_err": fin['lift_rel_err'],
        "why_not_scored": "The declared tolerance is on tip displacement. Drag and lift are an "
            "INDEPENDENT corroboration: they are built from the cylinder no-slip reaction plus the "
            "clamp reaction at the weld, which equilibrium makes equal and opposite to the fluid "
            "load on the flag since FSI1 puts no body force on the solid. The construction was "
            "derived before the comparison, not tuned to it. At an interface node the saved fluid "
            "momentum residual is NOT usable -- the equation there is closed by the penalty "
            "InterfaceKernel, whose contribution that residual does not see.",
    },
    "guards": {
        "steady_max": STEADY_MAX, "uy_change_per_step": fin['uy_change_per_step'],
        "slip_max": SLIP_MAX, "interface_slip": fin['interface_slip'],
        "note": "Guards, not scored criteria. They were not part of the pre-declared tolerance; "
                "they prevent scoring an unconverged transient or a leaking interface.",
    },
    "checks": checks, "verdict": verdict, "ranks": 1,
    "moose_version": "snapshot-20-10-27-41583-g2bd11a08a7",
    "notes": (
        f"Monolithic ALE coupling on the Turek & Hron FSI1 geometry, three mesh levels. "
        f"Finest ({fin['elements']} elements) gives ux = {fin['ux']:.4e} m "
        f"({fin['ux_rel_err']*100:.2f}%) and uy = {fin['uy']:.4e} m "
        f"({fin['uy_rel_err']*100:.2f}%) against Table 13, scored on the worse of the two at "
        f"{worst*100:.2f}% versus a 10% tolerance declared before the case was built. Error falls "
        f"monotonically in both components. Drag and lift corroborate independently at "
        f"{fin['drag_rel_err']*100:.2f}% and {fin['lift_rel_err']*100:.2f}%. The fluid and solid "
        f"halves were validated separately on this same mesh (CFD1, CSM1) before coupling, so a "
        f"failure here would have been localisable; see staged_validation_results."
    ),
    "limitations": (
        "FSI1 only -- the steady member of the benchmark family. FSI2 and FSI3 are periodic and are "
        "not attempted. Penalty interface coupling rather than a mortar or Lagrange-multiplier "
        "formulation; the penalty value is not derived, and its adequacy is argued from the measured "
        "interface slip rather than from theory. Two-dimensional."
    ),
}
(CASE / 'result.json').write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
