# Cortex — Autonomous Business OS

Cortex is an autonomous-business operating system designed to discover opportunities,
create and sell digital products, find clients, build custom AI agents, fulfill paid
work, track verified revenue, learn from results, and continuously repeat the business
cycle with bounded safety controls.

The core operating rule is:

**Observe → Decide → Guard → Execute → Verify → Learn → Repeat**

Cortex is not intended to be a chatbot that waits for a human to tell it what to do.
After initial infrastructure and account setup, the goal is for Cortex to operate normal
business activities autonomously. Safety boundaries remain automatic and fail-closed;
Cortex does not receive unlimited authority over money, credentials, spam, destructive
operations, or other high-risk actions.

## Business mission

Cortex has two primary revenue engines.

### 1. Digital products

Cortex can research demand and create/package digital products such as:

- AI prompt packs
- Templates and business documents
- Guides and ebooks
- Marketing/content kits
- Automation workflows
- Workspace/knowledge templates
- Code and software utilities
- AI-agent blueprints and reusable agent systems
- Other legitimate downloadable or digital products identified by market research

### 2. Custom AI agents

Cortex can turn client requirements into custom AI-agent projects. The intended lifecycle is:

**Client request → requirements → solution design → estimate/proposal → build → test → payment → delivery/deployment → support/improvement**

The architecture is designed to reuse trusted components instead of rebuilding every
agent from scratch.

## Autonomous business loop

The intended continuous loop is:

1. Research markets and customer problems.
2. Identify commercially useful opportunities.
3. Decide whether an opportunity is better suited to a digital product or a custom client project.
4. Create/package the product or design the requested agent solution.
5. Apply quality, security, pricing, and policy checks.
6. Find and research potential clients/prospects.
7. Qualify prospects and prepare relevant offers.
8. Use permitted sales/outreach channels without spam, deception, or fabricated claims.
9. Create Stripe Checkout sessions for purchases.
10. Verify Stripe webhook events independently of browser claims.
11. Create/activate the order only after verified payment.
12. Deliver the digital product or start/complete the paid custom-agent workflow.
13. Record verified revenue and business metrics.
14. Analyze conversion, profitability, feedback, and failures.
15. Improve offers, products, processes, and agent capabilities.
16. Run the next bounded cycle.

The system should not require a human to manually perform each ordinary business step.
External account ownership, infrastructure provisioning, legal requirements, and
high-risk authorization remain outside the unrestricted authority of the AI runtime.

## System architecture

### CEO / decision engine

The CEO layer evaluates the current business state and selects bounded actions such as
market research, product creation, prospect discovery, qualification, outreach planning,
financial review, offer improvement, and observation/rest.

### Autonomous runtime

The runtime coordinates bounded cycles and specialist work. It does not give an LLM
unrestricted access to arbitrary Python code or arbitrary external actions.

### Specialist registry and agent factory

Only explicitly registered trusted handlers can execute specialist actions. Agent hiring
is proposal-driven and bounded. Persisted agent records do not automatically regain
execution authority after restart.

### Client acquisition engine

Cortex includes market research, prospect discovery, qualification, acquisition planning,
and outreach drafting. External communication is policy-controlled; the system must not
turn into an uncontrolled spam engine.

### Product factory

Product creation is bounded and includes packaging and quality checks. Generated runtime
products are treated as runtime state and are not committed to Git.

### AI-agent factory

Custom AI-agent work can be represented as a controlled build/delivery workflow. Trusted
specialists and explicit capabilities can be assigned to supported actions.

### Stripe payments

Stripe is the payment provider. Cortex creates dynamic Checkout sessions using Cortex
order metadata and accepts payment state only from authenticated Stripe webhook events.

Payment flow:

**Cortex → Stripe Checkout → customer pays → Stripe webhook → signature verification →
order/amount/currency verification → paid order → delivery → verified revenue**

Stripe secret credentials are never stored in source code and must never be committed to
GitHub.

### Orders and delivery

Orders are payment-gated. Cortex does not treat a draft, pending payment, simulated sale,
or browser claim as a paid order. Delivery is allowed only for verified paid orders and
uses bounded/safe delivery paths.

### Revenue and finance

The payment ledger records verified transactions using exact decimal money handling.
Duplicate verified events are prevented from creating duplicate revenue.

### Guard / safety

The Guard is fail-closed. External, financial, customer-facing, and irreversible actions
can require explicit authorization according to policy. Automatic safety limits prevent
unbounded cycles and repeated failures.

### Scheduler

The scheduler supports continuous bounded observation. The decision-only runner can keep
Cortex evaluating the business state without independently granting execution authority.

### Command Center

The browser Command Center exposes runtime telemetry, status, traces, and the local Stripe
connection UI. Neural visualization and voice-related surfaces are connected to the
runtime communication model rather than fabricated business activity.

## Repository structure

Important production components include:

- `ai_ceo.py` — CEO decision logic
- `ceo_loop.py` — bounded CEO orchestration
- `cortex_autonomous_runtime.py` — autonomous runtime cycle
- `cortex_autonomous_growth_loop.py` — bounded growth stages
- `cortex_agent_factory.py` — guarded specialist/agent creation
- `cortex_specialist_registry.py` — trusted execution handlers
- `cortex_hiring_advisor.py` — bounded staffing recommendations
- `cortex_acquisition_pipeline.py` — prospect/acquisition planning
- `cortex_guard.py` — approval and safety boundary
- `cortex_stripe_adapter.py` — Stripe API, Checkout, and webhook adapter
- `cortex_stripe_ui.py` — local Stripe connection UI/API helpers
- `payment_webhook.py` — provider-neutral verified payment processing
- `payment_tracker.py` — verified payment/revenue tracking
- `order_engine.py` — payment-gated order lifecycle
- `cortex_revenue_loop.py` — revenue lifecycle coordination
- `cortex_revenue_ceo_bridge.py` — revenue-to-CEO decision bridge
- `cortex_scheduler_runner.py` — bounded continuous scheduler runner
- `cortex_http_api.py` — HTTP integration routes
- `cortex_production_server.py` — local/production HTTP server
- `cortex_dashboard.py` — Command Center
- `cortex_communication.py` — bounded inter-agent communication bus
- `cortex_neural_network.js` — neural Command Center visualization

