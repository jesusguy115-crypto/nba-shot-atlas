from pathlib import Path
import sys,math,json,csv,subprocess
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance,ImageChops
P=Path(__file__).resolve().parent;BASE=P;ROOT=P;OUT=P/'outputs';JOB=json.loads((P/'job.json').read_text());sys.path.insert(0,str(P))
import geometry as g
from zones import zone,NAMES,RULES,rows
from ui import font,portrait
S=2;W,H=1920,1080;SIZE=(W*S,H*S);N=len(rows)
RED='#dc2941';WHITE='#f2eee8';MUTED='#b7afb1';PAPER='#1b1b1e'
class D:
 def __init__(self,im):self.d=ImageDraw.Draw(im)
 def text(self,x,y,t,size=20,color=WHITE,weight='regular',anchor='lt'):self.d.text((x*S,y*S),t,font=font(size,weight),fill=color,anchor=anchor)
 def rect(self,b,c):self.d.rectangle(tuple(round(v*S) for v in b),fill=c)
 def line(self,pts,c,w=1):self.d.line([(x*S,y*S) for x,y in pts],fill=c,width=max(1,round(w*S)),joint='curve')

cam=np.array([0.,105.,70.]);f=np.array([0.,17.,0.])-cam;f/=np.linalg.norm(f);right=np.cross(f,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,f);C=(cam,right,up,f)
def project(p,c):
 cam,rt,up,f=c;q=np.asarray(p)-cam;z=q@f
 return np.stack((1190+(q@rt)/z*2400,585-(q@up)/z*2400),axis=-1)
g.project=project;g.FINALS=False
# Render the floor through the last image row; no reserved subtitle band.
def warp_floor_full(im,c):
 dest=project(g.FLOOR_CORNERS,c)*S;src=np.array([[0,0],[g.CW,0],[g.CW,g.CH],[0,g.CH]])
 A=[];rhs=[]
 for (x,y),(a,z) in zip(dest,src):
  A.extend([[x,y,1,0,0,0,-a*x,-a*y],[0,0,0,x,y,1,-z*x,-z*y]]);rhs.extend([a,z])
 cf=np.linalg.solve(A,rhs);top=0;bh=H*S
 a,b,c0,dd,e,f,gg,h=cf;denom=1+h*top
 cf=tuple(v/denom for v in (a,b,b*top+c0,dd,e,e*top+f,gg,h))
 layer=g.COURT_LIT.transform((W*S,bh),Image.Transform.PERSPECTIVE,cf,Image.Resampling.BICUBIC)
 im.paste(layer,(0,top),layer)
g.warp_floor=warp_floor_full
# Hoop centres are 83.5ft apart: 94ft court less 5.25ft inset at each end.
BASKETS=((0.,False),(83.5,True))
def basket_pair(d,c):
 # Draw the farther equipment first under the current orbit camera.
 for yy,reverse in sorted(BASKETS,key=lambda item:np.dot(np.array([0.,item[0],6.])-c[0],c[3]),reverse=True):
  original_decal=g.decal
  if reverse:
   def far_decal(draw,cam,patch,verts):return original_decal(draw,cam,patch.transpose(Image.Transpose.FLIP_LEFT_RIGHT),verts)
   g.decal=far_decal
  try:g.basket(d,c,yy,reverse=reverse)
  finally:g.decal=original_decal


im=Image.new('RGB',SIZE,'#08080b');g.arena(g.Draw(im),C);im=ImageEnhance.Brightness(im).enhance(.20);g.warp_floor(im,C);basket_pair(g.Draw(im),C)
COURT=im.copy()
# Clean sidebar with one straight divider and restrained directional shadow.
mask=Image.new('L',SIZE);ImageDraw.Draw(mask).rectangle((0,0,459*S-1,H*S),fill=255)
under_mask=mask
shadow=Image.new('L',SIZE);shadow.paste(mask,(8*S,0));shadow=shadow.filter(ImageFilter.GaussianBlur(11*S)).point(lambda v:round(v*.62))
im=Image.composite(Image.new('RGB',SIZE,'black'),im,shadow)
paper=Image.new('RGB',SIZE,'#1b1b1e');im=Image.composite(paper,im,mask)
d=D(im)
d.line([(458.5,0),(458.5,H)],'#51484d',1)
# Portrait and name remain in the same paper material as the information.
p=portrait();p=p.resize((round(p.width*.88),round(p.height*.88)),Image.Resampling.LANCZOS);im.paste(p,(34*S,12*S),p)
d.text(142,34,JOB['name_zh'],39,WHITE,'display')
xx=145
for ch in JOB['name_en']:d.text(xx,91,ch,16,'#9d9397','number');xx+=font(16,'number').getlength(ch)/S+1.15

d.line([(40,145),(412,145)],'#444045',.7)
# Static parts of the approved sidebar. Values and every shot are rendered from zero per frame.
d.text(40,166,JOB['season_label'],19,WHITE,'bold')
d.text(40,196,JOB['phase_label'],15,'#a99da3')
d.line([(40,231),(412,231)],'#444045',.7)
d.text(40,243,'累计出手',17,MUTED);d.text(165,317,f'/ {len(rows)}',23,'#91878b','number')
d.text(412,323,'% 命中率',14,'#b9aeb3',anchor='rt')
d.rect((40,382,49,391),RED);d.text(58,378,'命中',18,MUTED)
d.rect((238,382,247,391),WHITE);d.text(256,378,'未中',18,MUTED)
d.line([(40,420),(412,420)],'#444045',.7)
d.text(40,443,'投篮区域',24,WHITE,'bold');d.text(412,451,'命中 / 出手',14,'#bdb1b5',anchor='rt')
d.rect((41,488,51,498),RED);d.text(60,484,'命中',15,MUTED);d.rect((121,488,131,498),WHITE);d.text(140,484,'未中',15,MUTED)
for j,name in enumerate(NAMES):d.text(40,528+j*91,name,21,WHITE,'bold')

SCENE=im.copy();PANEL=im.crop((0,0,500*S,H*S))

UI_MASK=under_mask.crop((0,0,500*S,H*S))
SHADOW_ALPHA=shadow
