import json
LWD=json.load(open('work/lw.json'))
CALLS=json.load(open('forecast_calls.json',encoding='utf-8'))
LW_CSS='<style>.lwfig{position:relative;height:360px;margin-top:8px}.lwfig svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}.lwfig svg text{font:12px Inter,sans-serif;fill:var(--mut)}.sc-Hit{color:var(--good)}.sc-Miss{color:var(--red)}.sc-Partly{color:var(--warn)}.sc-Ahead{color:var(--mut)}</style>'
_M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
def MM(a,b): return (_M[int(a[5:7])-1]+' '+a[:4]) if a==b else f"{_M[int(a[5:7])-1]}–{_M[int(b[5:7])-1]} {b[:4]}"
def LW_SECTION(k):
    d=LWD[k]; n={s:sum(1 for r in d['rows'] if r['score']==s) for s in ('Hit','Partly','Miss','Ahead')}
    rows=''.join(f'<tr><td><b>{r["label"]}</b></td><td>{"Rise" if r["typ"]=="up" else "Fall" if r["typ"]=="down" else "Low" if r["typ"]=="low" else "Sideways"}</td><td>{MM(r["a"],r["b"])}</td><td><b class="sc-{r["score"]}">{r["score"]}</b></td><td>{r["note"]}</td></tr>' for r in d['rows'])
    return f'''<section class="band mk" id="fva-{k}"><div class="wrap">
<h2>{d["name"]}: {CALLS["year"]} forecast vs actual</h2>
<p class="lede">Shaded windows: the {CALLS["year"]} forecast by {CALLS["source"]}, shown as periods of expected rise (green), fall (red) and the expected major low (blue line). Blue line: actual month-end price, latest {MM(d["last"],d["last"])} (month to date).</p>
<div class="lwfig" data-k="{k}"><svg role="img" aria-label="{d["name"]} 2026 actual price with forecast windows"></svg><div class="tip"></div></div>
<div class="scroll"><table class="stack"><thead><tr><th>Forecast window</th><th>Expected</th><th>Months</th><th>Result</th><th>What happened</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="small">Score so far: <b class="sc-Hit">{n["Hit"]} hit</b> · <b class="sc-Partly">{n["Partly"]} partly</b> · <b class="sc-Miss">{n["Miss"]} miss</b>{" · "+str(n["Ahead"])+" ahead" if n["Ahead"] else ""}. Updated each month with the latest close.</p>
</div></section>'''
LW_JS='<script>{const LW='+json.dumps(LWD)+r''';
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
document.querySelectorAll('.lwfig').forEach(box=>{const d=LW[box.dataset.k],svg=box.querySelector('svg'),tip=box.querySelector('.tip');
 const L=[...d.m];while(L[L.length-1]<'2026-12'){const s=L[L.length-1];let y=+s.slice(0,4),m=+s.slice(5,7)+1;if(m>12){m=1;y++}L.push(y+'-'+String(m).padStart(2,'0'))}
 const N=L.length;
 const draw=()=>{const W=svg.clientWidth,H=svg.clientHeight;if(!W)return;const nar=W<520,ml=nar?50:64,mr=12,mt=30,mb=26,pw=W-ml-mr,ph=H-mt-mb;
  const X=i=>ml+(i+.5)/N*pw,cw=pw/N;let lo=Math.min(...d.v)*.94,hi=Math.max(...d.v)*1.04;const Y=v=>mt+ph-(v-lo)/(hi-lo)*ph;let g='';
  d.rows.forEach(r=>{const i0=L.indexOf(r.a),i1=L.indexOf(r.b);if(i0<0)return;const x0=ml+i0*cw,x1=ml+(i1+1)*cw;
   if(r.typ==='low'){const x=(x0+x1)/2;g+=`<line x1="${x}" x2="${x}" y1="${mt}" y2="${mt+ph}" stroke="var(--s1)" stroke-width="2" stroke-dasharray="5 4"/><text x="${x}" y="${mt-8}" text-anchor="middle" style="fill:var(--s1);font-weight:700">${nar?'Low':'Expected low'}</text>`;return}
   const c=r.typ==='up'?'var(--good)':r.typ==='down'?'var(--red)':'var(--mut)';g+=`<rect x="${x0}" y="${mt}" width="${x1-x0}" height="${ph}" fill="${c}" opacity=".13"/>`;
   if(!nar||x1-x0>60)g+=`<text x="${(x0+x1)/2}" y="${mt+16}" text-anchor="middle" style="fill:${c};font-weight:700">${r.typ==='up'?'Rise':r.typ==='down'?'Fall':'Flat'}</text>`});
  const tk=[lo+(hi-lo)*.1,(lo+hi)/2,hi-(hi-lo)*.1];tk.forEach(v=>{g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${ml-6}" y="${Y(v)+4}" text-anchor="end">${v>=1000?Math.round(v).toLocaleString('en-US'):v.toFixed(v<100?1:0)}</text>`});
  L.forEach((m,i)=>{if(!nar||i%2===0)g+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${MON[+m.slice(5)-1]}${m.slice(5)==='01'?" '"+m.slice(2,4):''}</text>`});
  let p='';d.v.forEach((v,i)=>{p+=(i?'L':'M')+X(i)+' '+Y(v)});g+=`<path d="${p}" fill="none" stroke="var(--s1)" stroke-width="2.5"/>`;
  d.v.forEach((v,i)=>{g+=`<circle cx="${X(i)}" cy="${Y(v)}" r="3.5" fill="var(--s1)" stroke="var(--bg)" stroke-width="1.5"/>`});
  g+=`<line class="cx" y1="${mt}" y2="${mt+ph}" stroke="var(--mut)" style="display:none"/>`;svg.innerHTML=g;
  svg.onpointermove=e=>{const r=svg.getBoundingClientRect(),i=Math.max(0,Math.min(d.v.length-1,Math.floor((e.clientX-r.left-ml)/cw)));const cx=svg.querySelector('.cx');cx.setAttribute('x1',X(i));cx.setAttribute('x2',X(i));cx.style.display='';
   const w=d.rows.find(r=>r.a<=L[i]&&L[i]<=r.b);tip.innerHTML=`<b>${MON[+L[i].slice(5)-1]} ${L[i].slice(0,4)}</b><br>Close: ${d.v[i]>=1000?Math.round(d.v[i]).toLocaleString('en-US'):d.v[i].toFixed(2)}`+(w?`<br>Forecast: ${w.label}`:'');tip.style.display='block';tip.style.left=Math.min(X(i)+12,W-170)+'px';tip.style.top=mt+'px'};
  svg.onpointerleave=()=>{tip.style.display='none'}};
 new ResizeObserver(draw).observe(svg);draw()})}</script>'''
