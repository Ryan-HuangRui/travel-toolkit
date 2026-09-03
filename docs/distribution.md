# Distribution and installation

Travel Toolkit keeps one shared skill implementation and uses thin manifests for each supported agent ecosystem.

## Repository layout

```text
travel-toolkit/
├── .agents/plugins/marketplace.json       # native OpenAI/Codex marketplace
├── .claude-plugin/marketplace.json        # Claude Code + Copilot CLI marketplace
└── plugins/travel-toolkit/
    ├── .codex-plugin/plugin.json           # OpenAI/Codex plugin metadata
    ├── .claude-plugin/plugin.json          # Claude Code + Copilot CLI plugin metadata
    └── skills/                             # shared implementation
```

OpenAI's GitHub marketplace importer also accepts Claude-compatible marketplace manifests, while GitHub Copilot CLI searches `.claude-plugin/marketplace.json`. The native Codex manifests are kept as the primary OpenAI representation; all ecosystems consume the same `skills/` tree.

## Claude Code

Add the marketplace and install the plugin:

```bash
claude plugin marketplace add Ryan-HuangRui/travel-toolkit
claude plugin install travel-toolkit@travel-toolkit
```

For local development:

```bash
claude --plugin-dir ./plugins/travel-toolkit
claude plugin validate .
```

## GitHub Copilot CLI

Add the same repository as a marketplace and install the same plugin name:

```bash
copilot plugin marketplace add Ryan-HuangRui/travel-toolkit
copilot plugin install travel-toolkit@travel-toolkit
```

Copilot CLI recognizes the repository-level `.claude-plugin/marketplace.json` and the plugin-level `.claude-plugin/plugin.json`, so there is no separate Copilot copy of the skills.

## ChatGPT / Codex workspace import

For an eligible managed workspace, an admin can import the GitHub repository as a plugin marketplace:

1. Open **Workspace settings → Plugins**.
2. Choose **Add → Import marketplace**.
3. Use `https://github.com/Ryan-HuangRui/travel-toolkit` as the source.
4. Leave **Path** empty to use the repository root.
5. Import, review the detected plugin, and configure its workspace installation policy.

A GitHub marketplace import makes the plugin available to that workspace. Public Plugin Directory listing or verification is a separate publication/review process.

## Release checklist

When publishing a versioned release, keep `0.x.y` metadata aligned in:

- `plugins/travel-toolkit/.codex-plugin/plugin.json`
- `plugins/travel-toolkit/.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json` marketplace metadata and plugin entry

Then run the repository validators:

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/travel-toolkit
python3 plugins/travel-toolkit/skills/plan-travel-guide/scripts/validate_trip.py examples/synthetic-city-break
python3 plugins/travel-toolkit/skills/travel-notify/scripts/validate_notification_request.py plugins/travel-toolkit/skills/travel-notify/references/notification-request.example.json
```

When Claude Code is available locally, also run:

```bash
claude plugin validate .
```

Before publishing, confirm that no API keys, recipient mappings, booking references, exact private addresses, or real itinerary exports are committed.
