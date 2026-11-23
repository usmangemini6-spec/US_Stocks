const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fm=s=>MON[+s.slice(5,7)-1]+' '+s.slice(0,4), fs=s=>MON[+s.slice(5,7)-1]+" '"+s.slice(2,4);
const num=(v,u)=>u.startsWith('%')?v.toFixed(2)+'%':(u.startsWith('US$')?'$':'')+(v>=1000?Math.round(v).toLocaleString('en-US'):v.toFixed(v>=100?1:2));
const pct=v=>(v>0?'+':'')+v.toFixed(1)+'%';
const PY=['Post-election year','Midterm year','Pre-election year','Election year'];
const TERM0=2025; // current US presidential term: Jan 2025 to Jan 2029
const pyl=s=>`Year ${Math.floor(s/12)+1} of 4 (${TERM0+Math.floor(s/12)}, ${PY[Math.floor(s/12)].replace(' year','').toLowerCase()})`;
function timetable(d){
 const p=[0,...d.pres],cal=d.seas.map(x=>x[0]),rows=[],nowY=+d.last.slice(0,4),nowM=+d.last.slice(5,7),st=y=>y<nowY?'Done':y===nowY?'<b>Now</b>':'Ahead';
 const ch=(a,b)=>d.additive?(b-a):((1+b/100)/(1+a/100)-1)*100,f=v=>d.additive?(v>0?'+':'')+v.toFixed(2)+' pts':pct(v);
 if(d.lt){const T=d.lt;rows.push(`<tr class="grp"><td><b>Long-term life cycle</b></td><td class="n">${T.P} years</td><td>${fm(T.last_low)} (last low)</td><td>${T.last_high>T.last_low?fm(T.last_high)+' (passed)':T.next_high?fm(T.next_high):'after 2040'}</td><td>${T.next_low?fm(T.next_low):'after 2040'}</td><td>${T.next_low?fm(T.next_low):'after 2040'}</td><td>—</td><td>${T.last_high>T.last_low?'Falling half':'Rising half'}</td></tr>`)}
 // whole presidential term
 const dtr=(arr,a,b,i)=>arr[i]-(arr[a]+(arr[b]-arr[a])*(i-a)/(b-a));let mx=1,mn=1;for(let i=1;i<=48;i++){if(dtr(p,0,48,i)>dtr(p,0,48,mx))mx=i;if(dtr(p,0,48,i)<dtr(p,0,48,mn))mn=i}
 const dt=i=>MON[(i-1)%12]+' '+(TERM0+Math.floor((i-1)/12));
 rows.push(`<tr class="grp"><td><b>Presidential cycle (whole term)</b></td><td class="n">4 years</td><td>Jan 2025</td><td>${dt(mx)}</td><td>${dt(mn)}</td><td>Dec 2028</td><td class="n">${f(p[48])}</td><td>${pyl(d.now)}</td></tr>`);
 for(let y=0;y<4;y++){let a=y*12,hi=a+1,lo=a+1;for(let i=a+1;i<=a+12;i++){if(dtr(p,a,a+12,i)>dtr(p,a,a+12,hi))hi=i;if(dtr(p,a,a+12,i)<dtr(p,a,a+12,lo))lo=i}
  rows.push(`<tr><td>&nbsp;&nbsp;Year ${y+1}: ${PY[y].replace(' year','')}</td><td class="n">12 months</td><td>Jan ${TERM0+y}</td><td>${MON[(hi-1)%12]} ${TERM0+y}</td><td>${MON[(lo-1)%12]} ${TERM0+y}</td><td>Dec ${TERM0+y}</td><td class="n">${f(ch(p[a],p[a+12]))}</td><td>${st(TERM0+y)}</td></tr>`)}
 // within-year cycle
 let c=0,cum=[0];cal.forEach(v=>{c+=v;cum.push(c)});let h=1,l=1;for(let i=1;i<=12;i++){if(dtr(cum,0,12,i)>dtr(cum,0,12,h))h=i;if(dtr(cum,0,12,i)<dtr(cum,0,12,l))l=i}
 const best=cal.indexOf(Math.max(...cal)),worst=cal.indexOf(Math.min(...cal));
 rows.push(`<tr class="grp"><td><b>Within-year cycle</b></td><td class="n">12 months</td><td>Jan ${nowY}</td><td>${MON[h-1]} ${nowY}</td><td>${MON[l-1]} ${nowY}</td><td>Dec ${nowY}</td><td class="n">${f(cum[12])}</td><td>${MON[nowM-1]} (month ${nowM} of 12)</td></tr>`);
 return `<h3>Cycle timetable</h3><p class="small">When each cycle started, when it typically peaks and bottoms, and when it ends. Peaks and bottoms are the months where the average path of each cycle is highest and lowest compared with its own trend, so they are typical months, not exact dates.</p>
 <div class="scroll"><table class="stack tt"><thead><tr><th>Cycle</th><th class="n">Length</th><th>Started</th><th>Typical peak</th><th>Typical bottom</th><th>Ends</th><th class="n">Average change</th><th>Where we are</th></tr></thead><tbody>${rows.join('')}</tbody></table></div>
 <p class="small">Best calendar month: <b>${MON[best]}</b> (${f(cal[best])} on average); weakest: <b>${MON[worst]}</b> (${f(cal[worst])}).</p>`}
