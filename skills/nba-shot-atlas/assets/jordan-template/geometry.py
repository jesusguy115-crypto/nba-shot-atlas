import os,sys,math,json,csv,re,subprocess,time
from pathlib import Path
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance,ImageChops
ASSET=Path(__file__).resolve().parent;ROOT=ASSET;WORK=ASSET;OUT=ASSET/'outputs';JOB=json.loads((ASSET/'job.json').read_text())
S=2; W,H=1920,1080; SIZE=(W*S,H*S); FPS=30;DUR=46
GOLD='#d7b762';WHITE='#faf5ff'; PURPLE='#ce89ff'
FONT=str(ASSET/'fonts/BarlowCondensed-Bold.ttf');REG=str(ASSET/'fonts/NotoSansSC.ttf');CJK=REG
@lru_cache(maxsize=100)
def ft(n,kind=0):return ImageFont.truetype([FONT,REG,CJK][kind],round(n*S),index=0)
FINALS=False
FINAL_COLOR_MAP={'#7c1724':'#131b29','#350e15':'#0e1520','#8c2831':'#1b2535','#a22c39':'#263448','#c15461':'#475363','#691725':'#152031','#811d2a':'#1a2537','#341117':'#101827','#67111e':'#182336','#9d2531':'#26354a','#4d0c19':'#111a29','#be5b62':'#485b75','#261418':'#111722','#40141b':'#172131','#6b1d28':'#1b2b40','#983542':'#2a3e54'}
class Draw:
 def __init__(self,im):self.im=im;self.d=ImageDraw.Draw(im)
 def line(self,p,fill,width=1):self.d.line([(x*S,y*S) for x,y in p],fill=fill,width=max(1,round(width*S)),joint='curve')
 def poly(self,p,fill):self.d.polygon([(x*S,y*S) for x,y in p],fill=FINAL_COLOR_MAP.get(fill,fill) if FINALS and isinstance(fill,str) else fill)
 def rect(self,b,fill,outline=None,width=1):self.d.rectangle(tuple(x*S for x in b),fill=fill,outline=outline,width=max(1,round(width*S)))
 def ellipse(self,b,fill=None,outline=None,width=1):self.d.ellipse(tuple(x*S for x in b),fill=fill,outline=outline,width=max(1,round(width*S)))
 def text(self,p,s,n=20,color=WHITE,anchor=None,kind=0):self.d.text((p[0]*S,p[1]*S),s,font=ft(n,kind),fill=color,anchor=anchor)
rows=list(csv.DictReader(open(ASSET/'shots.csv',encoding='utf-8-sig')))
rows.sort(key=lambda r:(int(r['game_number']),int(r['period']),-sum(float(a)*b for a,b in zip(re.findall(r'[\d.]+',r['clock']),[60,1]))))
N=len(rows);made=np.array([r['shot_result']=='Made' for r in rows]);values=np.array([int(r['shot_value']) for r in rows]);points=values*made
starts=np.r_[np.linspace(.1,90.1,N-1),94.0]
xy=np.array([[-float(r['x_legacy'])/10,float(r['y_legacy'])/10,.045] for r in rows])
# Smooth 192-segment illustrative flight, one path per made shot.
u=np.linspace(0,1,193);paths=[]
for x,y,z in xy:
 dist=math.hypot(x,y);height=4.2+dist*.09
 paths.append(np.column_stack((x*(1-u),y*(1-u),z*(1-u)+10*u+4*height*u*(1-u))))
