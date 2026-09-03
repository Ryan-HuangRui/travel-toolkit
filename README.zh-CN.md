# Travel Toolkit

一个开源的、面向 Agent 的旅行工具包：从旅行规划、每日路线核验，到出发前和旅途中的陪伴式提醒，围绕同一份可移植的行程资料持续工作。

同一套 Skills 可用于 **OpenAI Codex / ChatGPT**、**Claude Code** 和 **GitHub Copilot CLI**。

[English README](README.md)

## 快速开始

### Claude Code

```bash
claude plugin marketplace add Ryan-HuangRui/travel-toolkit
claude plugin install travel-toolkit@travel-toolkit
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add Ryan-HuangRui/travel-toolkit
copilot plugin install travel-toolkit@travel-toolkit
```

### ChatGPT / Codex

对于支持 GitHub Marketplace 导入的受管工作空间，管理员可以进入 **Workspace settings → Plugins → Add → Import marketplace**，将本仓库作为 Source 导入，Path 留空：

```text
https://github.com/Ryan-HuangRui/travel-toolkit
```

不同平台的安装、测试和发布说明见 [docs/distribution.md](docs/distribution.md)。

安装后可以直接从自然语言开始，例如：

```text
帮我规划一个 10 天的法国旅行，我想去巴黎和南法，
节奏不要太赶，而且后续订了酒店、门票以后希望可以持续修改同一份行程。
```

## 它和“一次性生成攻略”有什么不同

Travel Toolkit 把一次旅行当成一个会持续变化的项目，而不是让模型一次性生成一张行程表。

- 在做小时级行程之前，先比较城市顺序、住宿天数、季节限定活动和路线取舍。
- 把已经确认的决定、预订、候选项、待办和证据放在同一个可移植的 Travel Plan Bundle 中。
- 对重要 POI 和脆弱交通段使用地图服务核验，而不是只依赖模型对距离和时间的猜测。
- 当预约或计划改变时，只重排受影响的部分，不会悄悄改写已经确认的事实。
- 行程确定后继续提供行前准备、旅行当天简报、文化内容以及经过核实的异常提醒。

`trip.json` 是唯一的行程事实来源。Markdown 和 CSV 都只是可重新生成的人类可读视图。

## 工作流

```text
旅行想法 → plan-travel-guide → Travel Plan Bundle（trip.json）
                                  ↑
                    travel-maps-planner 核验地点与路线
                                  ↓
                             trip-buddy
             文化卡 / 行前准备 / 当日简报 / 异常关注
                                  ↓
                            travel-notify
                                  ↓
                    可选的通知平台适配器（先支持飞书 CLI）
```

地图服务提供带时效的地点与路线证据；Trip Buddy 读取最新的 Bundle，但不会在未明确确认的情况下改写已确定的行程。

## 包含的技能

- `plan-travel-guide`：探索目的地、确定行程骨架、生成并校验可移植的 Travel Plan Bundle。
- `travel-maps-planner`：通过 Google Maps 或高德地图统一地点信息、核验路线。
- `trip-buddy`：统筹出发前的内容、行前准备、行程中的日间简报与经核实的异常事件。
- `travel-culture-card`、`travel-readiness`、`travel-day-brief`、`travel-disruption-watch`：Trip Buddy 所调用的四类专用内容技能。
- `travel-notify`：与平台无关的通知请求与幂等性边界。
- `travel-notify-feishu-cli`：可选的飞书 IM 机器人适配器，默认只 dry-run，不会发送消息。

## 可移植行程资料

一份完整保存的旅行计划默认由少量文件组成：

```text
<trip-id>/
├── trip.json
├── itinerary.md
├── planning.md
├── budget.csv
├── sources.md
└── buddy/              # 可选的 Trip Buddy 状态
```

Bundle 不绑定 Notion、日历、预订平台或某一个 Agent。外部系统只是适配层，不会变成第二份互相冲突的行程事实源。

## 地图服务

Google Maps 是面向全球行程的默认服务。高德地图适用于中国大陆的 POI 和路线；其国内 Web Service 使用 GCJ-02 坐标。高德海外服务需要单独开通，并使用 WGS84 坐标；适配器必须显式传入 `--international`，以防止不同坐标系被意外混用。

密钥只应保存在本地环境中：

```bash
export GOOGLE_MAPS_API_KEY=...
export AMAP_API_KEY=...
```

不要提交 API Key、收件人配置、预订编号、精确的私人住址，或真实行程导出文件。集成配置见 [docs/integrations.md](docs/integrations.md)。

## 通知

工具包核心只生成经过校验的通知请求，不会自行发送。飞书适配器要求：本机已配置 `lark-cli` 机器人、私有的收件人 profile 映射、明确的用户授权、`state: "sending"`，以及稳定的幂等键。文档发布与消息投递被刻意设计为两个独立的适配层。

## 多 Agent 打包方式

Skills 本体只维护一份，位于 `plugins/travel-toolkit/skills/`。不同平台只保留很薄的发现和元数据层：

```text
.agents/plugins/marketplace.json
.claude-plugin/marketplace.json
plugins/travel-toolkit/.codex-plugin/plugin.json
plugins/travel-toolkit/.claude-plugin/plugin.json
plugins/travel-toolkit/skills/
```

这样 Codex、Claude Code 和 Copilot CLI 使用的是同一套旅行工作流，不需要维护三份逻辑。

## 开发与校验

仓库内的 `examples/synthetic-city-break/` 是一份虚构的示例 Bundle。发布前可运行以下检查：

```bash
python3 /path/to/plugin-creator/scripts/validate_plugin.py plugins/travel-toolkit
python3 plugins/travel-toolkit/skills/plan-travel-guide/scripts/validate_trip.py examples/synthetic-city-break
python3 plugins/travel-toolkit/skills/travel-notify/scripts/validate_notification_request.py plugins/travel-toolkit/skills/travel-notify/references/notification-request.example.json
```

如果本机安装了 Claude Code，还可以校验 marketplace 与 plugin manifest：

```bash
claude plugin validate .
```

发布新版本前建议阅读 [docs/distribution.md](docs/distribution.md)。

## 许可证

Apache-2.0。本项目为独立软件，与 OpenAI、Anthropic、GitHub、Google、高德或飞书/Lark 没有隶属关系。
