import csv,json
from pathlib import Path
import numpy as np
import netCDF4
import matplotlib.pyplot as plt

ROOT=Path(__file__).parent; REF=json.loads((ROOT/'reference.json').read_text()); rows=[]; coarsening=[]; full_energy=[]
for f in sorted((ROOT/'out').glob('ch_*.csv')):
    with f.open() as h: data=list(csv.DictReader(h))
    mass=[float(x['mass']) for x in data]; dt=float(f.stem.split('_')[-1].replace('p','.')); free=[float(x['free_energy_integral']) for x in data] if data and 'free_energy_integral' in data[0] else []
    grad=[float(x['gradient_energy_integral']) for x in data] if data and 'gradient_energy_integral' in data[0] else []
    native=[a+b for a,b in zip(free,grad)]
    rows.append({'file':f.name,'dt':dt,'end_time':float(data[-1]['time']),'mass_initial':mass[0],'mass_final':mass[-1],'mass_relative_drift':max(abs(x-mass[0]) for x in mass)/abs(mass[0]),'free_energy_initial':free[0] if free else None,'free_energy_final':free[-1] if free else None,'free_energy_max_increase':max(np.diff(free)) if len(free)>1 else None,'native_total_energy_initial':native[0] if native else None,'native_total_energy_final':native[-1] if native else None,'native_total_energy_max_increase':max(np.diff(native)) if len(native)>1 else None})
    ex=ROOT/'out'/f'{f.stem}.e'
    if ex.exists():
        ds=netCDF4.Dataset(ex); coords=np.asarray(ds.variables['coordx'][:]); n=int(round(np.sqrt(len(coords))))-1; domain=float(np.max(coords)); vals=np.asarray(ds.variables['vals_nod_var1'][:]); times=np.asarray(ds.variables['time_whole'][:]); dx=domain/n; kappa=40.0; energies=[]
        for field in vals:
            cgrid=field.reshape((n+1,n+1)); dcy,dcx=np.gradient(cgrid,dx,dx,edge_order=2); bulk=0.25*(1+cgrid)**2*(1-cgrid)**2; energies.append(float(np.sum((bulk+0.5*kappa*(dcx*dcx+dcy*dcy))*dx*dx)))
        full_energy.append({'file':f.name,'dt':dt,'times':times.tolist(),'total_energy':energies,'maximum_step_increase':float(max(np.diff(energies))) if len(energies)>1 else 0.0})
        k=np.fft.fftfreq(n+1,d=domain/n)*2*np.pi; KX,KY=np.meshgrid(k,k,indexing='ij'); k2=KX*KX+KY*KY
        for ti,t in enumerate(times[1:],start=1):
            a=vals[ti].reshape((n+1,n+1)); s=np.abs(np.fft.fft2(a-a.mean()))**2; den=float(s.sum()-s[0,0]); L=float(2*np.pi/np.sqrt((s*k2).sum()/den)) if den>0 else None; coarsening.append({'dt':dt,'time':float(t),'characteristic_length':L})
        ds.close()
rows.sort(key=lambda x:x['dt']); base=rows[1]
plt.figure(figsize=(6,4))
for r in rows:
    with (ROOT/'out'/r['file']).open() as h: d=list(csv.DictReader(h))
    plt.plot([float(x['time']) for x in d],[float(x['mass']) for x in d],'.-',label=f"dt={r['dt']}")
