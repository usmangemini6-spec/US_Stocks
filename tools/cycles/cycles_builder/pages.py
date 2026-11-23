exec(open('sightml.py',encoding='utf-8').read())
SIGCSS=CSS
PRES=open('pres_box.html').read()
SUMHEAD='<div class="scroll"><table class="stack"><thead><tr><th>Market</th><th class="n">Latest</th><th>Presidential cycle</th><th class="n">Next 12 months (cycle)</th><th>Cycle view</th><th>Reliability</th></tr></thead><tbody id="sum">{rows}</tbody></table></div>'
def pend(name,page,why): return f'<tr><td><a href="{page}">{name}</a></td><td class="n">—</td><td>—</td><td class="n">—</td><td>{why}</td><td><span class="badge mid">Data pending</span></td></tr>'
PENDING='' if 'psx' in D else pend('Pakistan KSE-100 (PSX)','psx.html','Data pending')
from cdata import daily_last
def _fact(key,name):
    x=daily_last(key)
    if not x: return ''
    d,v,rec,rd=x; dd=(v/rec-1)*100
    return f'<div><span>{name} · {d[8:]}/{d[5:7]}/{d[:4]}</span><b>{v:,.0f}</b><span>{"at its record" if dd>-0.5 else f"{dd:.1f}% from its record {rec:,.0f} ({rd[8:]}/{rd[5:7]}/{rd[:4]})"}</span></div>'
_c=D.get('cpi')
LIVE='<div class="facts">'+_fact('sp','S&amp;P 500')+_fact('nasdaq','NASDAQ')+_fact('dji','Dow Jones')+(f'<div><span>US inflation · {["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(_c["last"][5:7])-1]} {_c["last"][:4]}</span><b>{_c["y"][-1]:.1f}%</b><span>Fed target 2%</span></div>' if _c else '')+'</div>'
def _cb(keys):
    sn=[MK[k]["signal_now"]["signal"] for k in keys if k in MK and MK[k].get("signal_now")]
    if not any(k in MK for k in keys): return ('mid','Data pending')
    return ('good','Signal: '+sn[0]) if sn else ('mid','No reliable cycle')
CARDS=[('us-stocks.html','US stocks','S&amp;P 500, NASDAQ and Dow Jones: tested buy and sell signals, forecast vs actual.')+_cb(['sp','nasdaq']),
 ('ai-bubble.html','AI bubble: burst or correction?','Where the November sell-off stands, how stretched prices are, and what to watch.','good','Ready'),
 ('gold.html','Gold &amp; Shariah-compliant miners','Gold cycle test, and gold metal vs halal miners such as AEM.')+_cb(['gold']),
 ('silver.html','Silver','Silver cycle test and Larry Williams\' calls vs actual.')+_cb(['silver']),
 ('tasi.html','Saudi TASI','Saudi market cycle signals.')+_cb(['tasi']),
 ('psx.html','Pakistan KSE-100 (PSX)','Pakistan market cycles.')+_cb(['psx']),
 ('rates.html','Interest rates &amp; inflation','Fed rate, 10-year yield and US inflation.')+_cb(['cpi','us10y','fedfunds']),
 ('oil.html','Crude oil','Oil price cycle test.')+_cb(['oil']),
 ('real-estate.html','US real estate','US home prices (Case-Shiller) cycle test.')+_cb(['home'])]
