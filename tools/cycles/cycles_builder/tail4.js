{
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
 if(d.lt){const T=d.lt;rows.push(`<tr class="grp"><td><b>Long-term life cycle</b></td><td class="n">${T.P} years</td><td>${T.last_low?fm(T.last_low)+' (last low)':'before '+d.lt.start.slice(0,4)}</td><td>${T.last_high&&T.last_high>(T.last_low||'')?fm(T.last_high)+' (passed)':T.next_high?fm(T.next_high):'after 2040'}</td><td>${T.next_low?fm(T.next_low):'after 2040'}</td><td>${T.next_low?fm(T.next_low):'after 2040'}</td><td>—</td><td>${T.last_high&&T.last_high>(T.last_low||'')?'Falling half':'Rising half'}</td></tr>`)}
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
  const vals=[];cfg.series.forEach(s=>s.data.forEach(v=>v!=null&&vals.push(v)));(cfg.hlines||[]).forEach(h=>vals.push(h.y));let lo=Math.min(...vals),hi=Math.max(...vals);if(cfg.log){lo*=.85;hi*=1.15}else{const pad=(hi-lo)*.12||1;lo-=pad;hi+=pad}if(cfg.zero){lo=Math.min(lo,0);hi=Math.max(hi,0)}
  const ml=nar?46:62,mr=12,mt=cfg.bands?30:16,mb=28,pw=W-ml-mr,ph=H-mt-mb,X=i=>ml+(N<2?0:i/(N-1)*pw),Y=cfg.log?v=>mt+ph-Math.log(v/lo)/Math.log(hi/lo)*ph:v=>mt+ph-(v-lo)/(hi-lo)*ph;let g='';
  (cfg.bands||[]).forEach((b,j)=>{const x0=X(b.from)-(j?pw/(N-1)/2:0),x1=X(b.to)+(j<cfg.bands.length-1?pw/(N-1)/2:0);g+=`<rect x="${x0}" y="${mt}" width="${x1-x0}" height="${ph}" fill="${j%2?'var(--panel)':'transparent'}" opacity=".55"/><text x="${(x0+x1)/2}" y="${mt-10}" text-anchor="middle">${nar?b.short:b.label}</text>`});
  (cfg.log?niceLog(lo,hi):niceLin(lo,hi,nar?4:6)).forEach(v=>{g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text x="${ml-6}" y="${Y(v)+4}" text-anchor="end">${cfg.tick(v)}</text>`});
  if(cfg.zero)g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--mut)"/>`;
  (cfg.hlines||[]).forEach(h=>{g+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(h.y)}" y2="${Y(h.y)}" stroke="${h.color||'var(--s2)'}" stroke-dasharray="4 4" stroke-width="1.2"/><text x="${W-mr-4}" y="${Y(h.y)-4}" text-anchor="end" style="fill:${h.color||'var(--s2)'};font-weight:600">${h.label}</text>`});
  const every=Math.ceil(N/Math.max(3,Math.min(12,Math.floor(pw/70))));L.forEach((l,i)=>{if(cfg.xyears?(i>0&&l.slice(0,4)!==L[i-1].slice(0,4)&&+l.slice(0,4)%cfg.xyears(nar)===0):(i%every===0||i===N-1&&N<14))g+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${cfg.xl(l,i)}</text>`});
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
function bars(box,rows){ // rows [{label,v,up}]
 const mx=Math.max(...rows.map(r=>Math.abs(r.v)))||1;
 box.innerHTML=rows.map(r=>`<div class="br"><span>${r.label}</span><div class="bt"><i style="${r.v>=0?'left:50%':'right:50%'};width:${Math.abs(r.v)/mx*50}%;background:${r.v>=0?'var(--good)':'var(--red)'}"></i></div><b>${r.f}</b><em>${r.up}% up</em></div>`).join('')}
function verdict(h,n){const r=n?h/n:0;return r>=.58?['good','Useful',r]:r>=.53?['mid','Weak edge',r]:['weak','No edge',r]}
function stance(d){const [cl,w,r]=verdict(d.hit,d.n);if(d.additive)return {t:`Cycle view: ${d.f12>0.3?'inflation drifting up':d.f12<-0.3?'inflation easing':'flat'} over the next 12 months`,b:'Inflation has no reliable monthly cycle (direction right in '+Math.round(r*100)+'% of months), so watch the actual data, not the cycle.'};
 const buys=Object.entries(d.sig).filter(e=>e[1]==='Buy window').map(e=>e[0]),sells=Object.entries(d.sig).filter(e=>e[1]==='Sell window').map(e=>e[0]);
 const view=r<.53?'Neutral (cycle unreliable)':d.f12>5?'Positive: buy on dips':d.f12>0?'Mildly positive: hold, add on dips':'Cautious: hold, reduce into strength';
 return {t:'Cycle view: '+view,b:`Presidential cycle projects <b>${pct(d.f6)}</b> over 6 months and <b>${pct(d.f12)}</b> over 12 months. The within-year cycle gives <b>${pct(d.s3)}</b> for the next 3 months. Next buy window: <b>${buys[0]?fm(buys[0]):'none in 2 years'}</b>; next sell window: <b>${sells[0]?fm(sells[0]):'none in 2 years'}</b>. ${r<.53?'This market has followed the cycle only '+Math.round(r*100)+'% of months, so treat it as a weak hint.':'Direction was right in '+Math.round(r*100)+'% of months since 2005, tested without hindsight.'}`}}

function fibo(d){const y=d.y,t=d.t;let hi=0,lo=0;y.forEach((v,i)=>{if(v>y[hi])hi=i;if(v<y[lo])lo=i});
 const H=y[hi],Lw=y[lo],R=H-Lw,up=hi>lo,last=y[y.length-1];
 const lv=up?[[0,H],[23.6,H-.236*R],[38.2,H-.382*R],[50,H-.5*R],[61.8,H-.618*R],[78.6,H-.786*R],[100,Lw],[127.2,H+.272*R],[161.8,H+.618*R]]
            :[[0,Lw],[23.6,Lw+.236*R],[38.2,Lw+.382*R],[50,Lw+.5*R],[61.8,Lw+.618*R],[78.6,Lw+.786*R],[100,H],[127.2,Lw-.272*R],[161.8,Lw-.618*R]];
 return {up,H,Lw,hiD:t[hi],loD:t[lo],last,lv:lv.filter(x=>x[1]>0)}}
function fibSection(d,val){const f=fibo(d);
 const name=r=>r===0?(f.up?'Swing high':'Swing low'):r===100?(f.up?'Swing low':'Swing high'):r>100?`${r}% extension (${f.up?'target above high':'target below low'})`:`${r}% retracement`;
 const sorted=[...f.lv].sort((a,b)=>b[1]-a[1]);let below=null,above=null;sorted.forEach(x=>{if(x[1]>=f.last)above=x;else if(!below)below=x});
 const rows=sorted.map(x=>`<tr${x===above||x===below?' class="grp"':''}><td>${name(x[0])}</td><td class="n">${val(x[1])}</td><td class="n">${pct((x[1]/f.last-1)*100)}</td><td>${x===above?'Nearest level above (resistance)':x===below?'Nearest level below (support)':''}</td></tr>`).join('');
 return `<h3>Fibonacci levels</h3><p class="small">From the last 5 years: swing ${f.up?'low':'high'} ${val(f.up?f.Lw:f.H)} (${fm(f.up?f.loD:f.hiD)}) to swing ${f.up?'high':'low'} ${val(f.up?f.H:f.Lw)} (${fm(f.up?f.hiD:f.loD)}), monthly averages. In ${f.up?'an uptrend, retracements are where pullbacks often find support':'a downtrend, retracements are where rebounds often stall'}; extensions are common targets if the move continues. Price now ${val(f.last)} (${fm(d.last)}).</p>
 <div class="two"><div class="fig sm"><svg role="img" aria-label="${d.name} with Fibonacci levels"></svg><div class="tip"></div></div>
 <div class="scroll"><table class="stack"><thead><tr><th>Level</th><th class="n">Price</th><th class="n">From now</th><th>Role</th></tr></thead><tbody>${rows}</tbody></table></div></div>`}
const order=window.KEYS||Object.keys(D),PAGE={sp:'us-stocks.html',nasdaq:'us-stocks.html',dji:'us-stocks.html',gold:'gold.html',silver:'silver.html',tasi:'tasi.html',cpi:'rates.html',us10y:'rates.html',oil:'oil.html',home:'real-estate.html'},MAIN=document.getElementById('main');
if(document.getElementById('nav'))document.getElementById('nav').innerHTML=order.map(k=>`<a href="#m-${k}">${D[k].name}</a>`).join('');
if(document.getElementById('sum'))document.getElementById('sum').innerHTML=order.map(k=>{const d=D[k],s=stance(d),[cl,w]=verdict(d.hit,d.n);return `<tr><td><a href="${PAGE[k]}#m-${k}">${d.name}</a></td><td class="n">${num(d.y[d.y.length-1],d.unit)}</td><td>${pyl(d.now)}</td><td class="n">${d.additive?(d.f12>0?'+':'')+d.f12.toFixed(1)+' pts':pct(d.f12)}</td><td>${s.t.replace('Cycle view: ','')}</td><td><span class="badge ${cl}">${w}</span></td></tr>`}).join('')+document.getElementById('sum').innerHTML;
if(MAIN)order.forEach(k=>{const d=D[k],u=d.unit,s=stance(d),[cl,w,r]=verdict(d.hit,d.n),[scl,sw,sr]=verdict(d.sh,d.sn),val=v=>d.additive?v.toFixed(2)+'%':num(v,u);
 const el=document.createElement('section');el.className='band mk';el.id='m-'+k;
 el.innerHTML=`<div class="wrap"><h2>${d.name}</h2><p class="small">Latest ${fm(d.last)}: <b>${val(d.y[d.y.length-1])}</b> · Presidential cycle: ${pyl(d.now)}, month ${d.now+1} of 48 · data since ${d.since}</p>
 <div class="view"><b>${s.t}</b><p>${s.b}</p></div>
 ${timetable(d)}
 ${d.additive?'':fibSection(d,val)}
 ${d.lt?`<h3>1. Long-term life cycle, ${d.lt.start.slice(0,4)} to 2040</h3><p class="small">The dominant long wave found in ${d.since<d.lt.start?'':''}the full history: about <b>${d.lt.P} years</b> from low to low. ${d.lt.last_high?'Last cycle high '+fm(d.lt.last_high)+', ':''}${d.lt.last_low?'last low '+fm(d.lt.last_low)+';':''} ${!d.lt.next_low&&!d.lt.next_high?'no turn projected before 2040':'next '+(d.lt.next_low&&(!d.lt.next_high||d.lt.next_low<d.lt.next_high)?'low around <b>'+fm(d.lt.next_low)+'</b>':'high around <b>'+fm(d.lt.next_high)+'</b>')}. It matched ${d.lt.hits} of ${d.lt.n} past low${d.lt.n==1?'':'s'} <span class="badge ${d.lt.n>=3&&d.lt.hits/d.lt.n>=.6&&d.lt.r2>=.3?'good':d.lt.r2>=.3?'mid':'weak'}">${d.lt.n>=3&&d.lt.hits/d.lt.n>=.6&&d.lt.r2>=.3?'Useful':d.lt.r2>=.3?'Weak edge':'No edge'}</span> and explains ${Math.round(d.lt.r2*100)}% of the swings around the trend. Long waves repeat only a few times in the data, so use them for the big picture, not for timing trades.</p>
 <div class="fig"><svg role="img" aria-label="${d.name} long-term cycle"></svg><div class="tip"></div></div>
 <div class="legend"><span><i></i>Actual (quarterly)</span><span><i class="p"></i>Long cycle fitted to history</span><span><i class="p" style="border-top-color:var(--s3)"></i>Projected from now</span></div>`:''}
 <h3>2. Actual vs projection, month by month</h3><p class="small">Orange from ${fm(d.back[0][0])}: what the presidential cycle projected at that time (using only earlier data), then the projection forward from the latest month.</p>
 <div class="fig"><svg role="img" aria-label="${d.name} actual vs projection"></svg><div class="tip"></div></div>
 <div class="legend"><span><i></i>Actual</span><span><i class="p"></i>Projected back then</span><span><i class="p" style="border-top-color:var(--s3)"></i>Projection from now</span><span style="color:var(--good)">▲ Buy window</span><span style="color:var(--red)">▼ Sell window</span></div>
 <div class="two"><div><h3>3. Presidential cycle: average path over 4 years</h3><p class="small">Average ${d.additive?'change':'% gain'} through a presidential term since ${d.since}. Red line: where we are now. Direction right in ${Math.round(r*100)}% of months since 2005 <span class="badge ${cl}">${w}</span></p>
 <div class="fig sm"><svg role="img" aria-label="Presidential cycle average path"></svg><div class="tip"></div></div></div>
 <div><h3>4. Short cycle within the year: ${d.season.length?d.season[1][0].slice(0,4):''} projected vs actual</h3><p class="small">Average month-by-month pattern of the calendar year, started from last December. Direction right in ${Math.round(sr*100)}% of months <span class="badge ${scl}">${sw}</span></p>
 <div class="fig sm"><svg role="img" aria-label="Within-year cycle projected vs actual"></svg><div class="tip"></div></div></div></div>
 <h3>5. Average change by calendar month</h3><div class="bars"></div>
 <h3>6. Next 12 months</h3><div class="scroll"><table class="stack"><thead><tr><th>Month</th><th>Cycle year</th><th class="n">Expected change</th><th class="n">Months up in history</th><th class="n">Projected level</th><th>Signal</th></tr></thead><tbody>
 ${d.tab.map(t=>`<tr><td>${fm(t.m)}</td><td>Year ${t.year} (${PY[t.year-1].replace(' year','').toLowerCase()})</td><td class="n">${d.additive?(t.chg>0?'+':'')+t.chg.toFixed(2)+' pts':pct(t.chg)}</td><td class="n">${t.up}%</td><td class="n">${val(t.v)}</td><td>${t.sig?`<span class="badge ${t.sig[0]==='B'?'good':'weak'}">${d.additive?(t.sig[0]==='B'?'Trough':'Peak'):t.sig}</span>`:''}</td></tr>`).join('')}</tbody></table></div></div>`;
 MAIN.appendChild(el);
 let figs=[...el.querySelectorAll('.fig')];
 if(!d.additive){const f=fibo(d),FL=d.t;plot(figs[0],{labels:FL,series:[{name:'Actual',data:d.y,color:'var(--s1)',dots:1}],
  hlines:f.lv.filter(x=>[0,38.2,50,61.8,100,161.8].includes(x[0])).map(x=>({y:x[1],label:x[0]===0||x[0]===100?(x[1]===f.H?'High':'Low'):x[0]+'%',color:x[0]>100?'var(--s3)':'var(--s2)'})),
  tick:v=>num(v,u),val,xl:l=>fs(l),tt:l=>fm(l)});figs=figs.slice(1)}
 if(d.lt){const T=d.lt,LA=T.lab,last=LA.filter((m,i)=>T.act[i]!=null).pop();
  plot(figs[0],{labels:LA,log:T.log,zero:!T.log,series:[{name:'Actual',data:T.act,color:'var(--s1)'},{name:'Long cycle (fitted)',data:T.fit,color:'var(--s2)',dash:1},{name:'Long cycle (projected)',data:T.proj,color:'var(--s3)',dash:1}],here:LA.indexOf(last),hereLabel:'Now',
   tick:v=>d.additive?v+'%':(u.startsWith('US$')?'$':'')+v.toLocaleString('en-US'),val,xl:l=>l.slice(0,4),xyears:n=>LA.length>400?(n?40:20):(n?10:5),tt:l=>fm(l)});figs=figs.slice(1)}
 // 1 actual vs projection
 const L=[...new Set([...d.back.map(x=>x[0]),...d.fwd.map(x=>x[0])])].sort(),A=Object.fromEntries(d.t.map((m,i)=>[m,d.y[i]]));
 const P=Object.fromEntries([...d.back,...d.fwd]);const marks=Object.entries(d.sig).map(([m,sg])=>({i:L.indexOf(m),y:P[m],kind:sg[0]==='B'?'buy':'sell'})).filter(m=>m.i>=0);
 const B=Object.fromEntries(d.back),F=Object.fromEntries(d.fwd);
 plot(figs[0],{labels:L,series:[{name:'Actual',data:L.map(m=>A[m]??null),color:'var(--s1)',dots:1},{name:'Projected in '+fs(d.back[0][0]),data:L.map(m=>B[m]??null),color:'var(--s2)',dash:1},{name:'Projection from now',data:L.map(m=>F[m]??null),color:'var(--s3)',dash:1}],
  marks:d.additive?[]:marks,here:L.indexOf(d.last),hereLabel:'Latest',tick:v=>d.additive?v+'%':num(v,u),val,xl:l=>fs(l),tt:l=>fm(l)});
 // 2 presidential path
 const PL=d.pres.map((_,i)=>i);plot(figs[1],{labels:PL,series:[{name:'Average path',data:d.pres,color:'var(--s2)'}],here:d.now,zero:1,
  bands:PY.map((p,j)=>({from:j*12,to:j*12+11,label:`${TERM0+j} ${p.replace(' year','').toLowerCase()}`,short:String(TERM0+j)})),tick:v=>d.additive?v.toFixed(1):v.toFixed(0)+'%',val:v=>d.additive?(v>0?'+':'')+v.toFixed(2)+' pts':pct(v),
  xl:(l,i)=>MON[i%12],tt:(l,i)=>`Year ${Math.floor(i/12)+1}: ${MON[i%12]} ${TERM0+Math.floor(i/12)}`});
 // 3 within-year
 const SL=d.season.map(x=>x[0]);plot(figs[2],{labels:SL,series:[{name:'Actual',data:SL.map(m=>A[m]??null),color:'var(--s1)',dots:1},{name:'Seasonal projection',data:d.season.map(x=>x[1]),color:'var(--s2)',dash:1}],
  here:SL.indexOf(d.last),hereLabel:'Latest',tick:v=>d.additive?v+'%':num(v,u),val,xl:l=>MON[+l.slice(5,7)-1],tt:l=>fm(l)});
 bars(el.querySelector('.bars'),d.seas.map((s,i)=>({label:MON[i],v:s[0],f:d.additive?(s[0]>0?'+':'')+s[0].toFixed(2)+' pts':pct(s[0]),up:s[1]})));
});
}
