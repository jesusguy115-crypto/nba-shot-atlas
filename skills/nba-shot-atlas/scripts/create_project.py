#!/usr/bin/env python3
import argparse,json,shutil
from pathlib import Path
from validate_data import inspect
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('destination',type=Path);ap.add_argument('--job',type=Path);ap.add_argument('--shots',type=Path);ap.add_argument('--court',type=Path);ap.add_argument('--portrait',type=Path);ap.add_argument('--logo',type=Path);a=ap.parse_args()
 if a.destination.exists():raise FileExistsError('Choose a new project directory; existing work is not overwritten.')
 template=ROOT/'assets/jordan-template';job=json.loads((template/'job.json').read_text());job.update(json.loads(a.job.read_text()) if a.job else {})
 if job['player_id']!=893 and not all([a.shots,a.court,a.portrait,a.logo,a.job]):raise ValueError('Other players require their own shots, court, portrait, logo and job; never silently render Jordan assets.')
 shutil.copytree(template,a.destination)
 if a.shots:shutil.copy2(a.shots,a.destination/'shots.csv')
 for source,key in [(a.court,'court_image'),(a.portrait,'portrait_image'),(a.logo,'logo_image')]:
  if source:dest=key+source.suffix;shutil.copy2(source,a.destination/dest);job[key]=dest
 (a.destination/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2));report=inspect(a.destination/'shots.csv',job);print(json.dumps({'project':str(a.destination),'validation':report},ensure_ascii=False))
if __name__=='__main__':main()
