import csv,json,math,numpy as np
from cdata import merged
r=merged('sp_long','sp','1871-01')
d=[a for a,_ in r]; v=np.array([b for _,b in r]); ch=np.diff(np.log(v)); dd=d[1:]
def pres(s): y,m=int(s[:4]),int(s[5:7]); return ((y-1953)%4)*12+m-1
def dec(s): y,m=int(s[:4]),int(s[5:7]); return (y%10)*12+m-1
def add(s,k): y,m=int(s[:4]),int(s[5:7])-1+k; return f"{y+m//12}-{m%12+1:02d}"
def build(upto):
    P=[[] for _ in range(48)];Dc=[[] for _ in range(120)];C=[[] for _ in range(12)]
    for s,c in zip(dd,ch):
        if s>=upto: break
        if s>='1950': P[pres(s)].append(c)
        Dc[dec(s)].append(c); C[int(s[5:7])-1].append(c)
    m=lambda L:[float(np.mean(x)) if x else 0.0 for x in L]
    return m(P),m(Dc),m(C)
def comp(P,Dc,C,s): return (P[pres(s)]+Dc[dec(s)]+C[int(s[5:7])-1])/3
hit=n=0;cache={}
for s,c in zip(dd,ch):
    if s<'2005': continue
    y=s[:4]
    if y not in cache: cache[y]=build(y+'-01')
    p=comp(*cache[y],s); n+=1; hit+=int((p>0)==(c>0))
from datetime import datetime
Y=datetime.now().year-1          # forecast made from data before Jan of last year, so last year and this year are a real test
P,Dc,C=build(f'{Y}-01')
months=[add(f'{Y-1}-12',k) for k in range(0,37)]
f=[100.0]
for s in months[1:]: f.append(f[-1]*math.exp(comp(P,Dc,C,s)))
act={a:b for a,b in r}
tp=[]
for i in range(1,len(f)-1):
    w=f[max(0,i-3):i+4]
    if f[i]==max(w): tp.append((months[i],'High'))
    if f[i]==min(w): tp.append((months[i],'Low'))
print(hit,n,tp)
json.dump({"m":months,"f":[round(x,2) for x in f],"a":[act.get(s) for s in months],"tp":tp,"hit":hit,"n":n},open('work/fc.json','w'))
