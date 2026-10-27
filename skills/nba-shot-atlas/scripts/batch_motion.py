"""Game-batch timing, continuous sidebar quantities and the approved glowing hold."""
import math
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops

def timeline(rows,job):
 groups=job['game_batches'];mapping={str(g['game_id']):g['start'] for g in groups}
 return np.array([mapping[str(r['game_id'])] for r in rows])

def sidebar_state(t,rows,prefix,deltas,job):
 if job.get('animation_mode')!='game_batch':
  return None
 pos=0.
 for g in job['game_batches']:
  count=sum(str(r['game_id'])==str(g['game_id']) for r in rows)
  pos+=count*np.clip((t-g['start'])/job['batch_travel_seconds'],0,1)
 n=min(len(rows),int(pos+1e-8));fraction=max(0.,pos-n)
 bars=prefix[n].astype(float)
 if n<len(rows):bars+=fraction*deltas[n]
 return n,prefix[n],bars.tolist()

def glow_hold(base,t,xy,world_circles,made,project,camera,job):
 # Same final camera, positions and viewport offset as the shooting animation.
 S=2;W,H=base.size;cam=camera;centres=project(xy,cam);rings=project(world_circles,cam)
 layer=Image.new('RGB',(W*S,H*S));d=ImageDraw.Draw(layer);offset=job.get('layout_offset_x',69)
 ramp=min(1.,max(0.,t/.18));pulse=ramp*(.72+.28*math.sin(math.pi*t/1.25)**2)
 for j,(x,y) in enumerate(centres):
  col=tuple(round(c*pulse) for c in ([255,81,105] if made[j] else [240,246,255]))
  if made[j]:d.line([((float(a)+offset)*S,float(b)*S) for a,b in rings[j]],fill=col,width=3)
  else:
   x+=offset
   for sg in [-1,1]:d.line(((x-2.9)*S,(y-sg*2.9)*S,(x+2.9)*S,(y+sg*2.9)*S),fill=col,width=3)
 layer=layer.resize((W,H),Image.Resampling.LANCZOS)
 mask=Image.new('L',(W,H));bounds=(736,0,1919,1079) if job.get('layout_profile')=='reference-full-2026-10-27' else (805,96,1919,935);ImageDraw.Draw(mask).rectangle(bounds,fill=255)
 layer=Image.composite(layer,Image.new('RGB',(W,H)),mask)
 halo=ImageChops.add(layer.filter(ImageFilter.GaussianBlur(5)),layer.filter(ImageFilter.GaussianBlur(12)).point(lambda v:round(v*.55)))
 return ImageChops.add(base,ImageChops.add(layer,halo))
