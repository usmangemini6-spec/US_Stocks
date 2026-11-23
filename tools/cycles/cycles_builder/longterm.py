import csv, json, math
import numpy as np
from cdata import series, merged, yoy, have
def yr(d): return int(d[:4])+(int(d[5:7])-0.5)/12
def ym(x): return f"{int(x)}-{min(12,int((x%1)*12)+1):02d}"
def long_cycle(series, pmin, pmax, log=True, end=2041.0):
    t=np.array([yr(d) for d,_ in series]); y=np.array([v for _,v in series]); z=np.log(y) if log else y
    tc=t-t.mean(); A=np.column_stack([np.ones_like(t),tc,tc**2]); b,*_=np.linalg.lstsq(A,z,rcond=None); res=z-A@b
    m30=t>=t[-1]-30; b30=np.polyfit(t[m30],z[m30],1)[0]
    best=None
    for P in np.arange(pmin,pmax+.01,0.5):
        w=2*math.pi/P; X=np.column_stack([np.sin(w*t),np.cos(w*t)]); c,*_=np.linalg.lstsq(X,res,rcond=None)
        sse=((res-X@c)**2).sum()
        if best is None or sse<best[0]: best=(sse,P,c)
    _,P,c=best; w=2*math.pi/P
    wav=lambda tt: c[0]*np.sin(w*tt)+c[1]*np.cos(w*tt)
    r2=1-best[0]/((res-res.mean())**2).sum()
    tf=np.arange(t[0]+0.5/12,end,1/12); last=t[-1]
    tfc=tf-t.mean(); zin=b[0]+b[1]*tfc+b[2]*tfc**2+wav(tf)
    zout=z[-1]+b30*(tf-last)+wav(tf)-wav(np.array([last]))[0]
    fin=lambda a: np.exp(a) if log else a
    pin=np.where(tf<=last,fin(zin),np.nan); pout=np.where(tf>=last-1e-9,fin(zout),np.nan)
    # turning points of the wave
    phase=math.atan2(c[1],c[0])          # wave = A sin(w t + phase)
    lows=[(-math.pi/2-phase+2*math.pi*k)/w for k in range(-300,300)]; highs=[L+P/2 for L in lows]
    lows=[x for x in lows if t[0]<=x<=end]; highs=[x for x in highs if t[0]<=x<=end]
    # hit test: each past projected low vs lowest residual within +-P/2
    hits=n=0
    for L in lows:
        if L<t[0]+P/2 or L>last-P/2: continue
        m=(t>=L-P/2)&(t<=L+P/2); i=np.argmin(res[m]); n+=1; hits+=abs(t[m][i]-L)<=0.15*P
    step=3   # quarterly points keep the page light
    idx=list(range(0,len(tf),step))
    act={d:v for d,v in series}
    return dict(P=float(P),r2=round(float(r2),2),hits=int(hits),n=int(n),last_low=(ym(max(x for x in lows if x<=last)) if any(x<=last for x in lows) else None),last_high=(ym(max(x for x in highs if x<=last)) if any(x<=last for x in highs) else None),trend=round(float((math.exp(b30)-1)*100 if log else b30),2),
        lab=[ym(tf[i]) for i in idx],act=[round(act[ym(tf[i])],2) if ym(tf[i]) in act else None for i in idx],
        fit=[None if np.isnan(pin[i]) else round(float(pin[i]),2) for i in idx],proj=[None if np.isnan(pout[i]) else round(float(pout[i]),2) for i in idx],
        lows=[ym(x) for x in lows],highs=[ym(x) for x in highs],
        next_low=ym(min(x for x in lows if x>last)) if any(x>last for x in lows) else None,
        next_high=ym(min(x for x in highs if x>last)) if any(x>last for x in highs) else None,
        log=log,start=series[0][0])
sp=merged("sp_long","sp","1871-01")
gold=merged("gold_long","gold","1971-08")
cy=yoy(series("cpi"))
oil=series("wti_fred","1986-01") if have("wti_fred") else series("oil")
home=series("home","1975-01")
rdc=series
def LC(s,*a,**k):
    try:
        return long_cycle(s,*a,**k) if len(s)>=120 else None
    except Exception as e:
        print("  long cycle skipped:",e); return None
out={"sp":LC(sp,12,40),"oil":LC(oil,8,30),"nasdaq":LC(rdc("nasdaq"),8,30),"dji":LC(rdc("dji"),8,30),"tasi":LC(rdc("tasi"),6,20),"silver":LC(rdc("silver"),6,20),"us10y":LC([(d,v/(10 if v>30 else 1)) for d,v in rdc("us10y")],8,40,log=False),"home":LC(home,10,30),"gold":LC(gold,8,30),"cpi":LC(cy,10,60,log=False)}
out={k:v for k,v in out.items() if v}
if have("fedfunds"): out["fedfunds"]=LC(series("fedfunds"),8,40,log=False)
for k,v in out.items(): print(k,v["P"],"r2",v["r2"],"hits",v["hits"],"/",v["n"],"next low",v["next_low"],"next high",v["next_high"],"trend",v["trend"],len(v["lab"]))
d3=json.load(open("work/data3.json"))
for k in out:
    if k in d3: d3[k]["lt"]=out[k]
json.dump(d3,open("work/data4.json","w"))
