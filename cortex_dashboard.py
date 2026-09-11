"""TJ Cortex Command Center - zero-dependency dashboard foundation.

The dashboard reads real local ledgers/provider configuration and never invents
business telemetry. It is intentionally stdlib-only so it can run on a small VPS
or local machine without a paid service.
"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ai_ceo import AICEO
from ai_provider import provider_from_env
from cortex_chat import CortexCEOChat
from cortex_communication import communication_status, recent_messages
from cortex_learning import CortexLearning
from cortex_memory import CortexMemory
from cortex_runtime_singleton import get_cortex_orchestrator
from cortex_voice_api import build_voice_ceo
from cortex_voice_routes import json_response, voice_command_from_body, voice_status
from order_engine import load_orders
from payment_tracker import pending_payments, verified_payments, verified_revenue

HOST = "127.0.0.1"
PORT = 8080
MAX_REQUEST_BYTES = 16_384
MAX_COMMUNICATION_EVENTS = 50
NEURAL_JS = Path(__file__).with_name("cortex_neural_network.js")
VOICE_JS = Path(__file__).with_name("cortex_voice_ceo_ui.js")


def _safe_list(loader):
    try:
        return loader()
    except Exception:
        return None


def _ceo_state(pending_count):
    return {"market_researched": False, "has_product": False, "prospects_found": 0,
            "qualified_prospects": 0, "outreach_drafts": 0, "approved_outreach": 0,
            "pending_orders": pending_count, "recent_failures": 0}


def _provider_summary(provider):
    config = getattr(provider, "config", None)
    return {"mode": getattr(config, "mode", getattr(provider, "mode", "")),
            "model": getattr(config, "model", getattr(provider, "model", "")),
            "base_url": getattr(config, "normalized_base_url", getattr(provider, "base_url", ""))}


def build_snapshot():
    orders = _safe_list(load_orders)
    payments = _safe_list(verified_payments)
    pending = _safe_list(pending_payments)
    revenue = None
    if payments is not None:
        try: revenue = verified_revenue()
        except Exception: revenue = None
    if orders is None or payments is None or pending is None or revenue is None:
        ledger_status, orders_count, verified_count, pending_count, revenue_value = "DEGRADED", 0, 0, 0, None
    else:
        ledger_status, orders_count, verified_count, pending_count, revenue_value = "ONLINE", len(orders), len(payments), len(pending), revenue
    try:
        decision = AICEO().decide(_ceo_state(pending_count))
        ceo = {"action": decision.action, "priority": decision.priority, "reason": decision.reason, "approval_required": decision.approval_required}
    except Exception as error:
        ceo = {"action": "unavailable", "priority": 0, "reason": type(error).__name__, "approval_required": True}
    try: provider_config = _provider_summary(provider_from_env())
    except Exception as error: provider_config = {"mode": "invalid", "model": "", "base_url": "", "error": type(error).__name__}
    try: bus = communication_status()
    except Exception: bus = {"enabled": False, "events": 0, "max_events": 0, "storage": "unavailable", "live_stream_ready": False}
    return {"system": "TJ Cortex", "version": "command-center-5", "ledger": ledger_status,
            "orders": orders_count, "verified_payments": verified_count, "pending_payments": pending_count,
            "verified_revenue": revenue_value, "currency": "USD", "ceo": ceo, "ai_provider": provider_config,
            "communication_bus": bus, "governance": {"external_actions": "approval-gated", "money_movement": "blocked-by-default"}}


def build_communication_snapshot(limit=MAX_COMMUNICATION_EVENTS):
    try: bounded_limit = max(1, min(int(limit), MAX_COMMUNICATION_EVENTS))
    except (TypeError, ValueError): bounded_limit = MAX_COMMUNICATION_EVENTS
    try: events = recent_messages(bounded_limit)
    except Exception: events = []
    try: stream = communication_status()
    except Exception: stream = {"enabled": False, "events": 0, "max_events": 0, "storage": "unavailable", "live_stream_ready": False}
    return {"events": events, "stream": stream}


def build_chat_state():
    snapshot = build_snapshot()
    try: memory_context = CortexLearning(CortexMemory()).context(10)
    except Exception: memory_context = []
    return {"revenue": snapshot["verified_revenue"], "pending_orders": snapshot["pending_payments"],
            "paid_orders": snapshot["verified_payments"], "products": snapshot["orders"],
            "current_decision": snapshot["ceo"]["action"], "approval_required": snapshot["ceo"]["approval_required"],
            "ai_mode": snapshot["ai_provider"]["mode"], "ai_model": snapshot["ai_provider"]["model"],
            "learning_context": memory_context}


HTML = r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TJ Cortex — Command Center</title><style>
:root{--bg:#050711;--panel:#0b1020;--line:#1c2b4a;--cyan:#39e7ff;--violet:#a56cff;--text:#e8f3ff;--muted:#7e91ae;--good:#52f2a3;--warn:#ffd166;--bad:#ff7f7f}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 75% 5%,#17204a 0,#080b18 35%,var(--bg) 70%);color:var(--text);font:14px/1.5 system-ui,sans-serif;min-height:100vh}.wrap{max-width:1450px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:24px}.brand{display:flex;align-items:center;gap:14px}.mark{width:46px;height:46px;border:1px solid var(--cyan);border-radius:14px;box-shadow:0 0 22px #39e7ff55;display:grid;place-items:center;color:var(--cyan);font-weight:900;letter-spacing:-2px}.brand h1{margin:0;font-size:24px;letter-spacing:4px}.brand small{color:var(--muted);letter-spacing:2px}.pill{border:1px solid var(--line);border-radius:999px;padding:8px 13px;color:var(--muted);background:#080d19aa}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}.card{grid-column:span 3;background:linear-gradient(145deg,#0c1324ee,#080c17ee);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 10px 35px #0005}.wide{grid-column:span 6}.full{grid-column:span 12}.label{color:var(--muted);font-size:11px;letter-spacing:2px;text-transform:uppercase}.value{font-size:28px;font-weight:750;margin-top:8px}.ok{color:var(--good)}.warn{color:var(--warn)}.bad{color:var(--bad)}.accent{color:var(--cyan)}.muted{color:var(--muted)}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:10px 0}.bar{height:7px;background:#111a2c;border-radius:9px;overflow:hidden}.bar i{display:block;height:100%;width:62%;background:linear-gradient(90deg,var(--cyan),var(--violet));box-shadow:0 0 15px #39e7ff66}.ceo{min-height:190px}.action{font-size:25px;margin:10px 0;color:var(--cyan)}.reason{color:#b6c5da}.agent{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:12px;padding:9px 11px;margin:5px 4px 0 0;background:#080d18}.dot{width:7px;height:7px;border-radius:50%;background:var(--good);box-shadow:0 0 9px var(--good)}.controls{display:flex;gap:10px;flex-wrap:wrap}.btn{background:#101a2e;color:var(--text);border:1px solid #284064;border-radius:10px;padding:9px 13px}.btn:hover{border-color:var(--cyan)}.chat{display:grid;grid-template-columns:1fr auto;gap:10px}.chat input{min-width:0;background:#070c17;color:var(--text);border:1px solid #284064;border-radius:10px;padding:11px}.chat button{cursor:pointer}.reply{white-space:pre-wrap;margin-top:12px;color:#cbd8ea;min-height:22px}
.neural{position:relative;overflow:hidden;padding:0;background:linear-gradient(145deg,#080e1eee,#050914f4);min-height:560px}.neural-head{position:absolute;z-index:3;left:20px;right:20px;top:18px;display:flex;justify-content:space-between;align-items:flex-start;gap:16px;pointer-events:none}.neural-title{font-size:18px;font-weight:750;letter-spacing:1px}.neural-sub{font-size:11px;color:var(--muted);letter-spacing:1.4px;text-transform:uppercase;margin-top:3px}.neural-status{display:flex;gap:8px;align-items:center;font-size:11px;color:var(--good);letter-spacing:1.5px}.neural-status b{padding:6px 9px;border:1px solid #234b50;border-radius:999px;background:#07171a99}.neural-canvas{display:block;width:100%;height:520px}.neural-inspector{position:absolute;z-index:4;right:18px;bottom:18px;width:min(330px,calc(100% - 36px));max-height:180px;overflow:auto;background:#050a14dd;border:1px solid #263b60;border-radius:14px;padding:12px;backdrop-filter:blur(10px);box-shadow:0 12px 35px #0008}.neural-detail{border-top:1px solid #1a2b46;margin-top:8px;padding-top:7px}.neural-detail span{display:block;color:var(--cyan);font-size:11px}.neural-detail small{display:block;color:#9db0c8;margin-top:2px}.neural-legend{position:absolute;left:20px;bottom:18px;z-index:4;color:var(--muted);font-size:10px;letter-spacing:1px;background:#050a1499;border:1px solid #1a2b46;border-radius:10px;padding:8px 10px}.neural-legend strong{color:var(--cyan)}
.voice{min-height:170px}.voice-grid{display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center}.voice-orb{width:92px;height:92px;border:1px solid var(--cyan);border-radius:50%;display:grid;place-items:center;color:var(--cyan);box-shadow:0 0 30px #39e7ff44}.voice-orb.listening{animation:pulse 1s infinite;box-shadow:0 0 45px #39e7ff88}.voice-state{font-size:18px;color:var(--cyan);margin:5px 0}.voice-reply{white-space:pre-wrap;color:#b9c9dd;margin-top:8px}.voice-buttons{display:flex;gap:8px;flex-wrap:wrap}@keyframes pulse{50%{transform:scale(1.07)}}
@media(max-width:900px){.card,.wide{grid-column:span 6}.neural{min-height:500px}.neural-canvas{height:470px}.neural-inspector{position:absolute;left:18px;right:18px;width:auto}}@media(max-width:600px){.wrap{padding:14px}.card,.wide,.full{grid-column:span 12}.top{align-items:flex-start}.brand h1{font-size:19px}.chat{grid-template-columns:1fr}.neural-canvas{height:430px}.neural-head{left:14px;right:14px;top:14px}.neural-legend{left:14px;bottom:14px}.neural-inspector{left:14px;right:14px;bottom:14px;max-height:145px}.neural-status{font-size:9px}}
</style></head><body><main class="wrap"><header class="top"><div class="brand"><div class="mark">TJ</div><div><h1>TJ CORTEX</h1><small>COMMAND CENTER // AUTONOMOUS BUSINESS OS</small></div></div><div class="pill" id="system">CONNECTING…</div></header><section class="grid">
<div class="card"><div class="label">Verified Revenue</div><div class="value accent" id="revenue">—</div><div class="muted">Only independently verified payments</div></div><div class="card"><div class="label">Orders</div><div class="value" id="orders">—</div><div class="muted">Payment-gated lifecycle</div></div><div class="card"><div class="label">Pending Payments</div><div class="value warn" id="pending">—</div><div class="muted">Never counted as revenue</div></div><div class="card"><div class="label">Governance</div><div class="value ok">ARMED</div><div class="muted">External actions require approval</div></div>
<div class="card full neural" data-neural-network><div class="neural-head"><div><div class="neural-title">Cortex Neural Network</div><div class="neural-sub">Real inter-agent communication // event driven</div></div><div class="neural-status"><b data-neural-status>CONNECTING</b><span data-neural-count>0 observed events</span></div></div><canvas class="neural-canvas" aria-label="Animated Cortex agent communication network"></canvas><div class="neural-legend"><strong>LIVE</strong> packets represent observed Cortex bus events. No fake business messages.</div><div class="neural-inspector" data-neural-inspector><span class="muted">Select an agent node to inspect its latest observed communications.</span></div></div>
<div class="card wide ceo"><div class="label">Cortex CEO // Next Decision</div><div class="action" id="action">—</div><div class="reason" id="reason">Waiting for engine state…</div><div class="row"><span class="muted">Priority</span><strong id="priority">—</strong></div></div><div class="card wide"><div class="label">Cortex Link // AI Provider</div><div class="row"><span>Mode</span><strong class="accent" id="mode">—</strong></div><div class="row"><span>Model</span><strong id="model">—</strong></div><div class="row"><span>Connection</span><strong class="muted">Server-side provider configuration</strong></div><div class="bar"><i></i></div></div>
<div class="card full"><div class="label">Cortex Agents</div><div class="agent"><span class="dot"></span>CEO</div><div class="agent"><span class="dot"></span>Intelligence</div><div class="agent"><span class="dot"></span>Product</div><div class="agent"><span class="dot"></span>Agent Factory</div><div class="agent"><span class="dot"></span>Growth</div><div class="agent"><span class="dot"></span>Communications</div><div class="agent"><span class="dot"></span>Commerce</div><div class="agent"><span class="dot"></span>Finance</div><div class="agent"><span class="dot"></span>Guard</div><div class="agent"><span class="dot"></span>Memory</div></div>
<div class="card full"><div class="label">Cortex CEO // Chat</div><div class="chat"><input id="chatInput" maxlength="4000" placeholder="Ask the CEO about the current business state…"><button class="btn" id="chatBtn">SEND</button></div><div class="reply" id="reply"></div><p class="muted">Chat is decision-support only. External, financial, irreversible, and customer-facing actions remain approval-gated.</p></div>
<div class="card full voice"><div class="label">Cortex CEO // Voice Link</div><div class="voice-grid"><div class="voice-orb" data-voice-orb>MIC</div><div><div class="voice-state" data-voice-state>VOICE READY</div><div class="voice-buttons"><button class="btn" data-voice-start>START LISTENING</button><button class="btn" data-voice-stop disabled>STOP</button></div><div class="voice-reply" data-voice-reply></div></div></div><p class="muted">Browser speech recognition is used only when supported. Voice commands are routed through the governed Cortex Voice boundary.</p></div>
<div class="card full"><div class="label">Command Surface</div><div class="controls"><button class="btn" disabled>APPROVAL QUEUE — NEXT</button><button class="btn" disabled>TREASURY — NEXT</button><button class="btn" disabled>GROWTH — NEXT</button></div></div></section></main><script src="/cortex_neural_network.js"></script><script src="/cortex_voice_ceo.js"></script><script>
async function refresh(){try{const r=await fetch('/api/status',{cache:'no-store'});const s=await r.json();document.getElementById('system').textContent=s.ledger==='ONLINE'?'CORTEX ONLINE':'CORTEX DEGRADED';document.getElementById('revenue').textContent=s.verified_revenue==null?'—':`${s.currency} ${s.verified_revenue}`;document.getElementById('orders').textContent=s.orders;document.getElementById('pending').textContent=s.pending_payments;document.getElementById('action').textContent=s.ceo.action;document.getElementById('reason').textContent=s.ceo.reason;document.getElementById('priority').textContent=s.ceo.priority;document.getElementById('mode').textContent=s.ai_provider.mode||'—';document.getElementById('model').textContent=s.ai_provider.model||'—'}catch(e){document.getElementById('system').textContent='OFFLINE'}}
async function chat(){const input=document.getElementById('chatInput');const reply=document.getElementById('reply');if(!input.value.trim())return;reply.textContent='Cortex is thinking…';try{const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:input.value})});const p=await r.json();reply.textContent=p.reply||p.error||'No response';}catch(e){reply.textContent='CEO provider unavailable'}}document.getElementById('chatBtn').onclick=chat;document.getElementById('chatInput').addEventListener('keydown',e=>{if(e.key==='Enter')chat()});refresh();setInterval(refresh,3000);
</script></body></html>'''


class CortexHandler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        encoded = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(encoded))); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(encoded)

    def _voice(self):
        return build_voice_ceo(get_cortex_orchestrator())

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/": self._send(200, HTML, "text/html; charset=utf-8")
        elif path == "/api/status": self._send(200, json.dumps(build_snapshot()), "application/json; charset=utf-8")
        elif path == "/api/communications": self._send(200, json.dumps(build_communication_snapshot(parse_qs(urlparse(self.path).query).get("limit", [MAX_COMMUNICATION_EVENTS])[0])), "application/json; charset=utf-8")
        elif path == "/api/voice/status": self._send(200, json_response(voice_status(self._voice())))
        elif path == "/cortex_neural_network.js":
            try: self._send(200, NEURAL_JS.read_text(encoding="utf-8"), "application/javascript; charset=utf-8")
            except OSError: self._send(404, json.dumps({"error":"neural network asset unavailable"}))
        elif path == "/cortex_voice_ceo.js":
            try: self._send(200, VOICE_JS.read_text(encoding="utf-8"), "application/javascript; charset=utf-8")
            except OSError: self._send(404, json.dumps({"error":"voice asset unavailable"}))
        else: self._send(404, json.dumps({"error":"not found"}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/chat", "/api/voice/command"):
            self._send(404, json.dumps({"error":"not found"})); return
        try: length = int(self.headers.get("Content-Length", "0"))
        except ValueError: length = 0
        if length <= 0 or length > MAX_REQUEST_BYTES:
            self._send(413, json.dumps({"error":"request too large or empty"})); return
        raw = self.rfile.read(length)
        try:
            if path == "/api/voice/command": result = voice_command_from_body(self._voice(), raw)
            else:
                payload = json.loads(raw.decode("utf-8"));
                if not isinstance(payload, dict) or not isinstance(payload.get("message"), str): raise ValueError("message is required")
                reply = CortexCEOChat(provider_from_env()).respond(build_chat_state(), payload["message"])
                result = {"reply": reply}
            self._send(200, json_response(result))
        except ValueError as error: self._send(400, json.dumps({"error": str(error)}))
        except Exception: self._send(503, json.dumps({"error":"CEO service unavailable"}))

    def log_message(self, *_args): return


def serve(host=HOST, port=PORT):
    server = ThreadingHTTPServer((host, port), CortexHandler)
    print(f"TJ Cortex Command Center: http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__": serve()
