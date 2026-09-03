# Integrations and private configuration

## Maps

Google credentials are read from `GOOGLE_MAPS_API_KEY`; Amap credentials from `AMAP_API_KEY`. Optional local files are selected through `TRAVEL_MAPS_ENV_FILE` and `AMAP_ENV_FILE`. Keep them outside the repository with owner-only permissions.

## Feishu CLI notifications

Install and authenticate `lark-cli` as a bot according to your own Feishu tenant policy. Store the profile mapping in a local file such as `~/.config/travel-toolkit/notifications.json` with mode `0600`, then set `TRAVEL_NOTIFY_PROFILES` to that file if you use a different path.

The profile maps a semantic alias to a channel, bot identity, and chat ID. The alias may appear in a Bundle or notification request; the chat ID must not.

Before enabling a scheduler, independently test:

1. a request validator run;
2. the adapter dry-run;
3. bot identity, message-send permission, and target-group membership;
4. one explicitly authorized visible send;
5. an idempotency and uncertain-send reconciliation path.

## Publishing adapters

Feishu document creation, email, Telegram, Slack, and other delivery mechanisms should be separate adapters. They consume the same `trip-buddy-notification/v1` contract so the core planning and companion workflow stays portable.
