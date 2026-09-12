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
- Provider-neutral, signature-verified payment webhook handling
- Verified-payment-only revenue and financial synchronization
- Persistent Guard approval queue
- Communication bus and live Command Center telemetry
- Cycle history, trace, memory and learning surfaces
- Persistent scheduler with automatic safety pause after repeated failures
- Bounded decision-only scheduler runner for continuous live observation
- Browser Command Center, neural communication visualization and voice link

## Safety model

LLM recommendations never receive unrestricted execution authority. External,
financial, customer-facing and irreversible actions remain policy/Guard gated.
Payment state is accepted only from independently verified provider confirmation.
Cortex never treats a draft, pending payment, simulated sale or model claim as
real revenue.

## Running locally

Install dependencies from `requirements.txt`, configure `.env` from `.env.example`,
and start the Command Center with:

```bash
python cortex_dashboard.py
```

The default local dashboard is served at `http://127.0.0.1:8080`.

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
