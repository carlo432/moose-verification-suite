"""Single source of truth for the report page and the paper.

Everything numeric is read from the committed result.json / reference.json
artifacts, so the documents cannot drift from the suite. The only thing stored
here is the one-line editorial description of what each case is checked
against, which has no machine-readable home.

This module used to live in /tmp. A reboot deleted it and broke both builds;
it belongs in the repository.
"""
import json, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Which error field the verifier actually compared against its tolerance.
# Most cases score `relative`; these do not.
SCORED_FIELD = {
    'T1-09_cahn_hilliard': 'absolute',
    'T1-10_allen_cahn_grain_growth': 'absolute',
    'T3-25_dendrite': 'absolute',
    'T2-14_natural_convection': 'finest_Nu_relative',
}

AGAINST = {
    'T1-01': "Semi-infinite similarity solution for a surface step",
    'T1-02': "Finite-slab Fourier series at fixed surface concentration",
    'T1-03': "Straight fin, convective sides, adiabatic tip",
    'T1-04': "cosh profile, checked across three L/&lambda; regimes",
    'T1-05': "Von Mises plane-strain thick-cylinder limit pressure",
    'T1-06': "Norton law at constant stress and temperature",
    'T1-07': "Poiseuille parabola; u<sub>max</sub>/u<sub>avg</sub> = 3/2 and f&middot;Re = 96",
    'T1-08': "Hertz peak pressure and half-width, at the measured load",
    'T1-09': "LSW coarsening exponent &minus;1/3, ten-seed ensemble",
    'T1-10': "R&sup2; = R&#8320;&sup2; &minus; 2M&sigma;t",
    'T1-11': "Bare-slab and bare-sphere critical eigenvalues",
    'T1-12': "Ishigami function analytic Sobol indices",
    'T2-13': "Ghia, Ghia &amp; Shin (1982), Re = 1000 centreline profiles",
    'T2-14': "de Vahl Davis (1983) benchmark Nusselt numbers",
    'T2-15': "Parallel-plate constant-flux limit, Nu = 8.235",
    'T2-16': "Theis (1935) well-drawdown solution",
    'T2-17': "NAFEMS R0020 Test 1.1",
    'T2-18': "Rigid rotation gives F = R, so an objective law returns zero stress increment",
    'T2-19': "Recovery of a known source from four manufactured measurements",
    'T2-20': "Integrated closed form for a cosine-plus-uniform source",
    'T2-21': "Stefan similarity solution for the declared latent heat",
    'T3-22': "P<sub>cr</sub> = &pi;&sup2;EI/(KL)&sup2;, two boundary conditions 16&times; apart",
    'T3-23': "Closed form &sigma;<sub>xx</sub> = &minus;E&thinsp;e(y)/(1&minus;&nu;)",
    'T3-24': "Turek &amp; Hron (2006) Table 13 tip displacement",
    'T3-25': "Imposed anisotropy axis: &theta;<sub>m</sub> = &theta;&#8320; (mod 360/m)",
}

# Short scored-metric labels; the artifacts' own strings are often a sentence.
METRIC = {
    'T1-01': "max normalized L2 profile error, three times",
    'T1-02': "max normalized L2 profile error, three times",
    'T1-03': "fin tip temperature and base heat rate",
    'T1-04': "max normalized L2 profile error",
    'T1-05': "relative error in limit pressure",
    'T1-06': "relative error in final creep strain",
    'T1-07': "normalized L2 velocity-profile error",
    'T1-08': "relative error in p&#8320; and half-width a",
    'T1-09': "absolute error in the log&ndash;log slope",
    'T1-10': "deviation of the R&sup2;(t) fit from linearity",
    'T1-11': "relative k-effective error",
    'T1-12': "absolute Sobol-index error",
    'T2-13': "L2 profile deviation / U<sub>lid</sub>",
    'T2-14': "relative Nu and midplane-velocity error",
    'T2-15': "relative Nusselt error",
    'T2-16': "relative drawdown error",
    'T2-17': "relative J-integral error",
    'T2-18': "rotation-stage stress / elastic modulus",
    'T2-19': "relative recovered-source error",
    'T2-20': "relative profile L2 error",
    'T2-21': "relative front-position error",
    'T3-22': "relative error in Southwell-recovered P<sub>cr</sub>",
    'T3-23': "L2 error in &sigma;<sub>xx</sub>, normalized",
    'T3-24': "relative tip displacement error",
    'T3-25': "max error in arm direction, degrees",
}

TITLE = {
    'T3-24': "Fluid&ndash;structure interaction, Turek &amp; Hron FSI1",
    'T1-05': "J2 / von Mises elastoplasticity, thick cylinder",
    'T3-23': "Irradiation swelling eigenstrain and mismatch stress",
    'T2-17': "Fracture mechanics, J and interaction integrals",
    'T3-22': "Euler buckling from an imperfect column",
    'T1-07': "Laminar plane-channel flow",
    'T2-15': "Conjugate heat transfer across a fluid/solid interface",
    'T1-04': "Steady reaction&ndash;diffusion with a first-order sink",
    'T3-25': "Anisotropic solidification, growth-direction selection",
    'T1-09': "Split Cahn&ndash;Hilliard phase-field evolution",
    'T1-10': "Allen&ndash;Cahn curvature-driven grain growth",
    'T2-13': "Incompressible lid-driven cavity",
    'T2-14': "Boussinesq natural convection",
}

DOMAIN = {"1": "Solid mechanics and fracture", "2": "Heat transfer", "3": "Fluid dynamics",
          "4": "Porous flow", "5": "Phase field", "6": "Mass transport", "7": "Neutronics",
          "8": "Multiphysics coupling", "9": "Optimisation and uncertainty"}


def load():
    """Return the passing cases as (id, item, class, title, against, metric, err, tol)."""
    out = []
    for d in sorted((ROOT / 'cases').iterdir()):
        if not d.is_dir():
            continue
        res = json.loads((d / 'result.json').read_text())
        if res['verdict'] != 'PASS':
            continue
        ref = json.loads((d / 'reference.json').read_text())
        cid = d.name.split('_')[0]
        err = res.get('error') or {}
        key = SCORED_FIELD.get(d.name, 'relative')
        v = err.get(key)
        if v is None:
            v = err.get('absolute')
        tol = (res.get('tolerance') or {})['value']
        if abs(v) > tol:
            raise SystemExit(f"{cid}: scored {v} exceeds tolerance {tol} but is marked PASS")
        out.append((cid, ref.get('checklist_item', ''), res['validation_class'],
                    TITLE.get(cid, res['capability']), AGAINST[cid], METRIC[cid], abs(v), tol))
    out.sort(key=lambda c: [int(x) for x in c[1].split('.')])
    return out
