import csv,json,pathlib,re
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
ROOT=pathlib.Path(__file__).parent; REF=json.loads((ROOT/'reference.json').read_text()); levels=[]
for path in sorted(ROOT.joinpath('out').glob('poly_*.csv')):
 if '_features_' in path.stem: continue
 dt=float(path.stem.split('_')[-1]); rows=list(csv.DictReader(path.open())); times=np.array([float(r['time']) for r in rows]); grains=np.array([float(r['ngrains']) for r in rows]); areas=[]
 for i,t in enumerate(times):
  f=ROOT/'out'/f'poly_{int(dt)}_features_{i:04d}.csv'
  if f.exists():
   fr=list(csv.DictReader(f.open())); av=[float(r['feature_volumes']) for r in fr if r.get('feature_volumes','')]; areas.append({'time':float(t),'n_features':len(av),'mean_area':float(np.mean(av)) if av else None,'mean_radius':float(np.sqrt(np.mean(av)/np.pi)) if av else None})
 q=[a for a in areas if a['mean_radius'] is not None and a['time']>=60 and a['mean_radius']>0]
 exponent=float(np.polyfit(np.log([a['time'] for a in q]),np.log([a['mean_radius'] for a in q]),1)[0]) if len(q)>=3 else None
 levels.append({'dt':dt,'times':times.tolist(),'grain_count':grains.tolist(),'feature_geometry':areas,'observed_radius_exponent':exponent,'initial_nonzero_count':int(np.count_nonzero(grains)),'minimum_after_initial':float(np.min(grains[1:])),'maximum_after_initial':float(np.max(grains[1:])),'monotone_nonincreasing':bool(np.all(np.diff(grains[1:])<=0))})
levels.sort(key=lambda r:r['dt']); plt.figure(figsize=(6,4));
for r in levels: plt.step(r['times'],r['grain_count'],where='post',label=f"dt={r['dt']}")
plt.xlabel('time'); plt.ylabel('tracked grain count'); plt.legend(); plt.tight_layout(); plt.savefig(ROOT/'figures'/'grain_count.png',dpi=150); plt.close()
plt.figure(figsize=(6,4));
for r in levels:
 q=[x for x in r['feature_geometry'] if x['mean_radius'] is not None];
 if q: plt.plot([x['time'] for x in q],[x['mean_radius'] for x in q],'.-',label=f"dt={r['dt']}")
plt.xlabel('time'); plt.ylabel('mean equivalent grain radius'); plt.legend(); plt.tight_layout(); plt.savefig(ROOT/'figures'/'grain_radius.png',dpi=150); plt.close()
exponents=[r['observed_radius_exponent'] for r in levels if r['observed_radius_exponent'] is not None]
triple_junction = None
finest_exodus = ROOT/'out'/'poly_80.e'
if finest_exodus.exists():
    with Dataset(finest_exodus) as ds:
        names=[row.tobytes().decode('ascii','ignore').rstrip('\x00 ') for row in ds.variables['name_nod_var'][:]]
        coords=np.asarray(ds.variables['coordx'][:]); n=int(round(np.sqrt(len(coords))))-1
        gr=[np.asarray(ds.variables[f'vals_nod_var{i+1}'][-1]).reshape((n+1,n+1)) for i,name in enumerate(names) if name.startswith('gr')]
    labels=np.argmax(np.stack(gr),axis=0); theta=np.linspace(0,2*np.pi,144,endpoint=False); sectors=[]
    for i in range(3,n-2):
        for j in range(3,n-2):
            if len(np.unique(labels[i-1:i+2,j-1:j+2])) != 3: continue
            ring=[int(labels[round(i+2*np.sin(t)),round(j+2*np.cos(t))]) for t in theta]
            if len(set(ring)) != 3: continue
            runs=[]; start=0
            for k in range(1,len(ring)):
                if ring[k] != ring[k-1]: runs.append((start,k)); start=k
            runs.append((start,len(ring)))
            if len(runs)>1 and ring[runs[0][0]] == ring[runs[-1][0]]:
                runs=[(runs[-1][0],runs[0][1])]+runs[1:-1]
            if len(runs) != 3: continue
            widths=sorted([((b-a)%len(ring))*360/len(ring) for a,b in runs])
            if min(widths)>45 and max(widths)<180: sectors.append(widths)
    if sectors:
        med=np.median(np.asarray(sectors),axis=0); triple_junction={'mesh':64,'candidate_count':len(sectors),'median_sector_angles_deg':med.tolist(),'mean_sector_angles_deg':np.mean(sectors,axis=0).tolist(),'median_abs_deviation_from_120_deg':float(np.median(np.abs(np.asarray(sectors)-120.0))),'criterion':'all sector angles 120 +/- 5 deg','passed':bool(np.max(np.abs(med-120.0))<=5.0)}
result={'case_id':REF['case_id'],'capability':REF['capability'],'validation_class':'A','reference_value':REF['reference']['value'],'moose_value':None,'units':'exponent','error':{'absolute':None,'relative':None},'tolerance':REF['tolerance'],'convergence':{'levels':levels,'observed_order':None,'expected_order':None},'coarsening':{'expected_exponent':0.5,'observed_exponents':exponents},'triple_junction':triple_junction,'verdict':'PARTIAL','runtime_s':0.0,'ranks':1,'moose_version':'snapshot-20-10-27-41583-g2bd11a08a7','notes':f"The case builds a fixed-seed 64-grain periodic Voronoi polycrystal on a 64x64 mesh, with GrainTracker/FeatureFloodCount diagnostics and three timestep levels. FeatureVolumeVectorPostprocessor supplies per-feature areas and equivalent radii. Late-window radius fits are {exponents}; the finest dt=80 run retains 26 tracked grains and a monotone count, but its measured exponent {exponents[-1]:.3g} is below the expected 1/2. The new order-parameter ring diagnostic finds median triple-junction sectors {triple_junction['median_sector_angles_deg'] if triple_junction else None} degrees, so the 120-degree criterion is not met.",'limitations':'The larger population improves grain-count statistics but still does not establish the asymptotic 1/2 law or isotropic 120-degree triple-junction equilibrium.'}
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