function niceLog(a,b){const o=[];for(let e=Math.floor(Math.log10(a));e<=Math.ceil(Math.log10(b));e++)for(const m of (Math.log10(b/a)<1.3?[1,2,3,5]:[1,2,5])){const v=m*10**e;if(v>=a&&v<=b)o.push(v)}return o.length>8?o.filter(v=>/^1|^5/.test(String(v))):o}
function niceLin(a,b,n=5){const r=(b-a)||1,st=10**Math.floor(Math.log10(r/n)),m=[1,2,2.5,5,10].find(x=>r/(x*st)<=n)*st,o=[];for(let v=Math.ceil(a/m)*m;v<=b+1e-9;v+=m)o.push(+v.toFixed(6));return o}
// generic line chart: labels, series [{name,data,color,dash,dots}], marks [{i,y,kind}], bands [{from,to,label}], here index
function plot(box,cfg){
 const svg=box.querySelector('svg'),tip=box.querySelector('.tip');
 const draw=()=>{const W=svg.clientWidth,H=svg.clientHeight;if(!W)return;const nar=W<520,L=cfg.labels,N=L.length;
  const vals=[];cfg.series.forEach(s=>s.data.forEach(v=>v!=null&&vals.push(v)));let lo=Math.min(...vals),hi=Math.max(...vals);if(cfg.log){lo*=.85;hi*=1.15}else{const pad=(hi-lo)*.12||1;lo-=pad;hi+=pad}if(cfg.zero){lo=Math.min(lo,0);hi=Math.max(hi,0)}
  const ml=nar?46:62,mr=12,mt=cfg.bands?30:16,mb=28,pw=W-ml-mr,ph=H-mt-mb,X=i=>ml+(N<2?0:i/(N-1)*pw),Y=cfg.log?v=>mt+ph-Math.log(v/lo)/Math.log(hi/lo)*ph:v=>mt+ph-(v-lo)/(hi-lo)*ph;let g='';
  (cfg.bands||[]).forEach((b,j)=>{const x0=X(b.from)-(j?pw/(N-1)/2:0),x1=X(b.to)+(j<cfg.bands.length-1?pw/(N-1)/2:0);g+=`<rect x="${x0}" y="${mt}" width="${x1-x0}" height="${ph}" fill="${j%2?'var(--panel)':'transparent'}" opacity=".55"/><text x="${(x0+x1)/2}" y="${mt-10}" text-anchor="middle">${nar?b.short:b.label}</text>`});
  (cfg.log?niceLog(lo,hi):niceLin(lo,hi,nar?4:6)).forEach(v=>{g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${ml-6}" y="${Y(v)+4}" text-anchor="end">${cfg.tick(v)}</text>`});
  if(cfg.zero)g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--mut)"/>`;
  const every=Math.ceil(N/(nar?5:12));L.forEach((l,i)=>{if(cfg.xyears?(i>0&&l.slice(0,4)!==L[i-1].slice(0,4)&&+l.slice(0,4)%cfg.xyears(nar)===0):(i%every===0||i===N-1&&N<14))g+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${cfg.xl(l,i)}</text>`});
  if(cfg.here!=null){const x=X(cfg.here);g+=`<line x1="${x}" x2="${x}" y1="${mt}" y2="${mt+ph}" stroke="var(--red)" stroke-dasharray="2 3" stroke-width="1.5"/><text x="${x+4}" y="${mt+12}" style="fill:var(--red);font-weight:600">${cfg.hereLabel||'Now'}</text>`}
  cfg.series.forEach(s=>{let d='',pen=0;s.data.forEach((v,i)=>{if(v==null){pen=0;return}d+=(pen?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1);pen=1});
   g+=`<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2" ${s.dash?'stroke-dasharray="6 4"':''} stroke-linejoin="round"/>`;
   if(s.dots)s.data.forEach((v,i)=>{if(v!=null)g+=`<circle cx="${X(i)}" cy="${Y(v)}" r="3.5" fill="${s.color}" stroke="var(--bg)" stroke-width="1.5"/>`})});
  (cfg.marks||[]).forEach(m=>{const x=X(m.i),y=Y(m.y),b=m.kind==='buy',c=b?'var(--good)':'var(--red)',yy=b?y+14:y-14;
   g+=`<path d="M${x-7} ${b?yy+10:yy-10}L${x+7} ${b?yy+10:yy-10}L${x} ${yy}Z" fill="${c}"/><text x="${x}" y="${b?yy+24:yy-14}" text-anchor="middle" style="fill:${c};font-weight:600">${b?'Buy':'Sell'}</text>`});
  g+=`<line class="cx" y1="${mt}" y2="${mt+ph}" stroke="var(--mut)" style="display:none"/>`;svg.innerHTML=g;
  svg.onpointermove=e=>{const r=svg.getBoundingClientRect(),i=Math.max(0,Math.min(N-1,Math.round((e.clientX-r.left-ml)/pw*(N-1))));const cx=svg.querySelector('.cx');cx.setAttribute('x1',X(i));cx.setAttribute('x2',X(i));cx.style.display='';
   tip.innerHTML=`<b>${cfg.tt(L[i],i)}</b>`+cfg.series.map(s=>s.data[i]==null?'':`<br>${s.name}: ${cfg.val(s.data[i])}`).join('');tip.style.display='block';const tw=tip.offsetWidth;tip.style.left=(X(i)+12+tw>W?X(i)-tw-12:X(i)+12)+'px';tip.style.top=mt+'px'};
  svg.onpointerleave=()=>{tip.style.display='none';svg.querySelector('.cx').style.display='none'}};
 new ResizeObserver(draw).observe(svg);draw()}