exec(open('lw_snip.py').read())
OUTLOOK='''<section class="band mk"><div class="wrap"><h2>Looking ahead: 2027</h2>
<p class="lede">Larry Williams' main calls for 2027 from his Forecast 2026 report, next to what our own cycles say.</p>
<div class="scroll"><table class="stack"><thead><tr><th>Market</th><th>Larry Williams (Dec 2025)</th><th>Our cycles</th></tr></thead><tbody>
<tr><td>US stocks</td><td>Buy the 2026 low; a <b>bear raid on stocks in 2027</b></td><td>Pre-election year: S&amp;P rose Jan–Jul in 19 of 19 such years since 1950. Our signals: <b>buy into Jul 2027</b>, <b>caution Aug–Nov 2027</b></td></tr>
<tr><td>Recession</td><td>No recession expected before <b>mid-2027</b></td><td>No cycle measured</td></tr>
<tr><td>Jobs</td><td>Job growth until mid-2027, when unemployment should peak</td><td>No cycle measured</td></tr>
<tr><td>US real estate</td><td>Prices lower until a <b>low in late 2027</b>; next boom near the end of the decade</td><td>No cycle passed our backtest: no forecast</td></tr>
<tr><td>Interest rates</td><td>Rates <b>lower into 2030</b></td><td>No cycle passed our backtest: no forecast</td></tr>
<tr><td>Inflation</td><td>Picks up in mid-to-late 2026</td><td>Rose to about 3.7% by Sep 2026</td></tr></tbody></table></div>
<p class="small">Both views are tracked here each month against what actually happens. His 7-, 9- and 10-year cycles did not pass our backtest on our data.</p></div></section>'''
page('index.html','Cycles','''<h1 style="margin-top:22px">Cycles</h1>
<p class="lede">Where each market stands in its long-term, 4-year presidential and within-year cycles, what the cycles project, and how reliable they have been. Pick a market below for its full page.</p>'''+LIVE,
'<section class="band"><div class="wrap"><h2>Markets</h2><div class="cards">'+''.join(f'<a class="card" href="{f}"><b>{t}</b><p>{p}</p><span class="badge {c}">{s}</span></a>' for f,t,p,c,s in CARDS)+'</div>'
+'<h2 style="margin-top:36px">Signals now</h2><p class="small">From the cycles that passed our backtest for each market; month-end data, latest month to date.</p>'+SIGCSS+summary()+HOWTO+'</div></section>'
+OUTLOOK+'<section class="band mk"><div class="wrap">'+PRES+'</div></section>',[k for k in ['sp','nasdaq','dji','gold','silver','tasi','psx','oil','home','cpi','us10y','fedfunds'] if k in D])

exec(open('fc_snip.py').read())
FC_CSS=FC_HTML=FC_JS=''   # replaced by the tested signal charts
page('us-stocks.html','US stocks','<h1 style="margin-top:22px">US stocks</h1><p class="lede">S&amp;P 500, NASDAQ and Dow Jones. The cycle charts use month-end data to November 2026; the November sell-off is covered on the <a href="ai-bubble.html">AI bubble page</a>.</p>'+LIVE,
 LW_CSS+LW_SECTION('sp')+LW_SECTION('nasdaq')+LW_JS+FC_CSS+FC_HTML+FC_JS+'<main id="main"></main>',['sp','nasdaq','dji'])


