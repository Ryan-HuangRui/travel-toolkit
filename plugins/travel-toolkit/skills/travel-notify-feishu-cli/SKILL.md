---
name: travel-notify-feishu-cli
description: Deliver a verified Travel Notify request to Feishu through a locally configured lark-cli bot. Use only after the recipient, bot identity, content shape, cadence, and delivery mode are explicitly authorized.
---

# Travel Notify Feishu CLI

Use this adapter to deliver an already validated `trip-buddy-notification/v1` request through `lark-cli`. It uses bot identity only and never creates groups, sends as the user, or stores credentials or chat IDs in the repository.

Read [the Feishu CLI adapter contract](references/feishu-cli-adapter.md) before any actual send.

## Safe delivery

1. Display or otherwise confirm the semantic recipient profile, bot identity, concise message shape, and delivery intent before a visible send.
2. Run the adapter without `--send` first. It validates the request but does not need a profile file or access Feishu.
3. For a real send, require a host-private profile file through `TRAVEL_NOTIFY_PROFILES` or `--profiles`. It maps an alias to a bot chat ID and must never be committed.
4. The request must be `authorized: true` and `state: "sending"`. The stable idempotency key is passed unchanged to Feishu.
5. A CLI error or an unparseable receipt leaves the item uncertain. Do not auto-retry; reconcile it with the operator.

```bash
python3 scripts/send_feishu_notification.py --request path/to/request.json
python3 scripts/send_feishu_notification.py --request path/to/request.json --send
```

This is a notification adapter only. Publishing a Feishu document is a separate adapter and must complete before this one is invoked.
