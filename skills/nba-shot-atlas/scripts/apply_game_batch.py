#!/usr/bin/env python3
"""Apply after the approved stable-camera layout, before render_video."""
from pathlib import Path
import argparse,json,csv,shutil

def apply(p,duration=5.,pause=.5,hold=2.):
 p=Path(p).resolve();j=json.loads((p/'job.json').read_text())
 if j.get('game_batch_version')==1:return j
 if j.get('approved_layout_version')!='2026-10-17':raise ValueError('Apply approved layout first')
 rows=list(csv.DictReader((p/'shots.csv').open(encoding='utf-8-sig')))
 ids=list(dict.fromkeys(str(r['game_id']) for r in rows));G=len(ids)
 life=(duration-.1-.6-pause*(G-1))/G;travel=life-.2
 if pause<0 or hold<0 or travel<.25:raise ValueError('Too many games for readable complete arcs: extend duration, never drop shots')
 groups=[dict(game_id=gid,start=.1+i*(life+pause)) for i,gid in enumerate(ids)]
 j.update(animation_mode='game_batch',shot_animation_duration=duration,batch_pause_seconds=pause,batch_travel_seconds=travel,batch_life_seconds=life,glow_hold_seconds=hold,game_batches=groups,source_duration=duration+hold,delivery_duration=duration+hold,source_fps=60,delivery_fps=60,game_batch_version=1)
 f=p/'render.py';s=f.read_text();a=s.index('# A short, readable') if '# A short, readable' in s else s.index('# One synchronized burst');b=s.index('C=plate.C',a)
 s=s[:a]+"import batch_motion as _batch\nstarts=_batch.timeline(rows,JOB)\nTRAVEL=JOB['batch_travel_seconds'];LIFE=JOB['batch_life_seconds']\n"+s[b:]
 needle=" sidebar=_approved.render(view,rows,zone_prefix[n],n,P,t).resize((736,H),Image.Resampling.LANCZOS)"
 if needle not in s:raise ValueError('Unsupported sidebar wrapper; use a fresh project')
 s=s.replace(needle," display_n,counts,bars=_batch.sidebar_state(t,rows,zone_prefix,deltas,JOB)\n view['_bar_counts']=bars\n sidebar=_approved.render(view,rows,counts,display_n,P,t).resize((736,H),Image.Resampling.LANCZOS)")
 code="""
# Freeze the final camera for the breathing ground-marker hold; no further arcs.
_batch_original_frame=frame
def frame(t):
 cutoff=JOB['shot_animation_duration']
 if t<cutoff:return _batch_original_frame(t)
 return _batch.glow_hold(_batch_original_frame(cutoff),t-cutoff,xy,world_circles,made,project,camera(cutoff),JOB)

"""
 idx=s.index('def render_index(');s=s[:idx]+code+s[idx:];f.write_text(s)
 for name in ['batch_motion.py','approved_sidebar.py']:shutil.copy2(Path(__file__).with_name(name),p/name)
 (p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2));return j
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);ap.add_argument('--duration',type=float,default=5);ap.add_argument('--pause',type=float,default=.5);ap.add_argument('--hold',type=float,default=2);a=ap.parse_args();print(json.dumps(apply(a.project,a.duration,a.pause,a.hold),ensure_ascii=False))