AI_BODY='''<section class="band mk" id="ai"><div class="wrap">
<h2>Is the AI bubble bursting?</h2>
<p class="small">Written on 20 November 2026; updated when the situation changes.</p>
<div class="view"><b>Short answer: a sharp correction is under way; a full burst is not confirmed yet.</b>
<p>All three US indexes are now in a correction. The <b>S&amp;P 500 closed at 6,910 on 20 Nov, 11.6% below its 6 Oct record</b>, and the NASDAQ is 18.1% below its record, close to the 20% line of a bear market. The PHLX chip index was already 38% below its June record on 5 Nov. A burst would mean the AI spending itself is cut; so far no large cloud company has cut its spending plans.</p></div>
<div class="two" style="margin-top:8px"><div><h3>Signs of a bubble</h3><ul class="tight">
<li><b>Concentration:</b> more than half of the ~$32 trillion added to the S&amp;P 500 since ChatGPT came from just 10 AI-linked companies.</li>
<li><b>Spending:</b> the five largest cloud companies are spending about $800 billion in 2026, and AI spending drives about half of S&amp;P 500 earnings growth this year.</li>
<li><b>Sentiment turning:</b> fund managers cut tech by the most since 2006 in November; 52% expect at least one big cloud company to cut spending within six months.</li>
<li><b>Expert warnings:</b> one well-known bubble researcher now puts the chance of an AI bubble at 70%.</li>
<li><b>Triggers this month:</b> NVIDIA's CEO exit and a reported SEC inquiry, worries about data-center rules after the midterm elections, and inflation stuck near 4%.</li></ul></div>
<div><h3>Signs it is not (yet) a burst</h3><ul class="tight">
<li><b>Profits are real:</b> NVIDIA beat its own forecast again on 17 Nov and guided higher; earnings keep beating estimates.</li>
<li><b>Spending not cut:</b> Alphabet kept its 2026 plan of $195–205 billion, and 2027 plans are reported to be higher.</li>
<li><b>Central banks:</b> a US Fed governor said on 18 Nov there is nothing “bubble-like” in how AI is priced.</li>
<li><b>Size of the fall:</b> −11.6% is a normal correction; the S&amp;P 500 has had 27 corrections since 1928, most of which did not turn into bear markets.</li></ul></div></div>
<h3>How far each index has fallen</h3><p class="small">Distance below the record close, as of 20 Nov 2026 (chip index as of 5 Nov).</p>
<div class="ddbars">
<div class="dd"><span>Dow Jones</span><div class="bt"><i style="width:29.7%"></i></div><b>−11.4%</b></div>
<div class="dd"><span>S&amp;P 500</span><div class="bt"><i style="width:30.2%"></i></div><b>−11.6%</b></div>
<div class="dd"><span>NASDAQ</span><div class="bt"><i style="width:47.1%"></i></div><b>−18.1%</b></div>
<div class="dd"><span>Chip stocks (PHLX)</span><div class="bt"><i style="width:100%"></i></div><b>−38.4%</b></div></div>
<p class="small">Marks on the scale: −10% is a correction, −20% a bear market.</p>
<h3>Is the S&amp;P 500 stretched? Price vs its 10-year average</h3>
<p class="small">How far the S&amp;P 500 sits above the average of its previous 10 years, monthly since 1950. Past bubble peaks: <b>+131%</b> in 1999 (dot-com) and <b>+117%</b> in 1987; <b>+94%</b> at the end of 2021. In August 2026 it reached <b>+90%</b>; at the 20 Nov close it is about <b>+68%</b>.</p>
<div class="fig"><svg id="devc" role="img" aria-label="S&amp;P 500 percent above its 10-year average since 1950"></svg><div class="tip"></div></div>
<p class="small">Reading: high but below the 1987 and 2000 peaks. This measure says US stocks are expensive, not that a crash must follow; in 2021 a similar level was followed by a 25% fall in 2022.</p>
<h3>What the cycles add</h3>
<p>2026 is the <b>midterm year</b> (year 2 of the presidential cycle). Historically its low comes around Sep–Oct and the following 12 months, into the pre-election year, are the strongest of the four. This fall is arriving about a month later than usual. In the 2000–2002 dot-com burst the market kept falling for two and a half years, but its final low still came in the midterm year (October 2002).</p>
<h3>What to watch</h3>
<table class="stack"><thead><tr><th>Signal</th><th>Burst is getting more likely if…</th><th>When</th></tr></thead><tbody>
<tr><td>Cloud spending plans</td><td>Microsoft, Alphabet, Amazon or Meta cut 2027 spending</td><td>Q4 results, late Jan–Feb 2027</td></tr>
<tr><td>NASDAQ</td><td>Closes more than 20% below its record (bear market)</td><td>Daily</td></tr>
<tr><td>AI chip demand</td><td>NVIDIA guides lower, or customers delay orders</td><td>NVIDIA results, late Feb 2027</td></tr>
<tr><td>Inflation and rates</td><td>Inflation stays near 4% and the Fed cannot cut</td><td>Monthly CPI</td></tr></tbody></table>
<div class="view" style="margin-top:18px"><b>Suggestion at this point</b><p>Do not buy all at once. If you are adding to US stocks, spread buys over the next 2–3 months (for example in three parts), favour companies with strong free cash flow and net cash over the most crowded AI names, and keep cash for a deeper fall if the NASDAQ breaks −20%. Reduce if large cloud companies start cutting their 2027 spending. The cycles favour buying in this midterm-year weakness; the AI news decides how deep it goes.</p></div>
</div></section>'''

