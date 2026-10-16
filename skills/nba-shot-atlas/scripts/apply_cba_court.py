#!/usr/bin/env python3
"""Apply the validated modern CBA/FIBA geometry after the standard framing pipeline."""
from pathlib import Path
import json,argparse
ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);a=ap.parse_args();project=a.project.resolve()
job=json.loads((project/'job.json').read_text())
if job.get('league')!='CBA' or job.get('court_dimensions_m')!=[28,15]:raise ValueError('Requires an explicitly verified modern 28×15m CBA job')
if job.get('cba_geometry_version'):raise ValueError('Already adapted: start fresh rather than reapplying the framing pipeline')
# Adapt physical dimensions to FIBA; source coordinates remain unmodified.
f=project/'geometry.py';s=f.read_text();s=s.replace('((PY1-PY0)/50)','((PY1-PY0)/(15/.3048))').replace('((PX1-PX0)/94)-5.25','((PX1-PX0)/(28/.3048))-(1.575/.3048)');f.write_text(s)
f=project/'plates.py';s=f.read_text().replace('(83.5,True)','((28-3.15)/.3048,True)');f.write_text(s)
f=project/'zones.py';s=f.read_text();a=s.index('RULES=');b=s.index('counts=',a)
s=s[:a]+'''RULES='CBA/FIBA坐标几何分区：篮下半径1.25m，短两分为剩余禁区(宽4.9m，罚球线距篮心4.225m)，长两分为其他2分；底角三分按6.6m侧向、6.75m弧线接点区分，左右合并。球值沿用原始事件。'
def zone(r):
 x=-float(r['x_legacy'])/10*.3048;y=float(r['y_legacy'])/10*.3048
 if int(r['shot_value'])==3:return 4 if abs(x)>=6.6 and y<=1.416 else 3
 if math.hypot(x,y)<=1.25:return 0
 if abs(x)<=2.45 and y<=4.225:return 1
 return 2
''' +s[b:];f.write_text(s)
# Neutral steel and red team padding; no NBA badge on the support.
f=project/'geometry.py';s=f.read_text().replace("outline=(151,104,184,190)","outline=(230,70,75,180)").replace("fill='#6e4a88'","fill='#bd263d'");f.write_text(s)

f=project/'plates.py';text=f.read_text()
if job.get('missing_coordinate_attempts',0):text=text.replace('本季出手','坐标出手')
f.write_text(text)
job['cba_geometry_version']='fiba-28x15-v1';(project/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2))
print(project)
