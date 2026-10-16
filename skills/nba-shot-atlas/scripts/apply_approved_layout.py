#!/usr/bin/env python3
"""Keep the approved full-size sidebar, fit only the 3D viewport to subtitle bands."""
from pathlib import Path
import json,shutil,subprocess,sys,importlib.util
import numpy as np
p=Path(sys.argv[1]).resolve();job=json.loads((p/'job.json').read_text());SCRIPTS=Path(__file__).resolve().parent
if job.get('approved_layout_version')=='2026-10-17':raise SystemExit('Approved layout already installed')
if job.get('camera_motion')!='stable_reference':raise ValueError('Apply stable camera and any CBA court adaptation first')
sys.path.insert(0,str(p));spec=importlib.util.spec_from_file_location('layout_probe',p/'render.py');r=importlib.util.module_from_spec(spec);sys.modules[spec.name]=r;spec.loader.exec_module(r)
lo=np.array([np.inf,np.inf]);hi=-lo
near=np.array([[x,y,z] for x in [-4.,4.] for y in [-1.,1.] for z in [0.,16.]])
points=np.concatenate([r.paths.reshape(-1,3),near])
for t in np.linspace(0,r.DURATION,17):
 q=r.project(points,r.camera(t));lo=np.minimum(lo,q.min(0));hi=np.maximum(hi,q.max(0))
factor=min(1.,1055/(hi[0]-lo[0]),798/(hi[1]-lo[1]));origin=(lo+hi)/2
# One fixed calibration preserves slow camera motion and shared arc/marker projection.
code=f'''\n# Approved safe viewport: fixed transform, never follows individual shots.
_original_project=project
_SAFE_ORIGIN=np.array({origin.tolist()!r})
_SAFE_SCALE={factor!r}
def project(points,camera):return (_original_project(points,camera)-_SAFE_ORIGIN)*_SAFE_SCALE+np.array([1292.5,515.])
g.project=project
'''
f=p/'plates.py';f.write_text(f.read_text()+code)
shutil.copy2(SCRIPTS/'approved_sidebar.py',p/'approved_sidebar.py')
code='''
# Approved full-width panel, with dedicated top/logo and bottom/subtitle bands.
import approved_sidebar as _approved
_legacy_frame=frame
def frame(t):
 raw=_legacy_frame(t);n=state(t);out=Image.new('RGB',(W,H),(25,25,27))
 # Only the arena viewport is clipped; every arc was calibrated inside these bounds.
 out.paste(raw.crop((736,96,1851,936)),(805,96))
 view=dict(JOB);view['season_label']=str(int(rows[max(0,n-1)]['season'])-1)+'-'+str(rows[max(0,n-1)]['season'])[-2:]+'赛季'
 sidebar=_approved.render(view,rows,zone_prefix[n],n,P,t).resize((736,H),Image.Resampling.LANCZOS)
 out.paste(sidebar,(69,0))
 ImageDraw.Draw(out).text((1850,110),JOB.get('credit',''),font=font(9),fill='#a9a3a7',anchor='rt')
 return out
'''
f=p/'render.py';s=f.read_text();idx=s.index('def render_index(');s=s[:idx]+code+'\n'+s[idx:];f.write_text(s)
job.update(approved_layout_version='2026-10-17',layout_offset_x=69,safe_area={'top':96,'bottom':144},safe_viewport_scale=float(factor));(p/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2));print('Approved layout applied; fixed 3D viewport scale',factor)
