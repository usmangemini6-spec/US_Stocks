import csv,json
from cdata import CD
def add(m,k): y,mm=int(m[:4]),int(m[5:7])-1+k; return f"{y+mm//12}-{mm%12+1:02d}"
def closes(k):
    c={r["Date"][:7]:float(r["Close"]) for r in csv.DictReader(open(CD+k+".csv")) if r["Close"]}
    ms=sorted(c); m=ms[0]
    while m<ms[-1]:                      # fill rare missing months with the previous close
        n=add(m,1)
        if n not in c: c[n]=c[m]
        m=n
    return c
MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
# Forecast windows for 2026 (Larry Williams, Forecast 2026 report, Dec 2025, as summarised by month)
CALLS=json.load(open("forecast_calls.json",encoding="utf-8"))
PH={k:[tuple(x) for x in v] for k,v in CALLS["windows"].items()}
NAME={"sp":"S&P 500","nasdaq":"NASDAQ","gold":"Gold","silver":"Silver"}
out={}
for k,ph in PH.items():
    import os
    if not os.path.exists(CD+k+'.csv'): continue
    c=closes(k); last=max(c); months=[m for m in sorted(c) if CALLS["chart_start"]<=m<=last]
    rows=[]
    for a,b,typ,label in ph:
        if a>last: rows.append(dict(a=a,b=b,typ=typ,label=label,score="Ahead",note="Not reached yet"));continue
        b2=min(b,last); p0=c[add(a,-1)]; p1=c[b2]; ch=(p1/p0-1)*100
        win=[c[m] for m in sorted(c) if a<=m<=b2]
        if typ=="up":
            peak=(max(win)/p0-1)*100
            sc="Hit" if ch>0 else ("Partly" if peak>=3 else "Miss")
            note=f"{'+' if ch>=0 else ''}{ch:.1f}% over the window"+(f" (peak +{peak:.1f}% before falling back)" if sc=="Partly" else "")
        elif typ=="down":
            trough=(min(win)/p0-1)*100
            sc="Hit" if ch<0 else ("Partly" if trough<=-3 else "Miss")
            note=f"{'+' if ch>=0 else ''}{ch:.1f}% over the window"+(f" (fell {trough:.1f}% first, then recovered)" if sc=="Partly" else "")
        elif typ=="low":
            rng=[m for m in sorted(c) if add(a,-4)<=m<=add(a,2) and m<=last]
            lowm=min(rng,key=lambda m:c[m])
            sc="Hit" if lowm==a else "Miss"
            note=f"Lowest month-end of {MON[int(add(a,-4)[5:7])-1]}–{MON[int(add(a,2)[5:7])-1]} was {MON[int(lowm[5:7])-1]}"+("" if sc=="Hit" else f", not {MON[int(a[5:7])-1]}")
        else:
            sc="Ahead" if b>last else ("Hit" if abs(ch)<3 else "Miss"); note=f"{ch:+.1f}%"
        if b>last and sc!="Ahead": note+=" (window still open; latest close used)"
        rows.append(dict(a=a,b=b,typ=typ,label=label,score=sc,note=note))
    out[k]=dict(name=NAME[k],m=months,v=[round(c[m],2) for m in months],rows=rows,last=last)
    print('  '+k,[(r['label'],r['score'],r['note']) for r in rows])
json.dump(out,open('work/lw.json','w'))
