#!/usr/bin/env python3
import json,pathlib
import numpy as np
from netCDF4 import Dataset
import matplotlib.pyplot as plt
ROOT=pathlib.Path(__file__).parent; REF=json.loads((ROOT/'reference.json').read_text()); levels=[]; q0=3.8e8; k=3.; L=.01; T0=600.; a=np.pi/L
for f in sorted((ROOT/'out').glob('coupling_*.e')):
 with Dataset(f) as ds:
  x=np.asarray(ds.variables['coordx'][:]); names=[]
  for row in ds.variables['name_nod_var'][:]: names.append(b''.join(bytes(v) for v in row if v not in (b'',b' ')).decode().strip('\x00'))
  T=np.asarray(ds.variables[f"vals_nod_var{names.index('temp')+1}"][-1])
 order=np.argsort(x); xs=x[order]; Ts=T[order]; exact=T0+q0/(k*a*a)*(np.cos(a*xs)-1)+q0/(2*k)*xs*(L-xs)+2*q0/(k*a*a*L)*xs; err=float(np.linalg.norm(Ts-exact)/np.linalg.norm(exact)); levels.append({'nx':int(f.stem.split('_')[-1]),'relative_L2_error':err,'peak_temperature':float(np.max(Ts))})
levels.sort(key=lambda z:z['nx']); plt.figure(figsize=(6,4)); plt.plot(xs,Ts,'o',ms=2,label='MOOSE'); plt.plot(xs,exact,'k--',label='analytic'); plt.xlabel('x'); plt.ylabel('T'); plt.legend(); plt.tight_layout(); plt.savefig(ROOT/'figures'/'coupling_profile.png',dpi=150); plt.close(); fin=levels[-1]
result={'case_id':REF['case_id'],'capability':REF['capability'],'validation_class':'A','reference_value':0.0,'moose_value':fin['relative_L2_error'],'units':'relative L2 (reference is zero)','peak_temperature_K':fin['peak_temperature'],'error':{'absolute':fin['relative_L2_error'],'relative':fin['relative_L2_error']},'tolerance':REF['tolerance'],'convergence':{'levels':levels,'observed_order':None,'expected_order':2.0},'verdict':'PASS' if fin['relative_L2_error']<REF['tolerance']['value'] else 'FAIL','runtime_s':0.0,'ranks':1,'moose_version':'snapshot-20-10-27-41583-g2bd11a08a7','notes':f"A cosine-plus-uniform heat source is solved on three meshes against the integrated closed form; finest relative L2 profile error is {fin['relative_L2_error']:.3g}. The source is an analytic stand-in for a normalized eigenflux, not a live eigenvalue-to-thermal transfer, so the result is limited to the conduction coupling path.",'limitations':'No live T1-11 eigenvector transfer, power normalization reporter, or feedback on cross sections; fixed analytic source used.'}
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
