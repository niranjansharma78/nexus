function actionEsc(value) {
  return String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[ch]));
}

async function postJson(url, payload, method = "POST") {
  const response = await fetch(url, {
    method,
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Action failed");
  }

  return response.json();
}

function actionButtons(item, type) {
  const owner = item.owner || "Team";

  if ((type === "delegate" || type === "monitor") && owner && !item.delegated) {
    return `
      <div class="brief-actions">
        <button class="delegate-btn"
          data-id="${actionEsc(item.id)}"
          data-title="${actionEsc(item.title)}"
          data-summary="${actionEsc(item.summary)}"
          data-owner="${actionEsc(owner)}">
          Delegate to ${actionEsc(owner)}
        </button>
        ${type === "monitor" && item.id ? `
          <button class="monitor-btn secondary-action" data-id="${actionEsc(item.id)}">
            Acknowledge
          </button>` : ""}
      </div>`;
  }

  if ((type === "delegate" || type === "monitor") && item.delegated) {
    return `
      <div class="brief-actions">
        <button class="done-action" disabled>Already delegated</button>
        ${type === "monitor" && item.id ? `
          <button class="monitor-btn secondary-action" data-id="${actionEsc(item.id)}">
            Acknowledge
          </button>` : ""}
      </div>`;
  }

  if (type === "monitor" && item.id) {
    return `
      <div class="brief-actions">
        <button class="monitor-btn secondary-action" data-id="${actionEsc(item.id)}">
          Acknowledge
        </button>
      </div>`;
  }

  return "";
}

document.addEventListener("click", async event => {
  const delegateButton = event.target.closest(".delegate-btn");

  if (delegateButton) {
    delegateButton.disabled = true;
    delegateButton.textContent = "Creating task…";

    try {
      await postJson("/api/delegations", {
        evidence_id: Number(delegateButton.dataset.id) || null,
        title: delegateButton.dataset.title,
        summary: delegateButton.dataset.summary,
        owner: delegateButton.dataset.owner,
      });

      delegateButton.textContent = "Delegated";
      delegateButton.classList.add("done-action");

      const card = delegateButton.closest("article");
      if (card) {
        const tagArea = card.querySelector(".tags");
        if (tagArea && !tagArea.querySelector(".delegated-tag")) {
          tagArea.insertAdjacentHTML(
            "beforeend",
            '<span class="tag delegated-tag">Delegated</span>'
          );
        }
      }
    } catch (error) {
      console.error(error);
      delegateButton.disabled = false;
      delegateButton.textContent = "Try again";
    }

    return;
  }

  const monitorButton = event.target.closest(".monitor-btn");

  if (monitorButton) {
    monitorButton.disabled = true;
    monitorButton.textContent = "Saving…";

    try {
      await postJson("/api/delegations/monitor", {
        evidence_id: Number(monitorButton.dataset.id),
        status: "acknowledged",
      });

      const card = monitorButton.closest("article");
      if (card) {
        card.style.opacity = "0";
        card.style.transform = "translateY(-6px)";
        setTimeout(() => card.remove(), 220);
      }
    } catch (error) {
      console.error(error);
      monitorButton.disabled = false;
      monitorButton.textContent = "Try again";
    }
  }
});

window.nexusActionButtons = actionButtons;
