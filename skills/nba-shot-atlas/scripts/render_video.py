#!/usr/bin/env python3
import argparse,importlib.util,json,os,shutil,subprocess,sys
from pathlib import Path

def load(project):
 sys.path.insert(0,str(project));spec=importlib.util.spec_from_file_location('shot_render',project/'render.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m

def main():
 ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--mode',choices=['stills','check','video'],default='stills');ap.add_argument('--preview-seconds',type=float);a=ap.parse_args();project=a.project.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
 os.environ['SHOT_VIDEO_OUTPUT']=str(a.output)
 if not os.environ.get('FFMPEG_BINARY'):
  ff=shutil.which('ffmpeg')
  if not ff:
   import imageio_ffmpeg
   ff=imageio_ffmpeg.get_ffmpeg_exe()
  os.environ['FFMPEG_BINARY']=ff
 job=json.loads((project/'job.json').read_text())
 if job.get('approved_layout_version')!='2026-10-17':subprocess.run([sys.executable,str(Path(__file__).with_name('apply_approved_layout.py')),str(project)],check=True)
 shutil.copy2(Path(__file__).with_name('approved_sidebar.py'),project/'approved_sidebar.py')
 r=load(project);import numpy as np
 from validate_data import inspect
 report=inspect(project/'shots.csv',r.JOB)
 first=np.ceil(r.starts*r.FPS).astype(int)
 if r.JOB.get('animation_mode')=='season_batch':
  season_groups={}
  for row,start in zip(r.rows,r.starts):season_groups.setdefault(row['season'],set()).add(float(start))
  assert all(len(v)==1 for v in season_groups.values()) and len(set(first))==len(season_groups)
  assert r.state(r.DURATION-1/r.FPS)==r.N
 else:
  assert np.all(np.diff(r.starts)>0), 'Chronological shots must retain distinct ordered timestamps.'
  assert np.all(first/r.FPS < r.starts+r.LIFE), 'Every shot needs visible trajectory frames.'
  assert np.all(np.ceil((r.starts+r.TRAVEL)*r.FPS)/r.FPS < r.starts+r.LIFE), 'Every shot needs a visible complete arc.'
  assert np.all(first<r.TOTAL), 'Shot starts after the final frame.'
  assert r.state(r.DURATION-1/r.FPS)==r.N
  report['max_shots_started_per_frame']=int(np.bincount(first).max())
 assert r.state(0)==0 and np.allclose(r.paths[:,0],r.xy)
 assert np.array_equal(r.zone_prefix.sum(axis=(1,2)),np.arange(r.N+1))
 if r.JOB['bar_scale']<=0 or np.max(r.zone_prefix[-1].sum(axis=1))>r.JOB['bar_scale']:raise ValueError('bar_scale must cover the largest final region attempt count.')
 angles=[]
 for t in np.linspace(0,r.DURATION,121):
  cam=r.camera(t);assert np.max(np.abs(r.project(r.paths[:,0],cam)-r.project(r.xy,cam)))==0
  target=np.array([0.,17.,0.]);q=t/r.DURATION;raw=target+(cam[0]-target)/(r.JOB.get('camera_pull_factor',1)*(1-r.JOB['dolly_in_percent']/100*q));angles.append(np.arctan2(raw[0],raw[1]))
 angles=np.unwrap(angles);assert np.all(np.diff(angles)>0) and abs(angles[-1]-angles[0]-np.deg2rad(r.JOB['orbit_degrees']))<1e-9
 if r.JOB.get('court_scope')=='full_scene_half_framing':
  assert r.plate.g.COURT_LIT.size==r.plate.g.COURT.size, 'The full court texture must remain intact.'
  assert r.plate.g.CW==r.plate.g.COURT.width, 'Half-court framing must not crop the physical floor.'
 half=r.JOB.get('court_scope')=='half'
 far=(r.JOB['court_dimensions_m'][0]-3.15)/.3048 if r.JOB.get('league')=='CBA' else 83.5
 assert r.plate.BASKETS==(((0.,False),) if half else ((0.,False),(far,True)))
 report.update(animation_mode=r.JOB.get('animation_mode','shot_by_shot'),source_fps=r.FPS,source_duration=r.DURATION,arc_origin_projected_error_px=0,orbit_degrees=r.JOB['orbit_degrees'],court_scope=r.JOB.get('court_scope','full'),two_baskets=not half)
 if a.mode in {'check','stills'}:
  for t in [0,r.DURATION*.26,r.DURATION*.52,r.DURATION*.78,r.DURATION-1]:r.frame(t).save(a.output/f'frame-{t:.2f}.png')
  opening=np.asarray(r.frame(0)).copy();r.frame(r.DURATION-1)
  assert np.array_equal(opening,np.asarray(r.frame(0)))
 else:
  last=min(r.TOTAL,round(a.preview_seconds*r.FPS)) if a.preview_seconds else r.TOTAL
  os.environ['SHOT_VIDEO_FRAME_LIMIT']=str(last)
  subprocess.run([sys.executable,str(project/'render.py')],check=True)
  factor=r.JOB['delivery_duration']/r.DURATION;delivery_fps=r.JOB['delivery_fps']
  if delivery_fps*factor<r.FPS:raise ValueError('Delivery would drop source frames: raise delivery FPS or extend delivery duration.')
  out=a.output/'投篮档案.mp4';duration=last/r.FPS*factor
  subprocess.run([r.FF,'-y','-hide_banner','-loglevel','error','-i',str(r.TARGET),'-vf',f'setpts=(PTS-STARTPTS)*{factor:.12f},fps={delivery_fps}','-t',str(duration),'-an','-c:v','libx264','-preset','fast','-crf','13','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
  subprocess.run([r.FF,'-v','error','-i',str(out),'-f','null','-'],check=True)
  report.update(output=str(out),delivery_duration=duration,delivery_fps=delivery_fps,note=('Native independently rendered source frames.' if abs(factor-1)<1e-9 and delivery_fps==r.FPS else 'Repeated source frames; no claim of independently rendered delivery-FPS motion.'))
 (a.output/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
