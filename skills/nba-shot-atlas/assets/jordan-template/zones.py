import csv,json,math
from pathlib import Path
P=Path(__file__).resolve().parent
rows=list(csv.DictReader(open(P/'shots.csv',encoding='utf-8-sig')))
NAMES=['篮下','短两分','长两分','弧顶及侧翼三分','底角三分']
RULES='按原始出手坐标几何重建，非直接读取NBA SHOT_ZONE_BASIC。两分：距篮心≤4英尺归篮下；其余横向绝对值≤8英尺且纵向≤13.75英尺归短两分；其余两分归长两分。三分：横向绝对值≥22英尺且纵向≤9.2英尺归底角，左右合并；其余三分归弧顶及侧翼（含远距离三分）。使用原记录shot_value区分两分/三分，不靠坐标估计球值。'
def zone(r):
 x=float(r['x_legacy'])/10;y=float(r['y_legacy'])/10
 if int(r['shot_value'])==3:return 4 if abs(x)>=22 and y<=9.2 else 3
 if math.hypot(x,y)<=4:return 0
 if abs(x)<=8 and y<=13.75:return 1
 return 2
counts=[{'区域':a,'命中':0,'未中':0,'出手':0} for a in NAMES]
for r in rows:
 j=zone(r);counts[j]['命中' if r['shot_result']=='Made' else '未中']+=1;counts[j]['出手']+=1
for q in counts:q['命中率']=q['命中']/q['出手'] if q['出手'] else 0
assert sum(q['出手'] for q in counts)==len(rows)
if __name__=='__main__':
 (P/'分区统计.json').write_text(json.dumps({'method':RULES,'rows':counts},ensure_ascii=False,indent=2))
 print(json.dumps(counts,ensure_ascii=False,indent=2))
