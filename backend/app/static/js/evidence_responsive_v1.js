(function () {
  function findEvidenceTables() {
    const explicit = [
      ...document.querySelectorAll(
        "table.evidence-table, .evidence-table, table[data-evidence-table]"
      )
    ];

    if (explicit.length) return explicit;

    return [...document.querySelectorAll("table")].filter(table => {
      const text = (table.innerText || "").toLowerCase();
      return (
        text.includes("evidence") ||
        text.includes("summary") ||
        text.includes("confidence") ||
        text.includes("occurred")
      );
    });
  }

  function addLabels(table) {
    const headers = [...table.querySelectorAll("thead th")].map(th =>
      (th.textContent || "").trim()
    );

    if (!headers.length) return;

    table.classList.add("evidence-table");
    table.setAttribute("data-evidence-table", "true");

    [...table.querySelectorAll("tbody tr")].forEach(row => {
      [...row.children].forEach((cell, index) => {
        if (!cell.dataset.label) {
          cell.dataset.label = headers[index] || `Field ${index + 1}`;
        }
      });
    });
  }

  function constrainPage() {
    document.documentElement.style.overflowX = "hidden";
    document.body.style.overflowX = "hidden";

    findEvidenceTables().forEach(addLabels);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", constrainPage);
  } else {
    constrainPage();
  }

  const observer = new MutationObserver(constrainPage);
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true
  });
})();