DEV=json.dumps(json.load(open('work/dev.json')))
LIB=open('plotlib.js').read()
SCRIPT='<script>{'+LIB+'const DV='+DEV+';const L=DV.map(x=>x[0]),V=DV.map(x=>x[1]),fsY=l=>l.slice(0,4);plot(document.getElementById("devc").parentElement,{labels:L,zero:1,series:[{name:"Above 10-year average",data:V,color:"var(--s1)"}],here:L.length-1,hereLabel:"Sep 2026",tick:v=>v+"%",val:v=>(v>0?"+":"")+v.toFixed(0)+"%",xl:fsY,xyears:n=>n?20:10,tt:l=>fm(l)})}</script>'
page('ai-bubble.html','AI bubble','<h1 style="margin-top:22px">AI bubble: burst or correction?</h1><p class="lede">Where the November 2026 sell-off stands, how stretched US stock prices are, and the signals that would confirm a burst.</p>'+LIVE,
 '<style>.ddbars{display:grid;gap:8px;margin-top:10px;max-width:760px}.dd{display:grid;grid-template-columns:150px minmax(0,1fr) 64px;gap:10px;align-items:center;font-size:15px}.dd .bt{height:16px;position:relative;background:linear-gradient(to right,transparent calc(26.1% - 1px),var(--mut) calc(26.1% - 1px),var(--mut) 26.1%,transparent 26.1%,transparent calc(52.1% - 1px),var(--mut) calc(52.1% - 1px),var(--mut) 52.1%,transparent 52.1%)}.dd i{display:block;height:100%;background:var(--red);border-radius:3px;opacity:.85}.dd b{text-align:right;font-variant-numeric:tabular-nums}</style>'+AI_BODY+SCRIPT,[])
MINERS='''<section class="band mk" id="metal-or-miners"><div class="wrap">
<h2>Gold, silver or mining stocks?</h2>
<p class="lede">The same view of gold can be held through the metal or through mining stocks. This compares how each would do in different gold scenarios.</p>
<h3>Shariah-compliant mining stocks</h3>
<div class="facts"><div><span>Gold miner · Canada</span><b>AEM</b><span>Agnico Eagle Mines · HALAL</span></div><div><span>Gold miner · South Africa</span><b>DRD</b><span>DRDGOLD · HALAL</span></div><div><span>Silver miners</span><b>None</b><span>no halal silver miner found yet</span></div></div>
<h3>How much more miners move</h3>
<p>Mining stocks move more than the metal, up and down, because a mine's costs stay roughly fixed while the gold price changes its profit. In the latest fall, <b>gold dropped 18%</b> from its February 2026 high while <b>AEM dropped 33%</b> from its own high: about <b>1.8 times</b> the move. The scenarios below use that ratio.</p>
<div class="scroll"><table class="stack"><thead><tr><th>If gold over the next 12 months…</th><th class="n">Gold metal</th><th class="n">Halal gold miners (about 1.8×)</th><th>Better choice</th></tr></thead><tbody>
<tr><td>Rises strongly (+20%)</td><td class="n">+20%</td><td class="n">about +36%</td><td><span class="badge good">Miners</span></td></tr>
<tr><td>Rises (+10%)</td><td class="n">+10%</td><td class="n">about +18%</td><td><span class="badge good">Miners</span></td></tr>
<tr><td>Stays flat (0%)</td><td class="n">0%</td><td class="n">depends on company results and costs</td><td><span class="badge mid">Metal (less risk)</span></td></tr>
<tr><td>Falls (−10%)</td><td class="n">−10%</td><td class="n">about −18%</td><td><span class="badge mid">Metal</span></td></tr>
<tr><td>Falls sharply (−20%)</td><td class="n">−20%</td><td class="n">about −36%</td><td><span class="badge mid">Metal</span></td></tr></tbody></table></div>
<p class="small">Miners also carry company risks the metal does not have: mine problems, rising costs, taxes and country risk. Over the last 10 years AEM moved about 2% and DRD about 2.7% for each 1% move in gold (chart below), so 1.8× is a cautious figure.</p>
<h3>Silver</h3>
<p>No Shariah-compliant silver miner was found, so silver is held through the metal only. Silver usually moves more than gold in both directions. The 10-year chart below compares gold, silver and the halal gold miners.</p>
<div class="view" style="margin-top:18px"><b>How to choose now</b><p>Gold's cycles give no reliable signal for the next 12 months, so there is no strong case that gold will rise. In that situation the metal is the steadier choice; mining stocks suit only a smaller part of the position, for someone who expects gold to recover. Check the Shariah status of any gold or silver fund before buying.</p></div>
'''+miners_html()+'''
</div></section>'''
page('gold.html','Gold & miners','<h1 style="margin-top:22px">Gold &amp; Shariah-compliant miners</h1><p class="lede">Gold\'s three cycles, then gold and silver compared with Shariah-compliant mining stocks.</p>',LW_CSS+LW_SECTION('gold')+LW_JS+'<main id="main"></main>'+MINERS,['gold'])

