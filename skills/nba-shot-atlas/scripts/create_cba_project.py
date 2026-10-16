#!/usr/bin/env python3
"""Create a fresh CBA project with the tested configuration order."""
import argparse,json,subprocess,sys
from pathlib import Path
S=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('project',type=Path)
for name in ['job','shots','court','portrait','logo']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();job=json.loads(a.job.read_text())
if job.get('league')!='CBA' or job.get('court_dimensions_m')!=[28,15]:raise ValueError('Verify job league and modern FIBA court dimensions')
for key in ['player_id','name_zh','name_en','expected_attempts','expected_made','expected_games','bar_scale','court_texture_box','portrait_crop']:
 if key not in job:raise ValueError('Missing explicit CBA job field '+key)
subprocess.run([sys.executable,str(S/'create_project.py'),str(a.project),*sum(([f'--{k}',str(getattr(a,k))] for k in ['job','shots','court','portrait','logo']),[])],check=True)
for script in ['configure_video.py','apply_half_court.py','apply_scene_framing.py','apply_stable_camera.py','apply_cba_court.py']:
 subprocess.run([sys.executable,str(S/script),str(a.project)],check=True)
