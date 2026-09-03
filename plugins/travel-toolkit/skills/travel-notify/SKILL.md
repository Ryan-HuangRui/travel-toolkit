---
name: travel-notify
description: Create and validate platform-neutral, idempotent travel notification requests after Trip Buddy artifacts are verified. Use when a travel workflow needs a delivery request; do not send messages directly.
---

# Travel Notify

`travel-notify` is the delivery boundary for Trip Buddy. It creates a platform-neutral request after content or a document is verified; it never resolves a chat ID, accesses credentials, or sends a message.

Read [the notification contract](references/notification-contract.md) before creating or changing a request.

## Workflow

1. Confirm that the local artifact and any requested remote document were validated and read back. A draft is not deliverable.
2. Resolve a semantic `recipient_profile` only. Do not put chat IDs, addresses, account identifiers, or credentials in the request or Git.
3. Create a stable idempotency key from the trip, item, and delivery event. Preserve it on every retry.
4. Set the request to `sending` only immediately before calling an adapter. If its outcome is uncertain, stop for reconciliation; never silently issue a second send.
5. Pass the request to a selected adapter such as `travel-notify-feishu-cli`. The adapter returns a safe receipt; the orchestrator records `notified` only after a confirmed success.

Validate a request before dispatch:

```bash
python3 scripts/validate_notification_request.py path/to/request.json
```

Default to preparing a request. Changing recipient, cadence, delivery mode, or using an adapter's send mode requires explicit user authorization.
