import json, pathlib, re
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import brentq
from netCDF4 import Dataset
ROOT=pathlib.Path(__file__).parent; REF=json.loads((ROOT/'reference.json').read_text())
def levels(prefix, ref):
    out=[]
    for f in sorted((ROOT/'out').glob(f'{prefix}_*.log')):
        n=int(f.stem.split('_')[-1]); txt=re.sub(r'\x1b\[[0-9;]*m','',f.read_text()); vals=re.findall(r'Eigenvalue\s*=\s*([0-9.eE+-]+)',txt,flags=re.I)
        if not vals:
            tail=txt.rsplit('Executioner/eigenvalue',1)[-1]
            vals=re.findall(r'\|\s*[0-9.eE+-]+\s*\|\s*([0-9.eE+-]+)\s*\|',tail)
        out.append({'elements':n,'k_eff':float(vals[-1]),'relative_error':abs(float(vals[-1])/ref-1)})
    out.sort(key=lambda x:x['elements']); return out
slab=levels('ne',REF['reference']['value']); sphere=levels('sphere',REF['sphere_reference']['value'])
P=REF['reactor_mapping']
# Independent vacuum extrapolation check.  For a symmetric slab mode
# phi=cos(B(x-L/2)) with extrapolation length z=2D, the Robin condition gives
# tan(B L/2)=1/(z B), and k=1/(Sigma_a+D B^2).
L=float(P['geometry'].split('L=')[-1]); D=float(P['D']); sa=float(P['Sigma_a']); nuf=float(P['nuSigma_f'])
z=2.0*D
root=brentq(lambda B: np.tan(B*L/2.0)-1.0/(z*B), 1e-10, np.pi/L-1e-10)
extrapolated_k=float(nuf/(sa+D*root*root))
def order(a): return float(np.polyfit(np.log([1/x['elements'] for x in a]),np.log([x['relative_error'] for x in a]),1)[0])
so,ro=order(slab),order(sphere); fin=slab[-1]; fs=sphere[-1]
def shape_l2(path, spherical=False):
    with Dataset(path) as d:
        x=np.asarray(d.variables['coordx'][:], dtype=float)
        y=np.asarray(d.variables['vals_nod_var1'][-1,:], dtype=float)
    ref=np.sin(np.pi*x/L)
    if spherical:
        ref=np.divide(np.sin(np.pi*x/L), x, out=np.full_like(x, np.pi/L), where=x!=0)
    # Normalize both fields before a trapezoidal discrete L2 comparison.
    yn=y/np.sqrt(np.trapezoid(y*y,x)); rn=ref/np.sqrt(np.trapezoid(ref*ref,x))
    return float(np.sqrt(np.trapezoid((yn-rn)**2,x)))
slab_shape_l2=shape_l2(ROOT/'out'/f"ne_{fin['elements']}.e")
sphere_shape_l2=shape_l2(ROOT/'out'/f"sphere_{fs['elements']}.e", spherical=True)
plt.figure(figsize=(6,4)); plt.loglog([x['elements'] for x in slab],[x['relative_error'] for x in slab],'o-',label='slab'); plt.loglog([x['elements'] for x in sphere],[x['relative_error'] for x in sphere],'s-',label='sphere'); plt.xlabel('elements'); plt.ylabel('relative k error'); plt.legend(); plt.tight_layout(); plt.savefig(ROOT/'figures'/'eigen_convergence.png',dpi=150); plt.close()
ok=fin['relative_error']<REF['tolerance']['value'] and fs['relative_error']<REF['tolerance']['value'] and abs(so-2)<.2 and abs(ro-2)<.2 and slab_shape_l2<.01 and sphere_shape_l2<.01
result={'case_id':REF['case_id'],'capability':REF['capability'],'validation_class':'A','reference_value':REF['reference']['value'],'moose_value':fin['k_eff'],'units':'dimensionless','error':{'absolute':abs(fin['k_eff']-REF['reference']['value']),'relative':fin['relative_error']},'tolerance':REF['tolerance'],'convergence':{'slab_levels':slab,'sphere_levels':sphere,'slab_observed_order':so,'sphere_observed_order':ro,'expected_order':2.0},'flux_shape_l2':{'slab':slab_shape_l2,'sphere':sphere_shape_l2,'tolerance':0.01},'sphere':{'reference':REF['sphere_reference']['value'],'finest_k_eff':fs['k_eff'],'relative_error':fs['relative_error']},'extrapolated_boundary':{'extrapolation_length':z,'fundamental_B':root,'closed_form_k_eff':extrapolated_k},'verdict':'PASS' if ok else 'PARTIAL','runtime_s':0.0,'ranks':1,'moose_version':'snapshot-20-10-27-41583-g2bd11a08a7','notes':f"The one-group bare-slab and radial bare-sphere diffusion eigenproblems both run on three meshes. Finest slab and sphere relative errors are {fin['relative_error']:.3g} and {fs['relative_error']:.3g}; normalized flux-shape L2 errors are {slab_shape_l2:.3g} and {sphere_shape_l2:.3g}; observed orders are {so:.3f} and {ro:.3f}. An independent Robin/extrapolated-boundary derivation gives k_eff={extrapolated_k:.9g} for extrapolation length 2D; it is recorded as a boundary-condition cross-check, not as an OpenMC result. No OpenMC or transport comparison is claimed.",'limitations':'Diffusion approximation only; the extrapolated-boundary value is analytic rather than a separate MOOSE run, and no transport correction, OpenMC cross-check, or heterogeneous reactor geometry is included.'}
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
