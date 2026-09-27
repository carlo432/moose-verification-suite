import json, pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT=pathlib.Path(__file__).parent; REF=json.loads((ROOT/'reference.json').read_text()); qref=float(REF['reference']['value'])

def read_run(base, mesh):
    opt=pd.read_csv(base/'opt.csv'); report=pd.read_csv(base/'opt_OptimizationReporter_0001.csv'); main=pd.read_csv(base/'opt_main_0001.csv')
    q=float(report['parameter_results'].iloc[-1]); residual=float(np.sqrt(np.mean(main['misfit_values'].to_numpy(float)**2)))
    grad=float(report['grad_parameter_results'].iloc[-1]); objective=float(opt['OptimizationReporter/objective_value'].iloc[-1]); rel=abs(q/qref-1)
    return {'mesh_n':mesh,'parameter':'q','reference':qref,'recovered':q,'relative_error':rel,'objective_final':objective,'measurement_rms':residual,'adjoint_gradient':grad}

levels=[read_run(ROOT/'out',10)]
for n in (8,16,32,64):
    p=ROOT/'out'/f'mesh{n}'
    if (p/'opt.csv').exists(): levels.append(read_run(p,n))
levels.sort(key=lambda r:r['mesh_n']); finest=levels[-1]
noise=[]
for pct in (1,5,10):
    base=ROOT/'out'/f'noise{pct}'
    if (base/'opt.csv').exists():
        optn=pd.read_csv(base/'opt.csv'); repn=pd.read_csv(base/'opt_OptimizationReporter_0001.csv');
        qn=float(repn['parameter_results'].iloc[-1]); objn=float(optn['OptimizationReporter/objective_value'].iloc[-1])
        noise.append({'noise_percent':pct,'recovered':qn,'relative_error':abs(qn/qref-1),'objective_final':objn})
refined=[x for x in levels if x['mesh_n']>=16 and x['relative_error']>0]
observed_order=float(np.polyfit(np.log(1.0/np.array([x['mesh_n'] for x in refined])),np.log(np.array([x['relative_error'] for x in refined])),1)[0]) if len(refined)>=3 else None
opt=pd.read_csv(ROOT/'out/opt.csv'); plt.figure(figsize=(6,4)); plt.semilogy(opt['time'],np.maximum(opt['OptimizationReporter/objective_value'],1e-30),'o-'); plt.xlabel('TAO iteration'); plt.ylabel('objective'); plt.tight_layout(); plt.savefig(ROOT/'figures'/'pde_inverse_objective.png',dpi=150); plt.close()
noise_complete=len(noise)==3
all_good=finest['relative_error']<REF['tolerance']['value'] and abs(finest['adjoint_gradient'])<1e-8 and observed_order is not None and observed_order>1.0 and noise_complete
result={'case_id':REF['case_id'],'capability':REF['capability'],'validation_class':'A','reference_value':qref,'moose_value':finest['recovered'],'units':'W/m^3','error':{'absolute':abs(finest['recovered']-qref),'relative':finest['relative_error']},'tolerance':REF['tolerance'],'convergence':{'levels':levels,'observed_order':observed_order,'expected_order':2.0},'noise_study':noise,'verdict':'PASS' if all_good else 'PARTIAL','runtime_s':0.0,'ranks':1,'moose_version':'snapshot-20-10-27-41583-g2bd11a08a7','notes':f"TAO (taobqnls) optimizes a steady 2-D conduction PDE with four point measurements, a forward multi-app, an adjoint multi-app, and reporter transfers. Mesh levels {', '.join(str(x['mesh_n']) for x in levels)} recover q={finest['recovered']:.9g} W/m^3; the finest objective={finest['objective_final']:.3g}, measurement RMS={finest['measurement_rms']:.3g}, adjoint gradient={finest['adjoint_gradient']:.3g}, and observed source-error order={observed_order:.3g}. Deterministic Gaussian-noise sweeps at 1%, 5%, and 10% report recovery errors {[round(x['relative_error'],6) for x in noise]}; measurement RMS is reported as a discretization diagnostic rather than forced to zero on every mesh. ",'limitations':'Single scalar source parameter and manufactured measurements; the noise study quantifies sensitivity but does not provide a multi-parameter identifiability interval.'}
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