paths=np.array(paths)
assert len(rows)==JOB['expected_attempts'] and int(made.sum())==JOB['expected_made']
COURT=Image.open(ASSET/JOB['court_image']).convert('RGB')
# Official image inner regulation boundaries: x=338..2786, y=134..1440.
# 94ft x 50ft. The official complete artwork is mapped, not re-drawn.
CW,CH=COURT.size
PX0,PX1,PY0,PY1=map(float,JOB['court_texture_box'])
def tex_world(px,py):return [(py-(PY0+PY1)/2)/((PY1-PY0)/50),(px-PX0)/((PX1-PX0)/94)-5.25,0]
FLOOR_CORNERS=np.array([tex_world(0,0),tex_world(CW,0),tex_world(CW,CH),tex_world(0,CH)])
# Darken the fully preserved surface under a localized court lighting rig.
a=np.asarray(COURT).astype(np.float32)/255
Y,X=np.mgrid[0:CH,0:CW];light=.52+.15*np.exp(-((X-850)/1800)**2-((Y-790)/1100)**2)
a=np.clip(a*light[:,:,None],0,1)
COURT_LIT=Image.fromarray((a*255).astype('uint8')).convert('RGBA')
photo=Image.open(ASSET/JOB['portrait_image']).convert('RGBA').crop((280,15,760,510)).resize((164*S,170*S),Image.Resampling.LANCZOS)
logo=Image.open(ASSET/JOB['logo_image']).convert('RGBA').resize((150*S,150*S),Image.Resampling.LANCZOS)

def camera(t):
 az=math.radians(7*math.sin(t/DUR*math.pi*1.5-.6))
 cam=np.array([math.sin(az)*100,math.cos(az)*100,58.])
 target=np.array([0.,12.,0.]);f=target-cam;f/=np.linalg.norm(f)
 right=np.cross(f,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,f)
 return cam,right,up,f

def project(p,c):
 cam,right,up,f=c;q=np.asarray(p)-cam;z=q@f
 return np.stack((960+(q@right)/z*2600,580-(q@up)/z*2600),axis=-1)
def line3(d,p,c,col,width=1):d.line(project(p,c),col,width)
def poly3(d,p,c,col):d.poly(project(p,c),col)
def circ3(d,x,y,z,r,c,col,width=1):
 a=np.linspace(0,2*np.pi,97);line3(d,np.column_stack((x+r*np.cos(a),y+r*np.sin(a),np.full(len(a),z))),c,col,width)
def box(d,c,base,sz,color):
 x,y,z=base;a,b,h=sz
 poly3(d,[[x,y,z],[x+a,y,z],[x+a,y+b,z],[x,y+b,z]],c,color[0])
 poly3(d,[[x,y,z],[x+a,y,z],[x+a,y,z+h],[x,y,z+h]],c,color[1])
 poly3(d,[[x,y,z],[x,y+b,z],[x,y+b,z+h],[x,y,z+h]],c,color[2])
 poly3(d,[[x,y,z+h],[x+a,y,z+h],[x+a,y+b,z+h],[x,y+b,z+h]],c,color[3])

# Individually modelled seats, railings and row risers in an arena bowl.
SEATS=[]
for side in [-1,1]:
 for row in range(13):
  x=side*(36+row*2.15);z=row*.88
  for yi in np.arange(-16,104,2.2):
   if any(abs(yi-v)<2 for v in [0,26,55,83]):continue
   SEATS.append((x,yi,z,side,'side'))
for row in range(12):
 yy=-23-row*2.25;z=row*.9
 for x in np.arange(-30-row*.5,31+row*.5,2.1):
  if abs(x)<4:continue
  SEATS.append((x,yy,z,0,'end'))

