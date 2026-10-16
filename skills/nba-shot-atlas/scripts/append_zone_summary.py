#!/usr/bin/env python3
"""Append an expanding sidebar-background reveal and a coordinate-derived zone chart."""
from pathlib import Path
from functools import lru_cache
import argparse,csv,json,math,subprocess,os
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter

NAMES=['篮下','禁区短两分','左侧中距离','正面中距离','右侧中距离','左翼三分','弧顶三分','右翼三分','左底角三分','右底角三分']
def classify(row):
 # Player-facing orientation: hoop is below the player on the top-down diagram.
 # Thus player left is positive world x (diagram right), player right negative x.
 x=-float(row['x_legacy'])/10;y=float(row['y_legacy'])/10
 if int(row['shot_value'])==3:
  if abs(x)>=22 and y<=9.2:return 9 if x<0 else 8
  angle=math.atan2(x,max(y,.01))
  return 7 if angle<math.radians(-22) else (5 if angle>math.radians(22) else 6)
 if math.hypot(x,y)<=4:return 0
 if abs(x)<=8 and y<=13.75:return 1
 return 4 if x< -8 else (2 if x>8 else 3)

def ease(t):
 t=max(0.,min(1.,t));return t*t*(3-2*t)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('project',type=Path);ap.add_argument('--video',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--league-shots',type=Path,nargs='+',required=True);ap.add_argument('--preview-only',action='store_true');ap.add_argument('--tail-seconds',type=float,default=6);a=ap.parse_args()
 p=a.project.resolve();a.video=a.video.resolve();a.output=a.output.resolve();a.output.parent.mkdir(parents=True,exist_ok=True)
 job=json.loads((p/'job.json').read_text());rows=list(csv.DictReader(open(p/'shots.csv',encoding='utf-8-sig')))
 import imageio_ffmpeg
 ff=os.environ.get('FFMPEG_BINARY') or imageio_ffmpeg.get_ffmpeg_exe()
 work=p/'summary-work';work.mkdir(exist_ok=True)
 fps=int(job.get('delivery_fps',60));base_seconds=float(job['delivery_duration']);W,H=1920,1080;S=2;SIDEBAR=int(job.get('sidebar_width',736));BG='#19191b'
 subprocess.run([ff,'-y','-v','error','-ss',str(base_seconds-1/fps),'-i',str(a.video),'-frames:v','1',str(work/'last.png')],check=True)
 base=Image.open(work/'last.png').convert('RGB');BG=base.getpixel((SIDEBAR-20,10));frozen_left=base.crop((0,0,SIDEBAR,H));ImageDraw.Draw(frozen_left).rectangle((SIDEBAR-6,0,SIDEBAR,H),fill=BG)
 base.paste(frozen_left,(0,0))
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
 counts=np.zeros((10,2),dtype=int)
 for row in rows:counts[classify(row),0 if row['shot_result']=='Made' else 1]+=1
 assert counts.sum()==len(rows)==job['expected_attempts'] and counts[:,0].sum()==job['expected_made']
 # The ten spatial zones partition the original five categories exactly.
 import sys
 sys.path.insert(0,str(p));from zones import zone
 coarse=np.zeros((5,2),dtype=int)
 for row in rows:coarse[zone(row),0 if row['shot_result']=='Made' else 1]+=1
 reconstructed=np.stack([counts[0],counts[1],counts[2:5].sum(0),counts[5:8].sum(0),counts[8:10].sum(0)])
 assert np.array_equal(coarse,reconstructed)
 # Compute same-season, same-phase league baselines with identical geometry.
 import pyarrow.parquet as pq
 phases={str(r['season_type_id']) for r in rows};seasons={int(r['season']) for r in rows}
 league=np.zeros((10,2),dtype=int)
 covered=set();seen_files=set()
 for league_path in a.league_shots:
  resolved=league_path.resolve()
  if resolved in seen_files:raise ValueError('Duplicate league parquet input')
  seen_files.add(resolved)
  for r in pq.read_table(resolved,columns=['season','season_type_id','shot_value','shot_result','x_legacy','y_legacy']).to_pylist():
   if int(r['season']) in seasons and str(r['season_type_id']) in phases:
    covered.add(int(r['season']))
    league[classify(r),0 if r['shot_result']=='Made' else 1]+=1
 if covered!=seasons:raise ValueError(f'Missing league season data: {sorted(seasons-covered)}')
 assert (league.sum(1)>0).all()
 league_pct=100*league[:,0]/league.sum(1)
 player_pct=np.divide(100*counts[:,0],counts.sum(1),out=np.zeros(10),where=counts.sum(1)>0)
 delta=player_pct-league_pct
 palette=['#30a6d2','#8bd3e5','#d4d4d1','#f3bd39','#f23859']
 def color(i):return palette[0 if delta[i]<-5 else 1 if delta[i]<-2 else 2 if delta[i]<=2 else 3 if delta[i]<=5 else 4]
 (work/'分区数据.json').write_text(json.dumps({'rows':[{'区域':NAMES[i],'命中':int(v[0]),'出手':int(v.sum()),'命中率':round(float(player_pct[i]),2),'联盟命中':int(league[i,0]),'联盟出手':int(league[i].sum()),'联盟命中率':round(float(league_pct[i]),2),'较联盟百分点':round(float(delta[i]),2),'颜色':color(i)} for i,v in enumerate(counts)],'league_source':[str(v) for v in a.league_shots],'season_types':sorted(phases),'note':'球员与同赛季联盟同区域加权命中率比较；几何区域及赛事口径一致；左右以球员面向篮筐为准（图面右=球员左）。六边形颜色为区域效率，大小为坐标出手频次。','aggregate_matches_sidebar':True},ensure_ascii=False,indent=2))

 # Half-court summary is diagrammatic, with the same charcoal as the sidebar.
 chart=Image.new('RGB',(W*S,H*S),BG)
 text(chart,(SIDEBAR+70,73),'区域投篮',30,'#f2eee8','bold','lm')
 logo=Image.open(p/job['logo_image']).convert('RGBA');logo.thumbnail((116*S,75*S),Image.Resampling.LANCZOS);chart.paste(logo,(round(1768*S),round(44*S)),logo)
 CX=1330;BASE=990;K=17.7
 def xy(x,y):return CX+x*K,BASE-(y+5.25)*K
 # Subtle team watermark below the data.
 mark=Image.open(p/job['logo_image']).convert('RGBA');mark.thumbnail((270*S,160*S),Image.Resampling.LANCZOS);mark.putalpha(mark.getchannel('A').point(lambda v:round(v*.065)))
 chart.paste(mark,(round(CX*S-mark.width/2),round(580*S)),mark)

 # Size is location frequency; color is the matching region's FG% difference from league.
 bins={};radius=.68
 for row in rows:
  x=-float(row['x_legacy'])/10;y=float(row['y_legacy'])/10
  qf=(math.sqrt(3)/3*x-y/3)/radius;rf=(2*y/3)/radius
  # Cube-coordinate nearest-cell rounding on a pointy hexagonal grid.
  cx=qf;cz=rf;cy=-cx-cz;rx,ry,rz=round(cx),round(cy),round(cz)
  dx,dy,dz=abs(rx-cx),abs(ry-cy),abs(rz-cz)
  if dx>dy and dx>dz:rx=-ry-rz
  elif dy>dz:ry=-rx-rz
  else:rz=-rx-ry
  key=(rx,rz,classify(row));bins[key]=bins.get(key,0)+1
 max_bin=max(bins.values())
 for (q,r,zi),n in bins.items():
  wx=radius*math.sqrt(3)*(q+r/2);wy=radius*1.5*r;px,py=xy(wx,wy)
  rr=3.0+8.0*(math.log1p(n)/math.log1p(max_bin))**.6
  pts=arc_points(px,py,rr,math.pi/6,2*math.pi+math.pi/6,7)[:-1]
  poly(chart,pts,color(zi),'#e4ded7',.5)

 ink='#bbb7ba';soft='#6d696e'
 for seg in [[(-25,-5.25),(25,-5.25)], [(-25,-5.25),(-25,41.75)],[(25,-5.25),(25,41.75)],[(-25,41.75),(25,41.75)]]:line(chart,[xy(*v) for v in seg],ink,1.25)
 line(chart,[xy(-8,-5.25),xy(-8,13.75),xy(8,13.75),xy(8,-5.25)],ink,1.2)
 line(chart,[xy(*v) for v in arc_points(0,13.75,6,0,math.pi)],ink,1.15)
 # Restricted area and backboard/rim.
 line(chart,[xy(*v) for v in arc_points(0,0,4,0,math.pi)],'#d0c9cc',1.25)
 line(chart,[xy(-3,-1.25),xy(3,-1.25)],'#e4dce0',2.)
 line(chart,[xy(*v) for v in arc_points(0,0,.75,0,2*math.pi)],'#d8a1ab',1.4)
 cutoff=math.sqrt(23.75**2-22**2);theta=math.atan2(cutoff,22)
 line(chart,[xy(-22,-5.25),xy(-22,cutoff)],ink,1.35);line(chart,[xy(22,-5.25),xy(22,cutoff)],ink,1.35)
 line(chart,[xy(*v) for v in arc_points(0,0,23.75,theta,math.pi-theta)],ink,1.35)
 # The extra spatial subdivisions remain quiet and follow coordinate boundaries.
 for x in [-8,8]:line(chart,[xy(x,13.75),xy(x,math.sqrt(23.75**2-x*x))],soft,.7)
 for sg in [-1,1]:
  angle=math.pi/2+sg*math.radians(22)
  line(chart,[xy(23.75*math.cos(angle),23.75*math.sin(angle)),xy(41.75/math.sin(angle)*math.cos(angle),41.75)],soft,.7)
 # Compact reference-style legends: efficiency colors and shot frequency sizes.
 text(chart,(820,1040),'低于均值',21,palette[0],'bold','lm')
 for j,c in enumerate(palette):
  poly(chart,arc_points(952+j*27,1040,13,math.pi/6,2*math.pi+math.pi/6,7)[:-1],c,'#e9e4df',.6)
 text(chart,(1090,1040),'高于均值',21,palette[-1],'bold','lm')
 text(chart,(1490,1040),'出手频次',18,'#bdb9bc','regular','lm')
 for j,r in enumerate([4,6,9,12]):poly(chart,arc_points(1620+j*34,1040,r,math.pi/6,2*math.pi+math.pi/6,7)[:-1],'#c9c7c5')
 # Labels sit within their corresponding spatial areas; the rim uses a short callout.
 placements=[(10.8,-.2),(0,8.5),(15.2,11.0),(0,19.4),(-15.2,11.0),(18.2,27.5),(0,33.7),(-18.2,27.5),(23.5,2.7),(-23.5,2.7)]
 cards=[]
 for i,((wx,wy),value) in enumerate(zip(placements,counts)):
  m=int(value[0]);n=int(value.sum());pct=100*m/n if n else 0;px,py=xy(wx,wy)
  lay=Image.new('RGBA',(W*S,H*S));draw=ImageDraw.Draw(lay)
  draw.rounded_rectangle(((px-76)*S,(py-44)*S,(px+76)*S,(py+47)*S),radius=10*S,fill=(25,25,27,237))
  text(lay,(px,py-29),NAMES[i],14,'#aaa2a6')
  text(lay,(px,py+1),f'{pct:.1f}%' if n else '—',35,color(i),'number')
  text(lay,(px,py+32),f'{m} / {n}',20,'#dfd8da','number')
  cards.append(lay)
 # The restricted-area annotation is offset slightly to preserve the visible hoop.
 line(chart,[xy(1.9,1.6),xy(5.4,1.6),xy(7.0,.3)],'#a9868d',.75)
 full=chart.convert('RGBA')
 for card in cards:full=Image.alpha_composite(full,card)
 full=full.convert('RGB').resize((W,H),Image.Resampling.LANCZOS);full.paste(frozen_left,(0,0));full.save(work/'总结页.png')
 # Keep the entire source sidebar pixel-for-pixel stable throughout the reveal.
 chart_rgb=chart.convert('RGBA');base_big=base.resize((W*S,H*S),Image.Resampling.LANCZOS)
 def frame(t):
  # A real widening panel: its entire right edge travels across the old scene.
  reveal=ease(t/1.5);edge=round(SIDEBAR+(W-SIDEBAR)*reveal)
  im=base.copy();draw=ImageDraw.Draw(im)
  draw.rectangle((SIDEBAR,0,edge,H),fill=BG)
  # Soft moving drop shadow belongs only to the travelling panel edge.
  if 0<reveal<1:
   shadow=Image.new('RGBA',(W,H));sd=ImageDraw.Draw(shadow)
   for dx in range(32):sd.line((edge+dx,0,edge+dx,H),fill=(0,0,0,round(100*(1-dx/32)**2)))
   im=Image.alpha_composite(im.convert('RGBA'),shadow).convert('RGB')
  # Summary enters with the panel, delayed so the widening motion is readable.
  visible=ease((t-1.05)/.7)
  if visible:
   pane=chart_rgb.copy()
   for i,card in enumerate(cards):
    alpha=ease((t-1.45-i*.045)/.5)
    if alpha:
     c=card.copy();c.putalpha(c.getchannel('A').point(lambda v:round(v*alpha)))
     pane=Image.alpha_composite(pane,c)
   pane=pane.convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
   offset=round(50*(1-visible));shifted=Image.new('RGB',(W,H),BG);shifted.paste(pane,(offset,0))
   mask=Image.new('L',(W,H));ImageDraw.Draw(mask).rectangle((SIDEBAR,0,edge,H),fill=round(255*visible))
   im=Image.composite(shifted,im,mask)
  im.paste(frozen_left,(0,0))
  return im
 if a.preview_only:
  for k in [0,30,60,84,120,180]:frame(k/fps).save(work/f'transition-{k:03d}.png')
  print(work/'总结页.png');return
 tail=work/'summary-tail.mp4';enc=subprocess.Popen([ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(fps),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','13','-pix_fmt','yuv420p','-movflags','+faststart',str(tail)],stdin=subprocess.PIPE)
 for k in range(round(a.tail_seconds*fps)):
  im=frame(k/fps)
  if k in [0,round(.5*fps),round(1.4*fps),round(3*fps)]:im.save(work/f'transition-{k:03d}.png')
  assert np.array_equal(np.asarray(im)[:,:SIDEBAR],np.asarray(frozen_left))
  enc.stdin.write(im.tobytes())
  if k%60==0:print(f'TAIL {k}/{round(a.tail_seconds*fps)}',flush=True)
 enc.stdin.close();assert enc.wait()==0
 # Re-encode the two verified pieces together for consistent frame timing and codec.
 subprocess.run([ff,'-y','-v','error','-i',str(a.video),'-i',str(tail),'-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0[v]','-map','[v]','-an','-c:v','libx264','-preset','fast','-crf','13','-pix_fmt','yuv420p','-movflags','+faststart',str(a.output)],check=True)
 subprocess.run([ff,'-v','error','-i',str(a.output),'-f','null','-'],check=True)
 report={'source_seconds':base_seconds,'summary_seconds':a.tail_seconds,'total_seconds':base_seconds+a.tail_seconds,'made':int(counts[:,0].sum()),'attempts':len(rows),'sidebar_preserved_every_tail_frame':True,'fine_regions_match_sidebar':True,'fine_region_count':10,'league_comparison':True,'league_attempts':int(league.sum()),'no_fixed_seam':True,'fully_decoded':True}
 (work/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False));print(a.output)
if __name__=='__main__':main()
