from pathlib import Path
import sys,os,math,subprocess,time,csv,json
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
P=Path(__file__).resolve().parent;BASE=P;ROOT=P;OUT=Path(os.environ.get('SHOT_VIDEO_OUTPUT',P/'outputs'));OUT.mkdir(parents=True,exist_ok=True);JOB=json.loads((P/'job.json').read_text());sys.path.insert(0,str(P))
import plates as plate
from zones import zone,NAMES,RULES,rows
from ui import font
S=2;W,H=1920,1080;SIZE=(W*S,H*S);FPS=JOB['source_fps'];DURATION=float(JOB['source_duration']);TOTAL=round(FPS*DURATION)
N=len(rows);GAMES=len(set(r['game_id'] for r in rows));made=np.array([r['shot_result']=='Made' for r in rows]);xy=plate.g.xy
# A short, readable first eight attempts, then a steady rhythm. There is no preroll montage.
lead=min(8,N);starts=np.r_[.15+np.arange(lead)*.20,np.linspace(1.8,DURATION-2.7,N-lead)] if N>lead else .15+np.arange(lead)*.20
TRAVEL=.42;LIFE=.60
C=plate.C;project=plate.project
u=np.linspace(0,1,193);paths=[];circles=[];world_circles=[]
for x,y,z in xy:
 height=4.2+math.hypot(x,y)*.09
 paths.append(np.column_stack((x*(1-u),y*(1-u),z*(1-u)+10*u+4*height*u*(1-u))))
 a=np.linspace(0,2*np.pi,65);wc=np.column_stack((x+.32*np.cos(a),y+.32*np.sin(a),np.full(len(a),z)));world_circles.append(wc);circles.append(project(wc,C))
world_circles=np.asarray(world_circles)
paths=np.asarray(paths);projected_paths=project(paths,C);centres=project(xy,C)
# Each field is derived from the same prefix of the chronological shot list.
deltas=np.zeros((N,5,2),dtype=int)
for j,r in enumerate(rows):deltas[j,zone(r),0 if made[j] else 1]=1
zone_prefix=np.concatenate([np.zeros((1,5,2),dtype=int),np.cumsum(deltas,axis=0)])
made_prefix=np.r_[0,np.cumsum(made)]
FF=os.environ.get('FFMPEG_BINARY','ffmpeg')
TARGET=OUT/'source.mp4'

def state(t):return int(np.searchsorted(starts,t,side='right'))
BAR_SCALE=JOB['bar_scale']
BAR_WIDTH=372
def bar_geometry(made_count,missed_count):
 # Shared, fixed count scale across all zones and all frames.
 return BAR_WIDTH*made_count/BAR_SCALE,BAR_WIDTH*missed_count/BAR_SCALE

def gloss_bar(im,y,made_count,missed_count,t,phase):
 red_width,white_width=bar_geometry(made_count,missed_count)
 ww=round((red_width+white_width)*S);hh=36
 if ww<=0:return
 Y,X=np.mgrid[0:hh,0:ww];v=Y/(hh-1);x=X/S
 base=np.zeros((hh,ww,3),dtype=np.float32);split=round(red_width*S)
 base[:,:split]=[220,41,65];base[:,split:]=[242,238,232]
 material=.94+.11*np.exp(-((v-.20)/.23)**2)-.035*v;base*=material[:,:,None]
 centre=-90+((t+phase)%4.8)/4.8*(BAR_WIDTH+180);diagonal=x+v*18-centre
 shimmer=.16*np.exp(-(diagonal/46)**2)+.055*np.exp(-(diagonal/13)**2)
 base=base+(255-base)*shimmer[:,:,None]
 layer=Image.fromarray(np.clip(base,0,255).astype('uint8')).convert('RGBA')
 mask=Image.new('L',(ww,hh));ImageDraw.Draw(mask).rounded_rectangle((0,0,ww-1,hh-1),radius=min(18,ww/2),fill=255)
 layer.putalpha(mask);im.paste(layer,(80,round(y*S)),layer)