plt.xlabel('time'); plt.ylabel('element-integrated mass'); plt.legend(); plt.tight_layout(); plt.savefig(ROOT/'figures'/'mass_conservation.png',dpi=150); plt.close()
late=[r for r in coarsening if r['time']>0.5*max(x['time'] for x in coarsening)]; order=float(np.polyfit(np.log([r['time'] for r in late]),np.log([r['characteristic_length'] for r in late]),1)[0]) if len(late)>=3 else None
long_horizon=None
if (ROOT/'out'/'long_ch.e').exists():
    with netCDF4.Dataset(ROOT/'out'/'long_ch.e') as ds:
        n=int(round(np.sqrt(len(ds.variables['coordx'][:]))))-1; vals=np.asarray(ds.variables['vals_nod_var1'][:]); times=np.asarray(ds.variables['time_whole'][:]); domain=float(np.max(ds.variables['coordx'][:]))
    k=np.fft.fftfreq(n+1,d=domain/n)*2*np.pi; KX,KY=np.meshgrid(k,k,indexing='ij'); k2=KX*KX+KY*KY; lengths=[]
    for field in vals:
        cgrid=field.reshape((n+1,n+1)); spectrum=np.abs(np.fft.fft2(cgrid-cgrid.mean()))**2; den=float(spectrum.sum()-spectrum[0,0]); lengths.append(float(2*np.pi/np.sqrt((spectrum*k2).sum()/den)) if den>0 else None)
    window=(times>=20.0)&(times<=50.0)&(np.asarray(lengths)>0); coeff=np.polyfit(np.log(times[window]),np.log(np.asarray(lengths)[window]),1); fit_y=np.polyval(coeff,np.log(times[window])); log_y=np.log(np.asarray(lengths)[window]); r2=1.0-float(np.sum((log_y-fit_y)**2)/np.sum((log_y-log_y.mean())**2))
    long_horizon={'file':'long_ch.e','end_time':float(times[-1]),'fit_window':[20.0,50.0],'observed_exponent':float(coeff[0]),'r_squared':r2,'length_at_end':float(lengths[-1]),'note':'Diagnostic intermediate window; later finite-size flattening is not used for acceptance.'}
plt.figure(figsize=(6,4))
for dt in sorted({r['dt'] for r in coarsening}):
    q=[r for r in coarsening if r['dt']==dt]; plt.loglog([r['time'] for r in q],[r['characteristic_length'] for r in q],'.-',label=f'dt={dt}')
plt.xlabel('time'); plt.ylabel('structure-factor length'); plt.legend(); plt.tight_layout(); plt.savefig(ROOT/'figures'/'coarsening_length.png',dpi=150); plt.close()
fe_inc=max((r['free_energy_max_increase'] or 0) for r in rows); native_inc=max((r['native_total_energy_max_increase'] or 0) for r in rows); full_inc=max((r['maximum_step_increase'] for r in full_energy),default=0.0)
result={'case_id':REF['case_id'],'capability':REF['capability'],'validation_class':'A','reference_value':None,'moose_value':base['mass_final'],'units':'composition-volume','error':{'absolute':base['mass_final']-base['mass_initial'],'relative':base['mass_relative_drift']},'tolerance':REF['tolerance'],'convergence':{'levels':rows,'observed_order':None,'expected_order':None},'coarsening':{'levels':coarsening,'observed_exponent':order,'expected_exponent':1/3,'long_horizon_diagnostic':long_horizon},'free_energy':{'bulk_maximum_step_increase':fe_inc,'native_total_energy_maximum_step_increase':native_inc,'native_total_energy_monotone_nonincreasing':bool(native_inc<=1e-10),'full_discrete_levels':full_energy,'full_maximum_step_increase':full_inc,'full_reconstruction_monotone_nonincreasing':bool(full_inc<=1e-10)},'verdict':'PARTIAL' if max(r['mass_relative_drift'] for r in rows)<REF['tolerance']['value'] else 'FAIL','runtime_s':0.0,'ranks':1,'moose_version':'snapshot-20-10-27-41583-g2bd11a08a7','notes':f"Element-integrated mass is conserved to {max(r['mass_relative_drift'] for r in rows):.3g} across three timestep levels. Native bulk-plus-gradient energy has maximum step increase {native_inc:.3g}; nodal reconstruction is diagnostic only ({full_inc:.3g}). Standard late-window slope is {order if order is not None else float('nan'):.3g}; the separate t=100 diagnostic gives {long_horizon['observed_exponent'] if long_horizon else float('nan'):.3g} over t=20–50 with R2={long_horizon['r_squared'] if long_horizon else float('nan'):.3g}, followed by finite-size flattening. No asymptotic 1/3 acceptance claim is made.",'limitations':'Native gradient energy is authoritative; the long-horizon scaling window is diagnostic because finite-size effects reverse the trend later.'}
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
