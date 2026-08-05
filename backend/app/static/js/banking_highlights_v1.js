const bankEsc = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
  "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
}[ch]));

function formatMoney(value) {
  if (value === null || value === undefined) return "—";

  const number = Number(value);

  if (number >= 10000000) {
    return `₹${(number / 10000000).toFixed(2).replace(/\.00$/, "")} Cr`;
  }

  if (number >= 100000) {
    return `₹${(number / 100000).toFixed(2).replace(/\.00$/, "")} L`;
  }

  return `₹${number.toLocaleString("en-IN", {
    maximumFractionDigits: 2
  })}`;
}

async function loadBankingHighlights() {
  const response = await fetch("/api/banking-highlights?hours=72&limit=3");
  if (!response.ok) return;

  const data = await response.json();
  const target = document.getElementById("bankingHighlights");
  if (!target) return;

  const totals = data.totals || {
    credit: 0,
    debit: 0,
    bounce_count: 0,
  };

  target.innerHTML = `
    <div class="cash-summary-card">
      <div class="cash-summary-top">
        <div>
          <span>Credits</span>
          <strong class="cash-credit">${bankEsc(formatMoney(totals.credit))}</strong>
        </div>
        <div>
          <span>Debits</span>
          <strong class="cash-debit">${bankEsc(formatMoney(totals.debit))}</strong>
        </div>
        <div class="${totals.bounce_count ? "cash-alert-active" : ""}">
          <span>Cheque Bounce</span>
          <strong>${bankEsc(totals.bounce_count)}</strong>
        </div>
      </div>

      <div class="cash-latest">
        ${data.items.length
          ? data.items.map(item => {
              const type = item.direction === "credit"
                ? "Credit"
                : item.direction === "debit"
                ? "Debit"
                : "Bounce";

              const source = item.source === "Source not identified"
                ? item.bank
                : `${item.bank} · ${item.source}`;

              return `
                <div class="cash-latest-row ${bankEsc(item.direction)}">
                  <span class="cash-type">${bankEsc(type)}</span>
                  <span class="cash-source">${bankEsc(source)}</span>
                  <strong>${bankEsc(formatMoney(item.amount))}</strong>
                </div>`;
            }).join("")
          : '<div class="cash-empty">No recent banking transaction detected</div>'}
      </div>
    </div>`;
}

loadBankingHighlights().catch(console.error);
