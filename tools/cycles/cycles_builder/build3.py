import csv, json, math
import numpy as np
from cdata import series, merged, yoy, have
def slot(d):            # month of the 4-year presidential term: 0 = Jan of inauguration year (1953, ..., 2025)
    y,m=int(d[:4]),int(d[5:7]); return ((y-1953)%4)*12+m-1
def add(d,k): y,m=int(d[:4]),int(d[5:7])-1+k; return f"{y+m//12}-{m%12+1:02d}"
def model(series, additive=False, test_from="2005"):
    t=[d for d,_ in series]; y=np.array([v for _,v in series])
    ch=np.diff(y) if additive else np.diff(np.log(y)); tt=t[1:]
    def comp(upto=None):
        s=[[] for _ in range(48)]
        for d,c in zip(tt,ch):
            if upto and d>=upto: break
            s[slot(d)].append(c)
        return np.array([np.mean(x) if x else 0 for x in s]), np.array([np.mean(np.array(x)>0) if x else .5 for x in s])
    avg,pos=comp()
    # out-of-sample direction test: each year uses only earlier years
    hit=n=0
    for d,c in zip(tt,ch):
        if d<test_from: continue
        a,_=comp(d[:4]+"-01"); p=a[slot(d)]
        if p!=0: n+=1; hit+= (p>0)==(c>0)
    # actual vs projection: projection made at Jan of previous year from the actual value then
    start=str(int(t[-1][:4])-1)+"-01"; i0=t.index(start) if start in t else len(t)-24
    a_hist,_=comp(t[i0])
    def path(v0,d0,a,months):
        o=[];v=v0
        for k in range(1,months+1):
            d=add(d0,k); c=a[slot(d)]; v=v+c if additive else v*math.exp(c); o.append((d,v))
        return o
    back=[(t[i0],y[i0])]+path(y[i0],t[i0],a_hist,len(t)-1-i0)
    fwd=[(t[-1],y[-1])]+path(y[-1],t[-1],avg,26)
    # signals on the forward path: local lows/highs (at least 3 months apart)
    fv=[v for _,v in fwd]; sig={}
    for i in range(1,len(fv)-1):
        w=fv[max(0,i-2):i+3]
        if fv[i]==min(w): sig[fwd[i][0]]="Buy window"
        if fv[i]==max(w): sig[fwd[i][0]]="Sell window"
    # presidential average path (cumulative %, 48 months) and calendar seasonality
    cum=np.cumsum(avg); pres=(cum if additive else (np.exp(cum)-1)*100).tolist()
    cal=[[] for _ in range(12)]
    for d,c in zip(tt,ch): cal[int(d[5:7])-1].append(c)
    seas=[(float(np.mean(x))*(1 if additive else 100), float(np.mean(np.array(x)>0)*100)) for x in cal]

    # short-term cycle inside the year: average change by calendar month, learned from years BEFORE the current one
    cy_=t[-1][:4]; prevdec=str(int(cy_)-1)+"-12"
    cal_h=[[] for _ in range(12)]
    for d,c in zip(tt,ch):
        if d[:4]<cy_: cal_h[int(d[5:7])-1].append(c)
    sav=[np.mean(x) if x else 0 for x in cal_h]
    sy=[]; 
    if prevdec in t:
        v=y[t.index(prevdec)]; sy=[[prevdec,round(float(v),2)]]
        for mth in range(1,13):
            v=v+sav[mth-1] if additive else v*math.exp(sav[mth-1]); sy.append([f"{cy_}-{mth:02d}",round(float(v),2)])
    # seasonal direction accuracy (out of sample, since 2005)
    sh=sn=0
    for d,c in zip(tt,ch):
        if d<test_from: continue
        cc=[[] for _ in range(12)]
        for d2,c2 in zip(tt,ch):
            if d2[:4]>=d[:4]: break
            cc[int(d2[5:7])-1].append(c2)
        p=np.mean(cc[int(d[5:7])-1]) if cc[int(d[5:7])-1] else 0
        if p!=0: sn+=1; sh+=(p>0)==(c>0)
    # summary numbers
    f6=fwd[min(6,len(fwd)-1)][1]/y[-1]-1 if not additive else fwd[min(6,len(fwd)-1)][1]-y[-1]
    f12=fwd[12][1]/y[-1]-1 if not additive else fwd[12][1]-y[-1]
    s3=sum(sav[(int(add(t[-1],k)[5:7])-1)] for k in (1,2,3))
    tab=[]
    for k,(d,v) in enumerate(fwd[1:13],1):
        prev=fwd[k-1][1]; c=avg[slot(d)]
        tab.append(dict(m=d,v=round(float(v),2),chg=round(float(c if additive else (math.exp(c)-1)*100),2),
                        up=int(round(float(pos[slot(d)])*100)),sig=sig.get(d,""),year=int(slot(d)//12+1)))
    return dict(t=t[-60:],y=[round(float(v),2) for v in y[-60:]],
        back=[[d,round(float(v),2)] for d,v in back],fwd=[[d,round(float(v),2)] for d,v in fwd],
        sig=sig,pres=[round(float(v),2) for v in pres],now=int(slot(t[-1])),seas=[[round(a,2),round(b)] for a,b in seas],
        tab=tab,hit=int(hit),n=int(n),season=sy,sh=int(sh),sn=int(sn),f6=round(float(f6)*(1 if additive else 100),1),f12=round(float(f12)*(1 if additive else 100),1),s3=round(float(s3)*(1 if additive else 100),1),since=t[0][:4],last=t[-1],additive=additive)
sp=series("sp","1950-01")
gold=merged("gold_long","gold","1971-08")
cy=yoy(series("cpi"))
oil=series("wti_fred","1986-01") if have("wti_fred") else series("oil")
home=series("home","1975-01")
M={"sp":("S&P 500","index points",sp,False),"nasdaq":("NASDAQ Composite","index points",series("nasdaq"),False),"dji":("Dow Jones","index points",series("dji"),False),"tasi":("Saudi TASI","index points",series("tasi"),False),"silver":("Silver","US$ per ounce",series("silver"),False),"us10y":("US 10-year Treasury yield","%",[(d,v/ (10 if v>30 else 1)) for d,v in series("us10y")],True),"oil":("Crude oil (WTI)","US$ per barrel",oil,False),"home":("US home prices (Case-Shiller)","index points",home,False),"gold":("Gold","US$ per ounce",gold,False),"cpi":("US inflation","% over 12 months",cy,True)}
if have("fedfunds"): M["fedfunds"]=("Fed funds rate","%",series("fedfunds"),True)
if have("psx"): M["psx"]=("Pakistan KSE-100","index points",series("psx"),False)
M={k:v for k,v in M.items() if len(v[2])>=60}
out={}
for k,(name,unit,s,add_) in M.items():
    r=model(s,add_); r.update(name=name,unit=unit); out[k]=r
    print("  "+k,r["last"],"hit",r["hit"],"/",r["n"],"now slot",r["now"],"sig",r["sig"], r["tab"][0])
out={k:v for k,v in out.items()}
json.dump(out,open("work/data3.json","w"))
