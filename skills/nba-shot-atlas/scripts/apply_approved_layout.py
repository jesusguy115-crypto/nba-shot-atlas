#!/usr/bin/env python3
"""Native full-court viewport + full-height reference sidebar; summary alone reserves subtitles."""
from pathlib import Path
import json,shutil,sys
p=Path(sys.argv[1]).resolve();job=json.loads((p/'job.json').read_text());scripts=Path(__file__).resolve().parent
if job.get('layout_profile')=='reference-full-2026-10-27':raise SystemExit('Reference layout already installed')
if job.get('approved_layout_version'):raise ValueError('Use a fresh project; old viewport calibration must not be stacked')
if job.get('camera_motion')!='stable_reference':raise ValueError('Apply stable camera and league court adaptation first')
shutil.copy2(scripts/'reference_sidebar.py',p/'reference_sidebar.py')
code="""
# Native full-height court; do not crop or shift the viewport into a smaller safe rectangle.
import reference_sidebar as _reference
_reference_scene_frame=frame
def frame(t):
 raw=_reference_scene_frame(t);n=state(t);view=dict(JOB)
 sidebar=_reference.render(view,rows,zone_prefix[n],n,P,t).resize((736,H),Image.Resampling.LANCZOS)
 raw.paste(sidebar,(0,0));return raw

"""
f=p/'render.py';s=f.read_text();idx=s.index('def render_index(');f.write_text(s[:idx]+code+s[idx:])
job.update(approved_layout_version='2026-10-17',layout_profile='reference-full-2026-10-27',layout_offset_x=0,sidebar_width=736,safe_viewport_scale=1.,safe_area={'top':96,'bottom':144},summary_bottom_safe_px=144)
(p/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2));print('Reference native layout applied; only summary reserves subtitle band')
