"""TJ Cortex Command Center - zero-dependency dashboard foundation.

The dashboard reads real local ledgers/provider configuration and never invents
business telemetry. It is intentionally stdlib-only so it can run on a small VPS
or local machine without a paid service.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from ai_ceo import AICEO
from ai_provider import provider_from_env
from order_engine import load_orders
from payment_tracker import pending_payments, verified_payments, verified_revenue


HOST = "127.0.0.1"
PORT = 8080


def _safe_list(loader):
    try:
        return loader()
    except Exception:
        return None


def build_snapshot():
    """Return dashboard telemetry derived only from real engine state."""
    orders = _safe_list(load_orders)
    payments = _safe_list(verified_payments)
    pending = _safe_list(pending_payments)
    revenue = None
    if payments is not None:
        try:
            revenue = verified_revenue()
        except Exception:
            revenue = None

    if orders is None or payments is None or pending is None or revenue is None:
        ledger_status = "DEGRADED"
        orders_count = verified_count = pending_count = 0
        revenue_value = None
    else:
        ledger_status = "ONLINE"
        orders_count = len(orders)
        verified_count = len(payments)
        pending_count = len(pending)
        revenue_value = revenue

    state = {
        "market_researched": False,
        "has_product": orders_count > 0,
        "prospects_found": 0,
        "qualified_prospects": 0,
        "outreach_drafts": 0,
        "approved_outreach": 0,
        "pending_orders": pending_count,
        "recent_failures": 0,
    }
    try:
        decision = AICEO().decide(state)
        ceo = {
            "action": decision.action,
            "priority": decision.priority,
            "reason": decision.reason,
            "approval_required": decision.approval_required,
        }
    except Exception as error:
        ceo = {"action": "unavailable", "priority": 0, "reason": type(error).__name__, "approval_required": True}

    try:
        provider = provider_from_env()
        provider_config = {"mode": provider.mode, "model": provider.model, "base_url": provider.base_url}
    except Exception as error:
        provider_config = {"mode": "invalid", "model": "", "base_url": "", "error": type(error).__name__}

    return {
        "system": "TJ Cortex",
        "version": "command-center-1",
        "ledger": ledger_status,
        "orders": orders_count,
        "verified_payments": verified_count,
        "pending_payments": pending_count,
        "verified_revenue": revenue_value,
        "currency": "USD",
        "ceo": ceo,
        "ai_provider": provider_config,
        "governance": {"external_actions": "approval-gated", "money_movement": "blocked-by-default"},
    }


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TJ Cortex — Command Center</title>
<style>
:root{--bg:#050711;--panel:#0b1020;--line:#1c2b4a;--cyan:#39e7ff;--violet:#a56cff;--text:#e8f3ff;--muted:#7e91ae;--good:#52f2a3;--warn:#ffd166}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 75% 5%,#17204a 0,#080b18 35%,var(--bg) 70%);color:var(--text);font:14px/1.5 system-ui,sans-serif;min-height:100vh}
.wrap{max-width:1400px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:24px}.brand{display:flex;align-items:center;gap:14px}.mark{width:46px;height:46px;border:1px solid var(--cyan);border-radius:14px;box-shadow:0 0 22px #39e7ff55;display:grid;place-items:center;color:var(--cyan);font-weight:900;letter-spacing:-2px}.brand h1{margin:0;font-size:24px;letter-spacing:4px}.brand small{color:var(--muted);letter-spacing:2px}.pill{border:1px solid var(--line);border-radius:999px;padding:8px 13px;color:var(--muted);background:#080d19aa}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}.card{grid-column:span 3;background:linear-gradient(145deg,#0c1324ee,#080c17ee);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 10px 35px #0005}.wide{grid-column:span 6}.full{grid-column:span 12}.label{color:var(--muted);font-size:11px;letter-spacing:2px;text-transform:uppercase}.value{font-size:28px;font-weight:750;margin-top:8px}.ok{color:var(--good)}.warn{color:var(--warn)}.accent{color:var(--cyan)}.muted{color:var(--muted)}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:10px 0}.bar{height:7px;background:#111a2c;border-radius:9px;overflow:hidden}.bar i{display:block;height:100%;width:62%;background:linear-gradient(90deg,var(--cyan),var(--violet));box-shadow:0 0 15px #39e7ff66}.ceo{min-height:190px}.action{font-size:25px;margin:10px 0;color:var(--cyan)}.reason{color:#b6c5da}.agent{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:12px;padding:9px 11px;margin:5px 4px 0 0;background:#080d18}.dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 9px var(--good)}.controls{display:flex;gap:10px;flex-wrap:wrap}.btn{background:#101a2e;color:var(--text);border:1px solid #284064;border-radius:10px;padding:9px 13px}.btn:hover{border-color:var(--cyan)}@media(max-width:900px){.card,.wide{grid-column:span 6}}@media(max-width:600px){.wrap{padding:14px}.card,.wide,.full{grid-column:span 12}.top{align-items:flex-start}.brand h1{font-size:19px}}
</style></head>
<body><main class="wrap"><header class="top"><div class="brand"><div class="mark">TJ</div><div><h1>TJ CORTEX</h1><small>COMMAND CENTER // AUTONOMOUS BUSINESS OS</small></div></div><div class="pill" id="system">CONNECTING…</div></header>
<section class="grid">
<div class="card"><div class="label">Verified Revenue</div><div class="value accent" id="revenue">—</div><div class="muted">Only independently verified payments</div></div>
<div class="card"><div class="label">Orders</div><div class="value" id="orders">—</div><div class="muted">Payment-gated lifecycle</div></div>
<div class="card"><div class="label">Pending Payments</div><div class="value warn" id="pending">—</div><div class="muted">Never counted as revenue</div></div>
<div class="card"><div class="label">Governance</div><div class="value ok">ARMED</div><div class="muted">External actions require approval</div></div>
<div class="card wide ceo"><div class="label">Cortex CEO // Next Decision</div><div class="action" id="action">—</div><div class="reason" id="reason">Waiting for engine state…</div><div class="row"><span class="muted">Priority</span><strong id="priority">—</strong></div></div>
<div class="card wide"><div class="label">Cortex Link // AI Provider</div><div class="row"><span>Mode</span><strong class="accent" id="mode">—</strong></div><div class="row"><span>Model</span><strong id="model">—</strong></div><div class="row"><span>Connection</span><strong class="muted">Use provider test endpoint</strong></div><div class="bar"><i></i></div></div>
<div class="card full"><div class="label">Cortex Agents</div><div class="agent"><span class="dot"></span>CEO</div><div class="agent"><span class="dot"></span>Intelligence</div><div class="agent"><span class="dot"></span>Growth</div><div class="agent"><span class="dot"></span>Commerce</div><div class="agent"><span class="dot"></span>Finance</div><div class="agent"><span class="dot"></span>Guard</div><div class="agent"><span class="dot"></span>Memory</div></div>
<div class="card full"><div class="label">Command Surface</div><div class="controls"><button class="btn" disabled>CEO CHAT — NEXT</button><button class="btn" disabled>VOICE LINK — NEXT</button><button class="btn" disabled>APPROVAL QUEUE — NEXT</button><button class="btn" disabled>RUN CEO CYCLE — GOVERNED</button></div><p class="muted">UI controls will be connected to real engine actions only after their backend approval gates are implemented.</p></div>
</section></main>
<script>
async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});const s=await r.json();document.getElementById('system').textContent=s.ledger==='ONLINE'?'● CORTEX ONLINE':'● LEDGER DEGRADED';document.getElementById('system').className='pill '+(s.ledger==='ONLINE'?'ok':'warn');document.getElementById('revenue').textContent=s.verified_revenue===null?'UNAVAILABLE':('$'+Number(s.verified_revenue).toFixed(2));document.getElementById('orders').textContent=s.orders;document.getElementById('pending').textContent=s.pending_payments;document.getElementById('action').textContent=s.ceo.action.replaceAll('_',' ').toUpperCase();document.getElementById('reason').textContent=s.ceo.reason;document.getElementById('priority').textContent=s.ceo.priority;document.getElementById('mode').textContent=s.ai_provider.mode.toUpperCase();document.getElementById('model').textContent=s.ai_provider.model||'—'}catch(e){document.getElementById('system').textContent='● OFFLINE'}}refresh();setInterval(refresh,5000);
</script></body></html>'''


class CortexHandler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, HTML, "text/html; charset=utf-8")
        elif path == "/api/status":
            self._send(200, json.dumps(build_snapshot()), "application/json; charset=utf-8")
        else:
            self._send(404, json.dumps({"error": "not found"}), "application/json; charset=utf-8")

    def log_message(self, *_args):
        return


def serve(host=HOST, port=PORT):
    server = ThreadingHTTPServer((host, port), CortexHandler)
    print(f"TJ Cortex Command Center: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    serve()
