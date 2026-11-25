"""
page.py - builds portfolio.html (the password-locked page). Runs on GitHub (trade / daily / refresh jobs).
The menu comes from site_layout.py: tools/cycles/site_layout.py (copied there by DEPLOY_TO_GITHUB.bat),
or scripts/site_layout.py when run on the PC.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "..", "cycles"), os.path.join(HERE, "..", "..", "..", "..")):
    p = os.path.normpath(p)
    if os.path.exists(os.path.join(p, "site_layout.py")) and p not in sys.path:
        sys.path.append(p)

DEFAULT_REPO = "usmangemini6-spec/US_Stocks"
PAGE_FILE = "portfolio.html"

CSS = r"""body{margin:0;padding:14px;background:#faf6ef;color:#0f172a;font-family:'Inter','Segoe UI',system-ui,sans-serif}
.wrap{max-width:1500px;margin:0 auto}
.card{background:#fff;border:1px solid #e7dcc8;border-radius:12px;padding:14px 18px;margin-bottom:14px}
.lock{max-width:420px;margin:40px auto;text-align:center}
.lock h2{margin:0 0 6px;color:#1f5f2a} .lock p{color:#64748b;margin:0 0 14px}
.lock input[type=password]{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #e7dcc8;border-radius:8px;font-size:1rem;margin-bottom:10px}
.lock label{display:block;color:#64748b;font-size:.85rem;margin:6px 0 12px}
.btn{padding:8px 16px;border:1px solid #e7dcc8;border-radius:8px;background:#f6ecdc;font:inherit;font-weight:600;cursor:pointer;color:#1f2937}
.btn:hover{background:#efe1c8} .btn.g{background:#1f5f2a;border-color:#1f5f2a;color:#fff} .btn.g:hover{background:#174a20}
.btn.s{padding:3px 9px;font-size:.78rem;font-weight:600} .btn[disabled]{opacity:.45;cursor:not-allowed}
.err{color:#b91c1c;min-height:1.2em;margin-top:8px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}
.kpi{background:#fdf8f1;border:1px solid #efe4d2;border-radius:10px;padding:10px 14px}
.kpi .l{color:#64748b;font-size:.78rem;font-weight:600;text-transform:uppercase;letter-spacing:.03em}
.kpi .v{font-size:1.35rem;font-weight:700;margin-top:2px} .kpi .x{font-size:.82rem;color:#64748b}
.pos{color:#15803d} .neg{color:#b91c1c}
h2.sec{font-size:1.05rem;color:#1f5f2a;margin:4px 0 10px}
.tabs{display:flex;gap:6px;margin-bottom:12px} .tab{padding:8px 16px;border-radius:8px;border:1px solid #e7dcc8;background:#fff;cursor:pointer;font-weight:600}
.tab.on{background:#f6ecdc;color:#a8650a;border-color:#e2cfae}
table{border-collapse:collapse;width:100%;font-size:.8rem}
th{background:#f6ecdc;text-align:left;padding:6px;border-bottom:1px solid #e7dcc8;font-size:.74rem;vertical-align:bottom}
th.n,td.n{text-align:right} td{padding:5px 6px;border-bottom:1px solid #f1ebe0;vertical-align:top}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap} tr:nth-child(even) td{background:#fcfaf6}
.tblw{overflow:auto}
.dot{display:inline-block;width:11px;height:11px;border-radius:50%;vertical-align:-1px;margin-right:5px}
.GREEN{background:#16a34a} .AMBER{background:#f59e0b} .RED{background:#dc2626}
.flag{display:inline-block;background:#fee2e2;color:#991b1b;border-radius:6px;padding:1px 6px;font-size:.7rem;margin:1px 2px 1px 0}
.zone{display:inline-block;background:#dcfce7;color:#166534;border-radius:6px;padding:1px 6px;font-size:.7rem;font-weight:600}
.why{color:#64748b;font-size:.72rem}
.bars div{display:flex;align-items:center;gap:8px;font-size:.8rem;margin:3px 0} .bars span.b{height:10px;background:#c8a26b;border-radius:4px}
.bars span.b.over{background:#dc2626}
.legend{display:flex;gap:16px;font-size:.82rem;margin-top:6px} .legend i{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:5px}
.note{font-size:.84rem;line-height:1.5;color:#334155} .note li{margin:2px 0}
.mgr{background:#fff7e6;border:1px solid #f3d29b;color:#7c4a03;border-radius:10px;padding:8px 14px;margin-bottom:14px;font-size:.88rem}
.grid2{display:grid;grid-template-columns:2fr 1fr;gap:14px} @media(max-width:900px){.grid2{grid-template-columns:1fr}}
.conn{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between;background:#fdf8f1;border:1px solid #efe4d2;border-radius:10px;padding:8px 14px;margin-bottom:14px;font-size:.88rem}
.conn b{color:#1f5f2a} .linkbtn{background:none;border:0;color:#a8650a;font:inherit;font-weight:600;cursor:pointer;text-decoration:underline;padding:0}
.modal{position:fixed;inset:0;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;z-index:2000;padding:14px}
.modal .box{background:#fff;border-radius:12px;max-width:560px;width:100%;padding:18px 20px;box-shadow:0 20px 50px rgba(0,0,0,.25);font-size:.9rem;line-height:1.5}
.modal h3{margin:0 0 8px;color:#1f5f2a} .modal ol{padding-left:20px;margin:6px 0 12px} .modal input{width:100%;box-sizing:border-box;padding:9px 11px;border:1px solid #e7dcc8;border-radius:8px;font:inherit;margin:4px 0 10px}
.modal .row{display:flex;gap:8px;justify-content:flex-end}
.pending{position:sticky;top:8px;z-index:50;background:#fff7e6;border:1px solid #f3d29b;color:#7c4a03;border-radius:10px;padding:10px 14px;margin-bottom:14px;font-weight:600}
.pending.ok{background:#dcfce7;border-color:#86efac;color:#166534} .pending.bad{background:#fee2e2;border-color:#fca5a5;color:#991b1b}
"""

JS = r"""
(function(){
const $=s=>document.querySelector(s), REPO=window.PF_REPO, WF='portfolio.yml';
let PW=null, TOKEN=null, PENDING=null, MGR=false;
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const usd=(v,d=0)=>v==null?'':(v<0?'-':'')+'$'+Math.abs(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=(v,d=2)=>v==null?'':(v>0?'+':'')+v.toFixed(d)+'%';
const cls=v=>v>0?'pos':v<0?'neg':'';
const b64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const b64e=u=>{let s='';for(let i=0;i<u.length;i+=0x8000)s+=String.fromCharCode.apply(null,u.subarray(i,i+0x8000));return btoa(s);};
async function kdf(pw,salt,use){const base=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
  return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:310000,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,[use]);}
async function encrypt(obj,pw){const salt=crypto.getRandomValues(new Uint8Array(16)),iv=crypto.getRandomValues(new Uint8Array(12));
  const ct=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv},await kdf(pw,salt,'encrypt'),new TextEncoder().encode(JSON.stringify(obj))));
  return 'v1.'+b64e(salt)+'.'+b64e(iv)+'.'+b64e(ct);}
async function decrypt(blob,pw){
  const [v,s,n,c]=blob.split('.'); if(v!=='v1') throw new Error('format');
  const base=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
  const key=await crypto.subtle.deriveKey({name:'PBKDF2',salt:b64(s),iterations:310000,hash:'SHA-256'},base,{name:'AES-GCM',length:256},false,['decrypt']);
  const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:b64(n)},key,b64(c));
  return JSON.parse(new TextDecoder().decode(pt));
}
let D=null, TAB='you';
function chart(d){
  const S=[['You',d.you.hist,'#1f5f2a'],['SAlgo Autopilot',d.auto.hist,'#c8820f'],['S&P 500',d.bench,'#64748b']].filter(s=>s[1]&&s[1].length);
  if(!S.length) return '<p class="why">The chart starts with your first trade.</p>';
  const all=S.flatMap(s=>s[1].map(p=>p[1])), lo=Math.min(...all)*0.995, hi=Math.max(...all)*1.005;
  const dates=[...new Set(S.flatMap(s=>s[1].map(p=>p[0])))].sort(), W=900,H=240,P=48;
  const x=dt=>P+(dates.length<2?0:(dates.indexOf(dt)/(dates.length-1))*(W-P-10)), y=v=>H-24-(v-lo)/(hi-lo||1)*(H-40);
  let g='';
  for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4;g+=`<line x1="${P}" x2="${W-10}" y1="${y(v)}" y2="${y(v)}" stroke="#efe4d2"/><text x="${P-6}" y="${y(v)+4}" text-anchor="end" font-size="10" fill="#64748b">${usd(v)}</text>`;}
  g+=`<text x="${P}" y="${H-6}" font-size="10" fill="#64748b">${dates[0]}</text><text x="${W-10}" y="${H-6}" font-size="10" fill="#64748b" text-anchor="end">${dates[dates.length-1]}</text>`;
  for(const [n,h,c] of S) g+=`<polyline fill="none" stroke="${c}" stroke-width="2" points="${h.map(p=>x(p[0])+','+y(p[1])).join(' ')}"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto">${g}</svg><div class="legend">${S.map(s=>`<span><i style="background:${s[2]}"></i>${s[0]}</span>`).join('')}</div>`;
}
function kpis(d){
  const b=d.bench.length?(d.bench[d.bench.length-1][1]/100000-1)*100:null;
  const k=(l,v,x,c='')=>`<div class="kpi"><div class="l">${l}</div><div class="v ${c}">${v}</div><div class="x">${x}</div></div>`;
  return `<div class="kpis">${k('My portfolio',usd(d.you.total),`<span class="${cls(d.you.ret_pct)}">${pct(d.you.ret_pct)}</span> since start`)}
  ${k('SAlgo Autopilot',usd(d.auto.total),`<span class="${cls(d.auto.ret_pct)}">${pct(d.auto.ret_pct)}</span>${d.autopilot_start?' since '+d.autopilot_start:''}`)}
  ${k('S&P 500 (same start)',b==null?'-':pct(b),'$100,000 held in SPY')}
  ${k('My cash',usd(d.you.cash),`${(100-d.you.invested_pct).toFixed(1)}% of the portfolio`)}
  ${k('Realized / open P&L',`<span class="${cls(d.you.realized)}">${usd(d.you.realized)}</span>`,`open: <span class="${cls(d.you.unrealized)}">${usd(d.you.unrealized)}</span>`)}</div>`;
}
function holdings(B,mine){
  if(!B.holdings.length) return '<p class="why">No open positions.</p>';
  const rows=B.holdings.map(h=>`<tr>
   <td><span class="dot ${h.light}" title="${h.light==='GREEN'?'Passes all 8 checks':esc('Fails: '+(h.fails.join(', ')||'not in the latest data'))}"></span><b>${esc(h.t)}</b></td>
   <td>${esc(h.name)}<br><span class="why">${esc(h.sector)}</span></td>
   <td class="n">${usd(h.avg,2)}</td><td class="n">${usd(h.last,2)}</td><td class="n">${usd(h.value)}</td><td class="n">${h.weight.toFixed(1)}%</td>
   <td class="n ${cls(h.pl)}">${usd(h.pl)}<br>${pct(h.pl_pct)}</td>
   <td class="n">${h.target?usd(h.target,2):''}<br><span class="why">${h.to_target!=null?pct(h.to_target,1)+' to go':''}</span></td>
   <td class="n">${h.first}</td>
   <td>${h.light==='RED'?'<span class="flag">Exit review</span>':h.light==='AMBER'?'<span class="flag" style="background:#fef3c7;color:#92400e">No longer preferred</span>':''}${h.flags.map(f=>`<span class="flag">${esc(f)}</span>`).join('')}${h.buyzone?'<span class="zone">Buy zone</span>':''}</td>
   ${mine?`<td><button class="btn s" data-act="SELL" data-t="${esc(h.t)}">Sell $5,000</button> <button class="btn s" data-act="CLOSE" data-t="${esc(h.t)}">Close</button></td>`:''}</tr>`).join('');
  return `<div class="tblw"><table><thead><tr><th>Stock</th><th>Company</th><th class="n">Avg cost</th><th class="n">Last close</th><th class="n">Value</th><th class="n">Weight</th><th class="n">Gain / loss</th><th class="n">Target</th><th class="n">First buy</th><th>Status</th>${mine?'<th></th>':''}</tr></thead><tbody>${rows}</tbody></table></div>`;
}
function sectors(B){
  const e=Object.entries(B.sectors).sort((a,b)=>b[1]-a[1]);
  if(!e.length) return '';
  return '<div class="bars">'+e.map(([s,w])=>`<div><span style="width:130px">${esc(s)}</span><span class="b ${w>D.rules.max_sector+0.25?'over':''}" style="width:${Math.max(2,w*3)}px"></span><span>${w.toFixed(1)}%</span></div>`).join('')+`</div><p class="why">Limit ${D.rules.max_sector}% per sector, ${D.rules.max_stock}% per stock.</p>`;
}
function closedT(B){
  if(!B.closed.length) return '<p class="why">No closed trades yet.</p>';
  return `<div class="tblw"><table><thead><tr><th>Date</th><th>Stock</th><th>Why</th><th class="n">Price</th><th class="n">Proceeds</th><th class="n">Gain / loss</th></tr></thead><tbody>${
   B.closed.map(c=>`<tr><td>${c.date}</td><td><b>${esc(c.t)}</b></td><td>${esc(c.reason)}${c.full?'':' (part)'}</td><td class="n">${usd(c.price,2)}</td><td class="n">${usd(c.proceeds)}</td><td class="n ${cls(c.pl)}">${usd(c.pl)} (${pct(c.pl_pct,1)})</td></tr>`).join('')}</tbody></table></div>`;
}
function logT(B){
  if(!B.log.length) return '';
  return `<details><summary class="why" style="cursor:pointer">All trades (${B.log.length})</summary><div class="tblw"><table><thead><tr><th>Date</th><th>Stock</th><th>Side</th><th class="n">Price</th><th class="n">Amount</th><th>By</th></tr></thead><tbody>${
   B.log.map(l=>`<tr><td>${l.date}</td><td>${esc(l.t)}</td><td>${l.side}${l.reason?' - '+esc(l.reason):''}</td><td class="n">${usd(l.price,2)}</td><td class="n">${usd(l.amount)}</td><td>${esc(l.by)}</td></tr>`).join('')}</tbody></table></div></details>`;
}
function buyPanel(){
  const rows=D.eligible.map(e=>`<tr><td><b>${esc(e.t)}</b> ${e.buyzone?'<span class="zone">Buy zone</span>':''}</td><td>${esc(e.name)}<br><span class="why">${esc(e.sector)}</span></td>
   <td class="n">${usd(e.price,2)}</td><td class="n">${e.pt?usd(e.pt,2):''}</td><td class="n">${e.upside!=null?e.upside.toFixed(1)+'%':''}</td><td class="n">${e.salman??''}</td><td class="n">${e.ttm!=null?e.ttm.toFixed(1):''}</td>
   <td>${e.why_not?`<button class="btn s" disabled>Buy $5,000</button><div class="why">${esc(e.why_not)}</div>`:`<button class="btn s g" data-act="BUY" data-t="${esc(e.t)}">Buy $5,000</button>`}</td></tr>`).join('');
  return `<div class="card"><h2 class="sec">Buy (stocks passing all 8 checks)</h2>${MGR?'':'<p class="why">Connect this device to use the buttons.</p>'}<div class="tblw"><table><thead><tr><th>Stock</th><th>Company</th><th class="n">Last price</th><th class="n">Price Target</th><th class="n">Upside</th><th class="n">Salman</th><th class="n">Score TTM</th><th></th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}
function render(){
  const B=TAB==='you'?D.you:D.auto, mine=TAB==='you';
  $('#app').innerHTML=`${PENDING?`<div class="pending ${PENDING.cls||''}">${esc(PENDING.msg)}</div>`:''}
  <div class="conn">${MGR?'<span><b>Trading on:</b> Buy / Sell buttons send an encrypted request to GitHub (about 2-3 minutes).</span><button class="linkbtn" id="disc">Disconnect this device</button>':'<span>Viewing only. To Buy / Sell from this device, connect it to GitHub once.</span><button class="btn s g" id="conbtn">Connect this device</button>'}<button class="linkbtn" id="lockbtn">Lock</button></div>
  <div class="card">${kpis(D)}</div>
  <div class="card"><h2 class="sec">Value over time</h2>${chart(D)}</div>
  ${buyPanel()}
  <div class="tabs"><span class="tab ${mine?'on':''}" data-tab="you">My portfolio</span><span class="tab ${mine?'':'on'}" data-tab="auto">SAlgo Autopilot</span></div>
  <div class="grid2"><div class="card"><h2 class="sec">Open positions</h2>${holdings(B,mine)}</div><div class="card"><h2 class="sec">Sectors</h2>${sectors(B)||'<p class="why">-</p>'}<p class="why">Cash ${usd(B.cash)}</p></div></div>
  <div class="card"><h2 class="sec">Closed trades</h2>${closedT(B)}${logT(B)}</div>
  <div class="card note"><h2 class="sec">Rules</h2><ul>
   <li>Start $100,000. Each Buy puts $5,000 (5%) into a stock; buying again adds $5,000. Each Sell takes $5,000 out; Close sells all of it.</li>
   <li>Buy only while the stock passes all 8 Preferred checks (<span class="dot GREEN"></span>). Max ${D.rules.max_stock}% in one stock and ${D.rules.max_sector}% in one sector.</li>
   <li>A position closes by itself when a daily close reaches its target (the Price Target on the day of the last Buy).</li>
   <li><span class="dot AMBER"></span>No longer preferred: hold or sell, no adding. <span class="dot RED"></span>Exit review: fails 3 or more checks, Business Analysis SELL, or not in the latest data. Also flagged: down ${-D.rules.loss_flag}% from cost, or target not reached after 12 months. You decide.</li>
   <li><span class="zone">Buy zone</span> price is at or below the Business Analysis buy-below price.</li>
   <li>SAlgo Autopilot: its own $100,000 with the same rules; on every new monthly list it sells its red stocks and buys the Preferred stocks in order of Salman Score, then Score TTM.</li>
  </ul><p class="why">Prices to ${D.as_of} &middot; data ${D.data_date||'-'} &middot; built ${D.generated.replace('T',' ')}</p></div>`;
  document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{TAB=t.dataset.tab;render();});
  document.querySelectorAll('[data-act]').forEach(b=>b.onclick=()=>trade(b.dataset.act,b.dataset.t,b));
  if($('#conbtn')) $('#conbtn').onclick=connectDlg;
  if($('#disc')) $('#disc').onclick=()=>{try{localStorage.removeItem('salgo_pf_gh');}catch(e){} TOKEN=null;MGR=false;render();};
  $('#lockbtn').onclick=()=>{try{localStorage.removeItem('salgo_pf');}catch(e){} location.reload();};
  if(PENDING&&PENDING.busy) document.querySelectorAll('[data-act]').forEach(b=>b.disabled=true);
}
const gh=(path,opt={})=>fetch('https://api.github.com/repos/'+REPO+path,{...opt,headers:{'Authorization':'Bearer '+TOKEN,'Accept':opt.raw?'application/vnd.github.raw+json':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',...(opt.headers||{})}});
async function trade(act,t,btn){
  if(!TOKEN){connectDlg();return;}
  const what=act==='BUY'?'Buy $5,000 of':act==='SELL'?'Sell $5,000 of':'Close the whole position in';
  const h=(D.you.holdings.find(x=>x.t===t)||D.eligible.find(x=>x.t===t)||{});
  const last=h.last??h.price;
  const p=prompt(`${what} ${t}\n\nPrice you traded at (leave empty = the latest daily close${last?', about '+last:''}):`,'');
  if(p===null) return;
  const price=String(p).trim()===''?null:parseFloat(String(p).replace(/[$,]/g,''));
  if(price!==null&&!(price>0)){alert('Price must be a number above 0.');return;}
  const id=(crypto.randomUUID?crypto.randomUUID():Date.now()+'-'+Math.random().toString(16).slice(2)).replace(/[^A-Za-z0-9-]/g,'');
  PENDING={busy:true,msg:`Sending: ${what} ${t}...`};render();
  try{
    const request=await encrypt({id,t,act,price,ts:Date.now()},PW);
    const r=await gh('/actions/workflows/'+WF+'/dispatches',{method:'POST',body:JSON.stringify({ref:'main',inputs:{request}})});
    if(r.status!==204){throw new Error(r.status===401?'GitHub key not valid or expired - disconnect and connect again.':r.status===403||r.status===404?'GitHub key has no permission to start the Portfolio job (needs Actions: Read and write on this repository).':'GitHub answered '+r.status);}
    PENDING={busy:true,msg:`Sent to GitHub: ${what} ${t}. Waiting for the result (usually 2-3 minutes)...`};render();
    const t0=Date.now();
    while(Date.now()-t0<9*60000){
      await new Promise(res=>setTimeout(res,15000));
      try{
        const pr=await gh('/contents/portfolio.html?ref=main&n='+Date.now(),{raw:true}); if(!pr.ok) continue;
        const m=(await pr.text()).match(/\/\*PF_START\*\/window\.PF="([^"]+)";\/\*PF_END\*\//); if(!m) continue;
        const nd=await decrypt(m[1],PW), q=(nd.requests||[]).find(x=>x.id===id);
        if(q){window.PF=m[1];D=nd;PENDING={cls:q.ok?'ok':'bad',msg:(q.ok?'Done: ':'Not done: ')+q.msg+(q.ok?' (the public page refreshes in about a minute)':'')};render();return;}
      }catch(e){}
    }
    PENDING={cls:'bad',msg:'Still waiting after 9 minutes. Check GitHub > Actions > Portfolio, then reload this page later.'};render();
  }catch(e){PENDING={cls:'bad',msg:'Not sent: '+e.message};render();}
}
function connectDlg(){
  const w=document.createElement('div');w.className='modal';
  w.innerHTML=`<div class="box"><h3>Connect this device to GitHub</h3>
   <p>Needed once per device (phone, PC). The key is kept only on this device, encrypted with your portfolio password.</p>
   <ol><li>Open <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">GitHub &gt; New fine-grained token</a>.</li>
   <li>Name: <b>SAlgo portfolio</b>. Expiration: up to 1 year.</li>
   <li>Repository access: <b>Only select repositories</b> &gt; <b>${esc(REPO)}</b>.</li>
   <li>Permissions &gt; Repository: <b>Actions: Read and write</b>, <b>Contents: Read-only</b>.</li>
   <li>Generate, copy the key and paste it here.</li></ol>
   <input id="tok" type="password" placeholder="github_pat_..." autocomplete="off"><div class="err" id="terr"></div>
   <div class="row"><button class="btn" id="tcancel">Cancel</button><button class="btn g" id="tsave">Save</button></div></div>`;
  document.body.appendChild(w);
  w.querySelector('#tcancel').onclick=()=>w.remove();
  w.querySelector('#tsave').onclick=async()=>{
    const k=w.querySelector('#tok').value.trim(), er=w.querySelector('#terr'); if(!k){er.textContent='Paste the key.';return;}
    er.textContent='Checking...'; TOKEN=k;
    try{const r=await gh('/actions/workflows/'+WF);
      if(!r.ok){TOKEN=null;er.textContent=r.status===401?'Key not valid.':'This key cannot see the Portfolio job ('+r.status+'). Check the repository and Actions permission.';return;}
      try{localStorage.setItem('salgo_pf_gh',await encrypt({token:k},PW));}catch(e){}
      MGR=true;w.remove();render();
    }catch(e){TOKEN=null;er.textContent='Could not reach GitHub: '+e.message;}
  };
}
async function loadToken(){try{const s=localStorage.getItem('salgo_pf_gh');if(s){TOKEN=(await decrypt(s,PW)).token;MGR=!!TOKEN;}}catch(e){TOKEN=null;MGR=false;}}
async function show(d,pw){D=d;PW=pw;await loadToken();$('#lockbox').style.display='none';$('#app').style.display='block';render();}
if(!window.PF){$('#lockbox').style.display='block';$('#err').textContent='No portfolio published yet.';return;}
$('#lockbox').style.display='block';
async function open_(pw,silent){
  try{const d=await decrypt(window.PF,pw);try{if($('#rem').checked)localStorage.setItem('salgo_pf',pw);}catch(e){}await show(d,pw);}
  catch(e){if(!silent)$('#err').textContent='Wrong password.';try{localStorage.removeItem('salgo_pf');}catch(x){}}
}
$('#lf').onsubmit=e=>{e.preventDefault();$('#err').textContent='Opening...';open_($('#pw').value);};
try{const s=localStorage.getItem('salgo_pf');if(s){$('#rem').checked=true;open_(s,true);}}catch(e){}
})();
"""


def page_html(repo=DEFAULT_REPO):
    try:
        from site_layout import site_header_css, site_header_html
        hcss, hhtml = site_header_css(), site_header_html(PAGE_FILE, "My Portfolio", "Private - password required")
    except Exception:
        hcss, hhtml = "", '<h1 style="color:#1f5f2a">My Portfolio</h1>'
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"UTF-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "<meta name=\"robots\" content=\"noindex, nofollow\">\n<title>SAlgo - My Portfolio</title>\n"
            "<link rel=\"stylesheet\" href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap\">\n"
            "<style>\n" + hcss + "\n" + CSS + "</style>\n</head>\n<body>\n<div class=\"wrap\">\n" + hhtml + """
<div id="lockbox" class="card lock" style="display:none">
  <h2>Private page</h2><p>Type the portfolio password to open it.</p>
  <form id="lf"><input id="pw" type="password" autocomplete="current-password" placeholder="Password">
  <label><input id="rem" type="checkbox"> Remember on this device</label>
  <button class="btn g" type="submit">Open</button></form><div class="err" id="err"></div>
</div>
<div id="app" style="display:none"></div>
</div>
<script>window.PF_REPO=""" + json.dumps(repo) + """;/*PF_START*/window.PF="";/*PF_END*/</script>
<script>
""" + JS + """
</script>
</body>
</html>
""")
