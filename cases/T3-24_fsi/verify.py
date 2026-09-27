import json
from pathlib import Path
import matplotlib.pyplot as plt

fig,ax=plt.subplots(); ax.axis('off'); ax.text(.05,.7,'FSI1 benchmark blocked',fontsize=16); ax.text(.05,.5,'Flat-channel seed != Turek–Hron obstacle geometry',wrap=True); fig.savefig('figures/fsi_blocked.png',dpi=160,bbox_inches='tight'); plt.close(fig)
r={"case_id":"T3-24_fsi","capability":"Fluid-structure interaction benchmark FSI1","validation_class":"B","reference_value":[2.27e-5,8.209e-4],"moose_value":None,"units":"m","error":{"absolute":None,"relative":None},"tolerance":{"metric":"relative tip displacement error","value":0.10},"convergence":{"levels":[{"mesh":n,"tip":None} for n in [10,20,40]],"observed_order":None,"expected_order":None},"verdict":"BLOCKED","runtime_s":0.0,"ranks":1,"moose_version":"snapshot-20-10-27-41583-g2bd11a08a7","notes":"The shipped FSI flat-channel seed is not the Turek–Hron FSI1 obstacle benchmark; no defensible tip displacement can be extracted against the committed anchor. The seed is retained only as a coupling startup check.","limitations":"No obstacle geometry, Re=20 steady solve, benchmark comparison, or coupling-consistency fallback."}
Path('result.json').write_text(json.dumps(r,indent=2)+'\n')
