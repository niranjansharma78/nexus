const e=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
function card(x,type){
 const label=type==="needs_you"?"Needs you":type==="delegate"?"Delegate":type==="monitor"?"Monitor":"Handled";
 return `<article class="${type==="monitor"?"signal-card":"decision-card"}"><div class="tags"><span class="tag ${type==="needs_you"?"red":type==="delegate"?"amber":""}">${label}</span><span class="tag">${e(x.category)}</span>${x.owner?`<span class="tag">${e(x.owner)}</span>`:""}</div><h3>${e(x.title)}</h3><p>${e(x.summary)}</p>${window.nexusActionButtons ? window.nexusActionButtons(x,type) : ""}</article>`;
}
async function loadExecutiveBrief(){
 const r=await fetch("/api/executive-brief"); if(!r.ok)return;
 const b=await r.json();
 briefSummary.textContent=b.headline;
 reviewedCount.textContent=b.summary.reviewed;
 ignoredCount.textContent=b.summary.hidden;
 decisionsCount.textContent=b.summary.needs_you;
 timeSaved.textContent=`${b.summary.estimated_minutes_saved} min`;
 const action=[...b.needs_you.map(x=>card(x,"needs_you")),...b.delegate.map(x=>card(x,"delegate"))];
 decisionCards.innerHTML=action.length?action.join(""):'<article class="decision-card"><h3>No judgement needed</h3><p>No decisions or delegations require you.</p></article>';
 signalCards.innerHTML=b.monitor.length?b.monitor.map(x=>card(x,"monitor")).join(""):'<article class="signal-card"><h3>No important changes</h3><p>Nexus is monitoring quietly.</p></article>';
 handledCards.innerHTML=b.handled.length?b.handled.map(x=>card(x,"handled")).join(""):'<article class="handled-card"><strong>Quiet processing</strong><p>No grouped updates.</p></article>';
}
loadExecutiveBrief().catch(console.error);
