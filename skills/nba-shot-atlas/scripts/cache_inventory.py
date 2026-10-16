#!/usr/bin/env python3
"""Read an existing local cache manifest; optionally verify its file hashes."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('root',type=Path,nargs='?',default=Path.home()/'Documents/Codex/shot-atlas-cache');p.add_argument('--verify',action='store_true');a=p.parse_args()
m=json.loads((a.root/'manifest.json').read_text());failed=[]
if a.verify:
 for name,entry in m['files'].items():
  f=(a.root/name).resolve()
  if not f.is_relative_to(a.root.resolve()):raise ValueError('Invalid cache-relative path')
  if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=entry['sha256']:failed.append(name)
print(json.dumps({'root':str(a.root),'league_id':m.get('league_id'),'season':m.get('season'),'games':m.get('games'),'coordinate_attempts':m.get('coordinate_attempts'),'files':len(m['files']),'verified':a.verify,'failed':failed},ensure_ascii=False))
if failed:raise SystemExit(1)
