/* Every Program Since 1869 -- the chart behind every-program.html.
   Inlined into the page by scripts/build_every_program.py, which also supplies
   the TEAMS global: [{n: name, s: [[year-1869, W, L, T], ...]}, ...]. */
(function(){
const Y0=1869, NY=1+Math.max(...TEAMS.map(t=>t.s[t.s.length-1][0])), XMAX=1600;
// Precompute cumulative games and points for each program, by calendar year and by its own season count.
const T=TEAMS.map((t,i)=>{
  const first=t.s[0][0], last=t.s[t.s.length-1][0];
  const calN=new Float32Array(NY), calP=new Float32Array(NY);
  let n=0,p=0,j=0;
  for(let y=0;y<NY;y++){ if(j<t.s.length&&t.s[j][0]===y){const s=t.s[j];n+=s[1]+s[2]+s[3];p+=s[1]+s[3]/2;j++;} calN[y]=n;calP[y]=p; }
  const ownN=[],ownP=[]; n=0;p=0;
  for(const s of t.s){n+=s[1]+s[2]+s[3];p+=s[1]+s[3]/2;ownN.push(n);ownP.push(p);}
  const W=t.s.reduce((a,s)=>a+s[1],0),L=t.s.reduce((a,s)=>a+s[2],0),Ti=t.s.reduce((a,s)=>a+s[3],0);
  return {i,name:t.n,first,last,calN,calP,ownN,ownP,len:t.s.length,W,L,Ti};
});
const byName=new Map(T.map(t=>[t.name.toLowerCase(),t]));
const $=id=>document.getElementById(id);
const cv=$('cv'), ctx=cv.getContext('2d'), box=$('box'), tip=$('tip');
let mode='cal', t=NY-1, playing=false, picked=['Notre Dame','Michigan','Yale'].map(n=>byName.get(n.toLowerCase())).filter(Boolean);
const maxOwn=Math.max(...T.map(x=>x.len))-1;
const css=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();

// Where is a program at clock value k (integer step)? Returns {n,p,alive} or null if it hasn't started.
function at(tm,k){
  if(mode==='cal'){ if(k<tm.first) return null; const y=Math.min(k,NY-1); return {n:tm.calN[y],p:tm.calP[y],alive:y<=tm.last}; }
  const s=Math.min(k,tm.len-1); return {n:tm.ownN[s],p:tm.ownP[s],alive:k<tm.len};
}
function pos(tm,tt){ // smooth between whole steps
  const k=Math.floor(tt), f=tt-k, a=at(tm,k); if(!a||a.n===0) return null;
  const b=at(tm,k+1); let n=a.n,p=a.p;
  if(b&&b.n>0&&f>0){ n=a.n+(b.n-a.n)*f; p=a.p+(b.p-a.p)*f; }
  return {n,w:p/n,alive:a.alive||(f>0&&b&&b.alive)};
}
let W=0,H=0,dpr=1; const M={l:46,r:14,t:14,b:34};
function resize(){ const r=box.getBoundingClientRect(); dpr=window.devicePixelRatio||1; W=r.width;H=r.height; cv.width=W*dpr; cv.height=H*dpr; draw(); }
const X=n=>M.l+(Math.log10(Math.max(n,1))/Math.log10(XMAX))*(W-M.l-M.r);
const Yp=w=>M.t+(1-w)*(H-M.t-M.b);
let last=[];
function draw(){
  ctx.setTransform(dpr,0,0,dpr,0,0); ctx.clearRect(0,0,W,H);
  const ink=css('--ink'),muted=css('--muted'),rule=css('--rule'),steel=css('--steel'),rust=css('--rust'),gone=css('--gone'),fun=css('--funnel');
  // coin-flip funnel: .500 ± 2 standard deviations = ± 1/sqrt(n)
  ctx.beginPath(); for(let n=1;n<=XMAX;n*=1.05){ctx.lineTo(X(n),Yp(Math.min(1,.5+1/Math.sqrt(n))));}
  for(let n=XMAX;n>=1;n/=1.05){ctx.lineTo(X(n),Yp(Math.max(0,.5-1/Math.sqrt(n))));} ctx.closePath(); ctx.fillStyle=fun; ctx.fill();
  // grid + axes
  ctx.font='11px "Roboto Mono",monospace'; ctx.fillStyle=muted; ctx.strokeStyle=rule; ctx.lineWidth=1;
  for(const w of [0,.25,.5,.75,1]){ctx.beginPath();ctx.moveTo(M.l,Yp(w));ctx.lineTo(W-M.r,Yp(w));ctx.stroke(); ctx.textAlign='right';ctx.textBaseline='middle';ctx.fillText(w===1?'1.000':'.'+String(Math.round(w*1000)).padStart(3,'0'),M.l-6,Yp(w));}
  ctx.textAlign='center';ctx.textBaseline='top';
  for(const n of [1,10,100,1000]){ctx.beginPath();ctx.moveTo(X(n),M.t);ctx.lineTo(X(n),H-M.b);ctx.stroke();ctx.fillText(n.toLocaleString(),X(n),H-M.b+6);}
  ctx.textAlign='right'; ctx.fillText('games played (all-time) →',W-M.r,H-M.b+20);
  ctx.save();ctx.translate(11,M.t+(H-M.t-M.b)/2);ctx.rotate(-Math.PI/2);ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText('all-time winning %',0,0);ctx.restore();
  // dots
  last=[]; let alive=0,stopped=0;
  const pickedSet=new Set(picked);
  for(const tm of T){ const q=pos(tm,t); if(!q) continue; const x=X(q.n),y=Yp(q.w); last.push({tm,x,y,q});
    if(q.alive) alive++; else stopped++;
    if(pickedSet.has(tm)) continue;
    ctx.beginPath(); ctx.arc(x,y,q.alive?3:2.6,0,7);
    if(q.alive){ctx.fillStyle=steel;ctx.globalAlpha=.75;ctx.fill();} else {ctx.strokeStyle=gone;ctx.globalAlpha=.9;ctx.lineWidth=1.2;ctx.stroke();}
    ctx.globalAlpha=1; }
  // picked: trail + dot + label
  const labels=[];
  for(const tm of picked){ const k=Math.floor(t); ctx.beginPath(); let started=false;
    for(let s=0;s<=k;s++){const a=at(tm,s); if(!a||a.n===0) continue; const x=X(a.n),y=Yp(a.p/a.n); started?ctx.lineTo(x,y):(ctx.moveTo(x,y),started=true);}
    const q=pos(tm,t); if(!q) continue; ctx.lineTo(X(q.n),Yp(q.w));
    ctx.strokeStyle=rust;ctx.globalAlpha=.55;ctx.lineWidth=1.4;ctx.stroke();ctx.globalAlpha=1;
    ctx.beginPath();ctx.arc(X(q.n),Yp(q.w),4.5,0,7);ctx.fillStyle=q.alive?rust:css('--paper');ctx.fill();ctx.strokeStyle=rust;ctx.lineWidth=1.6;ctx.stroke();
    labels.push({name:tm.name,x:X(q.n),y:Yp(q.w)-9}); }
  // labels: stack top to bottom so close records don't print on top of each other
  labels.sort((a,b)=>a.y-b.y); for(let i=1;i<labels.length;i++) if(labels[i].y-labels[i-1].y<14) labels[i].y=labels[i-1].y+14;
  ctx.font='600 12px "Roboto Mono",monospace';ctx.fillStyle=rust;ctx.textBaseline='middle';
  for(const l of labels){const right=l.x>W-120; ctx.textAlign=right?'right':'left'; ctx.fillText(l.name,l.x+(right?-8:8),l.y);}
  // header readouts
  const k=Math.floor(t);
  $('clock').textContent= mode==='cal'? (Y0+Math.min(k,NY-1)) : 'Season '+(k+1);
  $('counts').innerHTML= mode==='cal'
    ? `<span><b>${alive}</b> programs playing</span><span><b>${stopped}</b> have stopped</span><span><b>${T.length-alive-stopped}</b> not started yet</span>`
    : `<span><b>${alive}</b> programs still going at season ${k+1}</span><span><b>${stopped}</b> stopped before it</span>`;
  leaders();
}
let lastLeadKey='';
function leaders(){
  const k=Math.floor(t), key=mode+k+':'+picked.length; if(key===lastLeadKey) return; lastLeadKey=key;
  const rows=[]; for(const tm of T){const a=at(tm,k); if(a&&a.n>=300) rows.push({tm,w:a.p/a.n,n:a.n,alive:a.alive});}
  rows.sort((a,b)=>b.w-a.w);
  $('lead-h').textContent='Best all-time records, '+(mode==='cal'?(Y0+Math.min(k,NY-1)):'season '+(k+1));
  $('lead').innerHTML= rows.length? rows.slice(0,8).map((r,i)=>`<tr><td class="num" style="text-align:left;width:2em">${i+1}</td><td class="${r.alive?'':'gone'}">${r.tm.name}${r.alive?'':' (stopped)'}</td><td class="num">${r.w.toFixed(3).replace(/^0/,'')}</td><td class="num" style="width:6em">${Math.round(r.n).toLocaleString()} gms</td></tr>`).join('')
    : '<tr><td>No program has reached 300 games yet.</td></tr>';
}
// controls
const slider=$('t');
function setMax(){ slider.max= mode==='cal'? NY-1 : maxOwn; }
slider.addEventListener('input',()=>{t=+slider.value; stop(); draw();});
function stop(){playing=false;$('play').textContent='▶ Play';}
let prev=0;
function tick(ts){ if(!playing) return; const dt=Math.min(.1,(ts-prev)/1000); prev=ts;
  t+=dt*(+$('speed').value); const mx=+slider.max; if(t>=mx){t=mx;stop();}
  slider.value=Math.floor(t); draw(); if(playing) requestAnimationFrame(tick); }
$('play').addEventListener('click',()=>{ if(playing){stop();return;} if(t>=+slider.max) t=0; playing=true; $('play').textContent='❚❚ Pause'; prev=performance.now(); requestAnimationFrame(tick); });
function setMode(m){ mode=m; $('m-cal').setAttribute('aria-pressed',m==='cal'); $('m-own').setAttribute('aria-pressed',m==='own'); stop(); setMax(); t=+slider.max; slider.value=t; lastLeadKey=''; draw(); }
$('m-cal').addEventListener('click',()=>setMode('cal')); $('m-own').addEventListener('click',()=>setMode('own'));
// find
$('names').innerHTML=T.map(x=>`<option value="${x.name}">`).join('');
function chips(){ $('chips').innerHTML=picked.map((tm,i)=>`<span class="chip">${tm.name}<button type="button" data-i="${i}" aria-label="Remove ${tm.name}">×</button></span>`).join(''); }
$('chips').addEventListener('click',e=>{const b=e.target.closest('button'); if(!b) return; picked.splice(+b.dataset.i,1); chips(); lastLeadKey=''; draw();});
function add(){ const tm=byName.get($('q').value.trim().toLowerCase()); if(tm&&!picked.includes(tm)){picked.push(tm);chips();draw();} if(tm) $('q').value=''; }
$('q').addEventListener('change',add); $('q').addEventListener('keydown',e=>{if(e.key==='Enter')add();});
// hover
function hover(e){ const r=cv.getBoundingClientRect(), mx=e.clientX-r.left, my=e.clientY-r.top; let best=null,bd=100;
  for(const d of last){const dd=(d.x-mx)**2+(d.y-my)**2; if(dd<bd){bd=dd;best=d;}}
  if(!best){tip.hidden=true;return;}
  const tm=best.tm, yrs=`${Y0+tm.first}–${tm.last===NY-1?'':Y0+tm.last}`;
  tip.textContent=`${tm.name} · ${best.q.w.toFixed(3).replace(/^0/,'')} over ${Math.round(best.q.n).toLocaleString()} games · major ${yrs}`;
  tip.style.left=Math.min(Math.max(best.x,120),W-120)+'px'; tip.style.top=best.y+'px'; tip.hidden=false; }
cv.addEventListener('pointermove',hover); cv.addEventListener('pointerleave',()=>tip.hidden=true);
cv.addEventListener('click',e=>{ hover(e); const r=cv.getBoundingClientRect(); const d=last.find(d=>(d.x-(e.clientX-r.left))**2+(d.y-(e.clientY-r.top))**2<100); if(d&&!picked.includes(d.tm)){picked.push(d.tm);chips();draw();} });
new ResizeObserver(resize).observe(box);
matchMedia('(prefers-color-scheme: dark)').addEventListener('change',draw);
new MutationObserver(draw).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
chips(); setMax(); slider.value=t; resize();
if(document.fonts) document.fonts.ready.then(draw);
})();
