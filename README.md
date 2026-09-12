# Cortex — Autonomous Business OS

Cortex is a governed autonomous-business runtime built around one rule:

**Observe → Decide → Guard → Execute → Verify → Learn → Repeat**

## What is implemented

- CEO decision engine with bounded one-action decisions
- Autonomous growth/runtime orchestration
- Specialist registry and guarded agent factory
- Hiring advisor with non-executing hire proposals
- Market research, product generation, prospecting and qualification
- Sales/outreach planning without automatic spam
- Payment-gated order lifecycle
- Stripe Checkout integration with signed webhook verification
- Local browser UI for securely connecting Stripe test/live credentials
- Verified-payment-only revenue and financial synchronization
- Persistent Guard approval queue
- Communication bus and live Command Center telemetry
- Cycle history, trace, memory and learning surfaces
- Persistent scheduler with automatic safety pause after repeated failures
- Bounded decision-only scheduler runner for continuous live observation
- Browser Command Center, neural communication visualization and voice link
- Production HTTP adapter exposing live observability and Stripe webhook routes

## Safety model

LLM recommendations never receive unrestricted execution authority. External,
financial, customer-facing and irreversible actions remain policy/Guard gated.
Payment state is accepted only from independently verified Stripe confirmation.
Cortex never treats a draft, pending payment, simulated sale or model claim as
real revenue.

## Running locally

Install dependencies from `requirements.txt` and start the production Command
Center with:

```bash
python cortex_production_server.py
```

The default local dashboard is served at `http://127.0.0.1:8080`.

### Connect Stripe from the UI

Open `http://127.0.0.1:8080/settings/payments`. Enter your Stripe secret key
and, once your webhook is configured, the Stripe webhook signing secret. Cortex
validates the secret key against Stripe before saving it locally. The credential
file is `.cortex_stripe_credentials.json`, is permission-restricted where the
platform supports it, and is excluded from Git. The browser receives only
masked connection status.

For local webhook delivery, forward Stripe events to:

`POST /api/payment/stripe/webhook`

The endpoint verifies Stripe's `Stripe-Signature` against the raw request body,
rejects stale/replayed signatures, accepts paid `checkout.session.completed`
events, verifies the Cortex order ID, amount and currency, and then hands the
normalized event to the existing payment ledger. It does not trust a browser
payment confirmation.

For deployment, `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` environment
variables may be used instead of the local credential file. Never commit real
Stripe credentials.

For continuous **decision-only** scheduler observation:

```python
from cortex_scheduler_runner import CortexSchedulerRunner

runner = CortexSchedulerRunner()
runner.run(max_cycles=10)
```

Execution remains governed by the existing scheduler, specialist registry and
Guard boundaries; the runner itself does not authorize external actions.

## Testing

The repository uses the standard-library unittest suite plus a JavaScript syntax
check in GitHub Actions:

```bash
python -m unittest discover -v
node --check cortex_neural_network.js
```

Runtime state, credentials, payment records, generated products and deliveries
are intentionally excluded from Git via `.gitignore`.
