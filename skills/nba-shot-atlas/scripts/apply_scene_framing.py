"""Enlarge the half-court presentation and add physical courtside context."""
from pathlib import Path
import argparse,json
ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);a=ap.parse_args();p=a.project.resolve()
j=json.loads((p/'job.json').read_text())
if j.get('scene_framing')=='large_arena':raise SystemExit('Large arena framing already applied.')
if j.get('court_scope')!='full_scene_half_framing':raise ValueError('Apply offensive-half framing first, preserving the full court.')
f=p/'plates.py';s=f.read_text().replace('(q@rt)/z*1850','(q@rt)/z*2800').replace('590-(q@up)/z*1850','550-(q@up)/z*2800')
# Add the stage edge before its wooden surface, and the equipment after it.
s=s.replace(' dest=project(g.FLOOR_CORNERS,c)*S;src=', ''' # Thin physical floor deck with a satin silver lip.
 dd=g.Draw(im);fc=g.FLOOR_CORNERS
 for k in sorted(range(4),key=lambda i:np.linalg.norm((fc[i]+fc[(i+1)%4])/2-c[0]),reverse=True):
  v=fc[k];w=fc[(k+1)%4];g.poly3(dd,[v,w,w+[0,0,-.65],v+[0,0,-.65]],c,'#292b2f')
  g.line3(dd,[v+[0,0,-.08],w+[0,0,-.08]],c,'#676a70',.8)
 dest=project(g.FLOOR_CORNERS,c)*S;src=''')
venue='''
# Physical courtside chairs, benches and an LED scorer table on the apron.
def courtside(d,c):
 chairs=[]
 for side in [-1,1]:
  for row in range(2):
   for y in np.arange(-3,36,2.15):chairs.append((side*(28.7+row*2.5),y,side))
 for x,y,side in sorted(chairs,key=lambda t:np.linalg.norm(np.array([t[0],t[1],1.])-c[0]),reverse=True):
  g.box(d,c,(x-.65,y-.66,.32),(1.3,1.32,.7),['#292b30','#30343b','#181b20','#424750'])
  if side:
   xx=x+side*.65
   v=[[xx,y-.68,.95],[xx,y+.68,.95],[xx,y+.68,2.35],[xx,y-.68,2.35]]
  else:v=[[x-.68,y-.67,.95],[x+.68,y-.67,.95],[x+.68,y-.67,2.35],[x-.68,y-.67,2.35]]
  g.poly3(d,v,c,'#343941');g.line3(d,[v[2],v[3]],c,'#6f7781',.65)
  for dx in [-.48,.48]:g.line3(d,[[x+dx,y,.05],[x+dx,y,.42]],c,'#7b8188',.6)
 # White low-output fascia keeps the court framed without distracting from data.
 for side in [-1,1]:
  x=side*32.3
  g.box(d,c,(x-.5,5,.05),(1.,22.,2.1),['#191b20','#30343b','#101217','#414750'])
  g.line3(d,[[x-side*.53,5,1.9],[x-side*.53,27,1.9]],c,'#b1bac5',1.)
  for y in [7,15,23]:g.line3(d,[[x-side*.54,y,.6],[x-side*.54,y+2.6,.6]],c,'#697b89',1.2)

'''
s=s.replace("im=Image.new('RGB',SIZE,'#08080b');g.arena",venue+"im=Image.new('RGB',SIZE,'#08080b');g.arena")
s=s.replace('enhance(.20);g.warp_floor(im,C);basket_pair','enhance(.60);g.warp_floor(im,C);courtside(g.Draw(im),C);basket_pair')
f.write_text(s)
f=p/'render.py';s=f.read_text().replace('math.cos(az)*105,70.','math.cos(az)*105,130.')
s=s.replace('enhance(.20);g.warp_floor(im,CURRENT_C);plate.basket_pair','enhance(.60);g.warp_floor(im,CURRENT_C);plate.courtside(g.Draw(im),CURRENT_C);plate.basket_pair')
f.write_text(s)
j.update(scene_framing='large_arena',projection_focal=2800,camera_height=130,court_stage_thickness_ft=.65,arena_brightness=.6)
(p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2));print(p)

# Keep the basket's baseline clear; only sideline chair rows are part of this style.
f=p/'geometry.py';s=f.read_text()
a=s.index(' # Two rows of courtside chairs behind the baseline.');b=s.index(' # Benches and scorer',a)
f.write_text(s[:a]+s[b:]);j['baseline_chair_icons']=False
(p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2))

# Pull the camera inward and track the shot cloud through the full orbit.
f=p/'render.py';s=f.read_text().replace("*(1-JOB['dolly_in_percent']/100*q)","*.88*(1-JOB['dolly_in_percent']/100*q)");f.write_text(s)
f=p/'plates.py';s=f.read_text();a=s.index('def project(p,c):');b=s.index('g.project=project;',a)
projection='from functools import lru_cache\nFRAMING_POINTS=g.paths[:,::4,:].reshape(-1,3)\n@lru_cache(maxsize=4)\ndef framing_offsets(camera_key):\n cam=np.array(camera_key[:3]);rt=np.array(camera_key[3:6]);up=np.array(camera_key[6:9]);f=np.array(camera_key[9:12])\n q=FRAMING_POINTS-cam;z=q@f\n xs=(q@rt)/z*2800;ys=-(q@up)/z*2800\n # Smooth lens shift follows the orbiting shot cloud, preserving every origin.\n return 1328-(xs.min()+xs.max())/2,540-(ys.min()+ys.max())/2\n\ndef project(p,c):\n cam,rt,up,f=c;q=np.asarray(p)-cam;z=q@f\n cx,cy=framing_offsets(tuple(np.concatenate(c)))\n return np.stack((cx+(q@rt)/z*2800,cy-(q@up)/z*2800),axis=-1)\n'
s=s[:a]+projection+s[b:];f.write_text(s)
j.update(camera_pull_factor=.88,shot_cloud_framing=True);(p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2))