def panel(t,n):
 im=plate.PANEL.copy();d=plate.D(im);m=int(made_prefix[n]);miss=n-m
 r=rows[max(0,n-1)];game=int(r['game_number']) if n else 0;year,month,day=r['game_date'].split('-')
 d.text(412,168,f'第 {game} / {GAMES} 场',16,'#c7bec2',anchor='rt');d.text(412,196,f'{year}年{int(month)}月{int(day)}日',14,'#a99da3',anchor='rt')
 d.text(38,272 if n<1000 else 283,str(n),78 if n<1000 else 64,plate.WHITE,'number')
 d.text(412,281,f'{m/n*100:.1f}' if n else '0.0',36,plate.WHITE,'number','rt')
 d.text(173,366,str(m),35,plate.WHITE,'number','rt');d.text(412,366,str(miss),35,plate.WHITE,'number','rt')
 for j,(m,miss) in enumerate(zone_prefix[n]):
  y=528+j*91;num=int(m+miss);ratio=float(m/num) if num else 0.
  d.text(412,y-1,f'{m} / {num}',25,plate.WHITE,'number','rt')
  gloss_bar(im,y+37,int(m),int(miss),t,j*.26)
  d.text(40,y+65,f'{ratio*100:.1f}% 命中率' if num else '暂无出手',13,'#b8acb0')
 return im

_MARKS=None;_MARK_N=0
CURRENT_C=C
DYNAMIC=False
DYNAMIC_CIRCLES=None;DYNAMIC_CENTRES=None
def camera(t):
 q=max(0.,min(1.,t/DURATION));az=math.radians(JOB['orbit_start_degrees']+JOB['orbit_degrees']*q)
 target=np.array([0.,17.,0.]);raw=np.array([math.sin(az)*105,math.cos(az)*105,70.]);cam=target+(raw-target)*(1-JOB['dolly_in_percent']/100*q)
 f=target-cam;f/=np.linalg.norm(f);rt=np.cross(f,[0,0,1]);rt/=np.linalg.norm(rt);up=np.cross(rt,f)
 return cam,rt,up,f

def draw_marker(d,j,bright=False,origin=None,opacity=1.):
 if made[j]:
  if DYNAMIC:
   p=DYNAMIC_CIRCLES[j]
  else:p=circles[j]
  col=np.array([255,101,112] if bright else [111,44,53]);d.line(p,tuple(np.round(col*opacity).astype(int)),1.3 if bright else .9)
 else:
  cx,cy=origin if origin is not None else (DYNAMIC_CENTRES[j] if DYNAMIC else centres[j])
  col=np.array([255,255,255] if bright else [119,113,107])
  for sg in [-1,1]:d.line([(cx-2.9,cy-sg*2.9),(cx+2.9,cy+sg*2.9)],tuple(np.round(col*opacity).astype(int)),1.15 if bright else .85)

def settled_markers(n):
 global _MARKS,_MARK_N
 if DYNAMIC:
  im=Image.new('RGB',SIZE);d=plate.g.Draw(im)
  for j in range(n):draw_marker(d,j)
  return im
 if _MARKS is None or n<_MARK_N:_MARKS=Image.new('RGB',SIZE);_MARK_N=0
 d=plate.g.Draw(_MARKS)
 for j in range(_MARK_N,n):draw_marker(d,j)
 _MARK_N=n
 return _MARKS

def background(t):
 if not DYNAMIC:return plate.COURT.copy()
 im=Image.new('RGB',SIZE,'#08080b');g=plate.g
 g.arena(g.Draw(im),CURRENT_C);im=plate.ImageEnhance.Brightness(im).enhance(.20);g.warp_floor(im,CURRENT_C);plate.basket_pair(g.Draw(im),CURRENT_C)
 return im

