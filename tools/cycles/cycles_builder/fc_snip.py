import json
FC=json.load(open('work/fc.json'))
from cdata import daily_last
_L=daily_last('sp')
FC['live']={'m':_L[0][:7],'v':round(_L[1],2),'d':_L[0]} if _L else None
import datetime as _dt
_Y0=_dt.datetime.now().year-1
FC_HTML='''<section class="band mk" id="forecast"><div class="wrap">
<h2>S&amp;P 500 cycle forecast %Y0%–%Y2%</h2>
<p class="lede">One combined forecast line from three cycles: the 4-year presidential cycle, the 10-year decade pattern (since 1871) and the within-year pattern. Top: the actual index. Bottom: the forecast line, made only from data before %Y0%, so %Y0%–%Y1% is a real test.</p>
<div class="fcwrap"><svg id="fc" role="img" aria-label="S&amp;P 500 actual vs cycle forecast with forecast turning points"></svg><div class="tip"></div></div>
<div class="legend"><span><i></i>S&amp;P 500 actual (monthly average)</span><span><i class="p"></i>Cycle forecast (shape and timing, not price level)</span><span style="color:var(--good)">■ forecast rising</span><span style="color:var(--red)">■ forecast falling</span></div>
<div class="scroll"><table class="stack" id="fctab"><thead><tr><th>Forecast turning point</th><th>Type</th><th>What actually happened</th></tr></thead><tbody></tbody></table></div>
<p class="small">The combined forecast got the monthly direction right in <b>%HIT%%</b> of months since 2005 (each year tested using only earlier data). The latest close is marked on the chart in red.</p>
</div></section>'''.replace('%Y0%',str(_Y0)).replace('%Y1%',str(_Y0+1)).replace('%Y2%',str(_Y0+2)).replace('%HIT%',str(round(FC['hit']/FC['n']*100)))
FC_JS='<script>{const F=%s;' % json.dumps(FC) + r'''
const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],fm=s=>MON[+s.slice(5,7)-1]+' '+s.slice(0,4);
const svg=document.getElementById('fc'),box=svg.parentElement,tip=box.querySelector('.tip'),M=F.m,N=M.length,LV=F.live,live=LV?{i:M.indexOf(LV.m),v:LV.v}:null;
const notes={};
document.querySelector('#fctab tbody').innerHTML=F.tp.map(([m,k])=>`<tr><td><b>${fm(m)}</b></td><td><span class="badge ${k==='Low'?'good':'weak'}">${k==='Low'?'Low (buy window)':'High (sell window)'}</span></td><td>${notes[m]||(LV&&m<=LV.m?'Passed: compare with the actual line above':'Ahead')}</td></tr>`).join('');
function draw(){const W=svg.clientWidth,H=svg.clientHeight;if(!W)return;const nar=W<520,ml=nar?46:60,mr=14,top=24,gap=34,ph1=(H-top-gap-48)*0.58,ph2=(H-top-gap-48)*0.42,y2=top+ph1+gap;
 const X=i=>ml+i/(N-1)*(W-ml-mr);const av=F.a.filter(v=>v!=null).concat(live?[live.v]:[]);let lo=Math.min(...av)*.95,hi=Math.max(...av)*1.03;const Y1=v=>top+ph1-(v-lo)/(hi-lo)*ph1;
 const fl=Math.min(...F.f),fh=Math.max(...F.f),Y2=v=>y2+ph2-(v-fl)/(fh-fl||1)*ph2;let g='';
 for(let i=0;i<N-1;i++){const up=F.f[i+1]>=F.f[i];g+=`<rect x="${X(i)}" y="${y2}" width="${X(i+1)-X(i)}" height="${ph2}" fill="${up?'var(--good)':'var(--red)'}" opacity=".10"/>`}
 [lo,(lo+hi)/2,hi].forEach(v=>{g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y1(v)}" y2="${Y1(v)}" stroke="var(--line)"/><text x="${ml-6}" y="${Y1(v)+4}" text-anchor="end">${Math.round(v).toLocaleString('en-US')}</text>`});
 g+=`<text x="${ml}" y="${top-8}" style="font-weight:600;fill:var(--ink)">Actual S&amp;P 500</text><text x="${ml}" y="${y2-8}" style="font-weight:600;fill:var(--ink)">Cycle forecast</text>`;
 M.forEach((m,i)=>{if(m.slice(5)==='01'||(!nar&&m.slice(5)==='07'))g+=`<text x="${X(i)}" y="${H-4}" text-anchor="middle">${m.slice(5)==='01'?m.slice(0,4):'Jul'}</text>`});
 F.tp.forEach(([m,k])=>{const i=M.indexOf(m),x=X(i),c=k==='Low'?'var(--good)':'var(--red)';g+=`<line x1="${x}" x2="${x}" y1="${top}" y2="${y2+ph2}" stroke="${c}" stroke-dasharray="4 4" stroke-width="1.5"/><text x="${x}" y="${y2+ph2+14}" text-anchor="middle" style="fill:${c};font-weight:700">${k} ${nar?m.slice(5):MON[+m.slice(5)-1]+' '+m.slice(2,4)}</text>`});
 let p='';F.a.forEach((v,i)=>{if(v!=null)p+=(p?'L':'M')+X(i)+' '+Y1(v)});g+=`<path d="${p}" fill="none" stroke="var(--s1)" stroke-width="2.5"/>`;
 if(live&&live.i>=0)g+=`<circle cx="${X(live.i)}" cy="${Y1(live.v)}" r="5" fill="var(--red)"/><text x="${X(live.i)+8}" y="${Y1(live.v)+4}" style="fill:var(--red);font-weight:600">${Math.round(live.v).toLocaleString('en-US')} (${LV.d.slice(8)}/${LV.d.slice(5,7)})</text>`;
 let q='';F.f.forEach((v,i)=>{q+=(i?'L':'M')+X(i)+' '+Y2(v)});g+=`<path d="${q}" fill="none" stroke="var(--s2)" stroke-width="2.5"/>`;
 const now=LV?M.indexOf(LV.m):-1;if(now>=0)g+=`<line x1="${X(now)}" x2="${X(now)}" y1="${top}" y2="${y2+ph2}" stroke="var(--ink)" stroke-width="1"/><text x="${X(now)+4}" y="${top+10}" style="fill:var(--ink);font-weight:600">Today</text>`;
 g+=`<line class="cx" y1="${top}" y2="${y2+ph2}" stroke="var(--mut)" style="display:none"/>`;svg.innerHTML=g;
 svg.onpointermove=e=>{const r=svg.getBoundingClientRect(),i=Math.max(0,Math.min(N-1,Math.round((e.clientX-r.left-ml)/(W-ml-mr)*(N-1))));const cx=svg.querySelector('.cx');cx.setAttribute('x1',X(i));cx.setAttribute('x2',X(i));cx.style.display='';
  tip.innerHTML=`<b>${fm(M[i])}</b>`+(F.a[i]!=null?`<br>Actual: ${Math.round(F.a[i]).toLocaleString('en-US')}`:'')+`<br>Forecast: ${i&&F.f[i]>=F.f[i-1]?'rising':'falling'}`;tip.style.display='block';tip.style.left=Math.min(X(i)+12,W-160)+'px';tip.style.top=top+'px'};
 svg.onpointerleave=()=>{tip.style.display='none'}}
new ResizeObserver(draw).observe(svg);draw()}</script>'''
FC_CSS='<style>.fcwrap{position:relative;height:520px;margin-top:10px}.fcwrap svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}.fcwrap svg text{font:12px Inter,sans-serif;fill:var(--mut)}@media(max-width:600px){.fcwrap{height:440px}}</style>'
