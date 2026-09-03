# Feishu CLI Adapter Contract

The adapter expects `lark-cli` to be installed and authenticated as an existing bot. Bot permissions, group membership, and message-send scope are deployment responsibilities; the plugin does not initiate interactive login or include app credentials.

Use a private profile file with mode `0600`, for example:

```json
{
  "schema": "travel-notify-profiles/v1",
  "profiles": {
    "trip-updates": {
      "channel": "feishu-cli",
      "identity": "bot",
      "chat_id": "value-held-in-local-private-config"
    }
  }
}
```

The repository supplies no real profile. Never log the profile file, chat ID, access token, app secret, or raw CLI output.
