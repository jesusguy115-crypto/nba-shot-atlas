"""Use a locked framing reference, tiny one-way camera move and gentle dolly."""
from pathlib import Path
import argparse,json
ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);a=ap.parse_args();p=a.project.resolve();j=json.loads((p/'job.json').read_text())
if j.get('camera_motion')=='stable_reference':raise SystemExit('Stable camera already applied.')
j.update(camera_motion='stable_reference',orbit_start_degrees=-6,orbit_degrees=8,dolly_in_percent=2.0,shot_cloud_framing=False)
(p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2))
f=p/'plates.py';s=f.read_text();needle='def project(p,c):'
fixed='''# Framing is calibrated once at the middle pose and remains locked throughout.
_anchor_target=np.array([0.,17.,0.]);_anchor_az=math.radians(JOB['orbit_start_degrees']+JOB['orbit_degrees']*.5)
_anchor_raw=np.array([math.sin(_anchor_az)*105,math.cos(_anchor_az)*105,130.])
_anchor_cam=_anchor_target+(_anchor_raw-_anchor_target)*JOB.get('camera_pull_factor',.88)*(1-JOB['dolly_in_percent']/200)
_anchor_f=_anchor_target-_anchor_cam;_anchor_f/=np.linalg.norm(_anchor_f)
_anchor_rt=np.cross(_anchor_f,[0,0,1]);_anchor_rt/=np.linalg.norm(_anchor_rt);_anchor_up=np.cross(_anchor_rt,_anchor_f)
FIXED_FRAMING_OFFSET=framing_offsets(tuple(np.concatenate((_anchor_cam,_anchor_rt,_anchor_up,_anchor_f))))

'''
s=s.replace(needle,fixed+needle).replace('cx,cy=framing_offsets(tuple(np.concatenate(c)))','cx,cy=FIXED_FRAMING_OFFSET');f.write_text(s);print(p)
