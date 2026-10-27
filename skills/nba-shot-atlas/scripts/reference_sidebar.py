"""Full-height reference sidebar, matching the approved native-court version."""
from pathlib import Path
from functools import lru_cache
import math,numpy as np
from PIL import Image,ImageDraw,ImageFont

def render(job,rows,counts,n,project,t=0):
 p=Path(project);S=2;im=Image.new('RGB',(736*S,1080*S),'#1b1b1e');d=ImageDraw.Draw(im)
 @lru_cache(None)
 def font(size,kind='regular'):
  name={'display':'SmileySans-Oblique.ttf','number':'BarlowCondensed-Bold.ttf'}.get(kind,'NotoSansSC.ttf')
  f=ImageFont.truetype(str(p/'fonts'/name),round(size*S))
  if name=='NotoSansSC.ttf':
   try:f.set_variation_by_axes([750 if kind=='bold' else 450])
   except (OSError,ValueError):pass
  return f
 def text(x,y,s,size=20,col='#f2eee8',kind='regular',anchor='la'):d.text((x*S,y*S),s,font=font(size,kind),fill=col,anchor=anchor)
 def hline(y):d.line((48*S,y*S,682*S,y*S),fill='#444045',width=2)
 portrait=Image.open(p/job['portrait_image']).convert('RGBA').crop(tuple(job['portrait_crop']));portrait.thumbnail((106*S,133*S),Image.Resampling.LANCZOS)
 alpha=np.asarray(portrait.getchannel('A')).astype(float);ramp=np.ones(portrait.height);k=int(portrait.height*.9);ramp[k:]=np.linspace(1,0,portrait.height-k);portrait.putalpha(Image.fromarray(np.uint8(alpha*ramp[:,None])))
 im.paste(portrait,(46*S,24*S),portrait)
 size=52
 while font(size,'display').getlength(job['name_zh'])>494*S and size>26:size-=1
 text(188,42,job['name_zh'],size,kind='display');text(191,111,job['name_en'],22,'#9d9397','number');hline(185)
 text(48,208,job['season_label'].replace('—','-').replace('–','-'),25,kind='bold')
 text(48,247,job['phase_label'],17,'#aaa3a5');text(682,212,f"{job['expected_games']} 场比赛",22,'#ccc5c7',anchor='rt')
 dates=job.get('date_label',rows[0]['game_date'].replace('-','.')+' — '+rows[-1]['game_date'].replace('-','.'))
 text(682,250,dates,17,'#aaa3a5',anchor='rt');hline(291)
 text(48,313,'坐标出手',18,'#aaa3a5');text(682,313,'投篮命中率',18,'#aaa3a5',anchor='rt')
 m=int(np.asarray(counts)[:,0].sum());text(46,340,str(n),92,kind='number');text(682,351,f'{100*m/n:.1f}%' if n else '0.0%',57,kind='number',anchor='rt')
 d.rectangle((48*S,448*S,59*S,459*S),fill='#ed314d');text(72,442,'命中',20,'#aaa3a5');text(313,429,str(m),43,kind='number',anchor='rt')
 d.rectangle((382*S,448*S,393*S,459*S),fill='#eeeae5');text(406,442,'未中',20,'#aaa3a5');text(682,429,str(n-m),43,kind='number',anchor='rt');hline(492)
 text(48,516,'投篮区域',26,kind='bold');text(682,524,'命中 / 出手',16,'#bdb1b5',anchor='rt')
 names=['篮下','短两分','长两分','弧顶及侧翼三分','底角三分'];bars=np.asarray(job.get('_bar_counts',counts),dtype=float)
 for i,(label,(made,miss)) in enumerate(zip(names,np.asarray(counts,dtype=int))):
  y=574+i*90;num=int(made+miss);text(48,y,label,22,kind='bold');text(682,y-1,f'{made} / {num}',27,kind='number',anchor='rt')
  text(48,y+59,f'{made/num*100:.1f}% 命中率' if num else '暂无出手',14,'#b8acb0')
  bm,bmiss=bars[i];bn=bm+bmiss;ww=round(634*bn/job['bar_scale']*S);hh=36
  if ww<=0:continue
  yy,xx=np.mgrid[0:hh,0:ww];v=yy/(hh-1);base=np.zeros((hh,ww,3));split=round(ww*bm/bn);base[:,:split]=[220,41,65];base[:,split:]=[242,238,232]
  base*= (.94+.11*np.exp(-((v-.2)/.23)**2)-.035*v)[:,:,None]
  center=-90+((t+i*.26)%4.8)/4.8*(634+180);shine=.16*np.exp(-((xx/S+v*18-center)/46)**2);base+=(255-base)*shine[:,:,None]
  layer=Image.fromarray(np.uint8(np.clip(base,0,255)));mask=Image.new('L',(ww,hh));ImageDraw.Draw(mask).rounded_rectangle((0,0,ww-1,hh-1),radius=min(18,ww/2),fill=255);im.paste(layer,(48*S,(y+35)*S),mask)
 return im
