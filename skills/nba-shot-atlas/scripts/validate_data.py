#!/usr/bin/env python3
import argparse,csv,json,math,re,collections
from pathlib import Path
REQUIRED={'game_id','game_date','season','period','clock','person_id','shot_result','shot_value','x_legacy','y_legacy','game_number'}
def clock_seconds(s):
 m=re.fullmatch(r'PT(?:(\d+)M)?([\d.]+)S',s)
 if m:return int(m[1] or 0)*60+float(m[2])
 a,b=s.split(':');return int(a)*60+float(b)
def inspect(path,expected=None):
 with Path(path).open(encoding='utf-8-sig') as f:
  reader=csv.DictReader(f);missing=REQUIRED-set(reader.fieldnames or []);rows=list(reader)
 if missing:raise ValueError(f'Missing fields: {sorted(missing)}')
 if not rows:raise ValueError('No shots')
 ids={int(r['person_id']) for r in rows}
 if len(ids)!=1:raise ValueError('Multiple players: validate separately; do not mix them.')
 keys=[];coords=[]
 for r in rows:
  if r['shot_result'] not in {'Made','Missed'} or int(r['shot_value']) not in {2,3}:raise ValueError('Unknown result/value or free throws in FGA input')
  x,y=float(r['x_legacy']),float(r['y_legacy'])
  if not(math.isfinite(x) and math.isfinite(y)):raise ValueError('Non-finite coordinate')
  if not r['game_date']:raise ValueError('Missing game date')
  keys.append((r['game_date'],str(r['game_id']),int(r['period']),-clock_seconds(r['clock'])));coords.append((x,y))
 if keys!=sorted(keys):raise ValueError('Shots not in game/date/period/clock order')
 made=sum(r['shot_result']=='Made' for r in rows);games=len({r['game_id'] for r in rows})
 if expected:
  for key,actual in [('expected_attempts',len(rows)),('expected_made',made),('expected_games',games),('player_id',next(iter(ids)))]:
   if key in expected and int(expected[key])!=actual:raise ValueError(f'{key}: expected {expected[key]}, found {actual}')
 phases=collections.Counter(r.get('season_type_id','unknown') for r in rows)
 if set(phases)-{'2','4'}:raise ValueError('Unapproved phases in input')
 return {'player_id':next(iter(ids)),'attempts':len(rows),'made':made,'missed':len(rows)-made,'games':games,'seasons':sorted({r['season'] for r in rows}),'zero_zero_coordinates':coords.count((0.,0.)),'repeated_coordinate_records':sum(n-1 for n in collections.Counter(coords).values()),'phases':dict(phases),'warning':'Repeated origins are retained; they are not corrected or jittered. Compare totals with an independent season/box-score source before calling coverage complete.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('csv',type=Path);ap.add_argument('--job',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();report=inspect(a.csv,json.loads(a.job.read_text()) if a.job else None);s=json.dumps(report,ensure_ascii=False,indent=2)
 if a.output:a.output.write_text(s)
 print(s)
