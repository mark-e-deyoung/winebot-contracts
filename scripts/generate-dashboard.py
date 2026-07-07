#!/usr/bin/env python3
"""Generate a conformance history dashboard HTML from compiled results.

Usage:
    python3 scripts/generate-dashboard.py \
        --history dashboard/history.json \
        --output dashboard/index.html
"""

import argparse
import json
import os


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WineBot/WinBot Conformance Dashboard</title>
<style>
  :root {
    --bg: #0d1117; --card: #161b22; --border: #30363d;
    --text: #c9d1d9; --text-muted: #8b949e;
    --green: #3fb950; --red: #f85149; --yellow: #d29922;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
         background: var(--bg); color: var(--text); padding: 20px; }
  h1 { font-size: 24px; margin-bottom: 4px; }
  .subtitle { color: var(--text-muted); font-size: 14px; margin-bottom: 24px; }
  .summary-row { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px;
          padding: 16px; flex: 1; min-width: 200px; }
  .card h3 { font-size: 12px; text-transform: uppercase; color: var(--text-muted);
             margin-bottom: 8px; letter-spacing: 0.5px; }
  .card .value { font-size: 28px; font-weight: 600; }
  .card .value.green { color: var(--green); }
  .card .value.red { color: var(--red); }
  .card .value.yellow { color: var(--yellow); }
  table { width: 100%; border-collapse: collapse; margin-bottom: 24px; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
  th { font-size: 12px; text-transform: uppercase; color: var(--text-muted); }
  td { font-size: 14px; font-family: 'SF Mono','Cascadia Code','Consolas',monospace; }
  .pass { color: var(--green); }
  .fail { color: var(--red); }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px;
           font-size: 11px; font-weight: 600; }
  .badge.pass { background: rgba(63,185,80,0.15); color: var(--green); }
  .badge.fail { background: rgba(248,81,73,0.15); color: var(--red); }
  .chart { margin: 24px 0; }
  .bar-row { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
  .bar-label { font-size: 12px; color: var(--text-muted); width: 100px; flex-shrink: 0; }
  .bar-track { flex: 1; height: 20px; background: var(--border); border-radius: 4px; overflow: hidden; }
  .bar-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
  .bar-fill.pass { background: var(--green); }
  .bar-fill.fail { background: var(--red); }
  .bar-pct { font-size: 12px; width: 50px; text-align: right; }
  .footer { font-size: 12px; color: var(--text-muted); margin-top: 32px; padding-top: 16px;
            border-top: 1px solid var(--border); }
</style>
</head>
<body>
<h1>🧪 WineBot / WinBot Conformance Dashboard</h1>
<p class="subtitle">Historical pass rates from shared <code>winebot-contracts</code> conformance test suite</p>

<div class="summary-row" id="summary"></div>

<div class="card" style="margin-bottom: 24px;">
  <h3>Per-Platform History</h3>
  <div id="platformHistory"></div>
</div>

<div class="card" style="margin-bottom: 24px;">
  <h3>Recent Runs</h3>
  <div style="overflow-x: auto;">
    <table>
      <thead><tr>
        <th>Date</th><th>Platform</th><th>Passed</th><th>Failed</th><th>Rate</th><th>Status</th>
      </tr></thead>
      <tbody id="runTable"></tbody>
    </table>
  </div>
</div>

<div class="footer" id="footer"></div>

<script>
const DATA = %DATA%;

function render() {
  // Summary cards
  const summary = document.getElementById('summary');
  summary.innerHTML = '';
  const totalRuns = DATA.total_runs || 0;
  const platKeys = Object.keys(DATA.platforms || {});

  const overallCard = document.createElement('div'); overallCard.className = 'card';
  overallCard.innerHTML = '<h3>Total Runs</h3><div class="value">' + totalRuns + '</div>';
  summary.appendChild(overallCard);

  for (const [plat, pdata] of Object.entries(DATA.platforms || {})) {
    const card = document.createElement('div'); card.className = 'card';
    const rate = pdata.total_tests > 0 ? Math.round(pdata.total_passed / pdata.total_tests * 100) : 0;
    const cls = rate >= 90 ? 'green' : rate >= 50 ? 'yellow' : 'red';
    card.innerHTML = '<h3>' + plat + '</h3>'
      + '<div class="value ' + cls + '">' + rate + '%</div>'
      + '<div style="font-size:12px;color:var(--text-muted);margin-top:4px;">'
      + pdata.total_passed + '/' + pdata.total_tests + ' passed (' + pdata.runs + ' runs)</div>';
    summary.appendChild(card);
  }

  // Platform history
  const histDiv = document.getElementById('platformHistory');
  histDiv.innerHTML = '';
  for (const [plat, pdata] of Object.entries(DATA.platforms || {})) {
    if (!pdata.history || pdata.history.length === 0) continue;
    const block = document.createElement('div'); block.style.marginBottom = '16px';
    block.innerHTML = '<h4 style="margin-bottom:8px;">' + plat + '</h4>';
    const recent = pdata.history.slice(-10);
    for (const run of recent) {
      const dt = new Date(run.timestamp).toLocaleDateString();
      const pct = run.pass_rate;
      const cls = pct >= 90 ? 'pass' : pct >= 50 ? 'yellow' : 'fail';
      const row = document.createElement('div'); row.className = 'bar-row';
      row.innerHTML = '<span class="bar-label">' + dt + '</span>'
        + '<div class="bar-track"><div class="bar-fill ' + cls + '" style="width:' + pct + '%;"></div></div>'
        + '<span class="bar-pct">' + pct + '%</span>';
      block.appendChild(row);
    }
    histDiv.appendChild(block);
  }

  // Recent runs table
  const table = document.getElementById('runTable');
  table.innerHTML = '';
  const allRuns = [...(DATA.runs || [])].reverse().slice(0, 30);
  for (const run of allRuns) {
    const dt = new Date(run.timestamp).toLocaleString();
    const plat = (run.platform && run.platform.name) || 'unknown';
    const s = run.summary;
    const cls = s.failed === 0 ? 'pass' : 'fail';
    const label = s.failed === 0 ? '✅ PASS' : '❌ FAIL';
    const tr = document.createElement('tr');
    tr.innerHTML = '<td>' + dt + '</td><td>' + plat + '</td>'
      + '<td class="pass">' + s.passed + '/' + s.total + '</td>'
      + '<td class="' + cls + '">' + s.failed + '</td>'
      + '<td>' + s.pass_rate + '%</td>'
      + '<td><span class="badge ' + cls + '">' + label + '</span></td>';
    table.appendChild(tr);
  }

  // Footer
  document.getElementById('footer').innerHTML =
    'Last updated: ' + (DATA.last_updated ? new Date(DATA.last_updated).toLocaleString() : 'never')
    + ' &middot; Dashboard auto-generated from <a href="https://github.com/mark-e-deyoung/winebot-contracts" style="color:var(--green);">winebot-contracts</a>';
}

render();
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate conformance dashboard HTML")
    parser.add_argument("--history", default="history.json", help="Compiled history JSON path")
    parser.add_argument("--output", default="index.html", help="Output HTML path")
    args = parser.parse_args()

    if not os.path.exists(args.history):
        print(f"History file not found: {args.history}")
        print("Generating empty dashboard...")
        data = {"total_runs": 0, "platforms": {}, "runs": [], "last_updated": ""}
    else:
        with open(args.history) as f:
            data = json.load(f)

    html = HTML_TEMPLATE.replace("%DATA%", json.dumps(data))

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        f.write(html)

    print(f"Dashboard generated: {args.output}")
    print(f"  Platforms: {list(data.get('platforms', {}).keys())}")
    print(f"  Total runs: {data.get('total_runs', 0)}")


if __name__ == "__main__":
    main()
