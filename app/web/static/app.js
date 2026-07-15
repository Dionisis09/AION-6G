async function runOrchestration() {
  const payload = {
    request: document.getElementById('request').value,
    policy: document.getElementById('policy').value,
    scenario: document.getElementById('scenario').value,
    fallback_allowed: true
  };
  const response = await fetch('/api/v1/orchestrate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  document.getElementById('intentOutput').textContent = JSON.stringify(data.intent, null, 2);
  const rows = ['<tr><th>Target</th><th>Eligible</th><th>Score</th><th>Reasons</th></tr>'];
  for (const candidate of data.candidates || []) {
    rows.push(`<tr><td>${candidate.target}</td><td>${candidate.eligible}</td><td>${candidate.score ?? 'n/a'}</td><td>${(candidate.rejection_reasons || []).join(', ') || 'none'}</td></tr>`);
  }
  document.getElementById('candidates').innerHTML = rows.join('');
  document.getElementById('executionOutput').textContent = JSON.stringify({
    execution: data.execution,
    verification: data.verification,
    fallback: data.fallback,
    orchestration_time_ms: data.orchestration_time_ms,
    network_data_type: data.network_data_type
  }, null, 2);
}
