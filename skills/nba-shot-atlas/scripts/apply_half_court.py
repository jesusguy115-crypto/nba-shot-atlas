"""Frame the offensive half while preserving the entire physical court."""
from pathlib import Path
import json,argparse
ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);a=ap.parse_args();p=a.project.resolve()
j=json.loads((p/'job.json').read_text())
if j.get('court_scope')=='half':raise SystemExit('This project was physically cropped; start from an intact court project.')
if j.get('court_scope')=='full_scene_half_framing':raise SystemExit('Offensive-half framing already applied.')
f=p/'plates.py';s=f.read_text().replace('(q@rt)/z*1640','(q@rt)/z*1850').replace('(q@up)/z*1640','(q@up)/z*1850');f.write_text(s)
j.update(court_scope='full_scene_half_framing',projection_focal=1850)
(p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2));print(p)
