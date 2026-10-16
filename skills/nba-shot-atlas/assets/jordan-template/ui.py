from pathlib import Path
from functools import lru_cache
import json,numpy as np
from PIL import Image,ImageFont
P=Path(__file__).resolve().parent;JOB=json.loads((P/'job.json').read_text());S=2
@lru_cache(maxsize=128)
def font(size,weight='regular'):
 name='SmileySans-Oblique.ttf' if weight=='display' else ('BarlowCondensed-Bold.ttf' if weight=='number' else 'NotoSansSC.ttf')
 f=ImageFont.truetype(str(P/'fonts'/name),round(size*S))
 if name=='NotoSansSC.ttf':
  try:f.set_variation_by_axes([750 if weight=='bold' else 450])
  except (OSError,ValueError):pass
 return f
@lru_cache(maxsize=1)
def portrait():
 p=Image.open(P/JOB['portrait_image']).convert('RGBA').crop(JOB['portrait_crop']);p.thumbnail((106*S,133*S),Image.Resampling.LANCZOS)
 a=np.asarray(p.getchannel('A')).astype(float);ramp=np.ones(p.height);k=int(p.height*.9);ramp[k:]=np.linspace(1,0,p.height-k);p.putalpha(Image.fromarray((a*ramp[:,None]).astype('uint8')));return p