def arena(d,c):
 # Floor surround and bowl foundations, faithful materials and layout, schematic geometry.
 poly3(d,[[-70,-60,-1],[70,-60,-1],[70,140,-1],[-70,140,-1]],c,'#050506')
 for side in [-1,1]:
  for row in range(13):
   xa=side*(34+row*2.15);xb=side*(36.3+row*2.15)
   poly3(d,[[xa,-20,row*.88-.1],[xb,-20,row*.88-.1],[xb,110,row*.88-.1],[xa,110,row*.88-.1]],c,'#111014')
 for row in range(12):
  y=-23-row*2.25
  poly3(d,[[-40,y,row*.9-.2],[40,y,row*.9-.2],[40,y-2.25,row*.9-.2],[-40,y-2.25,row*.9-.2]],c,'#111014')
 # Order farther seats first.
 for x,y,z,side,kind in sorted(SEATS,key=lambda p:np.linalg.norm(np.array(p[:3])-c[0]),reverse=True):
  col=(26+int(z*.35),24+int(z*.25),30+int(z*.3))
  if kind=='side':
   poly3(d,[[x-.7,y-.8,z+.8],[x+.7,y-.8,z+.8],[x+.7,y+.8,z+.8],[x-.7,y+.8,z+.8]],c,col)
   bx=x+side*.8
   poly3(d,[[bx,y-.85,z+.8],[bx,y+.85,z+.8],[bx,y+.85,z+2.35],[bx,y-.85,z+2.35]],c,'#211d25')
   line3(d,[[bx,y-.85,z+2.35],[bx,y+.85,z+2.35]],c,'#39313e',.6)
  else:
   poly3(d,[[x-.8,y-.7,z+.8],[x+.8,y-.7,z+.8],[x+.8,y+.7,z+.8],[x-.8,y+.7,z+.8]],c,col)
   poly3(d,[[x-.85,y-.8,z+.8],[x+.85,y-.8,z+.8],[x+.85,y-.8,z+2.35],[x-.85,y-.8,z+2.35]],c,'#211d25')
   line3(d,[[x-.85,y-.8,z+2.35],[x+.85,y-.8,z+2.35]],c,'#39313e',.6)
 # Walkway safety railings.
 for side in [-1,1]:
  for yy in [-1,27,56,84]:
   line3(d,[[side*35,yy,2],[side*62,yy,13]],c,'#49434c',.7)
 # Two rows of courtside chairs behind the baseline.
 for yy in [-17.4,-20]:
  for x in np.arange(-25,26,2):
   if abs(x)<4:continue
   box(d,c,(x-.7,yy-.6,.2),(1.4,1.2,.8),['#211825','#1a151d','#251b29','#28202b'])
   poly3(d,[[x-.75,yy-.65,1],[x+.75,yy-.65,1],[x+.75,yy-.65,2.5],[x-.75,yy-.65,2.5]],c,'#211827')
 # Benches and scorer's table, plus LED fascia.
 for side in [-1,1]:
  x=side*31.7
  for y in np.arange(4,29,2):
   box(d,c,(x-.6,y,0),(1.2,1.2,.8),['#221627','#17111c','#201325','#2e1b34'])
  poly3(d,[[x,30,0],[x,53,0],[x,53,2.1],[x,30,2.1]],c,'#221332')
  line3(d,[[x,30,2.2],[x,53,2.2]],c,'#8b6b27',.8)

def warp_floor(im,c):
 dest=project(FLOOR_CORNERS,c)*S;src=np.array([[0,0],[CW,0],[CW,CH],[0,CH]])
 A=[];b=[]
 for (x,y),(a,z) in zip(dest,src):
  A.extend([[x,y,1,0,0,0,-a*x,-a*y],[0,0,0,x,y,1,-z*x,-z*y]]);b.extend([a,z])
 cf=np.linalg.solve(A,b)
 # Transform only the visible scene rectangle, preserving 2x supersampling.
 top=145*S;bh=883*S
 a,b0,c0,d,e,f,g,h=cf
 cf=(a,b0,b0*top+c0,d,e,e*top+f,g,h)
 denom=1+h*top
 cf=tuple(v/denom for v in cf)
 layer=COURT_LIT.transform((W*S,bh),Image.Transform.PERSPECTIVE,cf,Image.Resampling.BICUBIC)
 im.paste(layer,(0,top),layer)

