const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));
async function load(){
 const p=new URLSearchParams({limit:"300"});
 [["q",q.value.trim()],["source",source.value],["domain",domain.value],["category",category.value],["min_signal",signal.value]].forEach(([k,v])=>{if(v)p.set(k,v)});
 const items=await(await fetch(`/api/developer/evidence?${p}`)).json();
 count.textContent=`${items.length} evidence items`;
 cards.innerHTML=items.map(x=>`<article class="e"><span class="tag">${esc(x.source)}</span><h3>${esc(x.title)}</h3><p>${esc(x.summary)}</p><div class="tags"><span class="tag">${esc(x.domain)}</span><span class="tag">${esc(x.category)}</span><span class="tag">Signal ${x.signal_score}</span><span class="tag">${Math.round(x.confidence*100)}%</span>${x.requires_decision?'<span class="tag">Decision</span>':''}</div></article>`).join("");
}
apply.addEventListener("click",load);q.addEventListener("keydown",e=>{if(e.key==="Enter")load()});load();
