from pathlib import Path
import json,csv,argparse
ap=argparse.ArgumentParser(description='Apply wide sidebar; chronological shots up to 10 seasons, season bursts above 10.')
ap.add_argument('project',type=Path);ap.add_argument('--mode',choices=['auto','shot_by_shot','season_batch'],default='auto');ap.add_argument('--duration',type=float);ap.add_argument('--season-seconds',type=float,default=45.53/20)
opts=ap.parse_args();p=opts.project.resolve()
if opts.season_seconds<2.0:ap.error('Use at least 2.0 seconds per season for the complete flight and hold.')
rows=list(csv.DictReader(open(p/'shots.csv',encoding='utf-8-sig')))
seasons=list(dict.fromkeys(r['season'] for r in rows))
original=json.loads((p/'job.json').read_text());render_original=(p/'render.py').read_text()
mode=('season_batch' if len(seasons)>10 else 'shot_by_shot') if opts.mode=='auto' else opts.mode
if original.get('sidebar_width')==736:raise SystemExit('Season-batch layout already applied; use a fresh project for revisions.')
games=len({r['game_id'] for r in rows})
date_label=rows[0]['game_date'][:7].replace('-','.')+' — '+rows[-1]['game_date'][:7].replace('-','.')
j=json.loads((p/'job.json').read_text());j.update(source_duration=round(.16+len(seasons)*opts.season_seconds+2.16,1),delivery_duration=round(.16+len(seasons)*opts.season_seconds+2.16,1),source_fps=60,delivery_fps=60,animation_mode='season_batch',season_seconds=opts.season_seconds,sidebar_width=736)
(p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2))
f=p/'plates.py';s=f.read_text().replace('1190+(q@rt)/z*2400,585-(q@up)/z*2400','1328+(q@rt)/z*1640,590-(q@up)/z*1640')
s=s[:s.index('# Clean sidebar')]+'''# Expanded information panel: 736px, with native text layout.
mask=Image.new('L',SIZE);ImageDraw.Draw(mask).rectangle((0,0,736*S-1,H*S),fill=255)
under_mask=mask
shadow=Image.new('L',SIZE);shadow.paste(mask,(9*S,0));shadow=shadow.filter(ImageFilter.GaussianBlur(12*S)).point(lambda v:round(v*.65))
im=Image.composite(Image.new('RGB',SIZE,'black'),im,shadow)
im=Image.composite(Image.new('RGB',SIZE,'#1b1b1e'),im,mask)
d=D(im);d.line([(735.5,0),(735.5,H)],'#51484d',1)
p=portrait();im.paste(p,(46*S,24*S),p)
d.text(188,42,JOB['name_zh'],52,WHITE,'display')
d.text(191,111,JOB['name_en'],22,'#9d9397','number')
d.line([(48,185),(682,185)],'#444045',.8)

d.text(48,247,JOB['phase_label'],17,'#aaa3a5')
d.text(682,212,f'{len(set(r["game_id"] for r in rows))} 场比赛',22,'#ccc5c7',anchor='rt')
d.text(682,250,rows[0]['game_date'][:7].replace('-','.')+' — '+rows[-1]['game_date'][:7].replace('-','.'),17,'#aaa3a5',anchor='rt')
d.line([(48,291),(682,291)],'#444045',.8)
d.text(48,313,'本季出手' if len(set(r['season'] for r in rows))==1 else '累计出手',18,MUTED)
d.text(682,313,'投篮命中率',18,MUTED,anchor='rt')
d.rect((48,448,59,459),RED);d.text(72,442,'命中',20,MUTED)
d.rect((382,448,393,459),WHITE);d.text(406,442,'未中',20,MUTED)
d.line([(48,492),(682,492)],'#444045',.8)
d.text(48,516,'投篮区域',26,WHITE,'bold')
d.text(682,524,'命中 / 出手',16,'#bdb1b5',anchor='rt')
for k,name in enumerate(NAMES):d.text(48,574+k*90,name,22,WHITE,'bold')
SCENE=im.copy();PANEL=im.crop((0,0,775*S,H*S))
UI_MASK=under_mask.crop((0,0,775*S,H*S));SHADOW_ALPHA=shadow
'''
f.write_text(s)
f=p/'render.py';s=f.read_text();a=s.index('# A short, readable');b=s.index('C=plate.C',a)
s=s[:a]+'''# One synchronized burst per season, matching the reference pacing.
seasons=list(dict.fromkeys(r['season'] for r in rows))
starts=np.array([.16+seasons.index(r['season'])*JOB['season_seconds'] for r in rows])
TRAVEL=.90;HOLD=.65;LIFE=1.90
'''+s[b:]
s=s.replace('BAR_WIDTH=372','BAR_WIDTH=634').replace('layer,(80,round(y*S))','layer,(96,round(y*S))')
a=s.index('def panel(t,n):');b=s.index('_MARKS=None',a)
s=s[:a]+'''def panel(t,n):
 im=plate.PANEL.copy();d=plate.D(im);m=int(made_prefix[n]);miss=n-m
 row=rows[max(0,n-1)];year=int(row['season']);d.text(48,208,f'{year-1}—{str(year)[-2:]}赛季',25,plate.WHITE,'bold')
 d.text(46,340,str(n),92,plate.WHITE,'number')
 d.text(682,351,f'{m/n*100:.1f}%' if n else '0.0%',57,plate.WHITE,'number','rt')
 d.text(313,429,str(m),43,plate.WHITE,'number','rt')
 d.text(682,429,str(miss),43,plate.WHITE,'number','rt')
 for k,(m,miss) in enumerate(zone_prefix[n]):
  y=574+k*90;num=int(m+miss)
  d.text(682,y-1,f'{m} / {num}',27,plate.WHITE,'number','rt')
  gloss_bar(im,y+35,int(m),int(miss),t,k*.26)
  d.text(48,y+59,f'{m/num*100:.1f}% 命中率' if num else '暂无出手',14,'#b8acb0')
 return im

'''+s[b:]
# A full season is over 1,400 simultaneous paths. Reduce individual stroke energy
# so the combined cloud retains colour and the individual ground symbols survive.
s=s.replace('tuple(np.round(col*fade).astype(int)),1.35','tuple(np.round(col*fade*.32).astype(int)),.72')
s=s.replace('draw_marker(d,j,True,origin=origin,opacity=fade)','draw_marker(d,j,True,origin=origin,opacity=fade*.65)')
s=s.replace("if age<TRAVEL:","if age<TRAVEL:")
s=s.replace('tuple(np.round(np.array([255,241,223])*fade).astype(int)),1.05','tuple(np.round(np.array([255,241,223])*fade*.32).astype(int)),.7')
s=s.replace("fill='#fff3df'","fill='#8b7d75'")
s=s.replace('round(p*.55)','round(p*.18)')
s=s.replace('history_strength=.32+.55*max','history_strength=.45+.42*max')
s=s.replace("fade=1. if age<=TRAVEL else max(0.,(LIFE-age)/(LIFE-TRAVEL))","fade=1. if age<=TRAVEL+HOLD else max(0.,(LIFE-age)/(LIFE-TRAVEL-HOLD))")
f.write_text(s)
print(p)

if mode=='shot_by_shot':
 duration=opts.duration or (20+3*(len(seasons)-1))
 if duration<5:raise ValueError('Chronological playback needs at least 5 seconds.')
 j.update(animation_mode='shot_by_shot',source_duration=duration,delivery_duration=duration)
 (p/'job.json').write_text(json.dumps(j,ensure_ascii=False,indent=2))
 f=p/'render.py';s=f.read_text();begin=s.index('# One synchronized burst');end=s.index('C=plate.C',begin)
 old=render_original[render_original.index('# A short, readable'):render_original.index('C=plate.C')]
 s=s[:begin]+old+s[end:]
 begin=s.index(' for j in active:');end=s.index(' im=ImageChops.add(im,fx.filter',begin)
 old=render_original[render_original.index(' for j in active:'):render_original.index(' im=ImageChops.add(im,fx.filter')]
 s=s[:begin]+old+s[end:]
 s=s.replace('round(p*.18)','round(p*.55)').replace('history_strength=.45+.42*max','history_strength=.32+.55*max')
 f.write_text(s)
 print(f'Configured chronological playback: {len(seasons)} season(s), {duration:g}s')
else:print(f'Configured season bursts: {len(seasons)} seasons, {j["source_duration"]:g}s')
