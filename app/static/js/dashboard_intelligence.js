function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[ch]));
}
function signalCard(item) {
  return `<article class="signal ${item.requires_decision ? 'decision-signal' : ''}">
    <div class="signal-top"><span class="signal-score">${item.signal_score}</span><span class="signal-domain">${escapeHtml(item.domain)}</span></div>
    <h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.summary)}</p>
    <div class="signal-meta"><span>${escapeHtml(item.category)}</span><span>${Math.round(item.confidence*100)}% confidence</span>${item.requires_decision ? '<strong>Decision required</strong>' : ''}</div>
  </article>`;
}
async function loadDashboardIntelligence() {
  const response = await fetch('/api/dashboard-intelligence');
  const data = await response.json();
  const strip = document.getElementById('nexusWorkStrip');
  if (strip) strip.innerHTML = `
    <div><b>${data.reviewed_24h}</b><small>reviewed in 24h</small></div>
    <div><b>${data.new_imap_24h}</b><small>new email evidence</small></div>
    <div><b>${data.high_signal_24h}</b><small>high signals</small></div>
    <div><b>${data.decisions_24h}</b><small>decisions</small></div>
    <div><b>${data.estimated_minutes_saved} min</b><small>estimated saved</small></div>`;
  const signals = document.getElementById('signalsGrid');
  if (signals) signals.innerHTML = data.signals.length ? data.signals.map(signalCard).join('') : '<article class="signal"><h3>Quiet period</h3><p>No material signals detected.</p></article>';
  const processed = document.getElementById('processedSummary');
  if (processed) processed.textContent = data.categories.map(x => `${x.category} ${x.count}`).join(' · ') || 'No new categories detected.';
}
loadDashboardIntelligence().catch(console.error);
