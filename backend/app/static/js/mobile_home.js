const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
}[ch]));

function setGreeting() {
  const hour = new Date().getHours();
  const period = hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening";
  document.getElementById("greeting").textContent = `Good ${period}, Niranjan`;
  document.getElementById("dynamicTitle").textContent =
    hour < 12 ? "Morning view" : hour < 17 ? "Afternoon view" : "Evening view";
}

function renderDecision(item) {
  return `
    <article class="decision-card">
      <div class="tags">
        <span class="tag red">Decision</span>
        <span class="tag">${esc(item.domain)}</span>
      </div>
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.summary)}</p>
      <div class="tags">
        <span class="tag amber">Priority ${esc(item.brain_priority ?? item.priority)}</span>
        <span class="tag">${Math.round((item.confidence || 0) * 100)}% confidence</span>
      </div>
    </article>`;
}

function renderSignal(item) {
  return `
    <article class="signal-card">
      <div class="signal-top">
        <span class="signal-score">${esc(item.brain_priority ?? item.signal_score ?? 0)}</span>
        <span class="tag">${esc(item.attention_type || "signal")}</span>
      </div>
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.summary)}</p>
      <div class="tags">
        <span class="tag">${esc(item.category || "communication")}</span>
        <span class="tag">${esc(item.domain)}</span>
      </div>
    </article>`;
}

function renderHandledItem(item) {
  return `
    <article class="handled-card">
      <strong>${esc(item.title)}</strong>
      <p>${esc(item.summary)}</p>
      <span class="tag">${esc(item.attention_type || "handled")}</span>
    </article>`;
}

function renderDynamicCards(state) {
  const hour = new Date().getHours();
  const cards = [];

  if (hour < 12) {
    cards.push(
      ["Start with judgement", `${state.morning_brief.decisions} decisions require you.`],
      ["Quietly handled", `${state.morning_brief.ignored} items needed no action.`],
      ["Relationships", `${state.declining_relationships.length} relationships need watching.`],
      ["Time saved", `${state.morning_brief.estimated_minutes_saved} minutes estimated.`],
    );
  } else if (hour < 17) {
    cards.push(
      ["Execution", `${state.morning_brief.signals} active signals.`],
      ["Follow-ups", `${state.signals.filter(x => x.attention_type === "follow_up").length} follow-ups.`],
      ["Business world", "Focus on items crossing your thresholds."],
      ["Brain confidence", `${state.brain.confidence}% current confidence.`],
    );
  } else {
    cards.push(
      ["Day review", `${state.morning_brief.reviewed} items reviewed today.`],
      ["Noise removed", `${state.morning_brief.ignored} items handled quietly.`],
      ["Tomorrow", "Nexus will keep monitoring overnight."],
      ["Personal reset", "Capture any unfinished thought in Notes."],
    );
  }

  document.getElementById("dynamicCards").innerHTML = cards.map(([title, text]) => `
    <article class="dynamic-card"><strong>${esc(title)}</strong><p>${esc(text)}</p></article>
  `).join("");
}

function updateWorlds(state) {
  const byDomain = {business:0,family:0,personal:0,digital:0};
  [...state.decisions, ...state.signals].forEach(item => {
    if (item.domain in byDomain) byDomain[item.domain] += 1;
  });

  document.getElementById("businessWorld").textContent =
    byDomain.business ? `${byDomain.business} active item${byDomain.business === 1 ? "" : "s"}` : "Under control";
  document.getElementById("familyWorld").textContent =
    byDomain.family ? `${byDomain.family} active item${byDomain.family === 1 ? "" : "s"}` : "Quiet";
  document.getElementById("personalWorld").textContent =
    byDomain.personal ? `${byDomain.personal} active item${byDomain.personal === 1 ? "" : "s"}` : "Stable";
  document.getElementById("digitalWorld").textContent =
    byDomain.digital ? `${byDomain.digital} active item${byDomain.digital === 1 ? "" : "s"}` : "Monitoring";
}

function setupNotes() {
  const field = document.getElementById("quickNote");
  const status = document.getElementById("noteStatus");
  document.getElementById("saveNote").addEventListener("click", () => {
    const text = field.value.trim();
    if (!text) return;
    const notes = JSON.parse(localStorage.getItem("nexus-mobile-notes") || "[]");
    notes.unshift({text, created_at: new Date().toISOString()});
    localStorage.setItem("nexus-mobile-notes", JSON.stringify(notes.slice(0, 50)));
    field.value = "";
    status.textContent = "Saved";
    setTimeout(() => status.textContent = "", 1500);
  });
}

async function loadHome() {
  setGreeting();
  setupNotes();

  const response = await fetch("/api/brain/state");
  if (!response.ok) throw new Error("Brain API unavailable");
  const state = await response.json();

  document.getElementById("brainState").textContent =
    state.brain.state.charAt(0).toUpperCase() + state.brain.state.slice(1);
  document.getElementById("healthState").textContent =
    state.brain.health.charAt(0).toUpperCase() + state.brain.health.slice(1);

  const brief = state.morning_brief;
  document.getElementById("briefSummary").textContent = brief.summary;
  document.getElementById("reviewedCount").textContent = brief.reviewed;
  document.getElementById("ignoredCount").textContent = brief.ignored;
  document.getElementById("signalsCount").textContent = brief.signals;
  document.getElementById("decisionsCount").textContent = brief.decisions;
  document.getElementById("decisionPill").textContent = brief.decisions;
  document.getElementById("timeSaved").textContent = `${brief.estimated_minutes_saved} min`;

  document.getElementById("decisionCards").innerHTML = state.decisions.length
    ? state.decisions.map(renderDecision).join("")
    : `<article class="decision-card"><h3>Everything is under control</h3><p>No decisions need your judgement right now.</p></article>`;

  document.getElementById("signalCards").innerHTML = state.signals.length
    ? state.signals.map(renderSignal).join("")
    : `<article class="signal-card"><h3>No material changes</h3><p>Nexus is monitoring quietly.</p></article>`;

  const grouped = state.grouped_recruitment || [];
  const handled = [
    ...grouped.slice(0, 3),
    ...(state.memories || []).slice(0, 1).map(m => ({
      title: m.title,
      summary: m.content,
      attention_type: "memory",
    })),
  ];

  document.getElementById("handledCards").innerHTML = handled.length
    ? handled.map(renderHandledItem).join("")
    : `<article class="handled-card"><strong>Quiet processing</strong><p>No grouped updates to show.</p></article>`;

  updateWorlds(state);
  renderDynamicCards(state);
}

loadHome().catch(error => {
  console.error(error);
  document.getElementById("brainState").textContent = "Needs attention";
  document.getElementById("healthState").textContent = "Check system";
  document.getElementById("briefSummary").textContent = "Nexus could not load the Brain briefing.";
});
