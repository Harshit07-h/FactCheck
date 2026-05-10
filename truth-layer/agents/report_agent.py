"""
Report Agent — generates CSV, JSON, and HTML reports.
Fields: claim, type, status, confidence, reasoning, evidence sources.
(corrected_fact and page removed)
"""

import csv
import io
from datetime import datetime
from typing import List, Dict


class ReportAgent:

    def to_csv(self, results: List[Dict]) -> str:
        output = io.StringIO()
        fieldnames = [
            "claim", "type", "status", "confidence", "reasoning",
            "evidence_source_1", "evidence_url_1",
            "evidence_source_2", "evidence_url_2",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            row = {
                "claim":      r.get("claim", ""),
                "type":       r.get("type", ""),
                "status":     r.get("status", ""),
                "confidence": r.get("confidence", ""),
                "reasoning":  r.get("reasoning", ""),
            }
            ev = r.get("evidence", [])
            if len(ev) > 0:
                row["evidence_source_1"] = ev[0].get("source", "")
                row["evidence_url_1"]    = ev[0].get("url", "")
            if len(ev) > 1:
                row["evidence_source_2"] = ev[1].get("source", "")
                row["evidence_url_2"]    = ev[1].get("url", "")
            writer.writerow(row)
        return output.getvalue()

    def to_html(self, results: List[Dict], filename: str = "document.pdf") -> str:
        now       = datetime.now().strftime("%B %d, %Y at %H:%M")
        verified  = sum(1 for r in results if r.get("status") == "VERIFIED")
        inaccurate = sum(1 for r in results if r.get("status") == "INACCURATE")
        false_cnt  = sum(1 for r in results if r.get("status") == "FALSE")

        status_colors  = {"VERIFIED":"#00d4aa","INACCURATE":"#ffd93d","FALSE":"#ff6b6b"}
        status_emojis  = {"VERIFIED":"✅","INACCURATE":"⚠️","FALSE":"❌"}

        rows_html = ""
        for r in results:
            status = r.get("status","UNKNOWN")
            color  = status_colors.get(status, "#888")
            emoji  = status_emojis.get(status, "❓")
            ev_links = "".join(
                f'<a href="{e.get("url","#")}" target="_blank">{e.get("source","Unknown")}</a><br>'
                for e in r.get("evidence",[])[:2]
            ) or "—"
            corrected = r.get("corrected_fact","") or ""
            corrected_html = (
                f'<div style="background:rgba(255,107,107,0.1);border-left:2px solid #ff6b6b;padding:6px 10px;border-radius:0 6px 6px 0;font-size:0.82em;margin-top:4px">'
                f'<strong style="color:#ff6b6b">✏️ Correct:</strong> {corrected}</div>'
            ) if corrected and status in ("FALSE","INACCURATE") else ""
            rows_html += f"""
            <tr>
                <td style="max-width:280px">{r.get("claim","")}{corrected_html}</td>
                <td><span class="badge" style="background:{color}20;color:{color};border:1px solid {color}">
                    {emoji} {status}</span></td>
                <td>{r.get("confidence",0)}%</td>
                <td style="font-size:0.85em;max-width:240px">{r.get("reasoning","")}</td>
                <td style="font-size:0.8em">{ev_links}</td>
            </tr>"""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fact-Check AI – Fact-Check Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&display=swap');
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Syne',sans-serif;background:#080c14;color:#e2e8f0;padding:2rem}}
  .header{{text-align:center;padding:3rem 0 2rem;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:2rem}}
  .header h1{{font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#00d4aa,#6bcbff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
  .header p{{color:#64748b;margin-top:0.5rem}}
  .summary{{display:flex;gap:1rem;margin-bottom:2rem;flex-wrap:wrap}}
  .metric-card{{background:#0f1623;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:1.5rem 2rem;flex:1;min-width:130px;text-align:center}}
  .metric-card .num{{font-size:2.2rem;font-weight:800}}
  .metric-card .label{{font-size:0.8rem;color:#64748b;margin-top:0.2rem}}
  table{{width:100%;border-collapse:collapse;background:#0f1623;border-radius:12px;overflow:hidden}}
  th{{background:#161f2e;padding:0.75rem 1rem;text-align:left;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.05em;color:#64748b}}
  td{{padding:0.9rem 1rem;border-bottom:1px solid rgba(255,255,255,0.05);vertical-align:top;font-size:0.88rem}}
  tr:last-child td{{border-bottom:none}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:700}}
  a{{color:#6bcbff;text-decoration:none}}
  a:hover{{text-decoration:underline}}
  .footer{{text-align:center;margin-top:2rem;color:#64748b;font-size:0.8rem}}
</style>
</head>
<body>
<div class="header">
  <h1>🔍 Fact-Check AI</h1>
  <p>PDF Fact-Check Report · {now}</p>
  <p style="margin-top:0.4rem;font-size:0.9rem">Document: <strong>{filename}</strong></p>
</div>
<div class="summary">
  <div class="metric-card"><div class="num">{len(results)}</div><div class="label">Total Claims</div></div>
  <div class="metric-card"><div class="num" style="color:#00d4aa">{verified}</div><div class="label">✅ Verified</div></div>
  <div class="metric-card"><div class="num" style="color:#ffd93d">{inaccurate}</div><div class="label">⚠️ Inaccurate</div></div>
  <div class="metric-card"><div class="num" style="color:#ff6b6b">{false_cnt}</div><div class="label">❌ False</div></div>
</div>
<table>
  <thead><tr><th>Claim</th><th>Status</th><th>Confidence</th><th>Reasoning</th><th>Sources</th></tr></thead>
  <tbody>{rows_html}</tbody>
</table>
<div class="footer"><p>Generated by Fact-Check AI · AI-Powered PDF Fact Verification</p></div>
</body>
</html>"""