Runtime state, credentials, generated products, deliveries, and other mutable operational
data belong outside source control and are excluded by `.gitignore`.

## Requirements

Cortex is intentionally **stdlib-first**. The repository currently has no required third-
party Python runtime dependency in `requirements.txt`.

You need:

- Python 3
- Git
- A modern browser
- Node.js only for the JavaScript syntax check
- A Stripe account for payments
- A server/VPS when you want Cortex running continuously 24/7

## Installation — local machine

### 1. Clone the repository

```bash
git clone https://github.com/jazibvirk007-hue/ai-survival-business.git
cd ai-survival-business
```

### 2. Create a virtual environment (recommended)

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install repository dependencies

```bash
python -m pip install -r requirements.txt
```

The requirements file is intentionally minimal. Optional integrations may add their own
dependencies later.

### 4. Run the test suite

```bash
python -m unittest discover -v
```

For the neural JavaScript syntax check, install Node.js and run:

```bash
node --check cortex_neural_network.js
```

### 5. Start Cortex

```bash
python cortex_production_server.py
```

The default local Command Center is:

`http://127.0.0.1:8080`

Open that address in a browser.

## Connecting Stripe

Cortex includes a local UI so Stripe credentials do not need to be pasted into chat or
committed to GitHub.

Open:

`http://127.0.0.1:8080/settings/payments`

Enter the Stripe secret key and, when ready to receive webhooks, the Stripe webhook signing
secret. Cortex validates the Stripe secret key against Stripe before saving the connection.
The browser receives masked connection information rather than the raw secret.

The local credential file is:

`.cortex_stripe_credentials.json`

It is permission-restricted where supported and excluded from Git. Never commit this file.

### Stripe test mode

Start with Stripe test-mode credentials. A test secret key normally begins with:

`sk_test_`

Test the complete checkout → webhook → order → delivery → revenue flow before replacing
the key with a live-mode key.

### Stripe webhook

Configure Stripe to send the relevant webhook to:

`POST /api/payment/stripe/webhook`

The endpoint verifies Stripe's `Stripe-Signature` using the raw request body, rejects stale
or invalid signatures, accepts paid `checkout.session.completed` events, verifies the Cortex
order ID, amount, and currency, and then passes the normalized event to the existing verified
payment ledger.

For local development, Stripe CLI can forward webhook events to the local endpoint. The
exact forwarding command depends on the Stripe CLI installation and account configuration.

For a deployed server, set runtime environment variables instead of committing credentials:

```text
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
```

Never place real values in source files, README files, screenshots, logs, or Git history.

## Running Cortex continuously

For a real autonomous deployment, Cortex needs a machine that stays online. A VPS is a
simple option.

Basic production concept:

```text
Internet
   ↓
HTTPS / domain
   ↓
Cortex HTTP server
   ↓
Cortex runtime
   ├── research
   ├── client acquisition
   ├── products
   ├── custom AI agents
   ├── sales
   ├── Stripe
   ├── orders/delivery
   ├── revenue
   └── learning
```

The deployment should also provide process supervision/restart, HTTPS, firewall rules,
secret management, backups, and monitoring. These are infrastructure responsibilities,
not unrestricted AI decisions.

## Autonomous scheduler

For bounded decision-only observation:

```python
from cortex_scheduler_runner import CortexSchedulerRunner

runner = CortexSchedulerRunner()
runner.run(max_cycles=10)
```

The scheduler remains subject to the existing Guard, specialist registry, failure limits,
and safety pause behavior. The runner does not itself authorize external actions.

## Security principles

- Never commit API keys, passwords, tokens, or webhook secrets.
- Never trust a browser claim that a payment succeeded.
- Verify Stripe webhook signatures against the raw body.
- Verify order ID, amount, and currency before recording payment.
- Make payment processing idempotent.
- Do not allow persisted records to create arbitrary executable handlers.
- Keep external actions behind trusted registries and Guard policies.
- Bound loops, retries, generated content, and hiring/workforce growth.
- Fail closed when state or configuration is corrupt or ambiguous.
- Keep runtime state out of Git.
- Do not use Cortex to send deceptive, abusive, or uncontrolled mass outreach.

## Testing

The repository uses the standard-library `unittest` suite plus JavaScript syntax validation:

```bash
python -m unittest discover -v
node --check cortex_neural_network.js
```

The GitHub Actions workflow runs these checks automatically on repository changes.

## Operational goal

The long-term goal is **setup once, operate autonomously**:

**Research → opportunity → product/client → build → sell → Stripe → verify → deliver →
revenue → learn → improve → repeat**

The human owner supplies the initial external infrastructure/accounts and any legally or
policy-required authorization. Cortex handles the ordinary business workflow inside its
configured safety boundaries.

## Repository hygiene

Keep the repository production-focused. Do not commit:

- credentials or `.env` files
- runtime databases/state
- generated product output
- customer private data
- delivery artifacts
- temporary/debug files
- abandoned experiments
- duplicate implementations
- unnecessary dependencies

If a component is obsolete, remove it rather than leaving dead code in the main branch.