def beam(d,c,a,b,w,h,colors):
 a=np.array(a,dtype=float);b=np.array(b,dtype=float);axis=b-a;axis/=np.linalg.norm(axis)
 u=np.array([1.,0.,0.]) if abs(axis[0])<.9 else np.array([0.,1.,0.]);v=np.cross(axis,u);v/=np.linalg.norm(v)
 verts=[p+su*u*w/2+sv*v*h/2 for p in [a,b] for su,sv in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 for ids,col in [([0,1,2,3],colors[0]),([0,1,5,4],colors[1]),([1,2,6,5],colors[2]),([2,3,7,6],colors[3]),([3,0,4,7],colors[0]),([4,5,6,7],colors[3])]:poly3(d,[verts[k] for k in ids],c,col)

def decal(d,c,patch,verts):
 dest=project(verts,c)*S;ww,hh=patch.size;src=[[0,0],[ww,0],[ww,hh],[0,hh]];A=[];b=[]
 for (x,y),(a,z) in zip(dest,src):
  A.extend([[x,y,1,0,0,0,-a*x,-a*y],[0,0,0,x,y,1,-z*x,-z*y]]);b.extend([a,z])
 cf=np.linalg.solve(A,b)
 # Only draw the small bounding rectangle of this equipment decal.
 x0=max(0,int(dest[:,0].min())-2);y0=max(0,int(dest[:,1].min())-2)
 x1=min(SIZE[0],int(dest[:,0].max())+3);y1=min(SIZE[1],int(dest[:,1].max())+3)
 if x1<=x0 or y1<=y0:return
 a,b0,c0,dd,e,f,g,h=cf;den=1+g*x0+h*y0
 cf=((a)/den,b0/den,(a*x0+b0*y0+c0)/den,dd/den,e/den,(dd*x0+e*y0+f)/den,g/den,h/den)
 lay=patch.transform((x1-x0,y1-y0),Image.Transform.PERSPECTIVE,cf,Image.Resampling.BICUBIC)
 d.im.paste(lay,(x0,y0),lay)

@lru_cache(maxsize=1)
def pad_decal():
 p=Image.new('RGBA',(360,540));q=ImageDraw.Draw(p)
 q.rounded_rectangle((9,9,351,531),radius=24,outline=(151,104,184,190),width=3)
 q.text((180,125),JOB.get('team_label',''),font=ImageFont.truetype(FONT,66),anchor='mm',fill='#e6c873')
 lg=Image.open(ASSET/JOB['logo_image']).convert('RGBA');lg.thumbnail((250,250));p.alpha_composite(lg,((360-lg.width)//2,205))
 q.line((45,485,315,485),fill='#6e4a88',width=3)
 return p

def basket(d,c,y,reverse=False):
 s=1 if reverse else -1
 def V(x,a,z):return [x,y+s*a,z]
 # Low wheeled ballast base and shaped padded tower behind the baseline.
 cols=['#261418','#40141b','#6b1d28','#983542']
 x1,x2=-2.3,2.3
 poly3(d,[V(x1,8.5,.25),V(x2,8.5,.25),V(x2,15,.25),V(x1,15,.25)],c,'#100c16')
 poly3(d,[V(x1,8.5,.25),V(x2,8.5,.25),V(x2,8.5,1.45),V(x1,8.5,1.45)],c,'#811d2a')
 poly3(d,[V(x1,8.5,1.45),V(x2,8.5,1.45),V(x2,15,1.45),V(x1,15,1.45)],c,'#691725')
 for x in [-2.3,2.3]:
  poly3(d,[V(x,8.5,.25),V(x,15,.25),V(x,15,1.45),V(x,8.5,1.45)],c,'#341117')
  for a in [9.4,13.8]:
   line3(d,[V(x,a,.25),V(x,a,.65)],c,'#070709',4.4)
 # Main upright and stabilizing linkage, kept separate from the safety padding.
 steel=['#33343d','#4c4c57','#262630','#73717d']
 beam(d,c,V(0,12.5,1.5),V(0,8.9,6.8),1.8,1.05,steel)
 for x in [-1.25,1.25]:
  beam(d,c,V(x,13.0,1.5),V(x,8.3,7.0),.22,.25,steel)
  beam(d,c,V(x,9.5,6.35),V(x,1.7,10.6),.32,.32,steel)
 beam(d,c,V(0,9.3,6.1),V(0,1.55,10.3),1.1,.72,steel)
 # Sculpted front cushion with stitch seams and actual team artwork.
 front=[V(-1.85,8.25,1.45),V(1.85,8.25,1.45),V(1.6,7.9,5.8),V(-1.6,7.9,5.8)]
 poly3(d,front,c,'#7c1724')
 for x,edge in [(-1.85,-1.6),(1.85,1.6)]:
  poly3(d,[V(x,8.25,1.45),V(x,10.6,1.45),V(edge,9.9,5.8),V(edge,7.9,5.8)],c,'#350e15' if x<0 else '#8c2831')
 poly3(d,[V(-1.6,7.9,5.8),V(1.6,7.9,5.8),V(1.6,9.9,5.8),V(-1.6,9.9,5.8)],c,'#a22c39')
 line3(d,[V(-1.65,8.21,1.65),V(-1.44,7.86,5.6)],c,'#c15461',.7)
 line3(d,[V(1.65,8.21,1.65),V(1.44,7.86,5.6)],c,'#c15461',.7)
 # Texture winding chosen to keep lettering readable from the playing court.
 vs=[V(1.48,7.87,5.53),V(-1.48,7.87,5.53),V(-1.68,8.22,1.7),V(1.68,8.22,1.7)]
 decal(d,c,pad_decal(),vs)
 # Rear steel backboard support yoke and bolted mounting plates.
 for x in [-2.25,2.25]:
  beam(d,c,V(0,1.7,10.35),V(x,1.55,11.7),.11,.13,steel)
  beam(d,c,V(x,1.55,9.4),V(x,1.55,12.15),.09,.10,steel)
 beam(d,c,V(-2.55,1.55,10.4),V(2.55,1.55,10.4),.14,.14,steel)
 # Transparent tempered glass, with a pale edge and restrained reflection.
 yy=1.25
 verts=[V(-3,yy,9),V(3,yy,9),V(3,yy,12.5),V(-3,yy,12.5)]
 glass=Image.new('RGBA',SIZE);gd=ImageDraw.Draw(glass)
 gd.polygon([tuple(p*S) for p in project(verts,c)],fill=(137,160,184,16))
 gd.polygon([tuple(p*S) for p in project([V(-2.8,yy,12.3),V(-2.42,yy,12.3),V(.25,yy,9.18),V(-.13,yy,9.18)],c)],fill=(220,235,248,12))
 d.im.paste(glass,(0,0),glass)
 line3(d,verts+[verts[0]],c,'#d6dce5',1.15)
 line3(d,[V(-2.95,yy-.02,12.45),V(2.95,yy-.02,12.45)],c,'#f5f6f8',.65)
 # Regulation target rectangle. Leave the board clear above it: no timer housing.
 rect=[V(-1,yy-.025,9.5),V(1,yy-.025,9.5),V(1,yy-.025,11),V(-1,yy-.025,11)]
 line3(d,rect+[rect[0]],c,'#f3f2f1',1.25)
 # Purple safety padding along the board's lower edge, with capped corners.
 beam(d,c,V(-3.02,yy,8.94),V(3.02,yy,8.94),.24,.24,['#67111e','#9d2531','#4d0c19','#be5b62'])
 for xx in [-2.5,2.5]:
  for zz in [9.45,12.02]:
   px,py=project([V(xx,yy-.035,zz)],c)[0]
   d.ellipse((px-.65,py-.65,px+.65,py+.65),fill='#c6c8cf')
 # Breakaway mounting bracket and spring connection behind the rim.
 beam(d,c,V(0,1.21,9.96),V(0,.68,9.96),.42,.16,['#8d3e19','#ba5623','#622d17','#df8442'])
 # Tubular orange rim, shaded with a thin top highlight rather than a flat circle.
 angles=np.linspace(0,2*math.pi,129)
 ring=np.column_stack((.75*np.cos(angles),y+.75*np.sin(angles),np.full(len(angles),10.)))
 line3(d,ring,c,'#783019',2.8)
 line3(d,ring+np.array([0,0,.025]),c,'#e2792d',1.85)
 line3(d,ring+np.array([0,0,.055]),c,'#f8b46f',.65)
 # Twelve net attachment points and interlocking diamond rope cells.
 n=12;levels=[(10.,.72),(9.65,.66),(9.29,.55),(8.94,.43),(8.58,.41)]
 for k in range(len(levels)-1):
  z1,r1=levels[k];z2,r2=levels[k+1]
  for j in range(n):
   a1=2*math.pi*(j+(k%2)*.5)/n
   for direction in [-1,1]:
    a2=a1+direction*math.pi/n
    p1=[r1*math.cos(a1),y+r1*math.sin(a1),z1]
    p2=[r2*math.cos(a2),y+r2*math.sin(a2),z2]
    col='#e3dce7' if math.sin(a1)>0 else '#89818e'
    line3(d,[p1,p2],c,col,.64)
    px,py=project([p2],c)[0];d.ellipse((px-.48,py-.48,px+.48,py+.48),fill=col)
 circ3(d,0,y,8.58,.41,c,'#c7bdcf',.65)

