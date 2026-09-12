# Cortex V13 Revenue Loop

## Lifecycle

Cortex now has a governed observation path connecting:

`Discovery → Sales → Order → Payment Confirmation → Delivery → Learning`

The revenue coordinator reads existing ledgers and exposes factual counts. It does not manufacture customers, payment confirmations, or revenue.

## Payment boundary

Orders remain `payment_pending` until the existing payment verification path records an independently confirmed provider event. Unpaid orders therefore contribute zero verified revenue.

## Delivery boundary

A paid order can become a delivery candidate. Delivery requires a one-time Cortex Guard approval and a safe delivery path. Approval is consumed before delivery is recorded, preventing reuse.

## CEO bridge

`cortex_revenue_ceo_bridge.py` merges revenue-loop observations into the bounded AI CEO observation state. The bridge is intentionally thin:

- observation is always factual;
- payment verification stays outside the CEO;
- unknown/unregistered actions cannot execute;
- governed CEO actions require Guard approval;
- execution is one bounded transition at a time.

## Next block

The next integration should connect the bridge to the existing application/scheduler entry point and then attach specialist handlers for acquisition, offer creation, qualification, outreach, and customer-outcome recording. External messaging and other irreversible actions must remain governed.
