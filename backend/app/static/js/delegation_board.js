const esc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
}[ch]));

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

function matchesSearch(item, query) {
  if (!query) return true;
  const text = `${item.title || ""} ${item.summary || ""} ${item.owner || ""}`.toLowerCase();
  return text.includes(query.toLowerCase());
}

function renderCard(item) {
  return `
    <article class="delegation-card">
      <div class="meta">
        <span class="tag ${esc(item.status)}">${esc(item.status.replace("_"," "))}</span>
        <span class="tag">${esc(item.owner)}</span>
      </div>
      <h3>${esc(item.title)}</h3>
      <p>${esc(item.summary || "No summary provided.")}</p>
      ${item.note ? `<p><strong>Note:</strong> ${esc(item.note)}</p>` : ""}
      <div class="actions">
        ${item.status === "open" ? `<button class="primary" data-action="in_progress" data-id="${item.id}">Start</button>` : ""}
        ${item.status !== "done" && item.status !== "cancelled" ? `<button class="done" data-action="done" data-id="${item.id}">Mark done</button>` : ""}
        ${item.status !== "cancelled" && item.status !== "done" ? `<button class="cancel" data-action="cancelled" data-id="${item.id}">Cancel</button>` : ""}
      </div>
    </article>`;
}

async function loadDelegations() {
  const status = document.getElementById("statusFilter").value;
  const query = document.getElementById("searchBox").value.trim();

  const items = await api(status ? `/api/delegations?status=${encodeURIComponent(status)}` : "/api/delegations");
  const filtered = items.filter(item => matchesSearch(item, query));

  document.getElementById("openCount").textContent = items.filter(x => x.status === "open").length;
  document.getElementById("progressCount").textContent = items.filter(x => x.status === "in_progress").length;
  document.getElementById("doneCount").textContent = items.filter(x => x.status === "done").length;
  document.getElementById("ownerCount").textContent = new Set(items.map(x => x.owner)).size;

  document.getElementById("delegationList").innerHTML = filtered.length
    ? filtered.map(renderCard).join("")
    : `<article class="empty">No delegations match this view.</article>`;
}

document.addEventListener("click", async event => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  button.disabled = true;
  try {
    await api(`/api/delegations/${button.dataset.id}`, {
      method: "PATCH",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({status: button.dataset.action}),
    });
    await loadDelegations();
  } catch (error) {
    console.error(error);
    button.disabled = false;
  }
});

document.getElementById("refreshBtn").addEventListener("click", loadDelegations);
document.getElementById("statusFilter").addEventListener("change", loadDelegations);
document.getElementById("searchBox").addEventListener("input", loadDelegations);

loadDelegations().catch(console.error);