def stub(f,title,lede,items):
    page(f,title,f'<h1 style="margin-top:22px">{title}</h1><p class="lede">{lede}</p>','<section class="band"><div class="wrap"><div class="pend"><b>Data pending.</b> This page fills in automatically once the monthly data is downloaded. It will show:<ul class="tight">'+''.join(f'<li>{i}</li>' for i in items)+'</ul></div></div></section>',[])
COMMON=['Summary box with the cycle view now','Cycle timetable: long-term, presidential and within-year cycles, with start, typical peak, bottom and end','Long-term life cycle chart to 2040','Actual vs projection month by month, with buy and sell windows','Within-year cycle: projected vs actual','Next 12 months table with projected levels and monthly high–low range']
page('oil.html','Crude oil','<h1 style="margin-top:22px">Crude oil</h1><p class="lede">WTI crude oil, monthly since 1986: buy and sell signals from the cycles that passed our backtest. Brent is added once its data is downloaded.</p>','<main id="main"></main>',['oil'])
page('real-estate.html','US real estate','<h1 style="margin-top:22px">US real estate</h1><p class="lede">US home prices (S&amp;P Case-Shiller national index, monthly since 1975): the long property cycle, the presidential cycle and the within-year pattern.</p>','<main id="main"></main>',['home'])
page('silver.html','Silver','<h1 style="margin-top:22px">Silver</h1><p class="lede">Silver: the 2026 forecast against what happened, then its long-term, presidential and within-year cycles. No Shariah-compliant silver miner was found, so silver is covered as the metal only.</p>',LW_CSS+LW_SECTION('silver')+LW_JS+'<main id="main"></main>',['silver'])
page('tasi.html','Saudi TASI','<h1 style="margin-top:22px">Saudi TASI</h1><p class="lede">The Saudi stock market index, monthly since 1998: buy and sell signals from the cycles that passed our backtest. The presidential cycle is a US pattern, so its reliability for TASI is shown separately.</p>','<main id="main"></main>',['tasi'])
if 'psx' in D:
    page('psx.html','Pakistan KSE-100 (PSX)','<h1 style="margin-top:22px">Pakistan KSE-100 (PSX)</h1><p class="lede">The KSE-100, main index of the Pakistan Stock Exchange: buy and sell signals from the cycles that passed our backtest.</p>','<main id="main"></main>',['psx'])
else:
    stub('psx.html','Pakistan KSE-100 (PSX)','The KSE-100 is the main index of the Pakistan Stock Exchange (PSX). This page shows its cycles.',COMMON+['Optional: the KMI-30, the Pakistan Stock Exchange\'s Shariah-compliant index, if its data is available'])
page('rates.html','Rates & inflation','<h1 style="margin-top:22px">Interest rates &amp; inflation</h1><p class="lede">US inflation, the 10-year Treasury yield and the Fed funds rate.</p>','<main id="main"></main>',[k for k in ['cpi','us10y','fedfunds'] if k in D])

