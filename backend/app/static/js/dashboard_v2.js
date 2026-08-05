const icons = {
  finance:"💰",
  business:"💼",
  family:"👨‍👩‍👧",
  calendar:"📅",
  personal:"🙋",
  timeline:"🕘",
  notes:"📝",
  projects:"📌"
};

const defaultTiles = [
  {id:"business",title:"Business",domain:"business"},
  {id:"family",title:"Family",domain:"family"},
  {id:"personal",title:"Personal",domain:"personal"},
  {id:"calendar",title:"Calendar",domain:"digital"},
  {id:"finance",title:"Finance",domain:"business"},
  {id:"notes",title:"Notes",domain:"personal"},
  {id:"timeline",title:"Timeline",domain:"digital"},
  {id:"projects",title:"Projects",domain:"business"}
];

function esc(value){
  return String(value ?? "").replace(/[&<>"']/g,ch=>({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[ch]));
}

function setGreeting(){
  const hour = new Date().getHours();
  const period = hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
  document.getElementById("greeting").textContent = `Good ${period}, Niranjan`;
}

function renderTiles(tiles){
  const grid = document.getElementById("workspaceGrid");
  const source = tiles?.length ? tiles : defaultTiles;
  grid.innerHTML = source.map(t=>`
    <article class="tile" draggable="true" data-id="${esc(t.id)}">
      <div class="tile-icon">${icons[t.id] || "◆"}</div>
      <h3>${esc(t.title)}</h3>
      <small>${esc(t.domain)}</small>
    </article>`).join("");
  enableDragging();
}

function enableDragging(){
  const grid = document.getElementById("workspaceGrid");
  let active = null;
  grid.querySelectorAll(".tile").forEach(tile=>{
    tile.addEventListener("dragstart",()=>{
      active=tile;
      tile.classList.add("dragging");
    });
    tile.addEventListener("dragend",async()=>{
      tile.classList.remove("dragging");
      active=null;
      const tile_ids=[...grid.children].map(x=>x.dataset.id);
      try{
        await fetch("/api/workspace/order",{
          method:"PUT",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({tile_ids})
        });
      }catch(e){console.error(e)}
    });
  });
  grid.addEventListener("dragover",event=>{
    event.preventDefault();
    if(!active) return;
    const siblings=[...grid.querySelectorAll(".tile:not(.dragging)")];
    const next=siblings.find(s=>event.clientY <= s.getBoundingClientRect().top+s.offsetHeight/2);
    grid.insertBefore(active,next || null);
  });
}

function renderNotes(){
  const notes = JSON.parse(localStorage.getItem("nexus-notes") || "[]");
  document.getElementById("recentNotes").innerHTML = notes.slice(0,3).map(n=>
    `<div class="recent-note">${esc(n.text)}<br><small>${esc(n.time)}</small></div>`
  ).join("");
}

document.getElementById("saveNote").addEventListener("click",()=>{
  const field=document.getElementById("quickNote");
  const text=field.value.trim();
  if(!text) return;
  const notes=JSON.parse(localStorage.getItem("nexus-notes") || "[]");
  notes.unshift({text,time:new Date().toLocaleString()});
  localStorage.setItem("nexus-notes",JSON.stringify(notes.slice(0,20)));
  field.value="";
  document.getElementById("noteStatus").textContent="Saved";
  renderNotes();
  setTimeout(()=>document.getElementById("noteStatus").textContent="",1600);
});

function signalCard(x){
  const score = x.signal_score ?? 0;
  return `
    <article class="signal-card">
      <div class="signal-top">
        <span class="signal-score">${score}</span>
        <span class="badge">${esc(x.domain)}</span>
      </div>
      <h3>${esc(x.title)}</h3>
      <p>${esc(x.summary)}</p>
      <div class="card-meta">
        <span class="badge">${esc(x.category || "uncategorized")}</span>
        <span class="badge">${Math.round((x.confidence || 0)*100)}%</span>
        ${x.requires_decision ? '<span class="badge red">Decision</span>' : ""}
      </div>
    </article>`;
}

async function load(){
  setGreeting();
  const dashboard = await (await fetch("/api/dashboard")).json();
  let intelligence = {reviewed_24h:0,new_imap_24h:0,high_signal_24h:0,decisions_24h:0,signals:[],estimated_minutes_saved:0};
  try{
    const r=await fetch("/api/dashboard-intelligence");
    if(r.ok) intelligence=await r.json();
  }catch(e){console.warn(e)}

  const confidence = dashboard.summary?.confidence ?? 0;
  document.getElementById("confidenceScore").textContent=confidence;
  document.getElementById("confidenceRing").style.background=
    `conic-gradient(var(--blue) ${confidence*3.6}deg,#e4e8f0 0deg)`;
  document.getElementById("confidenceText").textContent=
    confidence >= 90 ? "Everything important has been checked." : "Some evidence still needs verification.";

  document.getElementById("sensorCount").textContent=(dashboard.summary?.sources || []).length;
  document.getElementById("heroSummary").textContent=
    intelligence.decisions_24h
      ? `I've already reviewed the noise. ${intelligence.decisions_24h} decisions need your attention.`
      : "Everything important is under control.";

  const stats=[
    [intelligence.reviewed_24h,"Reviewed"],
    [intelligence.new_imap_24h,"Email evidence"],
    [intelligence.high_signal_24h,"High signals"],
    [intelligence.decisions_24h,"Decisions"],
    [`${intelligence.estimated_minutes_saved} min`,"Estimated saved"]
  ];
  document.getElementById("workStats").innerHTML=stats.map(([v,l])=>
    `<div class="work-stat"><strong>${esc(v)}</strong><small>${esc(l)}</small></div>`
  ).join("");

  const decisions=dashboard.decisions || [];
  document.getElementById("decisionCount").textContent=decisions.length;
  document.getElementById("decisionGrid").innerHTML=decisions.length
    ? decisions.map(x=>`
      <article class="decision-card">
        <span class="badge red">${esc(x.domain)}</span>
        <h3>${esc(x.title)}</h3>
        <p>${esc(x.summary)}</p>
        <div class="card-meta">
          <span class="badge">${Math.round((x.confidence||0)*100)}% confidence</span>
          <span class="badge amber">Priority ${esc(x.priority)}</span>
        </div>
      </article>`).join("")
    : `<article class="decision-card"><h3>Quiet period</h3><p>No decisions are pending.</p></article>`;

  renderTiles(dashboard.workspace || defaultTiles);

  document.getElementById("signalGrid").innerHTML=(intelligence.signals || []).length
    ? intelligence.signals.slice(0,6).map(signalCard).join("")
    : `<article class="signal-card"><h3>No material changes</h3><p>Nexus is monitoring quietly.</p></article>`;

  const dynamic=(dashboard.timeline || []).slice(0,8);
  document.getElementById("dynamicGrid").innerHTML=dynamic.map(x=>`
    <article class="dynamic-card">
      <strong>${esc(x.title)}</strong>
      <p>${esc(x.summary)}</p>
      <span class="badge">${esc(x.domain)}</span>
    </article>`).join("");

  renderNotes();
}

load().catch(error=>{
  console.error(error);
  document.getElementById("brainState").textContent="Needs attention";
  document.getElementById("heartbeatState").textContent="Check system";
});
