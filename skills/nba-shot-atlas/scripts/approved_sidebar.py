from pathlib import Path
from functools import lru_cache
from datetime import date
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def metadata(job,rows):
 j=dict(job);j.setdefault('league','NBA');j.setdefault('scope_label',j.get('phase_label',''))
 j.setdefault('record_label',f"{len({r['game_id'] for r in rows})} 场比赛")
 j.setdefault('date_label',rows[0]['game_date'].replace('-','.')+' — '+rows[-1]['game_date'].replace('-','.'))
 j.setdefault('baseline_label',j['season_label'].replace('赛季','')+j.get('phase_label',''));j.setdefault('age_as_of',rows[-1]['game_date']);j['season_label']=j['season_label'].replace('—','-').replace('–','-')
 return j

def render(job,rows,counts,n,project,t=0):
 job=metadata(job,rows);p=Path(project);S=2;W,H,SIDEBAR=1920,1080,736;BG=(25,25,27);made_count=int(np.asarray(counts)[:,0].sum());age=None
 if job.get('birth_date'):
  born=date.fromisoformat(job['birth_date']);now=date.fromisoformat(job['age_as_of']);age=now.year-born.year-((now.month,now.day)<(born.month,born.day))
 @lru_cache(None)
 def font(n,weight='regular'):
  name='BarlowCondensed-Bold.ttf' if weight=='number' else 'NotoSansSC.ttf'
  f=ImageFont.truetype(str(p/'fonts'/name),round(n*S))
  if name=='NotoSansSC.ttf':
   try:f.set_variation_by_axes([700 if weight=='bold' else 450])
   except (OSError,ValueError):pass
  return f
 def text(im,pos,s,n,color,weight='regular',anchor='mm'):
  ImageDraw.Draw(im).text(tuple(v*S for v in pos),s,font=font(n,weight),fill=color,anchor=anchor)
 def line(im,points,color,width=1):ImageDraw.Draw(im).line([(x*S,y*S) for x,y in points],fill=color,width=max(1,round(width*S)),joint='curve')
 def poly(im,points,fill,outline=None,width=1):ImageDraw.Draw(im).polygon([(x*S,y*S) for x,y in points],fill=fill,outline=outline,width=max(1,round(width*S)))
 def arc_points(x,y,r,t0,t1,n=100):return [(x+r*math.cos(t),y+r*math.sin(t)) for t in np.linspace(t0,t1,n)]

 side=Image.new('RGB',(SIDEBAR*S,H*S),BG)
 def st(x,y,t,size=23,col='#f2eee8',weight='regular',anchor='la'):
  text(side,(x,y),t,size,col,weight,anchor)
 def hline(y):line(side,[(48,y),(686,y)],'#414144',.8)
 portrait=Image.open(p/job['portrait_image']).convert('RGBA').crop(tuple(job['portrait_crop']));portrait.thumbnail((140*S,160*S),Image.Resampling.LANCZOS);side.paste(portrait,(35*S,104*S),portrait)
 # Name, English secondary title, then a quiet four-column metric row.
 zh_size=48;en_size=20
 zh=ImageFont.truetype(str(p/'fonts/SmileySans-Oblique.ttf'),zh_size*S)
 def english_font(size):
  f=ImageFont.truetype(str(p/'fonts/NotoSansSC.ttf'),size*S)
  try:f.set_variation_by_axes([600])
  except (OSError,ValueError):pass
  return f
 en_font=english_font(en_size)
 while zh.getlength(job['name_zh'])+en_font.getlength(job['name_en'])+(24+1.1*len(job['name_en']))*S>489*S and (zh_size>26 or en_size>14):
  if zh_size>26:zh_size-=1
  if en_size>14:en_size-=.25
  zh=ImageFont.truetype(str(p/'fonts/SmileySans-Oblique.ttf'),round(zh_size*S));en_font=english_font(en_size)
 ImageDraw.Draw(side).text((197*S,108*S),job['name_zh'],font=zh,fill='#f2eee8')
 # Normal-width Latin lettering, with measured tracking instead of condensed numerals.
 en_x=197*S+zh.getlength(job['name_zh'])+24*S;en_tracking=1.1*S
 for ch in job['name_en']:
  ImageDraw.Draw(side).text((round(en_x),132*S),ch,font=en_font,fill='#a39fa2',anchor='la')
  en_x+=en_font.getlength(ch)+en_tracking
 for j,(label,value) in enumerate([('身高',(f"{job['height_cm']:g} cm" if job.get('height_cm') is not None else '—')),('体重',(f"{job['weight_kg']:g} kg" if job.get('weight_kg') is not None else '—')),('年龄',str(age) if age is not None else '—'),(job['league']+'球龄',str(job['league_season_number']) if job.get('league_season_number') else '—')]):
  x=202+j*121
  st(x,205,label,14,'#9e999d');st(x,229,value,23,'#e1dfe0','bold')
  if j<3:line(side,[(x+105,209),(x+105,254)],'#343437',.7)
 hline(281)
 # Compact date-only band; the space saved gives the region rows more air.
 date_label=job['date_label']
 if '—' in date_label:
  left,right=map(str.strip,date_label.split('—',1))
  if len(right)==5 and len(left)>=10:right=left[:5]+right
  date_label=left+' — '+right
 st(48,304,'比赛日期：'+date_label,18,'#c6c2c5')
 hline(345)
 # Four independent columns: attempts, makes, misses, FG percentage.
 st(48,374,job.get('attempt_label','坐标出手' if job.get('missing_coordinate_attempts',0) else '出手'),19,'#aaa6a9')
 poly(side,[(220,382),(229,382),(229,391),(220,391)],'#e52b4a');st(239,374,'命中',19,'#aaa6a9')
 poly(side,[(386,382),(395,382),(395,391),(386,391)],'#ede9e3');st(405,374,'未中',19,'#aaa6a9')
 st(550,374,'投篮命中率',19,'#aaa6a9')
 for x in [194,360,524]:line(side,[(x,376),(x,467)],'#353437',.8)
 st(48,414,str(n),54,weight='number')
 st(220,414,str(made_count),54,weight='number')
 st(386,414,str(n-made_count),54,weight='number')
 st(550,414,f"{(100*made_count/n if n else 0):.1f}%",54,weight='number')
 hline(490)
 st(48,500,'投篮区域',29,weight='bold');st(683,509,'命中 / 出手',18,'#bdb8bb',anchor='ra')
 # Sidebar uses the same five rules as the ten-zone court.
 coarse_side=np.asarray(counts,dtype=int)
 names=['篮下','短两分','长两分','弧顶及侧翼三分','底角三分'];scale=max(1,job['bar_scale']);max_width=635
 for i,(label,(m,miss)) in enumerate(zip(names,coarse_side)):
  y=548+i*80;n=int(m+miss);st(48,y,label,23,weight='bold');st(683,y-2,f'{m} / {n}',28,weight='number',anchor='ra')
  bm,bmiss=np.asarray(job.get('_bar_counts',counts),dtype=float)[i];bn=bm+bmiss
  width=max_width*bn/scale;by=(y+38)*S;bh=14*S
  if width*S>=1:
   mask=Image.new('L',(round(width*S),bh));ImageDraw.Draw(mask).rounded_rectangle((0,0,mask.width-1,bh-1),radius=bh/2,fill=255)
   bar=Image.new('RGB',mask.size,'#eeeae5');red=round(mask.width*bm/bn)
   ImageDraw.Draw(bar).rectangle((0,0,max(0,red-1),bh),fill='#ed314d') if red else None
   # Soft continuous gloss, clipped to the rounded capsule.
   ar=np.asarray(bar).copy().astype(float)
   for yy in range(bh):ar[yy]=np.clip(ar[yy]+18*np.exp(-((yy-bh*.2)/(bh*.26))**2)-7*yy/bh,0,255)
   xx=np.arange(ar.shape[1])/S;centre=-90+((t+i*.26)%4.8)/4.8*(max_width+180)
   gloss=.10*np.exp(-((xx-centre)/46)**2)
   ar=np.clip(ar+(255-ar)*gloss[None,:,None],0,255)
   side.paste(Image.fromarray(ar.astype('uint8')),(48*S,by),mask)
  label_width=font(23,'bold').getlength(label)/S
  st(48+label_width+18,y+7,f'{100*m/n:.1f}%' if n else '—',17,'#a9a3a7')
 # Baseline remains in audit and delivery description; no extra text in subtitle band.
 return side