def frame(t):
 global CURRENT_C,DYNAMIC,DYNAMIC_CIRCLES,DYNAMIC_CENTRES
 DYNAMIC=True;CURRENT_C=camera(t)
 n=state(t);DYNAMIC_CIRCLES=project(world_circles[:n],CURRENT_C);DYNAMIC_CENTRES=project(xy[:n],CURRENT_C);base=background(t)
 history_strength=.32+.55*max(0.,min(1.,(t-(starts[-1]+LIFE))/.8))
 im=Image.blend(base,ImageChops.add(base,settled_markers(n)),history_strength)
 fx=Image.new('RGB',SIZE);d=plate.g.Draw(fx)
 active=np.where((starts<=t)&(starts>t-LIFE))[0]
 for j in active:
  age=t-starts[j];progress=min(age/TRAVEL,1.);lim=max(1,int(progress*192)+1)
  fade=1. if age<=TRAVEL else max(0.,(LIFE-age)/(LIFE-TRAVEL))
  col=np.array([255,66,86] if made[j] else [246,238,227]);pp=project(paths[j,:lim],CURRENT_C) if DYNAMIC else projected_paths[j,:lim]
  # One explicit screen anchor drives the line's first vertex and its O/X highlight.
  origin=DYNAMIC_CENTRES[j] if DYNAMIC else centres[j]
  pp=pp.copy();pp[0]=origin
  if lim>1:d.line(pp,tuple(np.round(col*fade).astype(int)),1.35)
  draw_marker(d,j,True,origin=origin,opacity=fade)
  ox,oy=origin;dot=tuple(np.round(np.array([255,220,211])*fade).astype(int))
  d.ellipse((ox-1.25,oy-1.25,ox+1.25,oy+1.25),fill=dot)
  if age<TRAVEL:
   if lim>1:d.line(pp[max(0,lim-24):],tuple(np.round(np.array([255,241,223])*fade).astype(int)),1.05)
   xx,yy=pp[-1];d.ellipse((xx-2,yy-2,xx+2,yy+2),fill='#fff3df')
 im=ImageChops.add(im,fx.filter(ImageFilter.GaussianBlur(2*S)).point(lambda p:round(p*.55)))
 im=ImageChops.add(im,fx)
 im=Image.composite(Image.new('RGB',SIZE,'black'),im,plate.SHADOW_ALPHA)
 im.paste(panel(t,n),(0,0),plate.UI_MASK)
 plate.D(im).text(1880,30,JOB.get('credit',''),20,'#bcb3b7',anchor='rt')
 return im.resize((W,H),Image.Resampling.LANCZOS)

def render_index(i):return frame(i/FPS).tobytes()
def encode(target,first,last,parallel=True):
 enc=subprocess.Popen([FF,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','13','-pix_fmt','yuv420p','-movflags','+faststart',str(target)],stdin=subprocess.PIPE)
 begin=time.time()
 if parallel:
  from concurrent.futures import ProcessPoolExecutor
  import multiprocessing as mp
  with ProcessPoolExecutor(max_workers=int(os.environ.get('SHOT_VIDEO_WORKERS','4')),mp_context=mp.get_context('spawn')) as ex:
   for st in range(first,last,12):
    for b in ex.map(render_index,range(st,min(st+12,last))):enc.stdin.write(b)
    if st%120==0:print(f'FRAME {st}/{last} elapsed {time.time()-begin:.0f}s',flush=True)
 else:
  for i in range(first,last):enc.stdin.write(render_index(i))
 enc.stdin.close();assert enc.wait()==0;print(target,flush=True)
if __name__=='__main__':
 if '--intro' in sys.argv:encode(OUT/'乔丹1998_起点对应_开场检查.mp4',0,180)
 elif '--stills' in sys.argv:
  for t in [0,2,4,7.5,32,84.8]:frame(t).save(OUT/f'乔丹1998_起点对应检查_{t:g}.png')
 else:encode(TARGET,0,min(TOTAL,int(os.environ.get('SHOT_VIDEO_FRAME_LIMIT',TOTAL))))
