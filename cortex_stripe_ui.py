"""Small self-contained Stripe connection page for local Cortex."""
from __future__ import annotations

import json

from cortex_stripe_adapter import connect, disconnect, status

HTML = """<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Cortex — Stripe</title><style>body{margin:0;background:#070b14;color:#eaf2ff;font:15px system-ui,sans-serif}.wrap{max-width:720px;margin:8vh auto;padding:24px}.card{background:#0d1424;border:1px solid #263a5b;border-radius:18px;padding:24px;box-shadow:0 20px 60px #0006}h1{margin-top:0}.muted{color:#8ea2bf}.row{display:grid;gap:7px;margin:16px 0}input{background:#080e1a;color:#fff;border:1px solid #30476c;border-radius:10px;padding:12px;width:100%;box-sizing:border-box}.btn{border:1px solid #31517c;background:#14223a;color:#fff;border-radius:10px;padding:11px 15px;cursor:pointer;margin:4px 6px 4px 0}.danger{border-color:#713d4b}.status{padding:12px;border-radius:10px;background:#091b19;margin:14px 0}.good{color:#52f2a3}.bad{color:#ff8b8b}.actions{margin-top:18px}.back{display:inline-block;margin-bottom:20px;color:#6ee7ff;text-decoration:none}</style></head><body><main class='wrap'><a class='back' href='/'>← Cortex Command Center</a><section class='card'><h1>Stripe Connection</h1><p class='muted'>Connect the local Cortex backend to your Stripe account. Secrets are stored locally and are never returned to this page.</p><div id='status' class='status'>Checking connection…</div><form id='form'><div class='row'><label for='key'>Stripe Secret Key</label><input id='key' name='key' type='password' autocomplete='off' placeholder='sk_test_…'></div><div class='row'><label for='webhook'>Webhook Secret <span class='muted'>(optional until webhook is configured)</span></label><input id='webhook' name='webhook' type='password' autocomplete='off' placeholder='whsec_…'></div><div class='actions'><button class='btn' type='submit'>Connect & Test</button><button class='btn' id='disconnect' type='button'>Disconnect</button></div></form><p id='message' class='muted'></p></section></main><script>const statusBox=document.getElementById('status'),message=document.getElementById('message');async function refresh(){try{const r=await fetch('/api/settings/stripe',{cache:'no-store'}),s=await r.json();if(s.connected){statusBox.innerHTML='<strong class="good">● Connected</strong><br>Mode: '+s.mode+'<br>Account: '+(s.account_id||'available')+'<br>Country: '+(s.country||'not reported')+'<br>Webhook: '+(s.webhook_configured?'configured':'not configured')}else{statusBox.innerHTML='<strong class="bad">● Not connected</strong>'+(s.error?'<br>'+s.error:'')}}catch(e){statusBox.textContent='Unable to read Stripe status'}}document.getElementById('form').onsubmit=async e=>{e.preventDefault();message.textContent='Testing Stripe credentials…';const body={secret_key:document.getElementById('key').value,webhook_secret:document.getElementById('webhook').value};try{const r=await fetch('/api/settings/stripe',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),p=await r.json();message.textContent=p.error|| (p.connected?'Stripe connected successfully.':'Connection failed.');document.getElementById('key').value='';document.getElementById('webhook').value='';refresh()}catch(e){message.textContent='Connection request failed'}};document.getElementById('disconnect').onclick=async()=>{if(!confirm('Remove local Stripe credentials?'))return;const r=await fetch('/api/settings/stripe',{method:'DELETE'});const p=await r.json();message.textContent=p.error||'Stripe disconnected.';refresh()};refresh();</script></body></html>"""


def page() -> str:
    return HTML


def api_get() -> tuple[int, dict]:
    return 200, status()


def api_post(payload: object) -> tuple[int, dict]:
    if not isinstance(payload, dict):
        return 400, {"ok": False, "error": "invalid JSON body"}
    return int((result := connect(payload.get("secret_key", ""), payload.get("webhook_secret", ""))).get("status", 400)), result


def api_delete() -> tuple[int, dict]:
    result = disconnect()
    return int(result.get("status", 503)), result
